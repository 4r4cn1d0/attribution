"""The stage-1 run kit's core (runkit/stage1-olmo/; B15 BUILD-CORE; brief notes/b15-brief.md §3-§7 with the lead's §8
defaults) on CPU, without RunPod, Hugging Face or GitHub: each job kind's numbers, the caps, guards and funding needs
against hand computations written in each test (never the kit's output); the W1-18 gate, the engine gates, the block
and seed tables, the edits by SHA-256, the regeneration link, the seal, the interleaving deal and the 4-job rule; and
the Gate B behaviour reused (requeue, confirm-stopped, defer, the stranded exception, stop evidence, the create price
limit, the guard's folders and lock, the secret scan). Every script runs from a copy of the kit in a temporary folder
(ROOT = tmp); every input is synthetic (no sealed file, row, prompt or answer is read); every fake token is built at
run time."""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import math
import os
import random
import re
import shutil
import string
import subprocess
import sys
from pathlib import Path

import pytest

KIT = Path(__file__).resolve().parents[1]
GBK = KIT.parent / "gate-b-olmo"
MODULES = ("stage1_rules", "gateb_mac", "plan_tool", "seal", "budget", "secret_scan", "host", "launch")

# the Gate A fixture's cap_projection (the values the Gate B kit's tests read by hand; synthetic file here)
E1, T = 4360.619162873324, 333.6683323532343
X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
Y = "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"
SENTINELS = ("0.7319284756", "SENTINEL-U-VALUE", "41.0613")      # synthetic outcome values in the sealed files
JUDGE_SENTINEL = 7777                                              # round 30: a synthetic HB/Granite count


def sha(path: Path) -> str:
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def quarter_up(seconds: float) -> float:
    return math.ceil(round(seconds / 900, 9)) / 4


def cents(x: float) -> float:          # half up, by hand (decimal string rounding)
    from decimal import Decimal, ROUND_HALF_UP
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def times_125(base: float) -> float:   # the frozen [D20] rule by hand: 1.25 x the rounded base, in decimal
    from decimal import Decimal
    return cents(float(Decimal(repr(base)) * Decimal("1.25")))


def fake_token() -> str:
    rng = random.Random(os.getpid())
    return "hf" + "_" + "".join(rng.choice(string.ascii_letters + string.digits) for _ in range(34))


def write_json(path: Path, obj) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=1, sort_keys=True) + "\n")
    return path


class World:
    """A copy of the kit at tmp/runkit/stage1-olmo (ROOT = tmp) with synthetic pins, sources and receipts."""

    def __init__(self, tmp: Path, monkeypatch):
        self.repo = tmp
        self.root = tmp / "runkit" / "stage1-olmo"
        shutil.copytree(KIT, self.root, ignore=shutil.ignore_patterns("__pycache__", "tests"))
        monkeypatch.syspath_prepend(str(self.root))
        for name in MODULES:
            monkeypatch.delitem(sys.modules, name, raising=False)
        self.mp = monkeypatch
        self.rules = importlib.import_module("stage1_rules")
        self.mac = importlib.import_module("gateb_mac")
        self.tool = importlib.import_module("plan_tool")
        self.seal = importlib.import_module("seal")
        r, mp = self.rules, monkeypatch
        reading = write_json(tmp / "stub" / "x.json", {}).parent / "reading_stub.py"
        reading.write_text("def compared_fields(environment, lock, policy):\n"
                           "    return {'lock_sha256': lock, **{k: environment.get(k) for k in sorted(environment)}}\n")
        mp.setattr(self.mac, "READING", reading)
        fx = write_json(tmp / r.GATE_A_FIXTURE, {"cap_projection": {"e1_upper_s": E1, "training_s": T}})
        mp.setattr(r, "PREREG_FIXTURE_SHA256", sha(fx))
        seal_out = tmp / Path(r.MAN_PATH).parent
        files = []
        for d in range(1, 6):
            e = write_json(seal_out / "edits" / f"r{d}.edit.json", {"counts": {"remove": 600}, "draw": d})
            files.append({"role": "edit", "family": "R", "draw": d, "arm": f"edit-r{d}",
                          "path": f"edits/r{d}.edit.json", "sha256": sha(e)})
        files += [{"role": "unit", "family": "unit", "unit": f"unit-{u}"} for u in range(8, 0, -1)]   # 3b: 8 groups
        mp.setattr(r, "MAN_SHA256", sha(write_json(tmp / r.MAN_PATH, {"files": files})))
        a1 = write_json(tmp / r.A1_EDIT["path"], {"counts": {"remove": 600}, "arm": "A1"})
        pin = {"path": r.A1_EDIT["path"], "sha256": sha(a1)}
        mp.setattr(r, "A1_EDIT", pin)
        mp.setattr(r, "MAN1_EDIT_ARMS", {"A1": pin})
        mp.setattr(r, "MAN1_SHA256", sha(write_json(tmp / r.MAN1_PATH, {"entries": [{**pin, "role": "sealed record"}]})))
        # the recipes: main's tree (engine X) holds REC, S and G; engine Y's frozen tree holds the same files and
        # B+Qi's, which is in Y's tree only (as in the repository); the same bytes in both trees, one pin per path
        self.y_tree = tmp / r.Y_TREE_DEFAULT
        for path in list(r.RECIPE_PINS):
            body = {"recipe": path}
            if path != r.RECIPE_BQI:
                write_json(tmp / path, body)
            mp.setitem(r.RECIPE_PINS, path, sha(write_json(self.y_tree / path, body)))
        for eng, ident in (("X", X), ("Y", Y)):
            write_json(self.root / "setup" / f"packed-stage1-{eng}" / "setup-receipt.json",
                       {"engine_sha256": ident, "sealed_files_sha256": "f" * 64})
        self.real = {name: getattr(self.tool, name) for name in ("recipe_sha", "recipe_training_identity",
                                                                 "recipe_sha_y", "recipe_training_identity_y")}
        self.calls = []                         # (engine, what, recipe path) of every recipe hash the kit asks for
        self.config = {"X": {}, "Y": {}}        # engine -> recipe path -> a config SHA-256 (tests set it)

        def config_sha(engine: str, path: str) -> str:
            self.calls.append((engine, "config", path))
            return self.config[engine].get(path, hashlib.sha256(path.encode()).hexdigest())

        mp.setattr(self.tool, "recipe_sha", lambda path: config_sha("X", path))
        mp.setattr(self.tool, "recipe_sha_y", lambda path: config_sha("Y", path))
        self.pools = {"plant": hashlib.sha256(b"plant pool (synthetic)").hexdigest(),
                      "decoy": hashlib.sha256(b"decoy pool (synthetic)").hexdigest(),
                      "s3_safe": hashlib.sha256(b"s3_safe pool (synthetic)").hexdigest()}
        two = {n: self.pools[n] for n in ("plant", "decoy")}
        mp.setattr(r, "D2_POOLS", two)
        filled = write_json(tmp / r.D2_POOL_PINS["path"], {"pools": {n: {"sha256": v, "items": 1} for n, v in two.items()}})
        req8 = write_json(tmp / r.D2_REQ8_RECORD["path"], {"kind": "stage1 plant record", "pools": {
            n: {"sha256": v, "items": 1} for n, v in two.items()}, "full_files": {f"{n}.pool.json": v for n, v in two.items()}})
        spool = write_json(tmp / r.S_POOL_RECORD["path"], {"kind": "stage1 s-pool record", "s3_pool": {
            "sha256": self.pools["s3_safe"]}, "full_files": {"s3_safe.pool.json": self.pools["s3_safe"]}})
        for name, f in (("D2_POOL_PINS", filled), ("D2_REQ8_RECORD", req8), ("S_POOL_RECORD", spool)):
            mp.setattr(r, name, {"path": getattr(r, name)["path"], "sha256": sha(f)})
        self.identity = {}                      # recipe path -> a training identity other than the pin (tests set it)
        self.identity_y = {}                    # the same under engine Y's code
        mp.setattr(self.tool, "recipe_training_identity",
                   lambda path: self.identity.get(path, getattr(r, "TRAINING_IDENTITY", "")), raising=False)

        def identity_y(path: str) -> str:
            self.calls.append(("Y", "identity", path))
            return self.identity_y.get(path, r.TRAINING_IDENTITY)

        mp.setattr(self.tool, "recipe_training_identity_y", identity_y)
        self.n = 0
        self.auto_plan = True                   # round 3a: record test_plan() before the group's first init
        self.group_b_funding = None             # round 32 (K4): block B's group's one funding record (its path)

    # ----- inputs -----
    def record(self, obj) -> tuple[str, str]:
        self.n += 1
        p = write_json(self.repo / "records" / f"r{self.n}.json", obj)
        return str(p), sha(p)

    def funding(self, blk: str, amount: float, **change) -> str:
        rec = {"block": blk, "amount_usd": amount, "utc": "2026-10-23T12:00:00Z", "source": "user RunPod top-up",
               "user_words": "synthetic words for this test", "recorded_by": "test", **change}
        return self.record(rec)[0]

    def jobs(self, launches, **extra) -> str:
        return self.record({"launches": launches, **extra})[0]

    def test_plan(self) -> tuple[str, str]:
        """Round 3a: a broad block-A plan for the tests that are not about the plan itself (the kit's default doc
        with every dealt pod in one arm launch, so any split of the deal fits, and two LN-12 pods: the a0 pairs with
        theta0, the R pairs), recorded by the kit's own CLI function."""
        plan = self.tool.load()
        code = self.tool.plan_code_now(plan)
        layout = self.tool.LN12_LAYOUT                 # round 3b: the a0 pairs, LN-15e and theta0; the R pairs and c0
        self.tool.LN12_LAYOUT = (("a0", "rescore", "theta0"), ("R", "c0"))
        try:
            doc, _ = self.tool.default_block_a_plan(plan, (self.tool.deal_pod_count(code),), recorded_by="test")
        finally:
            self.tool.LN12_LAYOUT = layout
        p, h = self.record(doc)
        self.tool.record_block_a_plan(p, h)
        return p, h

    def init(self, block: str, launches, amount: float = 500.0, dry_run: bool = False, group_jobs=None, **extra):
        """init-block BLOCK by the kit's own function. Round 32 (K4): block B's group has one funding record, so a
        later init of the group reuses the first one's file; certify's init (block B not planned) counts block B's
        jobs (``group_jobs``, default the deal's 6 pods in one launch, B_DEAL)."""
        plan = self.tool.load()
        if self.auto_plan and block in ("S1-0", "cert", "A") and plan["records"].get("block_a_plan") is None and \
                not any(b in plan["blocks"] for b in ("S1-0", "cert", "A")):
            self.test_plan()
        group = self.rules.FUNDING_BLOCK[block]
        planned_b = any(self.rules.FUNDING_BLOCK.get(b) == "B" for b in plan["blocks"])
        funding = self.group_b_funding if group == "B" and planned_b else self.funding(group, amount)
        if group == "B" and not planned_b:
            self.group_b_funding = funding
        if block == "certify" and group_jobs is None and "B" not in plan["blocks"]:
            group_jobs = {"B": B_DEAL}
        given = [f"{part}={self.jobs(launches_)}" for part, launches_ in (group_jobs or {}).items()]
        return self.tool.init_block(argparse.Namespace(block=block, jobs=self.jobs(launches, **extra),
                                                       funding=funding, dry_run=dry_run, group_jobs=given or None))

    def plan(self) -> dict:
        return self.mac.load_plan()

    def not_run(self, jobs=None, reason: str = "synthetic: this test does not run them") -> dict:
        """Round 3c (VP3b-3): the lead's not-run decision for ``jobs`` (default: every job of block A the kit lists as
        open), recorded with the kit's own CLI function."""
        jobs = list(self.tool.block_a_open(self.plan())) if jobs is None else list(jobs)
        p, h = self.record({"kind": "stage1 block-a not-run decision", "jobs": jobs, "reason": reason,
                            "utc": "2026-10-24T08:00:00Z", "recorded_by": "test"})
        return self.tool.record_block_a_not_run(p, h)

    def plan_or_none(self) -> dict | None:
        return self.mac.load_plan() if self.mac.PLAN.exists() else None

    def done(self, host: str, statuses=None, outputs=None, engine=None, gate: str = "passed") -> None:
        """A pulled JOB-DONE.json for HOST: unit kinds get a COMPLETE.json; unit-free kinds an output file. Round 32
        (K3): a complete b10_certify job names B10's gate (``gate``) with its comparison file among its outputs, as the
        runner records it; a failed gate leaves the certify unit job-I/evals/<seed>-certify only."""
        plan = self.plan()
        tree = self.root / "retrieved" / host / "tree"
        jobs = []
        for i, job in enumerate(plan["hosts"][host]["jobs"]):
            status = (statuses or {}).get(i, "complete")
            eng = engine or job["engine"]
            r = {"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "status": status,
                 "engine": eng, "engine_sha256": {"X": X, "Y": Y}[eng]}
            if status == "complete" and job["kind"] == "b10_certify":
                rel = f"job-{i}/evals/{job['seed']}-certify.compare.json"
                verdict = "pass" if gate == "passed" else "fail"
                r.update(certification_gate=gate, outputs={rel: sha(write_json(tree / rel, {"verdict": verdict}))})
            if status == "complete" and job["kind"] == "b10_certify" and gate == "failed":
                unit = f"job-{i}/evals/{job['seed']}-certify"
                r.update(unit=unit, complete_sha256=sha(write_json(tree / unit / "COMPLETE.json", {"i": i, "h": host})))
                r["units"] = [{"unit": unit, "complete_sha256": r["complete_sha256"], "verify_exit": 0}]
            elif status == "complete":
                if job["kind"] in self.rules.UNITLESS_KINDS:
                    rel = f"job-{i}/{job['kind']}.json"
                    body = (outputs or {}).get(i, {"kind": job["kind"], "value": SENTINELS[1]})
                    r["outputs"] = {rel: sha(write_json(tree / rel, body))}
                else:
                    unit = f"units/job-{i}"
                    write_json(tree / unit / "eval" / "e1" / "summary.json", {"u": float(SENTINELS[0])})
                    write_json(tree / unit / "cost-ledger.json", {"stages": {"training": 100.0}})
                    r.update(unit=unit, complete_sha256=sha(write_json(tree / unit / "COMPLETE.json", {"i": i, "h": host})))
                    if job["kind"] == "a0_arm" and plan["hosts"][host]["block"] == "B":   # round 32 (K6), block B
                        rel = f"job-{i}/a0-adapter-fingerprint.json"
                        body = {"kind": "stage1 a0 adapter fingerprint", "version": 1, "job": i, "arm": "a0",
                                "seed": job["seed"], "unit": unit, "complete_sha256": r["complete_sha256"],
                                "checkpoints": {"e1": hashlib.sha256(f"e1 {host} {i}".encode()).hexdigest(), "q": None},
                                "identity": {"manifest_sha256": "m" * 64, "training_identity": "t" * 64}}
                        r["outputs"] = {rel: sha(write_json(tree / rel, body))}
                    if job["kind"] in ("b10_certify", "ref_eval", "safe_lora"):   # the runner: one unit per point
                        r["units"] = [{"unit": unit, "complete_sha256": r["complete_sha256"], "verify_exit": 0}]
                        for k, point in enumerate((job.get("points") or [])[1:], 1):
                            extra = f"units/job-{i}-p{k}"
                            r["units"].append({"unit": extra, "verify_exit": 0, "complete_sha256": sha(write_json(
                                tree / extra / "COMPLETE.json", {"i": i, "h": host, "point": point}))})
            jobs.append(r)
        write_json(tree / "JOB-DONE.json", {"host": host, "jobs": jobs})
        self.tool.record_done(host)

    # ----- round 30: the judge files and the judge-completion record (addendum §30; R2, R3) -----
    def judge_units(self, block: str = "A") -> list[str]:
        """By hand: the units BLOCK's judge files must cover: the COMPLETE.json SHA-256 plan.json records for every
        complete arm and a0_arm job of the block (pulled), then the block's 7 pinned re-judged units (block A)."""
        plan = self.plan()
        new = [j["complete_sha256"] for n, h in sorted(plan["hosts"].items()) if h["block"] == block
               for j in h["jobs"] if j["kind"] in ("arm", "a0_arm") and j.get("status") == "complete"
               and j.get("pulled") is not False]
        return new + [p["complete_sha256"] for p in self.rules.REJUDGED_PINS.get(block, ())]

    def file_judges(self, block: str = "A", judges=("harmbench", "granite"), units=None, entry=None,
                    result=None) -> tuple[str, str]:
        """Gate B's layout for BLOCK's judges, all synthetic: one judge file per judge and unit in judges/BLOCK/
        (holding the sentinel count JUDGE_SENTINEL), judge-files-index.json (Gate B's index, version 2), each launch's
        judge-pod-result.json and fetched run record under tmp/judge-pod/TAG (the verified units' counts are the
        sentinel), and the lead's judge-completion record naming them. ``entry``/``result``: {judge: {key: value}}
        changes. Returns the record's path and SHA-256 (record_judges takes them)."""
        folder = self.root / "judges" / block
        units = self.judge_units(block) if units is None else units
        names = {"harmbench": "cais/HarmBench-Mistral-7b-val-cls", "granite": "granite-guardian-3.3-8b"}
        entries = []
        for key in judges:
            for i, c in enumerate(units):
                name = f"{key}--host{i}--unit{i}--{c[:12]}.json"
                p = write_json(folder / name, {"greedy": {"n": 200, "harm": JUDGE_SENTINEL, "unparsed": 0}})
                entries.append({"file": name, "sha256": sha(p), "judge": names[key], "arm": f"arm-{i}", "seed": 1102,
                                "host": f"host{i}", "unit": f"round1/unit{i}", "target": "e1",
                                "completed_utc": "2026-10-26T00:00:00+00:00", "complete_sha256": c})
        index = write_json(folder / "judge-files-index.json", {"kind": "gate-b judge files index", "version": 2,
                                                                 "complete_allowlist": [],
                                                                 "files": sorted(entries, key=lambda e: e["file"])})
        record = {"kind": "stage1 judge completion record", "block": block, "judges": {}, "index_sha256": sha(index),
                  "utc": "2026-10-27T09:00:00Z", "recorded_by": "test"}
        for key in judges:
            tag = f"s1{block.lower()}-{key}-1"
            d = self.repo / "tmp" / "judge-pod" / tag
            run_record = write_json(d / "fetched" / "out" / "run-record.json", {"device": "cuda", "judge": key})
            per = 800 if key == "harmbench" else 200
            body = {"kind": "judge-pod result", "version": 2, "tag": tag, "exit": 0,
                    "bundle_sha256": hashlib.sha256(tag.encode()).hexdigest(),
                    "fetched": {"out/run-record.json": sha(run_record)},
                    "stop": {"confirmed": True, "desiredStatus": "EXITED", "utc": "2026-10-27T08:40:00+00:00"},
                    "verification": {"complete": True, "judged": per * len(units), "records": per * len(units),
                                     "units": [{"unit": f"host{i}/u", "complete_sha256": c,
                                                "greedy": {"n": 200, "judged": 200, "yes": JUDGE_SENTINEL,
                                                           "unparsed": 0}} for i, c in enumerate(units)]}}
            if key == "granite":
                body["judge"] = "granite"
                body["verification"]["known_answers"] = {"enabled": True, "passed": True, "pod_yes": JUDGE_SENTINEL}
            for k, v in (result or {}).get(key, {}).items():
                body[k] = v
            res = write_json(d / "judge-pod-result.json", body)
            e = {"tag": tag, "result_sha256": sha(res), "run_record_sha256": sha(run_record),
                 "bundle_sha256": body["bundle_sha256"], "exit": 0, "judged": per * len(units), "complete": True}
            if key == "granite":
                e["known_answer_passed"] = True
            e.update((entry or {}).get(key, {}))
            record["judges"][key] = e
        return self.record(record)

    def old_seal(self, block: str = "A") -> dict:
        """The block sealed as the old seal.py (before round 30) sealed it: every file of the block's pulled trees and
        every file under judges/BLOCK/, by path and SHA-256; its SHA-256 in plan.json (block A is sealed so before
        round 30 lands; the new seal.py needs the judge-completion record first)."""
        plan = self.plan()
        files = []
        for host in sorted(n for n, h in plan["hosts"].items() if h["block"] == block):
            tree = self.root / "retrieved" / host / "tree"
            files += [{"host": host, "path": p.relative_to(tree).as_posix(), "sha256": sha(p), "class": "sealed"}
                      for p in sorted(tree.rglob("*")) if p.is_file()]
        folder = self.root / "judges" / block
        files += [{"host": f"judges/{block}", "path": p.relative_to(folder).as_posix(), "sha256": sha(p),
                   "class": "sealed"} for p in sorted(folder.rglob("*")) if p.is_file()]
        out = write_json(self.root / "seals" / f"block-{block}.json", {"kind": "stage1 block seal", "version": 1,
                                                                       "block": block, "files": files})
        plan["seals"][block] = {"path": f"seals/block-{block}.json", "sha256": sha(out), "files": len(files),
                                "sealed": len(files), "readable": 0}
        self.mac.save_plan(plan)
        return plan["seals"][block]

    # ----- the usual path -----
    def s10(self, branch: str = "128") -> None:
        self.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
        self.done("s10-1", outputs={0: {"kind": "stage1 over-refusal checks",
                                        "truncation_check": {"units": 11, "pass": branch == "128"}}})
        out = self.root / "retrieved" / "s10-1" / "tree" / "job-0" / "w1_18.json"
        p, h = self.record({"kind": "stage1 w1-18 branch record", "branch": branch, "host": "s10-1",
                            "output_path": "job-0/w1_18.json", "output_sha256": sha(out), "focus_commit": "abc1234",
                            "utc": "2026-10-23T12:00:00Z", "recorded_by": "test"})
        self.tool.record_branch(p, h)

    def gateb_final(self, **change) -> tuple[str, str]:
        """A synthetic Gate B measurements --final output, pinned as rules.GATEB_FINAL_SHA256 for this test."""
        p, h = self.record({"kind": "gate-b reading", "phase": "measurements", "version": 1,
                            "result": {"final": True, "code": "REPORTED", "u": SENTINELS[0]}, **change})
        self.mp.setattr(self.rules, "GATEB_FINAL_SHA256", h, raising=False)
        return p, h

    def verdict(self, sigma=3.9, **change) -> tuple[str, str]:
        """A synthetic Gate B verdict file (kind 'gate-b reading', phase 'verdict', the one field), pinned as
        rules.GATEB_VERDICT for this test."""
        body = {"kind": "gate-b reading", "phase": "verdict", "version": 1,
                "result": {"code": "SYNTHETIC", "readings": {"plain": {"sigma_hat_pp": sigma, "D_pp": SENTINELS[2]}}},
                **change}
        p, h = self.record(body)
        # the pin names this file under ROOT (= self.repo), as rules.GATEB_VERDICT names the committed file
        self.mp.setattr(self.rules, "GATEB_VERDICT", {"path": str(Path(p).relative_to(self.repo)), "sha256": h})
        return p, h

    def gateb(self, sigma: float = 3.9) -> None:
        p, h = self.gateb_final()
        self.tool.record_simple("gateb_final", p, h)
        self.tool.record_simple("plan_ab", *self.verdict(sigma))

    def sealed(self, arms=("L1", "H1", "S1", "S3", "S4"), draws=(6, 7, 8, 9, 10)) -> str:
        edits = []
        for a in arms:
            e = write_json(self.repo / "tmp" / "sealed" / f"{a}.edit.json", {"arm": a})
            edits.append({"arm": a, "path": f"tmp/sealed/{a}.edit.json", "sha256": sha(e)})
        for d in draws:
            e = write_json(self.repo / "tmp" / "sealed" / f"r{d}.edit.json", {"draw": d})
            edits.append({"arm": "R", "draw": d, "path": f"tmp/sealed/r{d}.edit.json", "sha256": sha(e)})
        p, h = self.record({"kind": "stage1 sealed edits", "edits": edits})
        self.tool.record_simple("sealed", p, h)
        return h

    def thresholds(self) -> tuple[str, str]:
        """C2's thresholds record written by the kit's own CLI (addendum §22 point 1 exactly), then recorded."""
        self.n += 1
        (self.repo / "records").mkdir(exist_ok=True)
        out = self.tool.write_thresholds(str(self.repo / "records" / f"thresholds-{self.n}.json"), "test")
        self.tool.record_simple("thresholds", out["path"], out["sha256"])
        return out["path"], out["sha256"]

    def c3_files(self, **change) -> dict:
        """A synthetic C3 subsample file (hashed only) and the writer's record naming it (write_c3_subsample.py's
        schema), returned as the lead's C3 pin record body."""
        self.n += 1
        sub = write_json(self.repo / "tmp" / "c3" / f"sub{self.n}.json", {"synthetic": "subsample", "n": self.n})
        h, prep = sha(sub), self.rules.PREPARED_MANIFESTS["prepared-kt-dolly-olmo2"]
        rec = {"kind": "stage1 c3 subsample record", "version": 1, "role": "development",
               "subsample": {"file_sha256": h, "bank": "subsample-" + h, "items": 16, "counts": {"k": 16}},
               "source": {"bank": "dev", "manifest_sha256": prep, "bank_file_sha256": "b" * 64},
               "draw": {"label": "c3-dev-first-16-in-bank-order",
                        "script_sha256": "c31bdb1bd7e69010fd6dec0392cb2d440db5344337d0f778057d1332ff460026",
                        "settings_sha256": "a8547e2dcd27cbbdbed48eef3cb636a4503a6f3d6101123080b26b9baa1cfc60"},
               "prepared_manifest_sha256": prep}
        for key, value in change.items():
            rec[key] = value
        r = write_json(self.repo / "records" / f"c3-record-{self.n}.json", rec)
        self.mp.setattr(self.rules, "C3_RECORD", {"path": f"records/c3-record-{self.n}.json", "sha256": sha(r)})
        return {"kind": "stage1 c3 subsample pin", "utc": "2026-10-23T17:00:00Z", "recorded_by": "test",
                "subsample": {"path": f"tmp/c3/sub{self.n}.json", "sha256": h},
                "record": {"path": str(r), "sha256": sha(r)}}

    def pin_c3_record(self, body: dict) -> None:
        """Round 3b: pin rules.C3_RECORD to the body's (edited) writer record, as the test means to test its content."""
        rel = str(Path(body["record"]["path"]).relative_to(self.repo))
        self.mp.setattr(self.rules, "C3_RECORD", {"path": rel, "sha256": sha(self.repo / rel)})

    def c3(self, **change) -> dict:
        self.tool.record_simple("c3", *self.record(self.c3_files(**change)))
        return self.plan()["records"]["c3"]

    def cert_records(self) -> None:
        rec = self.tool.load()["records"]
        if rec.get("c3") is None and rec.get("c3_fallback") is None:
            self.c3()
        if rec.get("thresholds") is None:
            self.thresholds()

    def certificate(self, passed: bool = True) -> None:
        self.cert_records()
        self.init("cert", [{"hosts": [CERT_POD]}])
        self.done("cert-1")
        ev = self.root / "retrieved" / "cert-1" / "tree" / "units" / "job-0" / "COMPLETE.json"
        self.tool.record_simple("certificate", *self.record({
            "kind": "stage1 x-y certificate", "pass": passed, "host": "cert-1", "utc": "u", "recorded_by": "t",
            "evidence": [{"path": "units/job-0/COMPLETE.json", "sha256": sha(ev)}]}))


CERT_POD = [{"kind": "cert_c1", "arm": "R", "seed": 1101}, {"kind": "cert_c2", "arm": "bqi", "seed": 1101},
            {"kind": "cert_c3"}]                 # round 3b: c0 moved to block A's LN-12 pod (addendum §26)
C0 = {"kind": "c0", "arm": "R", "seed": 1101}
DIAG_POD = [{"kind": "untuned_answers"}, {"kind": "rep_pass"}, {"kind": "l1_scan"}, {"kind": "classifier"}]
A_LAUNCHES = [{"deal": [0, 1, 2]}, {"deal": [3, 4]}]


@pytest.fixture
def w(tmp_path, monkeypatch):
    world = World(tmp_path, monkeypatch)
    yield world
    for name in MODULES:
        sys.modules.pop(name, None)


def arm_upper(steps: int, o: float) -> float:
    return E1 + T * steps / 38 + 1000 + 900 + o


# ===== Caps and money ==============================================================================================


def test_each_job_kinds_numbers_under_branch_full_by_hand(w):
    r, fx = w.rules, {"e1_upper_s": E1, "training_s": T}
    o = 1517.0                                                      # 0.517 FRE x 2,934 s, as the brief rounds it
    hand = {  # kind: (steps, points, recipe, upper_s, measured_upper_s)
        "w1_18": (None, None, None, 1800.0, 1800.0),
        "regenerate": (38, None, "S", T + 1900, 540.0),
        "o_only": (None, None, None, 1.25 * o + 1900, 1.25 * o),
        "rep_pass": (None, None, None, 5400.0, 3600.0),
        "untuned_answers": (None, None, None, 1.5 * 2100 * 3.6, 2100 * 3.6),
        "l1_scan": (None, None, None, 5400.0, 3600.0),
        "classifier": (None, None, None, 1.5 * 2012, 2012.0),
        "arm": (33, None, "S", E1 + T * 33 / 38 + 1900 + o, 52 * 60 + o),
        "a0_arm": (38, None, "S", E1 + T + 1900 + o, 52 * 60 + o),
        "c0": (33, None, "S", 2400 + 1900, 2400.0),
        "cert_c1": (33, None, "S", E1 + T * 33 / 38 + 1900, 3120.0),
        "cert_c2": (38, None, "bqi", (T + 1900) * 1.5, 540 * 1.5),
        "cert_c3": (None, None, None, 1800.0, 1800.0),
        "b10_certify": (None, ["certify", "scale:0"], "B", 540 + 2 * 0.93 * 2934 + 1900, 540 + 2 * 0.93 * 2934),
        "ref_eval": (None, ["scale:0.9", "scale:0.75", "scale:0.5"], "B", 540 + 3 * (0.93 * 2934 + o) + 1900,
                     540 + 3 * (0.93 * 2934 + o)),
        "safe_lora": (None, ["default"], "B", 540 + 0.03 * 2934 + 600 + 0.93 * 2934 + o + 1900,
                      540 + 0.03 * 2934 + 600 + 0.93 * 2934 + o),
        "ref_train": (38, None, "G", E1 + T + 1900 + o, 3120 + o),
        "retrain": (38, None, "S", T + 1900, 540.0),                # LN-15e (round 3b): Gate B's retrain rule
        "a1_rescore": (None, None, "S", 1.5 * 3.04 * 3600, 3.04 * 3600),   # Gate B's measured diagnostics, x 1.5
    }
    assert set(hand) | {"transfer_report"} == set(r.KINDS)
    for kind, (steps, points, recipe, up, measured) in hand.items():
        job = r.job_record(kind, None, None, None, steps, fx, branch="full", points=points, recipe=recipe)
        assert job["upper_s"] == pytest.approx(up, abs=1e-6), kind
        assert job["start_requirement_s"] == pytest.approx(up + 1800, abs=1e-6), kind
        assert job["measured_upper_s"] == pytest.approx(measured, abs=1e-6) == job["spend_upper_s"], kind
    bqi = r.job_record("ref_train", "bqi", 1102, None, 38, fx, branch="full", recipe="bqi", engine="Y")
    assert bqi["upper_s"] == pytest.approx(E1 + 1.5 * T + 1900 + o) and bqi["measured_upper_s"] == pytest.approx(3120 + o + 0.5 * T)
    assert r.job_record("arm", "A1", 1102, None, 33, fx)["start_requirement_s"] / 3600 == pytest.approx(2.7409, abs=1e-4)
    assert (52 * 60 + o) / 60 == pytest.approx(77.283, abs=1e-3)       # brief §5.4: 77.3 min
    with pytest.raises(ValueError, match="Branch 128 only"):
        r.job_record("transfer_report", "theta0", None, None, None, fx, branch="full")


def test_the_branch_128_numbers_by_hand(w):
    r, fx = w.rules, {"e1_upper_s": E1, "training_s": T}
    o = 1024.0                                                      # 1,517 x 27/40 rounded up (E, UNVERIFIED)
    assert math.ceil(1517 * 27 / 40) == o == r.O500_S["128"] and r.O500_S["full"] == 1517.0
    arm = r.job_record("arm", "A1", 1102, None, 33, fx, branch="128")
    assert arm["upper_s"] == pytest.approx(arm_upper(33, o)) and arm["measured_upper_s"] == 3120 + o
    assert r.job_record("o_only", "a0", 1101, None, None, fx, branch="128")["measured_upper_s"] == 1.25 * o
    tr = r.job_record("transfer_report", "theta0", None, None, None, fx, branch="128")
    assert tr["measured_upper_s"] == 1408.0 and tr["upper_s"] == 1408.0 + 1900       # $0.7 at $1.79/h = 1,408 s
    assert round(0.7 / 1.79 * 3600) == 1408
    assert r.job_record("w1_18", None, None, None, None, fx, branch="128")["upper_s"] == 1800.0   # branch-free
    assert r.job_record("cert_c1", "R", 1101, None, 33, fx, branch="128")["upper_s"] == pytest.approx(arm_upper(33, 0))


@pytest.mark.parametrize("branch, o, cap, guard, spend", [("full", 1517.0, 7.5, 19.88, 10.48),
                                                          ("128", 1024.0, 7.0, 18.95, 9.49)])
def test_a_four_arm_pod_cap_guard_and_spend_by_hand(w, branch, o, cap, guard, spend):
    r, fx = w.rules, {"e1_upper_s": E1, "training_s": T}
    jobs = [r.job_record("arm", a, 1102, None, 33, fx, branch=branch) for a in ("A1", "L1", "H1", "R")]
    worst = 2520 + 3 * (3120 + o) + arm_upper(33, o) + 1800        # the fourth job binds
    assert quarter_up(worst) == cap == r.cap_hours(jobs)
    assert cents(6 + cap * 1.85) == guard == cents(r.guard_usd(cap))
    assert cents((2520 + 4 * (3120 + o)) / 3600 * 1.79) == spend == cents(r.pod_spend_usd(jobs))
    mixed = jobs[:3] + [r.job_record("a0_arm", "a0", 1104, None, 38, fx, branch=branch)]
    assert r.cap_hours(mixed) == quarter_up(2520 + 3 * (3120 + o) + arm_upper(38, o) + 1800) == cap
    rounded_down = math.floor(round(worst / 900, 9)) / 4
    assert rounded_down < cap                                       # the cap is rounded up, never down


def test_block_a_funding_needs_for_the_launch_splits_by_hand(w):
    """Five 4-arm pods (cap 7.5 h, spend (2,520 + 4 x 4,637) / 3,600 x 1.79 each), the [D20] rule: base = the largest
    term rounded to the cent, need = 1.25 x base rounded to the cent."""
    r = w.rules
    s = (2520 + 4 * 4637) / 3600 * 1.79                           # $10.4754777...
    pod = {"cap_hours": 7.5, "spend_usd": s}
    one = cents(6 + 1.85 * 37.5)                                   # 75.375 -> 75.38
    three_two = cents(3 * s + 6 + 1.85 * 15)                       # 65.1764 -> 65.18
    two_two_one = cents(4 * s + 6 + 1.85 * 7.5)                    # 61.7769 -> 61.78
    assert (one, three_two, two_two_one) == (75.38, 65.18, 61.78)
    expected = {(5,): 94.23, (3, 2): 81.48, (2, 2, 1): 77.23, (1, 1, 1, 1, 1): 77.23}
    for split, need in expected.items():
        base = {1: one, 2: three_two}.get(len(split), two_two_one)
        assert cents(base * 1.25) == need
        got = r.funding_need_usd([[pod] * n for n in split], 1.25)
        assert (got["base_need_usd"], got["need_usd"]) == (base, need), split
        assert got["contingency_usd"] == cents(need - base)


def test_the_briefs_cents_come_from_rounding_each_pods_spend_first(w):
    """Brief §5.4 gives $94.22 / $81.49 / $77.25. Rounding each pod's spend to $10.48 before summing gives $81.49 and
    $77.25 (base $65.19 and $61.80); $94.22 is 1.25 x the unrounded $75.375. The kit keeps Gate B's [D20] rule
    unchanged (brief §5.2), so its needs are $94.23 / $81.48 / $77.23 (reported to the lead as an open item)."""
    assert cents(cents(3 * 10.48 + 6 + 27.75) * 1.25) == 81.49 and cents(3 * 10.48 + 6 + 27.75) == 65.19
    assert cents(cents(4 * 10.48 + 6 + 13.875) * 1.25) == 77.25 and cents(4 * 10.48 + 6 + 13.875) == 61.80
    assert cents(1.25 * 75.375) == 94.22 and cents(1.25 * cents(75.375)) == 94.23
    pod = {"cap_hours": 7.5, "spend_usd": 10.48}
    assert w.rules.funding_need_usd([[pod] * 3, [pod] * 2], 1.25)["need_usd"] == 81.49


def test_a_pod_uses_the_larger_of_the_plan_and_its_projection_with_the_o500_term(w):
    r, fx = w.rules, {"e1_upper_s": E1, "training_s": T}
    job = r.job_record("arm", "A1", 1102, None, 33, fx)
    slow = {"e1_upper_s": E1, "training_s": T, "overhead_s": 0, "margin_s": 0, "o500_s": 3000.0}
    assert r.own_requirement_s(job, slow) == pytest.approx(E1 + T * 33 / 38 + 1900 + 3000 + 1800)
    fast = {**slow, "o500_s": 10.0}
    assert r.own_requirement_s(job, fast) == job["start_requirement_s"]
    assert r.gate(None, 1.0) is False and r.gate(5.0, 5.0) is True and r.gate(4.9, 5.0) is False


def test_a_regeneration_and_its_o_only_pass_start_together(w):
    r, fx = w.rules, {"e1_upper_s": E1, "training_s": T}
    jobs = [r.job_record("regenerate", "a0", 1101, None, 38, fx),
            r.job_record("o_only", "a0", 1101, None, None, fx, regen_source=0)]
    o_start = 1.25 * 1517 + 1900 + 1800
    assert r.requirements(jobs) == [pytest.approx(540 + o_start), pytest.approx(o_start)]
    assert r.cap_hours(jobs) == quarter_up(2520 + 540 + o_start) == 2.5


def test_re_runs_are_paid_from_the_contingency_in_launch_order(w):
    tool, r = w.tool, w.rules
    job = r.job_record("arm", "A1", 1102, None, 33, {"e1_upper_s": E1, "training_s": T})
    plain = 4637 / 3600 * 1.79                                     # $2.3056
    new_pod = (4637 + 2520) / 3600 * 1.79                         # $3.5586 with the 42 min
    plan = {"contingency": {"A": {"usd": 6.0, "remaining_usd": 6.0, "spent": [], "not_rerun": []}}}
    paid = tool.pay_reruns(plan, [dict(job), dict(job), dict(job)], True, "test", "A")
    assert len(paid) == 2 and [round(s["cost_usd"], 4) for s in plan["contingency"]["A"]["spent"]] == [
        round(new_pod, 4), round(plain, 4)]
    assert plan["contingency"]["A"]["remaining_usd"] == pytest.approx(6.0 - new_pod - plain)
    assert len(plan["contingency"]["A"]["not_rerun"]) == 1
    assert r.unit_rerun_cost_usd([job, job], True) == pytest.approx(new_pod + plain)


def test_the_need_and_the_funding_rule_at_init(w):
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    group_before = w.plan()["blocks"]["S1-0"]["need_launches"]
    assert group_before == [[{"cap_hours": 1.75, "spend_usd": pytest.approx((2520 + 1800) / 3600 * 1.79)}]]
    out = w.init("A", A_LAUNCHES, dry_run=True)
    s = (2520 + 4 * 4637) / 3600 * 1.79
    s10 = (2520 + 1800) / 3600 * 1.79                              # W1-18's pod: 42 min + 0.5 h
    base = cents(max(6 + 1.85 * 1.75, s10 + 6 + 1.85 * 22.5, s10 + 3 * s + 6 + 1.85 * 15))
    assert out["base_need_usd"] == base and out["need_usd"] == cents(base * 1.25) and out["dry_run"]
    assert not any(p.startswith("a-") for p in w.plan()["hosts"]) and "A" not in w.plan()["blocks"]
    with pytest.raises(SystemExit, match="below the need"):
        w.init("A", A_LAUNCHES, amount=out["need_usd"] - 0.01)
    w.init("A", A_LAUNCHES, amount=out["need_usd"])                 # exactly the need is enough (>=)
    plan = w.plan()
    assert plan["blocks"]["A"]["need"]["need_usd"] == out["need_usd"]
    assert plan["contingency"]["A"]["usd"] == cents(out["need_usd"] - base)


@pytest.mark.parametrize("change, match", [({"source": "gate B balance"}, "source"), ({"block": "B"}, "block 'B'"),
                                           ({"user_words": " "}, "user's words"), ({"amount_usd": float("nan")}, "finite"),
                                           ({"amount_usd": True}, "finite"), ({"utc": "yesterday"}, "UTC"),
                                           ({"recorded_by": ""}, "recorded_by")])
def test_a_funding_record_that_breaks_the_users_rule_refuses(w, change, match):
    path = w.funding("A", 500.0, **change)
    with pytest.raises(SystemExit, match=match):
        w.tool.init_block(argparse.Namespace(block="S1-0", jobs=w.jobs([{"hosts": [[{"kind": "w1_18"}]]}]),
                                             funding=path, dry_run=False))
    with pytest.raises(SystemExit, match="needs --funding"):
        w.tool.init_block(argparse.Namespace(block="S1-0", jobs=w.jobs([{"hosts": [[{"kind": "w1_18"}]]}]),
                                             funding=None, dry_run=False))
    assert not (w.root / "plan.json").exists()


def test_a_funding_record_under_the_users_start_from_the_balance_rule(w, tmp_path):
    """Addendum §36: a funding record without a covering top-up is accepted only with the user's decision record,
    re-hashed at every use; a record with any other source still refuses."""
    dec = tmp_path / "decision.json"
    dec.write_text(json.dumps({"kind": w.tool.FUNDING_RULE_KIND, "user_words": "start it now"}))
    named = {"path": str(dec), "sha256": hashlib.sha256(dec.read_bytes()).hexdigest()}
    path = w.funding("A", 500.0, source=w.tool.FUNDING_SOURCE_RULE, user_decision=named)
    rec = w.tool.funding_record(path, "A")
    assert rec["source"] == w.tool.FUNDING_SOURCE_RULE and rec["user_decision"] == named
    assert "user_decision" not in w.tool.funding_record(w.funding("A", 500.0), "A")
    other = tmp_path / "other.json"
    other.write_text(json.dumps({"kind": "something else", "user_words": "x"}))
    empty = tmp_path / "empty.json"
    empty.write_text(json.dumps({"kind": w.tool.FUNDING_RULE_KIND, "user_words": " "}))
    for change, match in (({}, "path, sha256"),
                          ({"user_decision": {"path": str(dec), "sha256": "0" * 64}}, "differs"),
                          ({"user_decision": {"path": str(tmp_path / "gone.json"), "sha256": named["sha256"]}}, "differs"),
                          ({"user_decision": {"path": str(other), "sha256": hashlib.sha256(other.read_bytes()).hexdigest()}},
                           "not a"),
                          ({"user_decision": {"path": str(empty), "sha256": hashlib.sha256(empty.read_bytes()).hexdigest()}},
                           "not a")):
        bad = w.funding("A", 500.0, source=w.tool.FUNDING_SOURCE_RULE, **change)
        with pytest.raises(SystemExit, match=match):
            w.tool.funding_record(bad, "A")
    dec.write_text(json.dumps({"kind": w.tool.FUNDING_RULE_KIND, "user_words": "changed after recording"}))
    with pytest.raises(SystemExit, match="differs"):                   # re-hashed at every use
        w.tool.funding_record(path, "A")


def test_the_guard_reads_every_kit_folder_and_shares_the_lock(w, tmp_path):
    budget = importlib.import_module("budget")
    assert budget.KITS_GLOB == ("family-probe-*", "gate-b-olmo*", "stage1-olmo*")
    assert budget.LOCK_NAME == "family-probe-budget.lock"
    assert budget.RESERVE_USD == 6.0 and budget.PLANNING_PRICE == 1.85
    for name in ("gate-b-olmo", "family-probe-x", "stage1-olmo-work", "other-kit"):
        (w.root.parent / name).mkdir(exist_ok=True)
    found = {p.name for p in budget.kit_folders()}
    assert found == {"stage1-olmo", "gate-b-olmo", "family-probe-x", "stage1-olmo-work"}
    with budget.lock():
        assert (w.root.parent / "family-probe-budget.lock").exists()
    gbk = (GBK / "budget.py").read_text()
    rule = gbk[gbk.index("def main() -> int:"):]
    assert rule in (w.root / "budget.py").read_text()                # the guard's rule unchanged


def test_the_guard_counts_the_new_pod_at_its_full_cap(w, monkeypatch, capsys):
    budget = importlib.import_module("budget")
    for free, code in ((19.875, 0), (19.87, 3)):                    # 19.875 - 7.5 x 1.85 = 6.00 >= $6; 5.995 < $6
        monkeypatch.setattr(budget, "projection", lambda: {"balance": free, "committed_upper_usd": 0.0,
                                                           "free_after_commitments_usd": free, "reserve_usd": 6.0})
        monkeypatch.setattr(sys, "argv", ["budget.py", "check", "7.5", "1.85"])
        assert budget.main() == code
        assert json.loads(capsys.readouterr().out)["new_pod_upper_usd"] == cents(7.5 * 1.85)


ABSENT = object()


def _fake_pod_api(price, calls: list):
    def api(method, path, payload=None):
        calls.append((method, path, (payload or {}).get("name")))
        if (method, path) == ("GET", "/pods"):
            return 200, []
        if (method, path) == ("POST", "/pods"):
            pod = {"id": "pod-synthetic", "name": payload["name"], "desiredStatus": "RUNNING"}
            return 201, pod if price is ABSENT else {**pod, "costPerHr": price}
        if method == "POST" and path.endswith("/stop"):
            return 200, {}
        return 200, {"desiredStatus": "EXITED"}
    return api


@pytest.mark.parametrize("price, created", [(1.79, True), (10.0, True), (10.01, False), (float("nan"), False),
                                            (float("inf"), False), (None, False), (ABSENT, False), ("1.79", False)])
def test_create_refuses_a_missing_non_finite_or_over_ten_dollar_price_and_names_the_stage1_pod(w, monkeypatch, price,
                                                                                               created):
    host = importlib.import_module("host")
    assert host.MAX_PRICE == 10.0 and host.name_of("a-1") == "attribution-s1-a-1"
    (w.root / "plan.json").write_text(json.dumps({"hosts": {"a-1": {"cap_hours": 7.5, "container_disk_gb": 80,
                                                                     "volume_gb": 40}}}))
    (w.root / "ssh").mkdir(exist_ok=True)
    (w.root / "ssh" / "key.pub").write_text("synthetic public key\n")

    def timer_settings(args, **kwargs):
        out = Path(args[args.index("--out") + 1])
        out.write_text(json.dumps({"env": {"POD_TIMER_CAP_MINUTES": "450"}, "docker_start_cmd": ["bash"],
                                   "cap_stop_utc": "2026-10-23T20:00:00+00:00"}))
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(host, "subprocess", argparse.Namespace(run=timer_settings, DEVNULL=subprocess.DEVNULL))
    calls = []
    monkeypatch.setattr(host, "api", _fake_pod_api(price, calls))
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    if created:
        assert host.create("a-1")["id"] == "pod-synthetic"
    else:
        with pytest.raises(SystemExit, match=r"above \$10\.00/h"):
            host.create("a-1")
        assert ("POST", "/pods/pod-synthetic/stop", None) in calls
    names = [c[2] for c in calls if c[:2] == ("POST", "/pods")]
    assert names == ["attribution-s1-a-1"] and not any("gateb" in n for n in names)


# ===== (E) the user's decision: the live-balance guard off (FOCUS 8d3d505) ========================================

USER_WORDS = "synthetic words standing in for the user's verbatim decision"


def _guard_off(w, **change) -> tuple[str, str]:
    body = {"kind": "stage1 user decision: budget guard off", "user_words": USER_WORDS, "utc": "2026-10-25T12:00:00Z",
            "recorded_by": "test", **change}
    return w.record({k: v for k, v in body.items() if v is not None})


@pytest.mark.parametrize("change, match", [
    ({"kind": "stage1 user yes"}, "its kind is not"), ({"user_words": " "}, "non-empty texts"),
    ({"recorded_by": None}, "exactly"), ({"extra": 1}, "exactly"), ({"utc": "2026-10-25T17:30:00+05:30"}, "not a UTC"),
    ({"utc": "2099-01-01T00:00:00Z"}, "in the future")])
def test_record_guard_off_takes_only_the_users_decision_record(w, change, match):
    w.s10()
    with pytest.raises(SystemExit, match=match):
        w.tool.record_simple("guard_off", *_guard_off(w, **change))
    assert w.plan()["records"].get("guard_off") is None and w.rules.guard_off_record(w.root) is None


def test_record_guard_off_is_recorded_once_by_sha256_and_a_changed_file_turns_the_guard_back_on(w):
    w.s10()
    assert w.rules.guard_off_record(w.root) is None                          # no record: the guard as before
    p, h = _guard_off(w)
    assert w.tool.record_simple("guard_off", p, h) == {"recorded": "guard_off", "sha256": h}
    rec = w.plan()["records"]["guard_off"]
    assert rec["sha256"] == h and rec["user_words"] == USER_WORDS and Path(rec["path"]).is_absolute()
    assert w.rules.guard_off_record(w.root) == {"sha256": h, "utc": "2026-10-25T12:00:00Z", "recorded_by": "test"}
    with pytest.raises(SystemExit, match="already recorded off"):
        w.tool.record_simple("guard_off", *_guard_off(w, recorded_by="another"))
    Path(p).write_text(Path(p).read_text().replace("test", "tset"))
    assert w.rules.guard_off_record(w.root) is None                          # re-hashed at every use


class _StopLoop(Exception):
    pass


def _launch_round(w, monkeypatch, guard_exit: int) -> tuple[list, list]:
    """launch.py's create loop for s10-1 with fake children: reconcile ok, budget.py check exits ``guard_exit`` with a
    balance line, host.py create writes pod.json. Returns (the children run, the log lines)."""
    launch = importlib.import_module("launch")
    plan = w.plan()
    ran, logged = [], []
    line = json.dumps({"balance": 3.21, "committed_upper_usd": 9.0, "new_pod_upper_usd": 13.88, "reserve_usd": 6.0,
                       "allowed": guard_exit == 0})

    def run(args, **kwargs):
        ran.append(args[1:3])
        if args[1:3] == ["host.py", "create"]:
            write_json(w.root / "hosts" / args[3] / "pod.json", {"id": "pod-x"})
        out = line if args[1] == "budget.py" else ""
        return subprocess.CompletedProcess(args, guard_exit if args[1] == "budget.py" else 0, out, "")

    def sleep(seconds):
        raise _StopLoop()
    monkeypatch.setattr(launch, "log", lambda **f: logged.append(f))
    try:
        launch._create_all(plan, ["s10-1"], run, lambda *a, **k: None, sleep)
    except _StopLoop:
        pass
    return ran, logged


@pytest.mark.parametrize("recorded, guard_exit, created", [(False, 3, False), (False, 0, True), (False, 1, False),
                                                           (True, 3, True), (True, 0, True), (True, 1, False)])
def test_launch_goes_past_the_guards_refusal_only_with_the_users_recorded_decision(w, monkeypatch, recorded, guard_exit,
                                                                                    created):
    """Without the record the guard is as before (a refusal, exit 3, stops the create); with it, a refusal is logged
    beside the decision and the create goes on; the guard's live-balance read must still succeed (any other exit
    refuses either way), and budget.py check runs before every create."""
    w.s10()
    h = w.tool.record_simple("guard_off", *_guard_off(w))["sha256"] if recorded else None
    ran, logged = _launch_round(w, monkeypatch, guard_exit)
    assert ["budget.py", "check"] in ran and ran.index(["budget.py", "check"]) < len(ran)
    assert (["host.py", "create"] in ran) is created
    events = [f.get("event") for f in logged]
    assert ("budget-guard-refused" in events) is (not created)
    off = [f for f in logged if f.get("event") == "budget-guard-off"]
    if recorded and created:
        assert off == [{"host": "s10-1", "event": "budget-guard-off", "guard_exit": guard_exit, "decision_sha256": h,
                        "detail": json.dumps({"balance": 3.21, "committed_upper_usd": 9.0, "new_pod_upper_usd": 13.88,
                                              "reserve_usd": 6.0, "allowed": guard_exit == 0})}]
    else:
        assert off == []


def _extend(w, monkeypatch, guard_exit: int):
    host = importlib.import_module("host")
    write_json(w.root / "hosts" / "s10-1" / "pod.json", {"id": "pod-x", "name": host.name_of("s10-1"),
                                                         "cap_stop_utc": "2026-10-25T12:00:00+00:00"})
    monkeypatch.setattr(host, "ssh_base", lambda h: [])
    ran = []

    def runner(args, **kwargs):
        ran.append(args[1] if args[0] != "ssh" else "ssh")
        if args[0] == "ssh":
            return subprocess.CompletedProcess(args, 0, json.dumps({"governs": True, "acknowledged": True, "lease": "l1",
                                                                    "stop_at_utc": "2026-10-26T00:00:00+00:00"}), "")
        return subprocess.CompletedProcess(args, guard_exit, '{"allowed": false}', "")
    return host, ran, runner


@pytest.mark.parametrize("recorded, guard_exit, extended", [(False, 3, False), (True, 3, True), (True, 1, False),
                                                            (False, 0, True)])
def test_extend_cap_goes_past_the_guards_refusal_only_with_the_users_recorded_decision(w, monkeypatch, recorded,
                                                                                       guard_exit, extended):
    w.s10()
    h = w.tool.record_simple("guard_off", *_guard_off(w))["sha256"] if recorded else None
    host, ran, runner = _extend(w, monkeypatch, guard_exit)
    if not extended:
        with pytest.raises(SystemExit, match="the budget guard refused the extension"):
            host.extend_cap("s10-1", 6 * 3600, runner=runner)
        assert ran[-1].endswith("budget.py") and "ssh" not in ran
        return
    out = host.extend_cap("s10-1", 6 * 3600, runner=runner)
    assert ran[0].endswith("budget.py") and ran[-1] == "ssh"                 # the guard still runs first (the read)
    saved = json.loads((w.root / "hosts" / "s10-1" / "cap-override.json").read_text())
    if recorded:
        assert out["budget_guard"] == saved["budget_guard"] == "off" and out["decision_sha256"] == h
        assert out["guard_exit"] == guard_exit
    else:
        assert "budget_guard" not in out                                     # as before


@pytest.mark.parametrize("price, created", [(10.0, True), (10.01, False), (None, False)])
def test_with_the_guard_off_a_pod_above_ten_dollars_still_refuses_and_is_stopped(w, monkeypatch, price, created):
    """The $10/h create-time limit, the stop timer settings at the host's cap and stop-never-delete are not part of the
    switch: host.create refuses (and stops) an over-limit or unknown price with the decision recorded."""
    w.s10()
    w.tool.record_simple("guard_off", *_guard_off(w))
    assert w.rules.guard_off_record(w.root) is not None
    host = importlib.import_module("host")
    cap = w.plan()["hosts"]["s10-1"]["cap_hours"]
    seen = {}
    (w.root / "ssh").mkdir(exist_ok=True)
    (w.root / "ssh" / "key.pub").write_text("synthetic public key\n")

    def timer_settings(args, **kwargs):
        seen["cap_minutes"] = args[args.index("--cap-minutes") + 1]
        out = Path(args[args.index("--out") + 1])
        out.write_text(json.dumps({"env": {"POD_TIMER_CAP_MINUTES": seen["cap_minutes"]}, "docker_start_cmd": ["bash"],
                                   "cap_stop_utc": "2026-10-25T20:00:00+00:00"}))
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(host, "subprocess", argparse.Namespace(run=timer_settings, DEVNULL=subprocess.DEVNULL))
    calls = []
    monkeypatch.setattr(host, "api", _fake_pod_api(price, calls))
    monkeypatch.setattr(host, "SLEEP", lambda s: None)
    if created:
        assert host.create("s10-1")["id"] == "pod-synthetic"
    else:
        with pytest.raises(SystemExit, match=r"above \$10\.00/h"):
            host.create("s10-1")
        assert ("POST", "/pods/pod-synthetic/stop", None) in calls
    assert seen["cap_minutes"] == str(int(cap * 60))                          # the in-pod stop timer at the cap
    assert not any(m == "DELETE" for m, _, _ in calls)                       # stop, never delete


# ===== The W1-18 gate ==============================================================================================


def test_a_500_bank_job_before_the_branch_record_refuses(w):
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    w.done("s10-1")
    w.gateb()
    w.cert_records()
    with pytest.raises(SystemExit, match="c0 job does not belong to block cert"):
        w.init("cert", [{"hosts": [CERT_POD + [C0]]}])              # round 3b: c0 is block A's (addendum §26)
    w.init("cert", [{"hosts": [CERT_POD[:3]]}])                     # C1-C3 need no branch
    assert w.plan()["hosts"]["cert-1"]["cap_hours"] > 0
    w.sealed()
    with pytest.raises(SystemExit, match="500-bank job before W1-18's branch record"):
        w.init("A", [{"hosts": [[C0]]}] + A_LAUNCHES, dry_run=True)   # c0 holds the 500-prompt bank


@pytest.mark.parametrize("launches, match", [
    ([{"hosts": [[{"kind": "w1_18"}, {"kind": "rep_pass"}]]}], "does not belong"),
    ([{"hosts": [[{"kind": "w1_18"}], [{"kind": "w1_18"}]]}], "W1-18 alone"),
    ([{"hosts": [[{"kind": "w1_18"}]]}, {"hosts": [[{"kind": "w1_18"}]]}], "W1-18 alone")])
def test_w1_18_runs_alone_as_job_0_of_the_first_pod(w, launches, match):
    with pytest.raises(SystemExit, match=match):
        w.init("S1-0", launches)


def test_w1_18_in_another_block_or_another_block_first_refuses(w):
    w.gateb()
    w.cert_records()
    with pytest.raises(SystemExit, match="first job of the first stage-1 pod"):
        w.init("cert", [{"hosts": [CERT_POD[:3]]}])
    with pytest.raises(SystemExit, match="does not belong"):
        w.init("cert", [{"hosts": [[{"kind": "w1_18"}] + CERT_POD[:3]]}])
    p, h = w.record({"kind": "stage1 branch full by default", "branch": "full", "reason": "W1-18 cannot run",
                     "utc": "u", "recorded_by": "t"})
    assert w.tool.record_branch(p, h) == {"branch": "full", "source": "default"}
    w.init("cert", [{"hosts": [CERT_POD]}])                          # Branch full by default: the first host may be C1
    assert {j["branch"] for j in w.plan()["hosts"]["cert-1"]["jobs"]} == {"full"}


def test_the_branch_record_must_match_the_pulled_w1_18_output(w):
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    w.done("s10-1", outputs={0: {"kind": "stage1 over-refusal checks", "truncation_check": {"units": 11, "pass": True}}})
    out = w.root / "retrieved" / "s10-1" / "tree" / "job-0" / "w1_18.json"
    base = {"kind": "stage1 w1-18 branch record", "branch": "128", "host": "s10-1", "output_path": "job-0/w1_18.json",
            "output_sha256": sha(out), "focus_commit": "abc", "utc": "u", "recorded_by": "t"}
    p, h = w.record({**base, "output_sha256": "0" * 64})
    with pytest.raises(SystemExit, match="differs from the pulled W1-18 output"):
        w.tool.record_branch(p, h)
    p, h = w.record(base)
    with pytest.raises(SystemExit, match="SHA-256 differs from the one given"):
        w.tool.record_branch(p, "1" * 64)
    p2, h2 = w.record({**base, "branch": "full"})
    with pytest.raises(SystemExit, match="follow W1-18's bar"):
        w.tool.record_branch(p2, h2)
    assert w.tool.record_branch(p, h) == {"branch": "128", "source": "w1_18"}
    out.write_text(out.read_text() + " ")                            # a changed byte in the pulled output
    p3, h3 = w.record(base)
    with pytest.raises(SystemExit, match="differs from the pulled"):
        w.tool.record_branch(p3, h3)


def test_branch_full_applies_when_w1_18_fails(w):
    w.s10(branch="full")
    assert w.plan()["records"]["branch"]["branch"] == "full"
    out = w.root / "retrieved" / "s10-1" / "tree" / "job-0" / "w1_18.json"
    p, h = w.record({"kind": "stage1 w1-18 branch record", "branch": "128", "host": "s10-1",
                     "output_path": "job-0/w1_18.json", "output_sha256": sha(out), "focus_commit": "a", "utc": "u",
                     "recorded_by": "t"})
    with pytest.raises(SystemExit, match="follow W1-18's bar"):
        w.tool.record_branch(p, h)


def test_the_branch_never_changes_once_a_500_bank_job_is_planned_and_caps_follow_it(w):
    p, h = w.record({"kind": "stage1 branch full by default", "reason": "cannot run", "utc": "u", "recorded_by": "t"})
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    w.done("s10-1", statuses={0: "crashed"})                           # W1-18 failed: Branch full by default
    w.tool.record_branch(p, h)
    assert w.tool.defer("s10-1")["to"] == "s10-2"                       # its retry at the same pod kind
    w.done("s10-2", outputs={0: {"kind": "stage1 over-refusal checks", "truncation_check": {"units": 11, "pass": True}}})
    out = w.root / "retrieved" / "s10-2" / "tree" / "job-0" / "w1_18.json"
    rec = {"kind": "stage1 w1-18 branch record", "branch": "128", "host": "s10-2", "output_path": "job-0/w1_18.json",
           "output_sha256": sha(out), "focus_commit": "a", "utc": "u", "recorded_by": "t"}
    assert w.tool.record_branch(*w.record(rec))["branch"] == "128"   # no 500-bank job yet: the change is allowed
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    caps = {h["cap_hours"] for n, h in w.plan()["hosts"].items() if n.startswith("a-")}
    assert caps == {7.0}                                              # Branch 128's 4-arm pod cap
    with pytest.raises(SystemExit, match="never changes"):
        w.tool.record_branch(*w.record({**rec, "focus_commit": "b"}))


# ===== Engine gates =================================================================================================


def test_a_y_job_before_a_passing_certificate_refuses(w):
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    plan = w.plan()
    assert all(j["engine"] == "X" for h in plan["hosts"].values() for j in h["jobs"] if h["block"] == "A")
    with pytest.raises(SystemExit, match="engine Y before a recorded passing"):
        w.tool.gate_g4(plan, "B", [{"kind": "ref_train", "recipe": "bqi", "engine": "Y"}])
    with pytest.raises(SystemExit, match="engine Y before a recorded passing"):
        w.tool.gate_g4(plan, "B", [{"kind": "arm", "engine": "Y"}])
    w.tool.gate_g4(plan, "B", [{"kind": "arm", "engine": "X"}])


def test_after_a_failed_certificate_only_bqi_and_its_own_a0_run_on_y(w):
    w.s10()
    w.gateb()
    w.certificate(passed=False)
    plan = w.plan()
    w.tool.gate_g4(plan, "B", [{"kind": "ref_train", "recipe": "bqi", "engine": "Y"},
                               {"kind": "a0_arm", "role": "bqi_own_a0", "engine": "Y"}])
    with pytest.raises(SystemExit, match="engine Y"):
        w.tool.gate_g4(plan, "B", [{"kind": "arm", "engine": "Y"}])
    plan["records"]["certificate"]["pass"] = True
    with pytest.raises(SystemExit, match="own a0 runs only after a failed certificate"):
        w.tool.gate_g4(plan, "B", [{"kind": "a0_arm", "role": "bqi_own_a0", "engine": "Y"}])
    w.tool.gate_g4(plan, "B", [{"kind": "arm", "engine": "Y"}, {"kind": "ref_train", "recipe": "bqi", "engine": "Y"}])


def test_one_engine_per_pod_and_y_only_kinds(w):
    w.s10()
    w.gateb()
    w.cert_records()
    with pytest.raises(SystemExit, match="runs on engine Y"):
        w.init("cert", [{"hosts": [[{**CERT_POD[0], "engine": "X"}]]}])
    w.sealed()
    with pytest.raises(SystemExit, match="one engine per pod"):
        w.init("A", [{"hosts": [[{"kind": "regenerate", "arm": "a0", "seed": 1101, "engine": "X"},
                                 {"kind": "regenerate", "arm": "R", "seed": 1101, "engine": "Y"}]]}] + A_LAUNCHES)


def test_a_packed_engine_that_differs_from_its_pin_refuses(w):
    w.s10()
    w.gateb()
    w.sealed()
    write_json(w.root / "setup" / "packed-stage1-X" / "setup-receipt.json", {"engine_sha256": "9" * 64})
    with pytest.raises(SystemExit, match="packed engine X differs from its pin"):
        w.init("A", A_LAUNCHES)
    assert "A" not in w.plan()["blocks"]


def test_every_job_record_names_its_engine(w):
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    with pytest.raises(SystemExit, match="does not name the engine"):
        w.done("s10-1", engine="Y")
    tree = w.root / "retrieved" / "s10-1" / "tree"
    done = json.loads((tree / "JOB-DONE.json").read_text())
    done["jobs"][0].pop("engine")
    write_json(tree / "JOB-DONE.json", done)
    with pytest.raises(SystemExit, match="does not name the engine"):
        w.tool.record_done("s10-1")


def test_the_certificate_pod_needs_gate_bs_final_record_and_c2_its_thresholds(w):
    w.s10()
    with pytest.raises(SystemExit, match="Gate B's final record"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    w.gateb()
    with pytest.raises(SystemExit, match="C3 needs the lead's subsample record"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    w.c3()
    with pytest.raises(SystemExit, match="thresholds record"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    w.certificate(passed=True)
    host = w.plan()["hosts"]["cert-1"]
    assert host["engine"] == "Y" and host["counted"] == 3 and [j["kind"] for j in host["jobs"]] == [
        "cert_c1", "cert_c2", "cert_c3"]                               # round 3b: no c0 (addendum §26)
    starts = [E1 + T * 33 / 38 + 1900 + 1800, (T + 1900) * 1.5 + 1800, 3600]
    before = [0, 3120, 3120 + 810]
    assert host["cap_hours"] == quarter_up(max(2520 + b + s for b, s in zip(before, starts))) == 3.25


# ===== Blocks and seeds =============================================================================================


def test_plan_a_tables_exactly(w):
    r = w.rules
    methods = ("A1", "L1", "H1", "S1", "S3", "S4")
    a = set(r.block_runs("A", "A"))
    assert a == {(m, s) for m in methods for s in (1102, 1103, 1104)} | {("a0", 1104), ("R", 1104)} and len(a) == 20
    b = set(r.block_runs("A", "B"))
    assert b == {(m, s) for m in methods + ("a0", "R") for s in (1105, 1106, 1107)} and len(b) == 24
    for blk, run in (("A", ("R", 1104)), ("B", ("R", 1105))):          # Gate B called no extension: no R_4/R_5
        with pytest.raises(ValueError, match="no extension"):
            r.block_runs("A", blk, (run,))
    w.mp.setattr(r, "ALLOWED_REUSE", frozenset({("R", 1104), ("R", 1105)}))   # had the extension run (LW-32)
    assert len(r.block_runs("A", "A", (("R", 1104),))) == 19
    assert len(r.block_runs("A", "B", (("R", 1105),))) == 23
    with pytest.raises(ValueError):
        r.block_runs("A", "C")


def test_plan_b_tables_exactly(w):
    r = w.rules
    four = ("A1", "H1", "S1", "S4")
    assert set(r.block_runs("B", "A")) == {(m, s) for m in four for s in (1102, 1103, 1104)} | {("a0", 1104),
                                                                                                ("R", 1104)}
    assert set(r.block_runs("B", "B")) == {(m, s) for m in four + ("a0", "R") for s in (1105, 1106, 1107)}
    c = r.block_runs("B", "C")
    assert set(c) == {(m, s) for m in four + ("R",) for s in (1108, 1109, 1110)} and len(c) == 15
    assert sorted(r.r_draw(s) for a_, s in c if a_ == "R") == [8, 9, 10]
    assert not any(a_ in ("L1", "S3") for blk in "ABC" for a_, _ in r.block_runs("B", blk))


def test_method_arms_never_at_1101_and_a0_at_1101_to_1107_under_both_plans(w):
    r = w.rules
    for code, blocks in (("A", "AB"), ("B", "ABC")):
        runs = [x for blk in blocks for x in r.block_runs(code, blk)]
        assert all(s != 1101 for _, s in runs)
        a0 = sorted(s for a_, s in runs if a_ == "a0") + list(r.REUSED_SEEDS)
        assert sorted(a0) == list(range(1101, 1108))
        assert sorted(s for a_, s in runs if a_ == "R")[:1] == [1104]


def test_r_d_is_bound_at_seed_1100_plus_d_from_gate_bs_manifest(w):
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", [{"deal": [0, 1, 2, 3, 4]}])
    jobs = [j for h in w.plan()["hosts"].values() for j in h["jobs"] if j["arm"] == "R"]
    (r4,) = jobs
    assert r4["seed"] == 1104 and r4["edit"]["path"].endswith("edits/r4.edit.json")
    assert r4["edit"]["source"] == "gateb-MAN" and r4["edit"]["engine_arm"] == "edit-r4"


@pytest.mark.parametrize("sigma, code", [(4.5, "A"), (4.51, "B"), (6.0, "B"), (6.01, "none")])
def test_the_blinded_seed_rule(w, sigma, code):
    assert w.rules.plan_code_for(sigma) == code


def test_a_no_stage_1_record_refuses_block_a_and_a_typed_record_refuses(w):
    w.s10()
    p, h = w.gateb_final()
    w.tool.record_simple("gateb_final", p, h)
    typed = {"kind": "stage1 plan-ab record", "code": "A", "sigma_pp": 3.9, "gateb_final_sha256": h, "utc": "u",
             "recorded_by": "t"}                                       # round 1's typed record: no longer accepted
    with pytest.raises(SystemExit, match="derived from Gate B's verdict file only"):
        w.tool.record_simple("plan_ab", *w.record(typed))
    with pytest.raises(SystemExit, match="plan-A/B record is not recorded"):
        w.init("A", A_LAUNCHES)
    w.tool.record_simple("plan_ab", *w.verdict(6.2))
    with pytest.raises(SystemExit, match="no stage 1"):
        w.init("A", A_LAUNCHES)


def _finish_block_a(w):
    w.init("A", A_LAUNCHES)
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-4", "a-5"):
        w.done(host)
    w.not_run()                       # round 3c: the plan's diagnostics, LN-12 and judge jobs are left out here


def test_block_b_refuses_before_block_a_is_complete_and_sealed(w):
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    with pytest.raises(SystemExit, match="block A is not complete"):
        w.init("B", [{"deal": [0, 1, 2, 3, 4, 5]}])
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    with pytest.raises(SystemExit, match="block A is not complete"):   # launch 1 not released
        w.init("B", [{"deal": [0, 1, 2, 3, 4, 5]}])
    w.tool.release("A")
    for host in ("a-4", "a-5"):
        w.done(host)
    # round 3c (VP3b-3): every host is done, but the plan's 4 diagnostics jobs, 19 LN-12 jobs (Branch 128: theta0's
    # LN-14 report counts) and 2 judge launches have no completion record and no not-run decision
    with pytest.raises(SystemExit, match=r"block A is not complete \(G5\); 25 job\(s\) the block-A plan requires have "
                                         r"no completion record and no not-run decision: untuned_answers, rep_pass, "
                                         r"l1_scan, classifier, regenerate a0 1101, o_only a0 1101, "):
        w.init("B", [{"deal": [0, 1, 2, 3, 4, 5]}])
    w.not_run()
    with pytest.raises(SystemExit, match="block A is not sealed"):
        w.init("B", [{"deal": [0, 1, 2, 3, 4, 5]}])
    w.seal.seal_block("A")
    out = w.init("B", [{"deal": [0, 1, 2]}, {"deal": [3, 4, 5]}])
    assert out["funding_block"] == "B" and len(out["released"]) == 3
    with pytest.raises(SystemExit, match="plan B only"):
        w.init("C", [{"deal": [0, 1, 2, 3]}])


def test_a_launch_waits_for_the_launch_before_it(w):
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    with pytest.raises(SystemExit, match="launch 0's hosts are not done"):
        w.tool.release("A")
    assert sorted(n for n in w.plan()["hosts"] if n.startswith("a-")) == ["a-1", "a-2", "a-3"]


# ===== Edits and inputs =============================================================================================


def test_edits_are_bound_only_by_sha256_from_their_sources(w):
    w.s10()
    w.gateb()
    with pytest.raises(SystemExit, match="no edit file in MAN1"):
        w.init("A", A_LAUNCHES)                                      # L1 ... S4 not sealed yet
    w.sealed()
    (w.repo / "tmp" / "sealed" / "L1.edit.json").write_text("{}")   # a changed byte after the record
    with pytest.raises(SystemExit, match="not the sealed one"):
        w.init("A", A_LAUNCHES)
    (w.repo / "tmp" / "sealed" / "L1.edit.json").write_text(json.dumps({"arm": "L1"}, indent=1, sort_keys=True) + "\n")
    other = write_json(w.repo / "tmp" / "sealed" / "L1b.edit.json", {"arm": "L1", "v": 2})
    w.tool.record_simple("sealed", *w.record({"kind": "stage1 sealed edits", "edits": [
        {"arm": "L1", "path": "tmp/sealed/L1b.edit.json", "sha256": sha(other)}]}))
    with pytest.raises(SystemExit, match="two sources name different edit files"):
        w.init("A", A_LAUNCHES)


def test_a1_comes_from_man1_and_a_changed_man1_refuses(w):
    w.s10()
    w.gateb()
    w.sealed()
    man1 = w.repo / w.rules.MAN1_PATH
    man1.write_text(man1.read_text() + " ")
    with pytest.raises(SystemExit, match="MAN1"):
        w.init("A", A_LAUNCHES)


def test_a_recipe_that_differs_from_its_pin_refuses(w):
    w.s10()
    w.gateb()
    w.sealed()
    (w.repo / w.rules.RECIPE_S).write_text("{}")
    with pytest.raises(SystemExit, match="differs from its pin"):
        w.init("A", A_LAUNCHES)


# ===== Regeneration ==================================================================================================


def test_an_o_only_pass_needs_its_regeneration_earlier_on_the_same_pod(w):
    w.s10()
    w.gateb()
    w.sealed()
    lone = [{"kind": "o_only", "arm": "R", "seed": 1102, "regen_source": 0}]
    with pytest.raises(SystemExit, match="must name its regeneration"):
        w.init("A", [{"hosts": [lone]}] + A_LAUNCHES)
    wrong = [{"kind": "regenerate", "arm": "R", "seed": 1103}, {"kind": "o_only", "arm": "R", "seed": 1102,
                                                                 "regen_source": 0}]
    with pytest.raises(SystemExit, match="must name its regeneration"):
        w.init("A", [{"hosts": [wrong]}] + A_LAUNCHES)
    pair = [{"kind": "regenerate", "arm": "R", "seed": 1102}, {"kind": "o_only", "arm": "R", "seed": 1102,
                                                                "regen_source": 0},
            {"kind": "o_only", "arm": "theta0"}]
    w.init("A", [{"hosts": [pair]}] + A_LAUNCHES)
    host = w.plan()["hosts"]["a-1"]
    assert [j["kind"] for j in host["jobs"]] == ["regenerate", "o_only", "o_only"] and host["counted"] == 0
    assert host["jobs"][0]["edit"]["path"].endswith("edits/r2.edit.json")


def test_a_stranded_regeneration_is_requeued_in_front_of_its_o_only_pass(w):
    w.s10()
    w.gateb()
    w.sealed()
    pair = [{"kind": "regenerate", "arm": "a0", "seed": 1101}, {"kind": "o_only", "arm": "a0", "seed": 1101,
                                                                 "regen_source": 0}]
    w.init("A", [{"hosts": [pair]}] + A_LAUNCHES)
    w.done("a-1", statuses={1: "deferred"})
    out = w.tool.defer("a-1")
    plan = w.plan()
    moved = plan["hosts"][out["to"]]["jobs"][:2]
    assert [(j["kind"], j.get("reason")) for j in moved] == [("regenerate", "stranded-regenerate"), ("o_only", None)]
    assert moved[1]["regen_source"] == 0 and moved[0]["stranded_complete_sha256"] == plan["hosts"]["a-1"]["jobs"][0][
        "complete_sha256"]


def test_an_o_only_pass_never_moves_without_its_regeneration(w):
    w.s10()
    w.gateb()
    w.sealed()
    pair = [{"kind": "regenerate", "arm": "a0", "seed": 1101}, {"kind": "o_only", "arm": "a0", "seed": 1101,
                                                                 "regen_source": 0}]
    w.init("A", [{"hosts": [pair]}] + A_LAUNCHES)
    w.done("a-1", statuses={1: "crashed"})
    with pytest.raises(SystemExit, match="without its regeneration"):
        w.tool.defer("a-1")


# ===== Seal ==========================================================================================================


def test_the_seal_lists_every_file_by_sha256_and_no_command_prints_a_value(w, capsys):
    w.s10()
    w.gateb()
    w.sealed()
    _finish_block_a(w)
    with pytest.raises(SystemExit, match="usage"):
        w.seal.main([])
    assert w.seal.main(["block", "A"]) == 0
    printed = capsys.readouterr().out
    record = json.loads((w.root / "seals" / "block-A.json").read_text())
    trees = {h: w.root / "retrieved" / h / "tree" for h in ("a-1", "a-2", "a-3", "a-4", "a-5")}
    on_disk = sorted((h, p.relative_to(t).as_posix(), sha(p)) for h, t in trees.items() for p in t.rglob("*")
                     if p.is_file())
    assert sorted((f["host"], f["path"], f["sha256"]) for f in record["files"]) == on_disk
    assert len(on_disk) == 20 * 3 + 5                                 # 3 files per unit + each host's JOB-DONE
    classes = {f["path"].rsplit("/", 1)[-1]: f["class"] for f in record["files"]}
    assert classes == {"summary.json": "sealed", "cost-ledger.json": "readable", "COMPLETE.json": "sealed",
                       "JOB-DONE.json": "readable"}             # an engine COMPLETE.json holds its evaluation
    assert w.plan()["seals"]["A"]["sha256"] == sha(w.root / "seals" / "block-A.json")
    assert w.seal.main(["status"]) == 0
    printed += capsys.readouterr().out
    texts = [printed, (w.root / "seals" / "block-A.json").read_text(), (w.root / "plan.json").read_text(),
             (w.root / "operator-actions.jsonl").read_text()]
    for text in texts:
        for value in SENTINELS[:1]:
            assert value not in text
    assert "arm:complete" in printed and "seal A: 65 files (40 sealed)" in printed
    with pytest.raises(SystemExit, match="already sealed"):
        w.seal.seal_block("A")


def test_the_seal_refuses_an_incomplete_block(w):
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    with pytest.raises(SystemExit, match="not complete"):
        w.seal.seal_block("A")
    w.done("a-1", statuses={0: "crashed"})
    with pytest.raises(SystemExit, match="not complete"):
        w.seal.seal_block("A")
    assert not (w.root / "seals").exists()


def test_the_gate_b_status_copy_prints_completion_only(w):
    w.s10()
    out = subprocess.run([sys.executable, "-B", str(w.root / "status.py")], capture_output=True, text=True,
                         cwd=w.root, env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert out.returncode == 0 and "w1_18:complete" in out.stdout and "wave S1-0" in out.stdout
    assert SENTINELS[1] not in out.stdout


# ===== Interleaving and the 4-job rule =============================================================================


def test_the_deal_matches_the_pre_set_rule_by_hand(w):
    """Arm-major (A1, L1, H1, S1, S3, S4, a0, R), seed-minor; run i to pod i mod 5."""
    runs = [(a, s) for a in ("A1", "L1", "H1", "S1", "S3", "S4") for s in (1102, 1103, 1104)] + [("a0", 1104),
                                                                                                 ("R", 1104)]
    hand = [[runs[i] for i in range(p, 20, 5)] for p in range(5)]
    assert hand[0] == [("A1", 1102), ("L1", 1104), ("S1", 1103), ("S4", 1102)]
    assert w.rules.deal(w.rules.block_runs("A", "A")) == hand
    assert w.rules.split_pods(runs) != hand                          # Gate B's contiguous split is not the deal
    for code, blocks in (("A", "AB"), ("B", "ABC")):
        for blk in blocks:
            for pod in w.rules.deal(w.rules.block_runs(code, blk)):
                assert len(pod) <= 4 and len({a for a, _ in pod}) == len(pod)


def test_a_deal_that_would_put_one_arm_twice_on_a_pod_refuses(w, monkeypatch):
    monkeypatch.setattr(w.rules, "MAX_ARMS_PER_POD", 10)            # 2 pods for 20 runs: an arm's 3 runs collide
    with pytest.raises(ValueError, match="one arm twice"):
        w.rules.deal(w.rules.block_runs("A", "A"))


def test_a_pod_with_more_than_four_counted_jobs_refuses(w):
    w.s10()
    w.gateb()
    w.sealed()
    _finish_block_a(w)
    w.seal.seal_block("A")
    plan = w.plan()
    five = [{"kind": "ref_eval", "arm": "a0", "seed": 1101, "points": ["scale:0.9", "scale:0.75", "scale:0.5"]},
            {"kind": "safe_lora", "arm": "a0", "seed": 1101, "points": ["default", "conditional"]}]
    with pytest.raises(SystemExit, match="5 counted jobs, more than 4"):
        w.tool.build_block(plan, "B", {"launches": [{"hosts": [five]}, {"deal": [0, 1, 2, 3, 4, 5]}]})
    assert w.rules.counted("regenerate") == w.rules.counted("o_only") == w.rules.counted("rep_pass") == 0
    assert w.rules.counted("ref_eval", 3) == 3 and w.rules.counted("cert_c2") == 1


def test_training_runs_come_only_from_the_deal_and_every_dealt_pod_once(w):
    w.s10()
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match="from the block's deal only"):
        w.init("A", [{"hosts": [[{"kind": "arm", "arm": "A1", "seed": 1102}]]}] + A_LAUNCHES)
    with pytest.raises(SystemExit, match="exactly once"):
        w.init("A", [{"deal": [0, 1, 2]}, {"deal": [3]}])
    with pytest.raises(SystemExit, match="exactly once"):
        w.init("A", [{"deal": [0, 1, 2]}, {"deal": [2, 3, 4]}])
    w.init("A", [{"hosts": [DIAG_POD]}, {"deal": [0, 1, 2, 3, 4]}])
    plan = w.plan()
    assert plan["hosts"]["a-1"]["role"] == "diagnostics" and plan["blocks"]["A"]["deal"][0] == [
        ["A1", 1102], ["L1", 1104], ["S1", 1103], ["S4", 1102]]


def test_reference_points_need_their_records_and_a_passing_certification(w):
    w.s10()
    w.gateb()
    w.sealed()
    _finish_block_a(w)
    w.seal.seal_block("A")
    plan = w.plan()
    sp = [{"kind": "ref_eval", "points": ["prefix"]}]
    with pytest.raises(SystemExit, match="prefix point refuses"):
        w.tool.gate_records(plan, sp)
    with pytest.raises(SystemExit, match="K = 12"):
        w.tool.gate_records(plan, [{"kind": "safe_lora", "points": ["k12"]}])
    with pytest.raises(SystemExit, match="passing B10 certification"):
        w.tool.gate_certification(plan, [{"kind": "safe_lora", "points": ["default"]}])
    w.tool.record_simple("prefix", *w.record({"kind": "stage1 sp prefix pin", "text_sha256": "c" * 64,
                                              "source": "lead", "utc": "u", "recorded_by": "t"}))
    w.tool.record_simple("user_yes", *w.record({"kind": "stage1 user yes", "item": "safe_lora_k12",
                                                "user_words": "yes", "utc": "u", "recorded_by": "t"}))
    plan = w.plan()
    w.tool.gate_records(plan, sp + [{"kind": "safe_lora", "points": ["k12"]}])


def test_the_certification_pod_and_an_evaluation_only_reference(w):
    w.s10()
    w.gateb()
    w.sealed()
    _finish_block_a(w)
    w.seal.seal_block("A")
    w.init("certify", [{"hosts": [[{"kind": "b10_certify", "arm": "a0", "seed": 1101,
                                    "points": ["certify", "scale:0"]}]]}])
    host = w.plan()["hosts"]["cfy-1"]
    assert host["cap_hours"] == quarter_up(2520 + 540 + 2 * 0.93 * 2934 + 1900 + 1800) and host["counted"] == 2
    w.done("cfy-1")
    ev = w.root / "retrieved" / "cfy-1" / "tree" / "units" / "job-0" / "COMPLETE.json"
    w.tool.record_simple("certification", *w.record({"kind": "stage1 b10 certification", "pass": True, "host": "cfy-1",
                                                     "utc": "u", "recorded_by": "t",
                                                     "evidence": [{"path": "units/job-0/COMPLETE.json",
                                                                   "sha256": sha(ev)}]}))
    w.init("B", [{"hosts": [[{"kind": "safe_lora", "arm": "a0", "seed": 1104, "points": ["default"]}]]},
                 {"deal": [0, 1, 2, 3, 4, 5]}])
    assert w.plan()["hosts"]["b-1"]["jobs"][0]["recipe"] == "B"


# ===== The Gate B behaviour reused ===================================================================================


def _log(w, host: str, *events) -> None:
    fields = {"pre-job-failed": {"step": "bootstrap"}, "pre-job-stop": {"exit": 0}}
    (w.root / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(w.root / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        for e in events:
            handle.write(json.dumps({"utc": "2026-10-23T10:00:00+00:00", "host": host, "event": e,
                                     **fields.get(e, {})}) + "\n")


def _launch(w, host: str) -> None:
    write_json(w.root / "hosts" / host / "create-intent.json", {"cap_stop_utc": "2026-10-23T20:00:00+00:00"})


def test_requeue_moves_every_job_of_a_host_stopped_before_its_job_and_pays_the_unit(w):
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    _launch(w, "a-1")
    _log(w, "a-1", "bootstrap-started")
    with pytest.raises(SystemExit, match="no logged pre-job failure"):
        w.tool.requeue("a-1")
    _log(w, "a-1", "pre-job-failed", "pre-job-stop")
    for other in ("a-2", "a-3"):
        _launch(w, other)
    before = w.plan()["contingency"]["A"]["remaining_usd"]
    out = w.tool.requeue("a-1")
    plan = w.plan()
    assert out["to"] == "a-6" and [j["status"] for j in plan["hosts"]["a-1"]["jobs"]] == ["not_started"] * 4
    unit = (2520 + 4 * 4637) / 3600 * 1.79
    assert plan["contingency"]["A"]["remaining_usd"] == pytest.approx(before - unit)
    assert [(j["arm"], j["deferred_from"]) for j in plan["hosts"]["a-6"]["jobs"]] == [
        (j["arm"], "a-1") for j in plan["hosts"]["a-1"]["jobs"]]
    with pytest.raises(SystemExit, match="already deferred"):
        w.tool.requeue("a-1")


def test_requeue_refuses_a_started_host_and_an_unconfirmed_stop(w):
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    _log(w, "a-1", "pre-job-failed", "job-started")
    with pytest.raises(SystemExit, match="its job started"):
        w.tool.requeue("a-1")
    _log(w, "a-2", "job-start-unknown")
    with pytest.raises(SystemExit, match="not confirmed by the log"):
        w.tool.requeue("a-2")
    with pytest.raises(SystemExit, match="no pod status read"):
        w.tool.confirm_stopped("a-2")
    write_json(w.root / "hosts" / "a-2" / "pod-latest.json", {"desiredStatus": "EXITED",
                                                              "utc": "2026-10-23T09:00:00+00:00"})
    with pytest.raises(SystemExit, match="read before the last orchestrate record"):
        w.tool.confirm_stopped("a-2")
    write_json(w.root / "hosts" / "a-2" / "pod-latest.json", {"desiredStatus": "EXITED",
                                                              "utc": "2026-10-23T11:00:00+00:00"})
    assert w.tool.confirm_stopped("a-2") == {"host": "a-2", "confirmed": True}
    assert w.tool.requeue("a-2")["jobs"] == 4


def test_defer_goes_to_an_unlaunched_host_with_room_never_a_launched_one(w):
    w.s10()
    w.gateb()
    w.sealed()
    pods = [[{"kind": "regenerate", "arm": "a0", "seed": 1101}], [{"kind": "regenerate", "arm": "R", "seed": 1101}]]
    w.init("A", [{"hosts": pods}] + A_LAUNCHES)
    w.done("a-1", statuses={0: "crashed"})
    _launch(w, "a-2")
    out = w.tool.defer("a-1")
    assert out["to"] not in ("a-1", "a-2") and w.plan()["hosts"][out["to"]]["jobs"][0]["deferred_from"] == "a-1"
    with pytest.raises(SystemExit, match="already deferred"):
        w.tool.defer("a-1")


def test_a_complete_job_is_never_run_again(w):
    w.s10()
    w.gateb()
    w.sealed()
    pods = [[{"kind": "regenerate", "arm": "a0", "seed": 1101}]]
    w.init("A", [{"hosts": pods}] + A_LAUNCHES)
    w.done("a-1")
    job = dict(w.plan()["hosts"]["a-1"]["jobs"][0])
    with pytest.raises(SystemExit, match="never re-run"):
        w.tool.refuse_complete(w.plan(), [job], [])


def test_launch_refuses_a_wrong_cap_and_gives_no_child_a_token(w, monkeypatch):
    w.s10()
    launch = importlib.import_module("launch")
    plan = w.plan()
    launch.check_hosts(plan, ["s10-1"])
    bad = json.loads(json.dumps(plan))
    bad["hosts"]["s10-1"]["cap_hours"] = 1.5
    with pytest.raises(SystemExit, match="cap"):
        launch.check_hosts(bad, ["s10-1"])
    token = fake_token()
    monkeypatch.setenv("HF_TOKEN", token)
    assert "HF_TOKEN" not in launch.clean_env() and token not in json.dumps(launch.clean_env())


# (E, the user's decision of 25 Oct, FOCUS 8d3d505): the only other differences of launch.py and host.py from Gate B's
GUARD_OFF_LAUNCH = [('''                if guard.returncode != 0:
                    log(host=host, event="budget-guard-refused", detail=guard.stdout.strip()[-300:])
                    continue
''', '''                off = rules.guard_off_record(HERE)   # (E) the user's recorded decision: past the guard's refusal only
                if guard.returncode != 0 and not (off and guard.returncode == rules.GUARD_REFUSED_EXIT):
                    log(host=host, event="budget-guard-refused", detail=guard.stdout.strip()[-300:])
                    continue
                if off:                               # the live balance was read; its line is logged with the decision
                    log(host=host, event="budget-guard-off", guard_exit=guard.returncode, decision_sha256=off["sha256"],
                        detail=guard.stdout.strip()[-300:])
''')]
GUARD_OFF_HOST = [('''    override = folder(host) / "cap-override.json"
    with budget.lock():''', '''    override = folder(host) / "cap-override.json"
    guard_note = {}
    with budget.lock():'''),
                  ('''            if guard.returncode != 0:
                raise SystemExit("the budget guard refused the extension")
''', '''            off = rules.guard_off_record(HERE)   # (E) the user's recorded decision: past the guard's refusal only
            if guard.returncode != 0 and not (off and guard.returncode == rules.GUARD_REFUSED_EXIT):
                raise SystemExit("the budget guard refused the extension")
            if off:                                   # the live balance was read (budget-checks.jsonl); noted here
                guard_note = {"budget_guard": "off", "guard_exit": guard.returncode, "decision_sha256": off["sha256"]}
'''),
                  ('''"added_hours": round(added_h, 4)}
''', '''"added_hours": round(added_h, 4),
                  **guard_note}
''')]

# addendum §29 (round 29): the pull list gets rescore/ and cert/ (every folder a stage-1 job writes a unit to), and the
# finisher light-checks every host role (Gate B's kit keeps its own list and its "job", "first", "anchor" roles)
PULL_29 = [('''PULL_ITEMS = ("round1 job-* jobs anchor-* gatec cuda-preflight-* "
''', '''# Addendum §29 point 2 (stage-1 kit gap 1): every folder a stage-1 job writes a unit to is pulled. The job runner writes
# units to round1/ (arms, regenerations), rescore/ (LN-15e's retrains and re-scores) and cert/ (C1-C3), and job-I/
# (B10's units, O-ext and unit-free outputs, ledgers), job files to jobs/, records to job-done/, JOB-DONE.json and
# deferral.json (tests: every path the runner records lies under this list). pull-light leaves out *.safetensors.
PULL_ITEMS = ("round1 rescore cert job-* jobs anchor-* gatec cuda-preflight-* "
''')]
FINISHER_29 = [('''            elif role in ("job", "first", "anchor"):
                results = light_check(host, tree)
''', '''            else:      # addendum §29 point 4: every stage-1 role (w1_18, cert, certify, job, diagnostics, arms), any role
                results = light_check(host, tree)
'''), ('''                log(host=host, event="verified", units=len(results), ok=ok)
            elif receipt.get("exit_code") != 0:
                status = "review-needed-stopped"
''', '''                log(host=host, event="verified", units=len(results), ok=ok)
''')]
# round 31 (K5, cert runbook D9): the finisher treats a moved, not-done host as finished for the watch (seal.py's
# plan_tool.moved_hosts); (K6, D7) launch.py exits NO_POD_EXIT when a host it should create has no pod.json at its end
FINISHER_31 = [('''- the finisher removes the token variables from its own environment when it starts (it never needs them).
"""''', '''- the finisher removes the token variables from its own environment when it starts (it never needs them).
Round 31 (K5; cert runbook D9): a host that a deferral or requeue moved (plan_tool.moved_hosts, as seal.py) and that is
not recorded done (a-5, a-6, a-7: setup failed, stopped, never pulled; a requeue needs a confirmed stop) never gets a
finished.json. The watch treats it as finished: it is not watched, it sets no deadline, and "every planned host is
finished" no longer waits for it.
"""'''), ('''import secret_scan  # noqa: E402
''', '''import secret_scan  # noqa: E402
import plan_tool  # noqa: E402  (round 31, K5: moved_hosts, the seal's helper)
'''), ('''def deadline(p: dict, started: dt.datetime) -> dt.datetime:
    """3 h past every host's latest stop (review fix 13)."""
    ends = []
    for host, job in p["hosts"].items():
        stop = host_stop(host)
        ends.append(stop if stop is not None else started + dt.timedelta(hours=LAUNCH_HOURS + job["cap_hours"]))
    return max(ends) + dt.timedelta(hours=AFTER_STOP_HOURS)
''', '''def moved_undone(p: dict) -> set:
    """Round 31 (K5): the hosts a deferral or requeue moved (plan_tool.moved_hosts) that are not recorded done: finished
    for the watch (they never get a finished.json)."""
    return {host for host in plan_tool.moved_hosts(p) if not (p["hosts"].get(host) or {}).get("done")}


def finished_for_watch(p: dict, host: str) -> bool:
    return (HERE / "hosts" / host / "finished.json").exists() or host in moved_undone(p)


def deadline(p: dict, started: dt.datetime) -> dt.datetime:
    """3 h past every host's latest stop (review fix 13); a moved, not-done host sets none (K5)."""
    ends, skip = [], moved_undone(p)
    for host, job in p["hosts"].items():
        if host in skip:
            continue
        stop = host_stop(host)
        ends.append(stop if stop is not None else started + dt.timedelta(hours=LAUNCH_HOURS + job["cap_hours"]))
    return max(ends, default=started) + dt.timedelta(hours=AFTER_STOP_HOURS)
'''), ('''def watched() -> list[str]:
    return sorted(p.parent.name for p in (HERE / "hosts").glob("*/pod.json") if not (p.parent / "finished.json").exists())
''', '''def watched(p: dict | None = None) -> list[str]:
    skip = moved_undone(p) if p is not None else set()            # K5: a moved, not-done host is not watched
    return sorted(q.parent.name for q in (HERE / "hosts").glob("*/pod.json")
                  if not (q.parent / "finished.json").exists() and q.parent.name not in skip)
'''), ('''        if all((HERE / "hosts" / h / "finished.json").exists() for h in plan()["hosts"]) and not stops_pending():
            log(event="every planned host is finished"); return 0
        hosts = watched()
''', '''        p = plan()
        if all(finished_for_watch(p, h) for h in p["hosts"]) and not stops_pending():
            log(event="every planned host is finished"); return 0
        hosts = watched(p)
''')]
LAUNCH_31 = [('''a time (launch.lock). Every child gets an environment without any token variable.
"""''', '''a time (launch.lock). Every child gets an environment without any token variable.

Round 31 (K6; cert runbook D7): the exit code says whether every host was created. launch.py exits NO_POD_EXIT (4),
after its log line "hosts-not-created", when a host it was given has no hosts/HOST/pod.json at its end (every try was
refused or failed for MAX_HOURS); 0 only when every host has its pod.json. Nothing else changed.
"""'''), ('''SPACING, ROUND_PAUSE, MAX_HOURS = 45, 300, 2
''', '''SPACING, ROUND_PAUSE, MAX_HOURS = 45, 300, 2
NO_POD_EXIT = 4                     # round 31 (K6): a host it should create has no pod.json at the end
'''), ('''        held.close()
    return 0
''', '''        held.close()
    missing = [h for h in hosts if not (HERE / "hosts" / h / "pod.json").exists()]
    if missing:                      # round 31 (K6): no pod for a host it should create is not a success
        log(event="hosts-not-created", hosts=missing, exit=NO_POD_EXIT)
        return NO_POD_EXIT
    return 0
''')]


def test_the_kit_compiles_holds_no_secret_and_reuses_gate_b_files_as_documented(tmp_path):
    names = sorted(p.name for p in KIT.glob("*.py"))
    assert names == ["account.py", "backup_records_stage1.py", "budget.py", "compare_c1.py", "finisher.py",
                     "gateb_mac.py", "host.py",
                     "judge_units_stage1.py", "launch.py", "orchestrate.py", "pack_setup.py", "plan_tool.py", "probes.py",
                     "seal.py", "secret_scan.py", "stage1_rules.py", "status.py"]   # BUILD-RUNNER added 5 files
    import py_compile
    for n in names:
        py_compile.compile(str(KIT / n), cfile=str(tmp_path / "x.pyc"), doraise=True)
    sys.path.insert(0, str(KIT))
    try:
        sys.modules.pop("secret_scan", None)
        import secret_scan
        assert secret_scan.scan_paths([KIT / n for n in names if n != "secret_scan.py"]) == []
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("secret_scan", None)
    for same in ("secret_scan.py", "account.py", "status.py", "gateb_mac.py"):
        assert (KIT / same).read_bytes() == (GBK / same).read_bytes(), same
    imp = ("import gateb_rules as rules  # noqa: E402", "import stage1_rules as rules  # noqa: E402")
    for name, extra in (("launch.py", GUARD_OFF_LAUNCH + LAUNCH_31), ("finisher.py", FINISHER_29 + FINISHER_31),
                        ("host.py", [('    return f"attribution-gateb-{host}{suffix}"     # e.g. attribution-gateb-w0a-1',
                                      '    return f"attribution-s1-{host}{suffix}"     # e.g. attribution-s1-A-1'),
                                     *GUARD_OFF_HOST, *PULL_29]),
                        ("budget.py", [('KITS_GLOB = ("family-probe-*", "gate-b-olmo*")   # every family-probe and Gate B '
                                        'working copy beside this kit',
                                        'KITS_GLOB = ("family-probe-*", "gate-b-olmo*", "stage1-olmo*")   # every '
                                        'family-probe, Gate B and stage-1 working copy beside this kit')])):
        text = (GBK / name).read_text()
        for old, new in [imp] + extra:
            assert text.count(old) == 1
            text = text.replace(old, new)
        assert (KIT / name).read_text() == text, name
    rules_text = (KIT / "stage1_rules.py").read_text()
    gb = (GBK / "gateb_rules.py").read_text()
    import re
    for fn in re.findall(r"^def (\w+)\(", gb, re.M):
        assert f"\ndef {fn}(" in rules_text or f"\n{fn} = " in rules_text, fn
    for const in re.findall(r"^([A-Z][A-Z0-9_]+) = ", gb, re.M):
        assert re.search(rf"^{const}(, \w+)? = |^\w+, {const} = ", rules_text, re.M), const


def test_the_cli_dry_run_writes_nothing_and_deal_prints_the_rule(w, capsys):
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    before = (w.root / "plan.json").read_bytes()
    log_before = (w.root / "operator-actions.jsonl").read_bytes()
    jobs = w.jobs([{"hosts": [DIAG_POD]}] + A_LAUNCHES)
    assert w.tool.main(["init-block", "A", "--jobs", jobs, "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out["dry_run"] is True and [p["cap_hours"] for p in out["pods"]] == [
        quarter_up(2520 + 3600 + 7560 + 3600 + 1.5 * 2012 + 1800), 7.5, 7.5, 7.5, 7.5, 7.5]
    assert (w.root / "plan.json").read_bytes() == before and (w.root / "operator-actions.jsonl").read_bytes() == log_before
    assert w.tool.main(["deal", "A"]) == 0
    pods = json.loads(capsys.readouterr().out)["pods"]
    assert pods[4] == ["L1@1103", "S1@1102", "S3@1104", "R@1104"] and len(pods) == 5   # runs 4, 9, 14, 19
    with pytest.raises(SystemExit, match="no extension"):
        w.tool.main(["deal", "A", "--reuse", "R", "1104"])             # Gate B made no R_4


# ===== The B15 fix round (notes/b15-fix.json; each test failed on the kit before its fix) ============================


def _default(w) -> tuple[str, str]:
    return w.record({"kind": "stage1 branch full by default", "reason": "W1-18 failed", "utc": "u", "recorded_by": "t"})


def test_branch_full_by_default_only_when_w1_18_cannot_run_or_failed(w):
    """VMG-1: REV4 §6.3 'if W1-18 cannot run or fails, Branch full applies'."""
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    with pytest.raises(SystemExit, match="planned or running"):
        w.tool.record_branch(*_default(w))                              # W1-18 planned, not run
    w.done("s10-1", outputs={0: {"kind": "stage1 over-refusal checks", "truncation_check": {"units": 11, "pass": True}}})
    with pytest.raises(SystemExit, match="W1-18 completed"):
        w.tool.record_branch(*_default(w))                              # complete: its own output decides
    out = w.root / "retrieved" / "s10-1" / "tree" / "job-0" / "w1_18.json"
    w.tool.record_branch(*w.record({"kind": "stage1 w1-18 branch record", "branch": "128", "host": "s10-1",
                                    "output_path": "job-0/w1_18.json", "output_sha256": sha(out),
                                    "focus_commit": "a", "utc": "u", "recorded_by": "t"}))
    with pytest.raises(SystemExit, match="W1-18's branch record exists"):
        w.tool.record_branch(*_default(w))                              # never overrides W1-18's branch
    assert w.plan()["records"]["branch"]["branch"] == "128"


def test_branch_full_by_default_after_a_crashed_w1_18_and_no_s1_0_after_it(w):
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    w.done("s10-1", statuses={0: "crashed"})
    assert w.tool.record_branch(*_default(w)) == {"branch": "full", "source": "default"}
    w2 = w.plan()
    assert w2["records"]["branch"]["source"] == "default"


def test_no_s1_0_pod_once_branch_full_by_default_is_recorded(w):
    w.gateb()
    w.tool.record_branch(*_default(w))                                  # no S1-0 pod: W1-18 cannot run
    with pytest.raises(SystemExit, match="branch record exists"):
        w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])


def test_gate_b_final_is_recorded_once_and_block_a_reads_the_plan_ab_record_bound_to_it(w):
    """VMG-2."""
    w.s10()
    w.gateb()
    p, h = w.gateb_final(version=2)                                     # another file, pinned for this test
    with pytest.raises(SystemExit, match="already recorded"):
        w.tool.record_simple("gateb_final", p, h)
    plan = w.plan()
    plan["records"]["gateb_final"]["sha256"] = "9" * 64                 # a replaced final record (hand edit)
    w.mac.save_plan(plan)
    w.sealed()
    with pytest.raises(SystemExit, match="does not name the recorded Gate B final record"):
        w.init("A", A_LAUNCHES)


@pytest.mark.parametrize("body", [{}, {"kind": "gate-b reading", "phase": "measurements", "result": {"final": False,
                                                                                                    "code": "REPORTED"}},
                                  {"kind": "gate-b reading", "phase": "measurements", "result": {"final": True,
                                                                                                "code": "REFUSED"}},
                                  {"kind": "gate-b reading", "phase": "verdict", "result": {"final": True,
                                                                                           "code": "REPORTED"}}])
def test_only_gate_bs_pinned_final_output_is_its_final_record(w, body):
    """VMG-3: G3 reads Gate B's measurements --final output (code REPORTED) by its pinned SHA-256."""
    p, h = w.record(body)
    w.mp.setattr(w.rules, "GATEB_FINAL_SHA256", h, raising=False)       # even when the pin names this file
    with pytest.raises(SystemExit, match="measurements --final"):
        w.tool.record_simple("gateb_final", p, h)
    p2, h2 = w.record({"kind": "gate-b reading", "phase": "measurements", "result": {"final": True,
                                                                                   "code": "REPORTED"}, "x": 1})
    w.mp.setattr(w.rules, "GATEB_FINAL_SHA256", "0" * 64, raising=False)
    with pytest.raises(SystemExit, match="measurements --final"):
        w.tool.record_simple("gateb_final", p2, h2)                     # right fields, not the pinned file
    assert w.tool.load()["records"]["gateb_final"] is None


def test_the_gate_b_final_pin_is_the_reported_output():
    rules_text = (KIT / "stage1_rules.py").read_text()
    assert 'GATEB_FINAL_SHA256 = "06a7020aede28df5bf8a73740819c3453b483f02c61a148822c0c66c4798bd0f"' in rules_text


def test_s1_0_and_the_cert_pod_count_block_as_arm_pods_before_any_block_a_pod_launches(w):
    """VMG-4 (round 1), VG2-2 (round 2), rewritten for round 3a (addendum §20 point 1: block A's funding event covers
    the WHOLE block's cap-based need before S1-0 launches). With no lead record, S1-0's init needs the kit default's
    whole sequence (worked example in hand_default_need: $130.59 under Branch full and plan A); round 2's $103.53
    floor (S1-0, cert and the arm pods only) and round 1's $96.90 now refuse."""
    w.auto_plan = False
    terms, base, need = hand_default_need("full", (2, 2, 1))
    assert (base, need) == (104.47, 130.59)
    one = [{"hosts": [[{"kind": "w1_18"}]]}]
    out = w.init("S1-0", one, dry_run=True)
    assert out["need_usd"] == need and out["base_need_usd"] == base
    assert out["terms_cents"] == pytest.approx([t * 100 for t in terms], abs=1e-3)
    assert [x["role"] for x in out["block_a_plan"]["rest"]] == ["cert", "diagnostics", "ln12", "arms", "arms", "arms",
                                                               "judge", "judge"]
    unmeasured = {k for x in out["block_a_plan"]["rest"] for p in x["pods"] for k in p["unmeasured"]}
    assert {"rep_pass", "untuned_answers", "l1_scan", "classifier", "c0", "cert_c2", "cert_c3", "o_only", "arm",
            "a0_arm", "a1_rescore"} <= unmeasured                       # every estimated cap is flagged
    assert w.plan_or_none() is None                                     # a dry run writes nothing
    for short in (96.90, 103.53, 115.16, 116.31, 11.55, need - 0.01):   # rounds 1, 2, 3a, 3a + 27 units
        with pytest.raises(SystemExit, match="below the need"):
            w.init("S1-0", one, amount=short)
    got = w.init("S1-0", one, amount=need)
    assert got["block_a_plan"]["source"].startswith("kit default")
    rec = w.plan()["records"]["block_a_plan"]
    assert rec["source"] == "kit default" and rec["default"] == {"plan_code": "A", "c3": True, "split": [2, 2, 1]}
    assert rec["need_usd"] == need and w.plan()["blocks"]["S1-0"]["need"]["need_usd"] == need


def test_block_a_with_a_reused_r_4_refuses(w):
    """VMG-5: Gate B closed TOO CLOSE with no extension, so R_4 and R_5 do not exist."""
    w.s10()
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match="no extension"):
        w.init("A", [{"deal": [0, 1, 2, 3, 4]}], reused=[["R", 1104]])


def _block_b_ready(w, passed: bool):
    w.s10()
    w.gateb()
    w.sealed()
    w.certificate(passed=passed)
    _finish_block_a(w)
    w.seal.seal_block("A")


B_DEAL = [{"deal": [0, 1, 2, 3, 4, 5]}]
BQI = {"kind": "ref_train", "arm": "bqi", "recipe": "bqi", "seed": 1105}
OWN = {"kind": "a0_arm", "arm": "a0", "seed": 1105, "role": "bqi_own_a0", "engine": "Y"}


@pytest.mark.parametrize("hosts, match", [
    ([[BQI]], "own a0 on Y at that seed"),
    ([[BQI], [{**OWN, "seed": 1106}]], "own a0 on Y at that seed"),
    ([[BQI], [OWN], [OWN]], "own a0 on Y at that seed"),
    ([[BQI, OWN]], "two a0 calibrations at one seed")])
def test_after_a_failed_certificate_b_qi_runs_with_its_own_a0_at_each_seed(w, hosts, match):
    """VMG-6 (YB X-10) and VR-4 (the engine refuses a second a0 calibration at one seed in one run folder)."""
    _block_b_ready(w, passed=False)
    with pytest.raises(SystemExit, match=match):
        w.init("B", B_DEAL + [{"hosts": hosts}])
    w.init("B", B_DEAL + [{"hosts": [[BQI], [OWN]]}])                   # paired, on two Y pods
    ys = [h for h in w.plan()["blocks"]["B"]["pending"].values() if h["engine"] == "Y"]   # launch 1
    assert sorted(j["kind"] for h in ys for j in h["jobs"]) == ["a0_arm", "ref_train"]


def test_a_block_is_complete_only_when_its_judge_launch_is_released_and_filed(w):
    """VMG-7, as round 30 (R2, R3) has it: a block's judge launch is part of it; released is not done (gap 1); it is
    done once the judge-completion record names it and is valid, and only over at least the plan's units (Granite
    over 20 units stays open with a valid record); its files, the index and a pods/ subfolder are in the seal."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", [{"deal": [0, 1, 2, 3, 4]}, {"judge": {"judge": "harmbench", "arms": 27}},
                 {"judge": {"judge": "granite", "arms": 20}}])
    for host in ("a-1", "a-2", "a-3", "a-4", "a-5"):
        w.done(host)
    with pytest.raises(SystemExit, match="not complete"):
        w.seal.seal_block("A")                                          # the judge launches are not released
    assert w.tool.release("A")["launches_released"] == 3
    left = w.tool.block_a_open(w.plan())          # released, no record: both still open (gap 1); 4 + 19 + 2 open
    assert len(left) == 25 and left[-2:] == ["judge harmbench", "judge granite"]
    assert w.tool.record_judges("A", *w.file_judges())["judges"] == ["granite", "harmbench"]
    left = w.tool.block_a_open(w.plan())
    assert "judge harmbench" not in left and left[-1] == "judge granite"   # Granite over 20 of the plan's 27 units
    w.not_run()
    pods = write_json(w.root / "judges" / "A" / "pods" / "s1a-harmbench-1" / "bundle-record.json", {"tag": "t"})
    out = w.seal.seal_block("A")
    record = json.loads((w.root / "seals" / "block-A.json").read_text())
    index = w.root / "judges" / "A" / "judge-files-index.json"
    assert {"host": "judges/A", "path": "judge-files-index.json", "sha256": sha(index), "class": "sealed"} in \
        record["files"]
    assert {"host": "judges/A", "path": "pods/s1a-harmbench-1/bundle-record.json", "sha256": sha(pods),
            "class": "sealed"} in record["files"]
    judge_files = [f for f in record["files"] if f["host"] == "judges/A"]
    assert len(judge_files) == 2 * 27 + 2 and out["files"] == 65 + 56   # 54 judge files, the index, pods/
    assert record["judge_record"]["index_sha256"] == sha(index) and record["judge_record"]["units"] == 27
    assert str(JUDGE_SENTINEL) not in json.dumps(record) and SENTINELS[0] not in json.dumps(record)
    spec = importlib.util.spec_from_file_location("s1_backup_for_test", w.root / "backup_records_stage1.py")
    backup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backup)                                     # the backup stages what the seal lists
    sel = backup.select(w.plan(), sorted(n for n, h in w.plan()["hosts"].items() if h["block"] == "A"), 1 << 30)
    assert not any("seal of block A" in m for m in sel["missing"])
    assert sel["digests"]["units/judges/A/judge-files-index.json"] == sha(index)


def test_a_block_other_than_a_with_an_unreleased_launch_is_not_complete(w):
    """VMG-7 outside block A: round 3c's block_a_open covers block A only, so for every other block the released
    count is the only guard (the full-plan mutation run of 24 Oct found no test holding it)."""
    plan = {"blocks": {"B": {"released": 1, "launches": [{"hosts": [CERT_POD]},
                                                         {"judge": {"judge": "granite", "arms": 24}}]}},
            "hosts": {}, "deferrals": [], "requeues": []}
    recorded = set()
    w.mp.setattr(w.tool, "judges_done", lambda plan_, block: recorded)
    recorded.add("granite")
    assert w.tool.block_complete(plan, "B") is False                    # the judge launch is not released
    plan["blocks"]["B"]["released"] = 2
    assert w.tool.block_complete(plan, "B") is True                     # released and its valid record names it
    recorded.clear()                                                    # round 30 (R2): released, no valid record
    assert w.tool.block_complete(plan, "B") is False


def test_a_no_stage_1_record_refuses_every_block(w):
    """VMG-8: sigma above 6.0 pp: no stage-1 pod, the certificate pod included."""
    w.s10()
    w.gateb(sigma=6.2)
    w.cert_records()
    with pytest.raises(SystemExit, match="no stage 1"):
        w.init("cert", [{"hosts": [CERT_POD]}])


@pytest.mark.parametrize("hosts", [
    [[{"kind": "o_only", "arm": "theta0"}], [{"kind": "o_only", "arm": "theta0"}]],
    [[{"kind": "regenerate", "arm": "a0", "seed": 1101}, {"kind": "regenerate", "arm": "a0", "seed": 1101}]]])
def test_a_run_planned_twice_refuses(w, hosts):
    """VMG-9: never re-run a planned or completed job (PREREG's re-run rule)."""
    w.s10()
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match="planned twice"):
        w.init("A", [{"hosts": hosts}] + A_LAUNCHES)


@pytest.mark.parametrize("utc", ["2026-10-23T17:30:00+05:30", "2099-01-01T00:00:00Z"])
def test_a_funding_record_in_another_zone_or_the_future_refuses(w, utc):
    """VMG-10."""
    path = w.funding("A", 500.0, utc=utc)
    with pytest.raises(SystemExit, match="utc"):
        w.tool.init_block(argparse.Namespace(block="S1-0", jobs=w.jobs([{"hosts": [[{"kind": "w1_18"}]]}]),
                                             funding=path, dry_run=False))


def test_the_certification_pod_runs_certify_first(w):
    """VR-5: B10 refuses a gated run whose first evaluation is not certify (eval_adapter.run_sequence)."""
    plan = w.tool.skeleton()
    job = {"kind": "b10_certify", "arm": "a0", "seed": 1101, "points": ["scale:0", "certify"]}
    with pytest.raises(SystemExit, match="certify evaluation first"):
        w.tool.check_job(job, 0, [job], "certify", plan, set())
    w.tool.check_job({**job, "points": ["certify", "scale:0"]}, 0, [job], "certify", plan, set())


def test_recipe_s_training_identity_is_checked_at_release(w):
    """C-3 (§8 Q4): recipe S's training identity must equal f46279e5... (REC's)."""
    w.s10()
    w.gateb()
    w.sealed()
    w.identity[w.rules.RECIPE_S] = "0" * 64
    with pytest.raises(SystemExit, match="training identity"):
        w.init("A", A_LAUNCHES)
    w.identity.clear()
    w.init("A", A_LAUNCHES)
    assert w.plan()["recipes"][w.rules.RECIPE_S]["training_identity"] == w.rules.TRAINING_IDENTITY


# ----- the branch re-pin round: a Y host's recipes in engine Y's tree, by engine Y's code ---------------------------
# (FOCUS "BLOCK A: DIAGNOSTICS POD LAUNCHED" (1): B+Qi's recipe is only in Y's tree and engine X's loader refuses its
# train.constrained_sft field, so init-block cert failed with "missing or differs from its pin (recipe bqi)")

WS_Y_TREE = Path(os.environ.get("STAGE1_ENGINE_Y_TREE", str(KIT.parents[1] / "tmp" / "engine-y-34bfd288")))
REAL_RECIPE_PINS = {"S": "464708c91cd4c297aedf556958893cf84efdeb59b727e5c086a053b81528daf0",   # the committed pins
                    "bqi": "3031aaaa8d3f44057c3d5fa9c0489170940b0bd3a7184365b3b32c9f436dfd1c"}
# engine Y's own code in its tree (a separate python -I -c command, cwd the Y tree, 25 Oct 2026): the config SHA-256 of
# B+Qi's recipe, and recipe S's (equal to oext_unit.json's recipes.allowed.S pin, made with engine X's code)
Y_CONFIG = {"bqi": "37942cf565a7de7d4f68260ec4f769818fb03af9978b0f0356dc90851aa7644c",
            "S": "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"}


def _cert_ready(w) -> None:
    w.s10()
    w.gateb()
    w.cert_records()


def test_the_cert_pod_with_c2_plans_with_b_qi_checked_and_hashed_in_engine_ys_tree(w):
    """The defect's case: the cert pod (C1 recipe S, C2 B+Qi, C3) is planned and released on Y. B+Qi's recipe is not
    in main's tree; it is checked in Y's tree and hashed only by engine Y's code, and so is C1's recipe S on Y. Y's
    values are kept in plan["recipes_y"]; plan["recipes"] (what every pod's runner checks) takes Y's, marked engine Y."""
    r = w.rules
    _cert_ready(w)
    assert not (w.repo / r.RECIPE_BQI).exists() and (w.y_tree / r.RECIPE_BQI).is_file()
    w.calls.clear()
    out = w.init("cert", [{"hosts": [CERT_POD]}])
    plan = w.plan()
    assert out["hosts"] == ["cert-1"] and out["released"] == ["cert-1"] and plan["hosts"]["cert-1"]["engine"] == "Y"
    assert [j["recipe"] for j in plan["hosts"]["cert-1"]["jobs"]] == ["S", "bqi", None]
    assert w.calls == [("Y", "config", r.RECIPE_S), ("Y", "identity", r.RECIPE_S), ("Y", "config", r.RECIPE_BQI)]
    bqi = hashlib.sha256(r.RECIPE_BQI.encode()).hexdigest()           # the World's engine-Y config value
    assert plan["recipes_y"][r.RECIPE_BQI] == {"sha256": r.RECIPE_PINS[r.RECIPE_BQI], "config_sha256": bqi}
    assert plan["recipes"][r.RECIPE_BQI] == {"sha256": r.RECIPE_PINS[r.RECIPE_BQI], "config_sha256": bqi, "engine": "Y"}
    assert plan["recipes_y"][r.RECIPE_S]["training_identity"] == r.TRAINING_IDENTITY
    assert plan["recipes"][r.RECIPE_S]["engine"] == "Y" and "training_identity" not in plan["recipes"][r.RECIPE_S]


def test_a_changed_byte_or_a_missing_b_qi_recipe_in_engine_ys_tree_refuses(w):
    r = w.rules
    _cert_ready(w)
    f = w.y_tree / r.RECIPE_BQI
    good = f.read_bytes()
    f.write_bytes(good[:-2] + bytes([good[-2] ^ 1]) + good[-1:])          # one byte changed
    w.calls.clear()
    with pytest.raises(SystemExit, match=r"missing from engine Y's tree or differs from its pin \(recipe bqi"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    assert ("Y", "config", r.RECIPE_BQI) not in w.calls and "cert" not in w.plan()["blocks"]
    f.unlink()
    with pytest.raises(SystemExit, match=r"missing from engine Y's tree or differs from its pin \(recipe bqi"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    write_json(w.repo / r.RECIPE_BQI, {"recipe": r.RECIPE_BQI})       # the pinned bytes in main's tree do not help
    with pytest.raises(SystemExit, match=r"missing from engine Y's tree or differs from its pin \(recipe bqi"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    f.write_bytes(good)
    assert w.init("cert", [{"hosts": [CERT_POD]}])["released"] == ["cert-1"]


def test_a_b_qi_recipe_on_an_x_host_still_refuses(w):
    """An X host never reads Y's tree or uses Y's code: the job gates refuse B+Qi on X; past them, the X check reads
    main's tree, where B+Qi's recipe is missing (it is in Y's tree, at its pin); with the pinned bytes copied into
    main's tree it is engine X's code that hashes it, and engine X's own loader refuses B+Qi's recipe."""
    r = w.rules
    plan = w.tool.load()
    bqi = {"kind": "ref_train", "arm": "bqi", "seed": 1102, "recipe": "bqi", "engine": "X"}
    with pytest.raises(SystemExit, match="B[+]Qi runs on engine Y only"):
        w.tool.check_job(bqi, 0, [bqi], "B", plan, set())
    with pytest.raises(SystemExit, match="cert_c2 runs on engine Y"):
        w.tool.check_job({**CERT_POD[1], "engine": "X"}, 0, [CERT_POD[1]], "cert", plan, set())
    w.mp.setattr(w.tool, "check_launch_gates", lambda *a: None)        # the recipe check alone
    host = {"engine": "X", "jobs": [dict(bqi)]}
    w.calls.clear()
    with pytest.raises(SystemExit, match=re.escape(f"{r.RECIPE_BQI}: missing or differs from its pin (recipe bqi)")):
        w.tool.release_hosts(plan, "B", [("b-1", host)])
    assert w.calls == [] and plan["hosts"] == {} and "recipes_y" not in plan
    write_json(w.repo / r.RECIPE_BQI, {"recipe": r.RECIPE_BQI})       # the same bytes as Y's tree's, in main's tree
    w.tool.release_hosts(plan, "B", [("b-1", host)])
    assert w.calls == [("X", "config", r.RECIPE_BQI)] and "engine" not in plan["recipes"][r.RECIPE_BQI]
    real_y = WS_Y_TREE / r.RECIPE_BQI                               # engine X's own loader on B+Qi's committed recipe
    done = subprocess.run([sys.executable, "-I", "-B", "-c", "import sys;sys.path.insert(0,sys.argv[1]);"
                           "from experiments.safety_selection.config import load_recipe;load_recipe(sys.argv[2])",
                           str(KIT.parents[1]), str(real_y)], capture_output=True, text=True, timeout=120,
                          cwd=str(KIT.parents[1]), env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert sha(real_y) == REAL_RECIPE_PINS["bqi"] and done.returncode != 0 and "constrained_sft" in done.stderr


def test_an_x_hosts_recipes_are_checked_as_before_and_a_y_first_recipe_is_hashed_again_by_x(w):
    """An X host's recipes: main's tree and engine X's code only, entries as before (no engine mark). When a Y host
    hashed a shared recipe first (S on the cert pod), the next X host hashes it again with X's code and the entry
    becomes X's; engine values that differ refuse, in either order."""
    r = w.rules
    w.mp.setattr(w.tool, "check_launch_gates", lambda *a: None)
    s_job = {"kind": "classifier", "arm": None, "seed": None, "recipe": "S", "engine": "X"}   # no edit to bind
    plan = w.tool.load()
    w.tool.release_hosts(plan, "A", [("a-1", {"engine": "X", "jobs": [dict(s_job)]})])
    assert w.calls == [("X", "config", r.RECIPE_S)] and "recipes_y" not in plan
    assert plan["recipes"][r.RECIPE_S] == {"sha256": r.RECIPE_PINS[r.RECIPE_S],
                                           "config_sha256": hashlib.sha256(r.RECIPE_S.encode()).hexdigest(),
                                           "training_identity": r.TRAINING_IDENTITY}
    y_job = {"kind": "a0_arm", "arm": "a0", "seed": 1105, "role": "bqi_own_a0", "recipe": "S", "engine": "Y"}
    w.tool.release_hosts(plan, "cert", [("cert-1", {"engine": "Y", "jobs": [dict(y_job)]})])   # Y agrees with X
    assert "engine" not in plan["recipes"][r.RECIPE_S] and plan["recipes_y"][r.RECIPE_S]["config_sha256"] == \
        plan["recipes"][r.RECIPE_S]["config_sha256"]
    plan = w.tool.load()
    w.tool.release_hosts(plan, "cert", [("cert-1", {"engine": "Y", "jobs": [dict(y_job)]})])   # Y first
    assert plan["recipes"][r.RECIPE_S]["engine"] == "Y"
    w.calls.clear()
    w.tool.release_hosts(plan, "A", [("a-1", {"engine": "X", "jobs": [dict(s_job)]})])
    assert w.calls == [("X", "config", r.RECIPE_S)] and "engine" not in plan["recipes"][r.RECIPE_S]
    assert plan["recipes"][r.RECIPE_S]["training_identity"] == r.TRAINING_IDENTITY
    for first, second, host_first, host_second in (("Y", "X", ("cert-1", "Y", y_job), ("a-1", "X", s_job)),
                                                   ("X", "Y", ("a-1", "X", s_job), ("cert-1", "Y", y_job))):
        plan = w.tool.load()
        w.config[second][r.RECIPE_S] = "0" * 64                        # the second engine's code disagrees
        name, eng, job = host_first
        w.tool.release_hosts(plan, "A", [(name, {"engine": eng, "jobs": [dict(job)]})])
        name, eng, job = host_second
        with pytest.raises(SystemExit, match="engine Y's config SHA-256 differs from engine X's"):
            w.tool.release_hosts(plan, "A", [(name, {"engine": eng, "jobs": [dict(job)]})])
        w.config[second].clear()


def test_recipe_s_training_identity_on_engine_y_is_checked_with_ys_code(w):
    r = w.rules
    _cert_ready(w)
    w.identity_y[r.RECIPE_S] = "0" * 64
    w.identity[r.RECIPE_S] = r.TRAINING_IDENTITY                       # engine X's would pass: Y's is the one checked
    with pytest.raises(SystemExit, match="training identity under engine Y"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    w.identity_y.clear()
    assert w.init("cert", [{"hosts": [CERT_POD]}])["released"] == ["cert-1"]


def test_the_real_engine_y_code_in_ys_tree_hashes_the_committed_recipes(w):
    """Engine Y's real code and tree (python -I, cwd and import path in Y's tree, code identity checked): the cert pod
    gets B+Qi's and recipe S's config SHA-256 as engine Y's own code computes them; a Y tree whose code is not engine
    Y's pin refuses."""
    r = w.rules
    _cert_ready(w)
    bytecode = set((WS_Y_TREE / "experiments").rglob("*.pyc"))      # Y's frozen tree gets no new file
    for name in ("recipe_sha_y", "recipe_training_identity_y"):
        w.mp.setattr(w.tool, name, w.real[name])
    w.mp.setattr(w.tool, "y_tree", lambda: WS_Y_TREE)
    w.mp.setattr(w.tool, "PY", Path(sys.executable))
    for name in ("S", "bqi"):
        w.mp.setitem(r.RECIPE_PINS, r.RECIPE_NAMES[name], REAL_RECIPE_PINS[name])
    w.mp.setitem(r.ENGINES, "Y", "0" * 64)                             # Y's tree is not this "engine Y"
    with pytest.raises(SystemExit, match="the code in engine Y tree is not engine Y"):
        w.tool.check_recipe_y(w.tool.load(), "bqi")
    w.mp.setitem(r.ENGINES, "Y", Y)
    w.init("cert", [{"hosts": [CERT_POD]}])
    plan = w.plan()
    assert plan["recipes_y"][r.RECIPE_BQI] == {"sha256": REAL_RECIPE_PINS["bqi"], "config_sha256": Y_CONFIG["bqi"]}
    assert plan["recipes_y"][r.RECIPE_S] == {"sha256": REAL_RECIPE_PINS["S"], "config_sha256": Y_CONFIG["S"],
                                             "training_identity": r.TRAINING_IDENTITY}
    assert plan["recipes"][r.RECIPE_BQI]["config_sha256"] == Y_CONFIG["bqi"]
    assert set((WS_Y_TREE / "experiments").rglob("*.pyc")) == bytecode


def test_fallback_c_refuses_o_ext_only_jobs_and_never_changes_after_a_500_bank_job(w):
    """C-1: addendum §11 point 1 fallback (c), overrefusal_bank.status = dev100_recipe_cap."""
    w.s10()
    w.gateb()
    w.sealed()
    rec = {"kind": "stage1 oext fallback", "status": "dev100_recipe_cap", "reason": "oext_eval not verified",
           "utc": "u", "recorded_by": "t"}
    with pytest.raises(SystemExit, match="dev100_recipe_cap"):
        w.tool.record_simple("oext_fallback", *w.record({**rec, "status": "other"}))
    w.tool.record_simple("oext_fallback", *w.record(rec))
    assert w.plan()["records"]["oext_fallback"]["status"] == "dev100_recipe_cap"
    with pytest.raises(SystemExit, match="O-ext pass only"):
        w.init("A", [{"hosts": [[{"kind": "o_only", "arm": "theta0"}]]}] + A_LAUNCHES)
    w.init("A", A_LAUNCHES)
    plan = w.plan()
    plan["records"]["oext_fallback"] = None
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="never changes once a 500-bank job"):
        w.tool.record_simple("oext_fallback", *w.record(rec))


def test_an_engine_unit_complete_record_is_sealed(w):
    """VR-1: an engine unit's COMPLETE.json carries its evaluation summary, so it is never 'readable'."""
    assert w.seal.classify("COMPLETE.json") == "sealed"
    assert w.seal.classify("JOB-DONE.json") == "readable" and w.seal.classify("cost-ledger.json") == "readable"


# ===== B15 round 2 (addendum §19-§23; notes/b15r2-build.json) ======================================================

REPO = KIT.parents[1]                 # this repository (hashing only: no data file is parsed here)


@pytest.mark.parametrize("sigma, code", [(0.0, "A"), (4.5, "A"), (4.5000001, "B"), (6.0, "B"), (6.0000001, "none"),
                                         (7, "none")])
def test_the_plan_ab_record_is_derived_from_gate_bs_verdict_at_its_one_field(w, sigma, code):
    """Item 3: the kit reads result.readings.plain.sigma_hat_pp of the pinned verdict file and applies REV4 §1.3
    (<= 4.5 pp A; 4.5 < x <= 6.0 B; > 6.0 none); the record names the file by SHA-256, the field, the value, the code."""
    w.s10()
    p, h = w.gateb_final()
    w.tool.record_simple("gateb_final", p, h)
    vp, vh = w.verdict(sigma)
    out = w.tool.record_simple("plan_ab", vp, vh)
    assert out == {"recorded": "plan_ab", "sha256": vh, "field": "result.readings.plain.sigma_hat_pp",
                   "sigma_pp": float(sigma), "code": code}
    rec = w.plan()["records"]["plan_ab"]
    assert (rec["sha256"], rec["field"], rec["sigma_pp"], rec["code"], rec["derived"], rec["gateb_final_sha256"]) == \
        (vh, "result.readings.plain.sigma_hat_pp", float(sigma), code, True, h)
    assert rec["rule"].startswith("REV4 §1.3")


@pytest.mark.parametrize("case", ["another hash", "measurements phase", "no field", "field elsewhere", "a string",
                                  "a boolean", "negative", "twice", "before the final record"])
def test_another_verdict_file_hash_or_field_refuses(w, case):
    w.s10()
    p, h = w.gateb_final()
    if case != "before the final record":
        w.tool.record_simple("gateb_final", p, h)
    body = {"another hash": {}, "measurements phase": {"phase": "measurements"},
            "no field": {"result": {"readings": {"plain": {"D_pp": 1.0}}}},
            "field elsewhere": {"result": {"readings": {"G2": {"sigma_hat_pp": 3.0}}}, "sigma_hat_pp": 3.0},
            "a string": {"result": {"readings": {"plain": {"sigma_hat_pp": "3.9"}}}},
            "a boolean": {"result": {"readings": {"plain": {"sigma_hat_pp": True}}}},
            "negative": {"result": {"readings": {"plain": {"sigma_hat_pp": -1.0}}}}}.get(case, {})
    vp, vh = w.verdict(3.9, **body)
    if case == "another hash":
        w.mp.setattr(w.rules, "GATEB_VERDICT", {"path": "x", "sha256": "0" * 64})
    if case == "twice":
        w.tool.record_simple("plan_ab", vp, vh)
    with pytest.raises(SystemExit):
        w.tool.record_simple("plan_ab", vp, vh)
    if case != "twice":
        assert w.tool.load()["records"]["plan_ab"] is None


def test_a_hand_edited_plan_ab_record_refuses_every_later_block(w):
    w.s10(branch="full")
    w.gateb(sigma=3.9)
    w.sealed()
    for change in ({"code": "B"}, {"sha256": "0" * 64}, {"field": "result.readings.G2.sigma_hat_pp"},
                   {"derived": False}, {"sigma_pp": 5.0}):
        plan = w.plan()
        good = dict(plan["records"]["plan_ab"])
        plan["records"]["plan_ab"].update(change)
        w.mac.save_plan(plan)
        with pytest.raises(SystemExit, match="not the one derived"):
            w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES, dry_run=True)
        plan["records"]["plan_ab"] = good
        w.mac.save_plan(plan)
    assert w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES, dry_run=True)["dry_run"] is True


def test_the_round_2_pins_are_the_files_in_this_repository():
    """Items 1, 3, 6: the pinned files hash to their pins here (hashing only; nothing is parsed)."""
    sys.path.insert(0, str(KIT))
    try:
        sys.modules.pop("stage1_rules", None)
        import stage1_rules as r
        for pin in (r.GATEB_VERDICT, r.D2_POOL_PINS, r.D2_REQ8_RECORD, r.S_POOL_RECORD, r.YHASH_PIN, r.C3_RECORD,
                    r.A1_EDIT, {"path": r.MAN_PATH, "sha256": r.MAN_SHA256},
                    {"path": r.MAN1_PATH, "sha256": r.MAN1_SHA256}):      # fix round (F4): Gate B's MANIFEST, MAN1
            assert sha(REPO / pin["path"]) == pin["sha256"], pin["path"]
        for rel, pin in {**r.D2_CODE, **r.S1_CODE}.items():           # round 3b/3c: the S1 package (re-pinned, a02c1aa)
            assert sha(REPO / rel) == pin, rel
        assert r.D2_POOL_PINS["path"] == ".ai/inputs/stage1-post-w1-20261023/pool-pins/representation_pools.filled.json"
        assert r.C3_RECORD == {"path": ".ai/inputs/stage1-post-w1-20261023/c3/c3_subsample_record.json",
                               "sha256": "1a24c7a39eb45fd94527806b16edd358975169661ed2a079f8b4c1d8793dd92e"}
        assert r.S1_CODE["scripts/stage1_s1/__init__.py"] == \
            "818919ca18627b7169d80c2a6f6c24149f6e1c529bff9d37a5ddee2122bddd32"           # VR2-5: packed and pinned
        assert len(r.S1_CODE) == 11 and not hasattr(r, "S1_UNPINNED") and r.S1_COMMIT == "3ea5ae1"
        assert {k: r.S1_CODE[k] for k in ("scripts/stage1_s1/oext_unit.py", "scripts/stage1_s1/settings/oext_unit.json")} \
            == {"scripts/stage1_s1/oext_unit.py": "ae2fb5b5fbea36cbd2b27c4eaa20f10504b9856961ae8ee100311c923876b8e3",
                "scripts/stage1_s1/settings/oext_unit.json":
                    "3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189"}   # the branch re-pin (11.7)
        assert sha(REPO / "scripts/stage1_s1/c3_subsample/write_c3_subsample.py") == r.C3_WRITER["script_sha256"]
        assert sha(REPO / "scripts/stage1_s1/c3_subsample/settings/write_c3_subsample.json") == \
            r.C3_WRITER["settings_sha256"]
        assert r.GATEB_VERDICT["sha256"] == "bec5f103a1c5164ce0d4364cdf3d46c5a66ad941cd2f81a47d381e948811d404"
        assert (r.D2_POOL_PINS["sha256"], r.D2_REQ8_RECORD["sha256"]) == (
            "a33e96649385b6bc9bcdb35493228c716fb02fc610514c4fba98b23eba345d5e",
            "cc04b6634502406f4e2110e21ae0f1b6ecd0d1737f5dfbcf4a6b1320718be2cc")
        assert r.D2_POOLS == {"plant": "37739f40e476ff8bdecacdc47a806b36a0533b0f079919ab4d63d84832e67a59",
                              "decoy": "d102b665b8f2fc538fdf08fb85020c1e8a1f8a1bf9265f999e55133d473f9db6"}
        assert r.ENGINES["Y"] == "34bfd28879fdefc5d6605cb73a707d1edd2ec5d102b4b86c0026bc6ac36969f6"   # §23
        assert r.Y_TREE_DEFAULT == "tmp/engine-y-34bfd288"
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("stage1_rules", None)


def test_gate_bs_real_manifest_lists_8_distinct_unit_groups():
    """Fix round (F4): LN-15e's groups come from Gate B's sealed MANIFEST (pinned above); the real file lists exactly 8
    distinct unit groups, so plan_tool.rescore_groups plans the re-score in production (file entries read, no data)."""
    sys.path.insert(0, str(KIT))
    try:
        sys.modules.pop("stage1_rules", None)
        import stage1_rules as r
        man = json.loads((REPO / r.MAN_PATH).read_text())
        groups = [e["unit"] for e in man["files"] if e.get("family") == "unit"]
        assert len(groups) == len(set(groups)) == r.UNITS == 8
    finally:
        sys.path.remove(str(KIT))
        sys.modules.pop("stage1_rules", None)


C2_RULE = {    # addendum §22 point 1, written here by hand
    "statistic": "constrained.mean_weight.t2_5", "file": "steps.jsonl", "steps": 38,
    "job": "cert_c2: B+Qi, seed 1101, to e1, training only",
    "binds": {"rule": "the value is <= 0.50 at some step s <= 3", "value_at_most": 0.5, "step_at_most": 3},
    "equals_recipe_b_by_construction": {"rule": "the value is >= 0.90 at 20 or more of the 38 steps",
                                        "value_at_least": 0.9, "steps_at_least": 20},
    "neither": "partly binding", "both": "both labels are reported", "labels_change_the_arm": False,
    "on_equals_recipe_b": "the lead writes a proposal to the user; B+Qi runs as registered unless the user decides "
                          "otherwise",
    "reference": "addendum §22 point 1 (2026-10-23T16:16 UTC)"}


def test_the_c2_thresholds_record_carries_section_22_point_1_exactly(w, capsys):
    out = w.repo / "records" / "c2.json"
    out.parent.mkdir(exist_ok=True)
    assert w.tool.main(["write-thresholds", "--out", str(out), "--recorded-by", "test"]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["sha256"] == sha(out)
    doc = json.loads(out.read_text())
    assert doc["kind"] == "stage1 c2 binding thresholds" and doc["thresholds"] == C2_RULE and doc["recorded_by"] == "test"
    with pytest.raises(SystemExit, match="never overwritten"):
        w.tool.write_thresholds(str(out), "test")
    for change in ({"binds": {**C2_RULE["binds"], "value_at_most": 0.49}},
                   {"binds": {**C2_RULE["binds"], "step_at_most": 4}},
                   {"equals_recipe_b_by_construction": {**C2_RULE["equals_recipe_b_by_construction"],
                                                        "steps_at_least": 19}},
                   {"equals_recipe_b_by_construction": {**C2_RULE["equals_recipe_b_by_construction"],
                                                        "value_at_least": 0.85}},
                   {"labels_change_the_arm": True}, {"steps": 38.0}, {"statistic": "constrained.mean_weight.t1"}):
        bad = {**doc, "thresholds": {**C2_RULE, **change}}
        with pytest.raises(SystemExit, match="exactly"):
            w.tool.record_simple("thresholds", *w.record(bad))
    with pytest.raises(SystemExit, match="exactly"):
        w.tool.record_simple("thresholds", *w.record({**doc, "thresholds": [0.5, 1.0]}))      # round 1's free form
    assert w.tool.main(["record-thresholds", str(out), "--sha256", sha(out)]) == 0
    assert w.plan()["records"]["thresholds"]["sha256"] == sha(out)
    with pytest.raises(SystemExit, match="already recorded"):
        w.tool.record_simple("thresholds", str(out), sha(out))


def _steps(values, extra=None) -> list[str]:
    """38 steps.jsonl lines, step k (1-based) holding values[k - 1], plus fields the reader must ignore."""
    return [json.dumps({"step": k, "rows": ["r"], "loss": SENTINELS[0], **(extra or {}),
                        "constrained": {"objective": 9.9, "mean_weight": {"t1": 0.1, "t2_5": v, "t_after_5": 0.2}}})
            for k, v in enumerate(values, 1)]


@pytest.mark.parametrize("values, labels, binds_at, high", [
    ([0.8] * 38, ["partly binding"], [], 0),
    ([0.51, 0.51, 0.50] + [0.8] * 35, ["binds"], [3], 0),                       # 0.50 exactly at step 3
    ([0.51, 0.51, 0.51, 0.50] + [0.8] * 34, ["partly binding"], [], 0),         # step 4 is too late
    ([0.5000001] + [0.8] * 37, ["partly binding"], [], 0),
    ([0.2, 0.8, 0.3] + [0.8] * 35, ["binds"], [1, 3], 0),
    ([0.90] * 20 + [0.89] * 18, ["equals recipe B by construction"], [], 20),   # 0.90 exactly, 20 steps
    ([0.90] * 19 + [0.8999999] * 19, ["partly binding"], [], 19),              # 19 steps
    ([0.4] + [0.95] * 20 + [0.6] * 17, ["binds", "equals recipe B by construction"], [1], 20),   # both reported
    ([0.95] * 38, ["equals recipe B by construction"], [], 38)])
def test_the_c2_reader_labels_at_every_boundary(w, values, labels, binds_at, high):
    out = w.rules.c2_labels(w.rules.c2_reading(_steps(values)))
    assert out == {"statistic": "constrained.mean_weight.t2_5", "labels": labels, "binds_at_steps": binds_at,
                   "steps_at_or_above_0.90": high, "steps": 38, "arm_changed": False}


@pytest.mark.parametrize("lines", [
    _steps([0.8] * 37), _steps([0.8] * 39), _steps([0.8] * 38)[:5] + _steps([0.8] * 38)[4:-1],
    [json.dumps({"step": 0, "constrained": {"mean_weight": {"t2_5": 0.8}}})] + _steps([0.8] * 38)[1:],
    _steps([None] + [0.8] * 37), _steps([True] + [0.8] * 37), _steps(["0.8"] + [0.8] * 37),
    [json.dumps({"step": 1, "constrained": {"mean_weight": {"t1": 0.8}}})] + _steps([0.8] * 38)[1:],
    ["{not json"] + _steps([0.8] * 38)[1:]])
def test_the_c2_reader_refuses_an_incomplete_or_malformed_steps_file(w, lines):
    with pytest.raises(ValueError):
        w.rules.c2_reading(lines)


def test_c2_label_reads_only_the_statistic_with_the_recorded_thresholds(w, capsys):
    steps = w.repo / "pulled" / "steps.jsonl"
    steps.parent.mkdir(parents=True)
    steps.write_text("\n".join(_steps([0.3] + [0.8] * 37, extra={"text": "SENTINEL-U-VALUE"})) + "\n")
    with pytest.raises(SystemExit, match="thresholds record is not recorded"):
        w.tool.c2_label(str(steps), sha(steps))
    w.thresholds()
    with pytest.raises(SystemExit, match="SHA-256 differs"):
        w.tool.c2_label(str(steps), "0" * 64)
    assert w.tool.main(["c2-label", str(steps), "--sha256", sha(steps)]) == 0
    text = capsys.readouterr().out
    out = json.loads(text)
    assert out["labels"] == ["binds"] and out["binds_at_steps"] == [1] and out["arm_changed"] is False
    assert out["thresholds_sha256"] == w.plan()["records"]["thresholds"]["sha256"]
    assert not any(s in text for s in SENTINELS)                      # no other field of a record is printed


def test_c3_takes_the_subsample_file_and_its_record_by_sha256_from_the_lead_record(w):
    w.s10()
    w.gateb()
    rec = w.c3()
    w.thresholds()
    out = w.init("cert", [{"hosts": [CERT_POD]}])
    c3 = next(j for j in w.plan()["hosts"]["cert-1"]["jobs"] if j["kind"] == "cert_c3")
    assert c3["c3"] == {"subsample": rec["subsample"], "record": rec["record"]}
    assert out["c3"] == "planned: subsample " + rec["subsample"]["sha256"]
    with pytest.raises(SystemExit, match="already recorded"):
        w.c3()


@pytest.mark.parametrize("change, match", [
    ({"subsample": {"file_sha256": "0" * 64, "bank": "subsample-" + "0" * 64, "items": 16}}, "does not name"),
    ({"role": "edit_confirmation"}, "does not name"),
    ({"draw": {"script_sha256": "0" * 64, "settings_sha256": "a8547e2dcd27cbbdbed48eef3cb636a4503a6f3d6101123080b26b9baa1cfc60"}},
     "does not name"),
    ({"prepared_manifest_sha256": "0" * 64}, "does not name"),
    ({"source": {"bank": "hidden", "manifest_sha256": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"}},
     "does not name"),
    ({"kind": "stage1 c3 something"}, "does not name")])
def test_a_c3_record_that_does_not_match_its_file_p_or_the_writer_refuses(w, change, match):
    with pytest.raises(SystemExit, match=match):
        w.c3(**change)
    assert w.tool.load()["records"]["c3"] is None


@pytest.mark.parametrize("case", ["another record file", "the pinned path, other bytes"])
def test_the_c3_record_must_be_the_pinned_post_w1_record(w, case):
    """Round 3b item 2: record-c3 takes only the writer record rules.C3_RECORD names (the post-W1 inputs folder,
    1a24c7a3...): a valid record at another path, or at the pinned path with other bytes, refuses."""
    body = w.c3_files()
    pinned = dict(w.rules.C3_RECORD)
    if case == "another record file":
        other = w.repo / "records" / "c3-copy.json"
        other.write_bytes(Path(body["record"]["path"]).read_bytes())
        body["record"] = {"path": str(other), "sha256": sha(other)}
    else:
        rp = Path(body["record"]["path"])
        rp.write_text(rp.read_text() + " ")
        body["record"]["sha256"] = sha(rp)
    with pytest.raises(SystemExit, match="must be the writer's record at"):
        w.tool.record_simple("c3", *w.record(body))
    assert w.tool.load()["records"]["c3"] is None and w.rules.C3_RECORD == pinned


def test_a_c3_pin_whose_file_changed_or_has_fifteen_items_refuses(w):
    body = w.c3_files()
    (w.repo / body["subsample"]["path"]).write_text("changed\n")
    with pytest.raises(SystemExit, match="differs from its SHA-256"):
        w.tool.record_simple("c3", *w.record(body))
    body = w.c3_files()
    rec = json.loads(Path(body["record"]["path"]).read_text())
    rec["subsample"]["items"] = 15
    Path(body["record"]["path"]).write_text(json.dumps(rec))
    body["record"]["sha256"] = sha(body["record"]["path"])
    w.pin_c3_record(body)                                           # round 3b: the edited record is the pinned one
    with pytest.raises(SystemExit, match="16 items"):
        w.tool.record_simple("c3", *w.record(body))


def test_the_c3_fallback_drops_c3_and_says_so(w):
    w.s10()
    w.gateb()
    w.thresholds()
    with pytest.raises(SystemExit, match="plan C3 .* or record its"):
        w.init("cert", [{"hosts": [[CERT_POD[0], CERT_POD[1]]]}])
    fb = {"kind": "stage1 c3 fallback", "status": "dropped", "reason": "not verified", "utc": "u", "recorded_by": "t"}
    with pytest.raises(SystemExit, match="status 'dropped'"):
        w.tool.record_simple("c3_fallback", *w.record({**fb, "status": "kept"}))
    w.tool.record_simple("c3_fallback", *w.record(fb))
    assert w.plan()["records"]["c3_fallback"]["status"] == "dropped"
    with pytest.raises(SystemExit, match="C3 is dropped"):
        w.init("cert", [{"hosts": [CERT_POD]}])
    with pytest.raises(SystemExit, match="already recorded"):
        w.c3()
    out = w.init("cert", [{"hosts": [[CERT_POD[0], CERT_POD[1]]]}])
    assert out["c3"] == "dropped: the §22 point 2 fallback record is recorded"


def test_c3_fallback_after_the_c3_pin_refuses(w):
    w.c3()
    fb = {"kind": "stage1 c3 fallback", "status": "dropped", "reason": "r", "utc": "u", "recorded_by": "t"}
    with pytest.raises(SystemExit, match="already recorded"):
        w.tool.record_simple("c3_fallback", *w.record(fb))


def _block_a_ready(w):
    w.s10(branch="full")
    w.gateb()
    w.sealed()


# ----- (D, 25 Oct: pod a-1) J6 complete, J5 crashed, J7 and J8 not started: they move to a new diagnostics pod ------


def _a1_pulled(w, record_change=None, pool_listed=True) -> dict:
    """a-1 (the diagnostics pod J6, J5, J7, J8) pulled and recorded: J6 complete with its untuned/ outputs (a synthetic
    s3_orig pool and a text-free record of J6's schema naming it), J5 crashed, J7 and J8 not started."""
    _block_a_ready(w)
    w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES)
    tree = w.root / "retrieved" / "a-1" / "tree"
    pool = write_json(tree / "job-0/untuned/s3_orig.pool.json", {"kind": "stage1 text pool", "version": 1,
                                                                  "name": "s3_orig", "items": "synthetic"})
    record = {"kind": "stage1 untuned answers record", "version": 1, "complete": True,
              "full_files": {"s3_orig.pool.json": sha(pool)}, "lists": {"s3": {"s3_orig_pool_sha256": sha(pool)}}}
    record.update(record_change or {})
    rec = write_json(tree / "job-0/untuned/untuned_answers_record.json", record)
    outputs = {"job-0/untuned/untuned_answers_record.json": sha(rec)}
    if pool_listed:
        outputs["job-0/untuned/s3_orig.pool.json"] = sha(pool)
    jobs = [{"index": i, "kind": k, "arm": None, "seed": None, "status": s, "engine": "X", "engine_sha256": X,
             **({"outputs": outputs} if i == 0 else {})}
            for i, (k, s) in enumerate((("untuned_answers", "complete"), ("rep_pass", "crashed"),
                                        ("l1_scan", "not_started"), ("classifier", "not_started")))]
    write_json(tree / "JOB-DONE.json", {"host": "a-1", "jobs": jobs})
    w.tool.record_done("a-1")
    return {"pool": pool, "record": rec}


def _pack_s3_orig(w, digest: str) -> str:
    """engine X's packed stage re-packed with the input pool:s3_orig (synthetic sealed-files.json and receipt)."""
    packed = w.root / "setup" / "packed-stage1-X"
    rel = "inputs/pool-s3_orig/s3_orig.pool.json"
    sealed = write_json(packed / "sealed-files.json", {"files": {rel: digest}, "inputs": {"pool:s3_orig": rel}})
    write_json(packed / "setup-receipt.json", {"engine_sha256": X, "sealed_files_sha256": sha(sealed)})
    return sha(sealed)


def test_defer_moves_a_1s_j5_j7_j8_to_a_new_diagnostics_pod_with_j6s_s3_orig_pool_pinned(w):
    """J6 is complete and never re-run (PREREG): only J5 (crashed), J7 and J8 (not started) move, in order, to a new
    block-A diagnostics host bound to the current packed stage, which must hold pool:s3_orig at the SHA-256 J6's own
    record gives; the moved J5 carries that pin; only the crashed J5 is paid from block A's contingency (with the new
    pod's overhead); the new host is outside the recorded plan's launches (as every defer) and its completed jobs close
    block A's diagnostics labels."""
    r = w.rules
    files = _a1_pulled(w)
    pool_sha = sha(files["pool"])
    with pytest.raises(SystemExit, match="sealed-files.json is missing or is not its receipt's"):
        w.tool.defer("a-1")                                              # the pack first (pool:s3_orig at J6's pin)
    _pack_s3_orig(w, "0" * 64)
    with pytest.raises(SystemExit, match=re.escape("holds no pool:s3_orig at J6's pin")):
        w.tool.defer("a-1")
    bound = _pack_s3_orig(w, pool_sha)
    before = w.plan()["contingency"]["A"]["remaining_usd"]
    out = w.tool.defer("a-1")
    plan = w.plan()
    new = plan["hosts"][out["to"]]
    assert out["to"] not in ("a-1",) and new["block"] == "A" and new["role"] == "diagnostics" and new["engine"] == "X"
    assert [j["kind"] for j in new["jobs"]] == ["rep_pass", "l1_scan", "classifier"]
    assert all(j["status"] == "planned" and j["deferred_from"] == "a-1" for j in new["jobs"])
    assert new["sealed_files_sha256"] == bound
    assert new["jobs"][0]["s3_orig"] == {"host": "a-1", "index": 0, "sha256": pool_sha,
                                         "record": {"path": "job-0/untuned/untuned_answers_record.json",
                                                    "sha256": sha(files["record"])},
                                         "pool": {"path": "job-0/untuned/s3_orig.pool.json", "sha256": pool_sha}}
    assert "s3_orig" not in new["jobs"][1] and "s3_orig" not in new["jobs"][2]
    assert new["jobs"][0]["d2"] == plan["hosts"]["a-1"]["jobs"][1]["d2"]     # the D-2 pins move with it
    assert plan["hosts"]["a-1"]["jobs"][0]["status"] == "complete"            # J6 stays; never re-run
    spent = plan["contingency"]["A"]["spent"]
    cost = r.rerun_cost_usd(plan["hosts"]["a-1"]["jobs"][1], True)
    assert [(s["kind"], s["cost_usd"]) for s in spent] == [("rep_pass", cost)]
    assert plan["contingency"]["A"]["remaining_usd"] == pytest.approx(before - cost)
    assert plan["deferrals"][-1]["from"] == "a-1" and plan["deferrals"][-1]["from_indices"] == [1, 2, 3]
    assert out["to"] not in [n for launch in plan["blocks"]["A"]["launches"] for n in launch.get("hosts", [])]
    w.tool.check_planned_group_a(plan, "A")                                   # the recorded plan still conforms
    open_before = w.tool.block_a_open(plan)
    assert {"rep_pass", "l1_scan", "classifier"} <= {x.split(" ")[0] for x in open_before}
    w.done(out["to"])
    left = {x.split(" ")[0] for x in w.tool.block_a_open(w.plan())}
    assert not left & {"rep_pass", "l1_scan", "classifier", "untuned_answers"}
    with pytest.raises(SystemExit, match="already deferred"):
        w.tool.defer("a-1")


@pytest.mark.parametrize("change, listed, match", [
    ({"complete": False}, True, "is not a complete"), ({"kind": "stage1 other record"}, True, "is not a complete"),
    ({"full_files": {"s3_orig.pool.json": "0" * 64}}, True, "does not name its s3_orig.pool.json"),
    (None, False, "recorded no untuned_answers_record.json or no s3_orig.pool.json")])
def test_j6s_s3_orig_pin_refuses_a_record_that_does_not_name_the_pool(w, change, listed, match):
    files = _a1_pulled(w, record_change=change, pool_listed=listed)
    _pack_s3_orig(w, sha(files["pool"]))
    with pytest.raises(SystemExit, match=match):
        w.tool.defer("a-1")
    assert not w.plan()["deferrals"]


def test_j6s_s3_orig_pin_refuses_a_pulled_record_changed_after_record_done(w):
    files = _a1_pulled(w)
    _pack_s3_orig(w, sha(files["pool"]))
    files["record"].write_bytes(files["record"].read_bytes() + b" ")
    with pytest.raises(SystemExit, match="differs from its recorded SHA-256"):
        w.tool.defer("a-1")
    assert not w.plan()["deferrals"]


def test_j5_records_recipe_s_in_new_plans_and_on_a_deferred_host_and_its_price_is_unchanged(w):
    """(G) J5's two steps pass recipe S (representation_pass.json pins it), so its job record names S: in a new plan,
    on a deferred host whose source record (planned before this round) named B, and in the re-run keys (an old B
    record and a new S one are the same job). The price does not depend on it; a lead spec naming another refuses."""
    r = w.rules
    _a1_pulled(w)
    plan = w.plan()
    rec = {j["kind"]: j for j in plan["hosts"]["a-1"]["jobs"]}
    assert (rec["rep_pass"]["recipe"], rec["classifier"]["recipe"], rec["l1_scan"]["recipe"]) == ("S", "S", "B")
    assert r.RECIPE_S in plan["recipes"]
    fx = plan["fixture"]
    assert r.job_record("rep_pass", None, None, None, None, fx, recipe="S")["spend_upper_s"] == \
        r.job_record("rep_pass", None, None, None, None, fx, recipe="B")["spend_upper_s"]
    with pytest.raises(SystemExit, match="a rep_pass job runs recipe S"):
        w.tool.check_job({"kind": "rep_pass", "recipe": "B"}, 0, [], "A", plan, set())
    old = json.loads(json.dumps(plan))
    old["hosts"]["a-1"]["jobs"][1]["recipe"] = "B"                         # a-1 as recorded before this round
    w.mac.save_plan(old)
    with pytest.raises(SystemExit, match="planned twice"):
        w.tool.refuse_duplicates(w.plan(), [{"kind": "rep_pass", "engine": "X", "recipe": "S"}])
    _pack_s3_orig(w, w.plan()["hosts"]["a-1"]["jobs"][0]["outputs"]["job-0/untuned/s3_orig.pool.json"])
    out = w.tool.defer("a-1")
    moved = w.plan()["hosts"][out["to"]]["jobs"][0]
    assert moved["kind"] == "rep_pass" and (moved["recipe"], moved["recipe_was"]) == ("S", "B")
    assert w.plan()["hosts"][out["to"]]["jobs"][1]["recipe"] == "B" and "recipe_was" not in \
        w.plan()["hosts"][out["to"]]["jobs"][1]                             # J7 keeps REC (its script's pin)


def test_j5_and_j8_carry_the_d2_pins_by_sha256_in_the_plan(w):
    """Item 1-2: the filled pins file and REQ-8's record by SHA-256, the plant and decoy pools as both records give
    them, s3_safe from the S-pool record (J5 only)."""
    _block_a_ready(w)
    w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES)
    jobs = {j["kind"]: j for j in w.plan()["hosts"]["a-1"]["jobs"]}
    pins = {"pool_pins": dict(w.rules.D2_POOL_PINS), "req8_record": dict(w.rules.D2_REQ8_RECORD)}
    assert jobs["rep_pass"]["d2"] == {**pins, "pools": {"plant": w.pools["plant"], "decoy": w.pools["decoy"],
                                                        "s3_safe": w.pools["s3_safe"]}}
    assert jobs["classifier"]["d2"] == {**pins, "pools": {"plant": w.pools["plant"], "decoy": w.pools["decoy"]}}
    assert "d2" not in jobs["l1_scan"] and "d2" not in jobs["untuned_answers"]


@pytest.mark.parametrize("case, match", [
    ("rep_pass first", "needs J6"), ("rep_pass on Y", "runs on engine X"), ("classifier on Y", "runs on engine X"),
    ("req8 pool differs", "plant pool's SHA-256"), ("filled pins changed", "filled pool pins file"),
    ("s-pool record changed", "S-pool record"), ("s-pool s3 mismatch", "names no s3_safe")])
def test_the_d2_plan_gates_refuse(w, case, match):
    _block_a_ready(w)
    r = w.rules
    hosts = [DIAG_POD]
    if case == "rep_pass first":
        hosts = [[{"kind": "rep_pass"}, {"kind": "untuned_answers"}]]
    elif case == "rep_pass on Y":
        hosts = [[{"kind": "untuned_answers"}, {"kind": "rep_pass", "engine": "Y"}]]
    elif case == "classifier on Y":
        hosts = [[{"kind": "classifier", "engine": "Y"}]]
    elif case == "req8 pool differs":
        f = w.repo / r.D2_REQ8_RECORD["path"]
        doc = json.loads(f.read_text())
        doc["pools"]["plant"]["sha256"] = "0" * 64
        w.mp.setattr(r, "D2_REQ8_RECORD", {"path": r.D2_REQ8_RECORD["path"], "sha256": sha(write_json(f, doc))})
    elif case == "filled pins changed":
        (w.repo / r.D2_POOL_PINS["path"]).write_text("{}")
    elif case == "s-pool record changed":
        (w.repo / r.S_POOL_RECORD["path"]).write_text("{}")
    elif case == "s-pool s3 mismatch":
        f = w.repo / r.S_POOL_RECORD["path"]
        doc = json.loads(f.read_text())
        doc["full_files"]["s3_safe.pool.json"] = "0" * 64
        w.mp.setattr(r, "S_POOL_RECORD", {"path": r.S_POOL_RECORD["path"], "sha256": sha(write_json(f, doc))})
    with pytest.raises(SystemExit, match=match):
        w.init("A", [{"hosts": hosts}] + A_LAUNCHES, dry_run=True)


def test_the_d2_fallback_record_names_its_jobs_and_never_changes_after_they_are_planned(w):
    _block_a_ready(w)
    fb = {"kind": "stage1 d2 fallback", "reason": "D-2 not verified", "utc": "u", "recorded_by": "t"}
    for jobs in ([], ["l1_scan"], ["classifier", "classifier"], "classifier"):
        with pytest.raises(SystemExit, match="jobs among"):
            w.tool.record_simple("d2_fallback", *w.record({**fb, "jobs": jobs}))
    w.tool.record_simple("d2_fallback", *w.record({**fb, "jobs": ["classifier"]}))
    with pytest.raises(SystemExit, match="already recorded"):
        w.tool.record_simple("d2_fallback", *w.record({**fb, "jobs": ["rep_pass"]}))
    w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES)
    jobs = {j["kind"]: j for j in w.plan()["hosts"]["a-1"]["jobs"]}
    fbrec = w.plan()["records"]["d2_fallback"]
    assert jobs["classifier"]["d2"] == {"fallback": {"path": fbrec["path"], "sha256": fbrec["sha256"]}, "pools": {}}
    assert set(jobs["rep_pass"]["d2"]) == {"pool_pins", "req8_record", "pools"}      # J5 keeps D-2


def test_the_d2_fallback_for_j5_keeps_s3_safe_only_and_refuses_once_j5_is_planned(w):
    _block_a_ready(w)
    fb = {"kind": "stage1 d2 fallback", "reason": "r", "utc": "u", "recorded_by": "t", "jobs": ["rep_pass", "classifier"]}
    p, h = w.record(fb)
    w.tool.record_simple("d2_fallback", p, h)
    w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES)
    rep = next(j for j in w.plan()["hosts"]["a-1"]["jobs"] if j["kind"] == "rep_pass")
    assert rep["d2"] == {"fallback": {"path": p, "sha256": h}, "pools": {"s3_safe": w.pools["s3_safe"]}}
    plan = w.plan()
    plan["records"]["d2_fallback"] = None
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="never changes"):
        w.tool.record_simple("d2_fallback", *w.record({**fb, "jobs": ["rep_pass"]}))


def test_block_a_needs_under_plan_a_for_both_branches_and_every_launch_split_by_hand(w):
    """Item 8, by hand: plan A's 20 runs are 5 pods of 4 (pod 4 holds a0@1104 at 38 steps, the rest 33-step arms or a
    mix). Every pod's cap is 7.5 h (Branch full) or 7.0 h (Branch 128); spend per arm job = 3,120 + O500 s; the need
    = cents(1.25 x cents(max over launches k of (spend before k + $6 + $1.85 x caps of k)))."""
    for branch, cap, o in (("full", 7.5, 1517.0), ("128", 7.0, 1024.0)):
        s = (2520 + 4 * (3120 + o)) / 3600 * 1.79
        for split, terms in {(5,): [6 + 1.85 * 5 * cap], (4, 1): [6 + 1.85 * 4 * cap, 4 * s + 6 + 1.85 * cap],
                             (3, 2): [6 + 1.85 * 3 * cap, 3 * s + 6 + 1.85 * 2 * cap],
                             (2, 2, 1): [6 + 1.85 * 2 * cap, 2 * s + 6 + 1.85 * 2 * cap, 4 * s + 6 + 1.85 * cap],
                             (1, 1, 1, 1, 1): [k * s + 6 + 1.85 * cap for k in range(5)]}.items():
            pods = w.rules.deal(w.rules.block_runs("A", "A"))
            jobs = [[w.rules.job_record("a0_arm" if a == "a0" else "arm", a, sd, None, 38 if a in ("a0", "S1", "S3", "S4")
                                        else 33, {"e1_upper_s": E1, "training_s": T}, branch=branch) for a, sd in pod]
                    for pod in pods]
            assert [w.rules.cap_hours(j) for j in jobs] == [cap] * 5, branch
            k, launches = 0, []
            for n in split:
                launches.append([{"cap_hours": w.rules.cap_hours(j), "spend_usd": w.rules.pod_spend_usd(j)}
                                 for j in jobs[k:k + n]])
                k += n
            got = w.rules.funding_need_usd(launches, 1.25)
            base = cents(max(terms))
            assert (got["base_need_usd"], got["need_usd"]) == (base, cents(1.25 * base)), (branch, split)


# ----- B15 round-2 fix round (notes/b15r2-verify-gates.json VG2-1..VG2-5, b15r2-verify-runner.json VR2-1) -----------

PLAN_B_A = [{"hosts": [DIAG_POD]}, {"deal": [0, 1]}, {"deal": [2, 3]}]      # plan B's block A: 14 runs in 4 pods


@pytest.mark.parametrize("sigma, edit, launches", [
    (3.9, {"sigma_pp": 5.0, "code": "B"}, PLAN_B_A),                        # A -> B, kept in agreement
    (5.0, {"sigma_pp": 3.9, "code": "A"}, [{"hosts": [DIAG_POD]}] + A_LAUNCHES),   # B -> A
    (6.2, {"sigma_pp": 3.9, "code": "A"}, [{"hosts": [DIAG_POD]}] + A_LAUNCHES),   # 'none' (no stage 1) -> A
    (3.9, {"sigma_pp": 2.0}, [{"hosts": [DIAG_POD]}] + A_LAUNCHES)])        # sigma alone, code A kept
def test_a_coherent_hand_edit_of_the_plan_ab_record_refuses_every_block(w, sigma, edit, launches):
    """VG2-1 / VR2-1: gate_order re-reads Gate B's verdict file by its pin and re-derives sigma and the code; a
    plan.json record edited so that sigma and code still agree refuses at block A, at the cert pod and at S1-0."""
    w.s10(branch="full")
    w.gateb(sigma=sigma)
    w.sealed()
    plan = w.plan()
    plan["records"]["plan_ab"].update(edit)
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not the one derived"):
        w.init("A", launches, dry_run=True)
    w.cert_records()
    with pytest.raises(SystemExit, match="not the one derived"):
        w.init("cert", [{"hosts": [CERT_POD]}], dry_run=True)
    with pytest.raises(SystemExit, match="not the one derived"):
        w.tool.deal_command("A", [])


def test_a_coherent_hand_edit_before_s1_0_refuses_s1_0_and_its_floor(w):
    """VG2-1: block_a_floor read the record's code, so an edited code B lowered S1-0's floor; S1-0 now re-derives."""
    p, h = w.gateb_final()
    w.tool.record_simple("gateb_final", p, h)
    w.tool.record_simple("plan_ab", *w.verdict(3.9))
    w.auto_plan = False                                              # round 3a: the kit default's need
    assert w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], dry_run=True)["need_usd"] == 130.59
    plan = w.plan()
    plan["records"]["plan_ab"].update(sigma_pp=5.0, code="B")
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not the one derived"):
        w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], dry_run=True)


@pytest.mark.parametrize("change", ["emptied", "deleted", "one byte", "same sigma, other bytes"])
def test_a_verdict_file_changed_after_recording_refuses(w, change):
    """VR2-1: the verdict file is re-read at every block; one that no longer hashes to its pin refuses."""
    w.s10(branch="full")
    w.gateb(sigma=3.9)
    w.sealed()
    vp = w.repo / w.rules.GATEB_VERDICT["path"]
    if change == "emptied":
        vp.write_text("{}")
    elif change == "deleted":
        vp.unlink()
    elif change == "same sigma, other bytes":                       # still valid, same field value: only the pin catches it
        doc = json.loads(vp.read_text())
        doc["result"]["readings"]["plain"]["D_pp"] = "changed"
        write_json(vp, doc)
    else:
        data = vp.read_bytes()
        vp.write_bytes(bytes([data[0] ^ 0x01]) + data[1:])
    with pytest.raises(SystemExit, match="verdict file"):
        w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES, dry_run=True)


def test_release_re_derives_the_plan_ab_record(w):
    """VG2-1: every gate is checked again at release; a coherent hand edit made after init-block A refuses the next
    launch, and the restored record releases it."""
    w.s10()
    w.gateb(sigma=3.9)
    w.sealed()
    w.init("A", A_LAUNCHES)
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    plan = w.plan()
    good = dict(plan["records"]["plan_ab"])
    plan["records"]["plan_ab"].update(sigma_pp=5.0, code="B")
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not the one derived"):
        w.tool.release("A")
    plan = w.plan()
    plan["records"]["plan_ab"] = good
    w.mac.save_plan(plan)
    assert w.tool.release("A")["released"] == ["a-4", "a-5"]


def _branch_full(w, host="s10-1"):
    w.done(host, outputs={0: {"kind": "stage1 over-refusal checks", "truncation_check": {"units": 11, "pass": False}}})
    out = w.root / "retrieved" / host / "tree" / "job-0" / "w1_18.json"
    w.tool.record_branch(*w.record({"kind": "stage1 w1-18 branch record", "branch": "full", "host": host,
                                    "output_path": "job-0/w1_18.json", "output_sha256": sha(out),
                                    "focus_commit": "abc1234", "utc": "2026-10-23T12:00:00Z", "recorded_by": "test"}))


def test_the_block_a_floor_counts_the_cert_pod_until_it_is_planned_and_c3s_fallback_drops_c3(w):
    """Round 3a (rewritten from round 2's VG2-2 test): one top-up of S1-0's need ($130.59, Branch full, the kit
    default) launches S1-0, then the cert pod, then all of block A as the plan has it (diagnostics pod, LN-12 pod,
    the deal as 2 + 2 + 1, HarmBench and Granite), each init on the same amount; no part is refused for money."""
    w.auto_plan = False
    _, _, need = hand_default_need("full", (2, 2, 1))
    one = [{"hosts": [[{"kind": "w1_18"}]]}]
    w.init("S1-0", one, amount=need)
    _branch_full(w)
    w.gateb()
    w.cert_records()
    got = w.init("cert", [{"hosts": [CERT_POD]}], amount=need)          # the same funding event covers it
    assert got["need_usd"] == need and [x["role"] for x in got["block_a_plan"]["rest"]] == [
        "diagnostics", "ln12", "arms", "arms", "arms", "judge", "judge"]
    w.sealed()
    out = w.init("A", DEFAULT_A_FULL, amount=need)                       # and so does all of block A
    assert out["need_usd"] == need and out["block_a_plan"]["launch_map"] == [0, 1, 2, 3, 4, 5, 6]
    assert out["block_a_plan"]["rest"] == []
    w.done("a-1")
    assert w.tool.release("A")["released"] == ["a-2"]                   # the LN-12 pod: the plan is checked again


def test_the_c3_fallback_floor_has_no_c3(w):
    """Under C3's §22 point 2 fallback the default plan's cert pod is C1, C2 (round 3b: c0 is on the LN-12 pod; cap
    3.25 h, still worst at C1's start; spend (2,520 + 3,120 + 810) s x $1.79/h; hand_default_need): S1-0 needs $129.48
    under Branch full (10,447.2421 - 89.50 = 10,357.7421 cents -> 1.25 x 103.58 = 129.475)."""
    w.auto_plan = False
    w.tool.record_simple("c3_fallback", *w.record({"kind": "stage1 c3 fallback", "status": "dropped",
                                                   "reason": "synthetic", "utc": "u", "recorded_by": "t"}))
    _, base, need = hand_default_need("full", (2, 2, 1), c3=False)
    assert (base, need) == (103.58, 129.48)
    doc, args = w.tool.default_block_a_plan(w.tool.load())
    assert [j["kind"] for j in doc["launches"][1]["hosts"][0]] == ["cert_c1", "cert_c2"] and args["c3"] is False
    assert w.tool.plan_launches(w.tool.load(), doc)[1]["pods"][0]["cap_hours"] == 3.25
    assert w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], dry_run=True)["need_usd"] == need


@pytest.mark.parametrize("pod", [[CERT_POD[0], CERT_POD[2]],                      # no C2
                                 [CERT_POD[1], CERT_POD[2]],                     # no C1
                                 [CERT_POD[2]]])                                 # neither
def test_the_cert_pod_runs_c1_and_c2(w, pod):
    """VG2-3 (brief §4 G4: 'C1, C2 and C3 run on one pod'; §22 point 1's binding check is seen on C2): a cert pod
    without C1 or without C2 refuses, so the thresholds record and C2's label can never be skipped."""
    w.s10(branch="full")
    w.gateb()
    w.cert_records()
    with pytest.raises(SystemExit, match="C1 and C2 once each"):
        w.init("cert", [{"hosts": [pod]}], dry_run=True)
    assert w.init("cert", [{"hosts": [CERT_POD]}], dry_run=True)["dry_run"] is True


@pytest.mark.parametrize("field, value", [("version", True), ("version", 1.0), ("items", 16.0), ("items", True)])
def test_a_c3_record_with_a_non_integer_version_or_item_count_refuses(w, field, value):
    """VG2-4: version and items are compared by type as well (16.0 == 16 and True == 1 in Python)."""
    body = w.c3_files()
    rp = Path(body["record"]["path"])
    rec = json.loads(rp.read_text())
    if field == "version":
        rec["version"] = value
    else:
        rec["subsample"]["items"] = value
    write_json(rp, rec)
    body["record"]["sha256"] = sha(rp)
    w.pin_c3_record(body)                                           # round 3b: the edited record is the pinned one
    with pytest.raises(SystemExit, match="does not name"):
        w.tool.record_simple("c3", *w.record(body))
    assert w.tool.load()["records"]["c3"] is None


def test_a_huge_integer_refuses_cleanly_as_sigma_c2_statistic_or_funding(w):
    """VG2-5: an integer too large for a float (10**400) is refused as a ValueError / SystemExit, never an
    OverflowError traceback."""
    huge = 10 ** 400
    with pytest.raises(ValueError):
        w.rules.plan_code_for(huge)
    with pytest.raises(ValueError):
        w.rules.verdict_sigma({"kind": "gate-b reading", "phase": "verdict",
                               "result": {"readings": {"plain": {"sigma_hat_pp": huge}}}})
    with pytest.raises(ValueError):
        w.rules.c2_reading([json.dumps({"step": 1, "constrained": {"mean_weight": {"t2_5": huge}}})]
                           + _steps([0.8] * 38)[1:])
    p, h = w.gateb_final()
    w.tool.record_simple("gateb_final", p, h)
    vp = w.repo / "records" / "huge.json"
    vp.write_text('{"kind": "gate-b reading", "phase": "verdict", "result": {"readings": {"plain": {"sigma_hat_pp": 1'
                  + "0" * 400 + "}}}}")
    w.mp.setattr(w.rules, "GATEB_VERDICT", {"path": "records/huge.json", "sha256": sha(vp)})
    with pytest.raises(SystemExit):
        w.tool.record_simple("plan_ab", str(vp), sha(vp))
    with pytest.raises(SystemExit, match="positive finite number"):
        w.tool.funding_record(w.funding("A", huge), "A")


# ----- B15 round 3a: the block-A launch plan (addendum §20 point 1; the user's rule) --------------------------------

A0U, RU = [("a0", s) for s in (1101, 1102, 1103)], [("R", s) for s in (1101, 1102, 1103)]


def ln12_pod(units, theta0: bool = False) -> list[dict]:
    """J2 then its linked J3 for each unit (regen_source names the J2 on the same pod), then theta0's J3."""
    out = []
    for arm, s in units:
        out += [{"kind": "regenerate", "arm": arm, "seed": s},
                {"kind": "o_only", "arm": arm, "seed": s, "regen_source": len(out)}]
    return out + ([{"kind": "o_only", "arm": "theta0"}] if theta0 else [])


RESCORE = [{"kind": "retrain", "arm": "a0", "seed": 1102}, {"kind": "a1_rescore", "arm": "a0", "seed": 1102, "regen_source": 0},
           {"kind": "retrain", "arm": "a0", "seed": 1103}, {"kind": "a1_rescore", "arm": "a0", "seed": 1103, "regen_source": 2}]


def with_rescore(pod: list, at: int | None = None) -> list:
    """Round 3b: LN-15e's two retrain + re-score pairs inserted at ``at`` (default: the end), links shifted."""
    at = len(pod) if at is None else at
    out = [dict(j) for j in pod[:at]]
    out += [{**j, "regen_source": j["regen_source"] + at} if "regen_source" in j else dict(j) for j in RESCORE]
    k = len(RESCORE)
    out += [{**j, "regen_source": j["regen_source"] + k} if j.get("regen_source") is not None and j["regen_source"] >= at
            else dict(j) for j in pod[at:]]
    return out


# round 3b: the default LN-12 pod (one pod): the a0 and R pairs, LN-15e's two pairs, theta0's J3 (and LN-14 under
# Branch 128), then c0 (addendum §26)
LN12_FULL = with_rescore(ln12_pod(A0U + RU)) + [{"kind": "o_only", "arm": "theta0"}, C0]
HB27, GR27 = {"judge": {"judge": "harmbench", "arms": 27}}, {"judge": {"judge": "granite", "arms": 27}}
HB26, GR26 = HB27, GR27                     # round 3a's names (round 3b: 27 units, addendum §25 point 2)
DEFAULT_A_FULL = [{"hosts": [DIAG_POD]}, {"hosts": [LN12_FULL]}, {"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]},
                  HB27, GR27]


def hand_default_need(branch: str, split: tuple, c3: bool = True) -> tuple[list, float, float]:
    """The kit default block-A plan's need by hand (plan A; never the kit's output). Seconds are the brief's §3
    estimates (rules constants), each cap = the largest over the pod's jobs k of 2,520 + the measured uppers before k
    + job k's start requirement (upper + 1,800), rounded up to 0.25 h; spend = (2,520 + the measured uppers) s x
    $1.79/h; a term = spend of the earlier launches + $6 + $1.85 x this launch's caps; need = 1.25 x cents(max term).

    WORKED EXAMPLE (round 3b), Branch full, split 2 + 2 + 1 (cents; the kit must give the same):
      L0 S1-0: W1-18 (measured 1,800; start 3,600): cap 2,520 + 3,600 = 6,120 s -> 1.75 h; spend 4,320 s = 214.80.
      L1 cert (C1, C2, C3; c0 moved to LN-12, §26): C1 start 4,360.62 + 289.76 + 1,900 + 1,800 = 8,350.38 at 0;
         C2 (333.67 + 1,900) x 1.5 + 1,800 = 5,150.50 at 3,120; C3 3,600 at 3,930: worst at C1 2,520 + 8,350.38 =
         10,870.38 s -> 3.25 h; spend (2,520 + 3,120 + 810 + 1,800) s = 8,250 s = 410.2083.
      L2 diagnostics: J6 7,560 (upper x 1.5 = 11,340), J5 3,600, J7 3,600, J8 2,012 (upper 3,018): worst at J8
         2,520 + 14,760 + 4,818 = 22,098 s -> 6.25 h; spend 19,292 s = 959.2411.
      L3 LN-12 (one pod): 6 x (J2 540 [start max(4,033.67, 540 + 5,596.25) = 6,136.25] + J3 1,896.25 [start
         5,596.25]) = 14,617.5; LN-15e 2 x (retrain 540 [start 540 + 18,216 = 18,756] + re-score 10,944 [3.04 h;
         upper 1.5 x 10,944 = 16,416; start 18,216]); theta0's J3 1,896.25 [5,596.25]; c0 2,400 [4,300 + 1,800 =
         6,100]: second re-score at 2,520 + 26,641.5 + 18,216 = 47,377.5; c0 at 2,520 + 39,481.75 + 6,100 =
         48,101.75 s -> 13.5 h (the worst); spend (2,520 + 41,881.75) s = 44,401.75 s = 2,207.7537.
      L4-L6 arms: 4-arm pods (each arm 3,120 + 1,517 = 4,637 s), cap 7.5 h, spend 21,068 s = 1,047.5478 each.
      L7 HarmBench, 27 units (20 new + the 6 re-judged a0/R at 1101-1103 + theta0's, §25 point 2) x 800 = 21,600
         answers: (1,800 + 5,400 + 900) / 3,600 = 2.25 h -> 2.5 h; spend 447.50.
      L8 Granite, 27 x 200 + 200 = 5,600 answers: (1,800 + 2,800 + 900) / 3,600 = 1.53 h -> 2.0 h; spend 358.00.
      terms: 600 + 185 x 1.75 = 923.75; 214.80 + 600 + 601.25 = 1,416.05; 625.0083 + 600 + 1,156.25 = 2,381.2583;
         1,584.2494 + 600 + 2,497.5 = 4,681.7494; 3,792.0031 + 600 + 2,775 = 7,167.0031; 5,887.0987 + 3,375 =
         9,262.0987; 7,982.1943 + 600 + 1,387.5 = 9,969.6943; 9,029.7421 + 600 + 462.5 = 10,092.2421;
         9,477.2421 + 600 + 370 = 10,447.2421. base = 10,447 cents; need = 1.25 x 104.47 = 130.5875 -> $130.59.
      All five arm pods in one launch: 3,792.0031 + 600 + 185 x 37.5 = 11,329.5031 -> base 113.30 -> $141.63.
    """
    rate = 1.79 / 3600
    o = {"full": 1517.0, "128": 1024.0}[branch]
    cert = (3.25, 2520 + 3120 + 810 + (1800 if c3 else 0))            # C3 dropped: still worst at C1 -> 3.25 h
    ln12_s = 2520 + 6 * (540 + 1.25 * o) + 2 * (540 + 10944) + 1.25 * o + (1408 if branch == "128" else 0) + 2400
    ln12 = (13.5 if branch == "full" else 12.75, ln12_s)               # 128: worst at c0, 45,196 s -> 12.75 h
    arm = (7.5 if branch == "full" else 7.0, 2520 + 4 * (3120 + o))
    pods = [[(1.75, 4320)], [cert], [(6.25, 19292)], [ln12]]
    pods += [[arm] * n for n in split]
    launches = [[(c, s * rate) for c, s in launch] for launch in pods] + [[(2.5, 2.5 * 1.79)], [(2.0, 2.0 * 1.79)]]
    terms, spent = [], 0.0
    for launch in launches:
        terms.append(spent + 6 + 1.85 * sum(c for c, _ in launch))
        spent += sum(s for _, s in launch)
    base = cents(max(terms))
    return terms, base, times_125(base)


@pytest.mark.parametrize("branch, split, base, need", [
    ("full", (2, 2, 1), 104.47, 130.59), ("full", (5,), 113.30, 141.63), ("full", (1, 4), 109.90, 137.38),
    ("full", (3, 2), 104.47, 130.59), ("128", (2, 2, 1), 98.13, 122.66), ("128", (5,), 107.23, 134.04)])
def test_the_block_a_plan_need_by_hand_for_both_branches_and_splits(w, branch, split, base, need):
    """Item 4 of round 3a, re-valued in round 3b (c0 on the LN-12 pod, LN-15e in the plan, 27 judge units): the kit's
    block-a-need report equals the hand computation (terms included). The worst split is all five arm pods in one
    launch: (5,) needs $141.63 (Branch full; its arm launch's term 37.920031 + 6 + 69.375 = $113.30 dominates); 2+2+1
    and 3+2 are bounded by the last judge term ($104.47 -> $130.59)."""
    terms, b, n = hand_default_need(branch, split)
    assert (b, n) == (base, need)
    doc = w.tool.default_block_a_doc("A", True, split, "2026-10-23T00:00:00Z", "test")
    report = w.tool.plan_report(w.tool.load(), doc)
    got = report[branch]
    assert (got["base_need_usd"], got["need_usd"]) == (base, need)
    assert got["terms_cents"] == pytest.approx([t * 100 for t in terms], abs=1e-3)
    assert report["frozen"]["need_usd"] == hand_default_need("full", split)[2]   # frozen = Branch full here


def test_harmbench_and_granite_judge_launch_caps_by_hand(w):
    """The launcher's rule (judge_pod.cap_hours_for): HarmBench 0.25 s per answer, 800 answers per unit; Granite 0.5 s,
    200 per unit + the gate's 200; the smallest half hour >= 30 min + answers + 15 min, at least 1 h, above 6 h
    refused. Gate B's launch H (15 units, 12,000 answers) had cap 2.0 h."""
    r = w.rules
    assert r.harmbench_pod(15)["cap_hours"] == 2.0 and r.harmbench_pod(15)["answers"] == 12000
    assert r.harmbench_pod(26)["cap_hours"] == 2.5 and r.harmbench_pod(1)["cap_hours"] == 1.0
    assert r.harmbench_pod(37)["cap_hours"] == 3.0                    # (1,800 + 7,400 + 900) / 3,600 = 2.81 h
    assert r.granite_pod(26)["cap_hours"] == 1.5 and r.granite_pod(27)["cap_hours"] == 2.0   # 5,600 answers: 1.53 h
    with pytest.raises(ValueError, match="above 6.0 h"):
        r.harmbench_pod(100)                                            # 80,000 answers: 6.31 h
    with pytest.raises(ValueError, match="unknown judge"):
        r.judge_pod("llama-guard", 3)


def _plan_doc(w, **change):
    doc, _ = w.tool.default_block_a_plan(w.tool.load(), recorded_by="test")
    doc.update(change)
    return doc


def _bad(launches_edit):
    def edit(doc):
        launches_edit(doc["launches"])
        return doc
    return edit


@pytest.mark.parametrize("edit, match", [
    (lambda d: d.update(extra=1) or d, "holds exactly"),
    (lambda d: d.update(kind="other") or d, "version 1"),
    (lambda d: d.update(plan_code="C") or d, "plan_code"),
    (_bad(lambda L: L.insert(2, L.pop(3))), "launch order"),                       # LN-12 before diagnostics
    (_bad(lambda L: L.insert(3, L.pop(1))), "launch order"),                       # the cert pod in the middle
    (_bad(lambda L: L.insert(4, L.pop(-1))), "launch order"),                      # a judge before the arms
    (_bad(lambda L: L.pop(-1)), "one HarmBench and one Granite"),
    (_bad(lambda L: L[-1]["judge"].update(arms=19)), "at least block A's 20 new units"),
    (_bad(lambda L: L[-2]["judge"].update(arms=100)), "above 6.0 h"),
    (_bad(lambda L: L.pop(6)), "split the deal's 5 pods"),                         # pod 4 never launched
    (_bad(lambda L: L.__setitem__(4, {"role": "arms", "deal": [1, 0]})), "split the deal's 5 pods"),
    (_bad(lambda L: L[2]["hosts"].append([{"kind": "l1_scan"}])), "is one pod"),
    (_bad(lambda L: L[2]["hosts"][0].append({"kind": "regenerate", "arm": "a0", "seed": 1101})), "holds only"),
    (_bad(lambda L: L[3]["hosts"].append([{"kind": "regenerate", "arm": "a0", "seed": 1101}])), "planned twice"),
    (_bad(lambda L: L[3]["hosts"][0].insert(0, {"kind": "o_only", "arm": "R", "seed": 1104, "regen_source": 0})),
     "must name its regeneration"),
    (_bad(lambda L: L[2]["hosts"][0].reverse()), "needs J6"),
    (_bad(lambda L: L[1]["hosts"][0].pop(1)), "C1 and C2 once each")])
def test_a_malformed_block_a_plan_refuses(w, edit, match):
    """The plan record's own rules: the order S1-0 -> cert -> diagnostics -> LN-12 -> arm launches -> judges, a
    split of the deal in order, both judges over at least the new units, the job rules of each pod."""
    doc = edit(_plan_doc(w))
    with pytest.raises(SystemExit, match=match):
        w.tool.record_block_a_plan(*w.record(doc))
    assert w.tool.load()["records"]["block_a_plan"] is None


def test_the_plan_record_is_refused_once_s1_0_exists_and_its_plan_code_must_be_the_plan_ab_code(w):
    w.auto_plan = False
    p, h = w.record(_plan_doc(w))
    first = w.tool.record_block_a_plan(p, h)
    assert first["need_usd"] == 130.59 and first["replan"] is False
    assert w.tool.record_block_a_plan(*w.record(_plan_doc(w, recorded_by="test2")))["recorded"] == "block_a_plan"
    assert len(w.tool.load()["records"]["block_a_plan_history"]) == 1     # replaced before S1-0, history kept
    with pytest.raises(SystemExit, match="follows the group's first launch"):
        w.tool.record_block_a_plan(p, h, replan=True)
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    with pytest.raises(SystemExit, match="refused once block A's funding group has a planned launch"):
        w.tool.record_block_a_plan(*w.record(_plan_doc(w)))
    p2, h2 = w.gateb_final()
    w.tool.record_simple("gateb_final", p2, h2)
    w.tool.record_simple("plan_ab", *w.verdict(5.0))                    # plan B
    with pytest.raises(SystemExit, match="not the re-derived plan-A/B record's code"):
        w.tool.record_block_a_plan(*w.record(_plan_doc(w, plan_code="A")), replan=True)


def test_the_cli_writes_records_and_reports_the_block_a_plan(w, capsys):
    w.auto_plan = False
    out = w.repo / "records" / "block-a-plan.json"
    out.parent.mkdir(exist_ok=True)
    assert w.tool.main(["write-block-a-plan", "--out", str(out), "--recorded-by", "test", "--split", "3,2"]) == 0
    wrote = json.loads(capsys.readouterr().out)
    assert wrote["sha256"] == sha(out) and wrote["need_usd"] == 130.59
    with pytest.raises(SystemExit, match="never overwritten"):
        w.tool.main(["write-block-a-plan", "--out", str(out), "--recorded-by", "test"])
    assert w.tool.main(["block-a-need", str(out), "--sha256", sha(out)]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["source"] == "file" and rep["full"]["need_usd"] == 130.59 and rep["128"]["need_usd"] == 122.66
    assert rep["full"]["terms_cents"][-1] == pytest.approx(10447.2421, abs=1e-3)
    assert w.tool.main(["record-block-a-plan", str(out), "--sha256", sha(out)]) == 0
    capsys.readouterr()
    assert w.tool.main(["block-a-need"]) == 0
    assert json.loads(capsys.readouterr().out)["source"] == "recorded"
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], amount=130.59)


def _default_after_s1_0(w):
    w.auto_plan = False
    w.s10(branch="full")
    w.gateb()
    w.sealed()


@pytest.mark.parametrize("launches", [
    [{"hosts": [DIAG_POD]}, {"hosts": [LN12_FULL]}, {"deal": [0, 1, 2, 3, 4]}, HB26, GR26],           # merged arms
    [{"hosts": [DIAG_POD]}, {"hosts": [ln12_pod(A0U), ln12_pod(RU)]}, {"deal": [0, 1]}, {"deal": [2, 3]},
     {"deal": [4]}],                                                                                  # two LN-12 pods
    [{"hosts": [LN12_FULL]}, {"hosts": [DIAG_POD]}, {"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]}],   # order
    [{"hosts": [DIAG_POD]}, {"deal": [0, 1]}, {"hosts": [LN12_FULL]}, {"deal": [2, 3]}, {"deal": [4]}],   # order
    [{"hosts": [DIAG_POD]}, HB26, {"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]}],                     # order
    [{"hosts": [[DIAG_POD[0], DIAG_POD[1], DIAG_POD[3], DIAG_POD[2]]]}, {"deal": [0, 1]}, {"deal": [2, 3]},
     {"deal": [4]}],                                                       # J8 before J7: cap 6.5 h > the plan's 6.25
    [{"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]}, {"judge": {"judge": "harmbench", "arms": 28}}],   # more units
    [{"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]}, HB26, HB26],                                     # a third judge
    [{"hosts": [DIAG_POD + [{"kind": "o_only", "arm": "theta0"}]]}, {"deal": [0, 1]}, {"deal": [2, 3]},
     {"deal": [4]}],                                                        # a job the diagnostics launch never holds
    [{"hosts": [DIAG_POD[:2] + [{"kind": "o_only", "arm": "theta0"}]]}, {"deal": [0, 1]}, {"deal": [2, 3]},
     {"deal": [4]}],                                     # the same with a smaller cap (5.5 h) and spend: the job alone
    [{"deal": [2, 3]}, {"deal": [0, 1]}, {"deal": [4]}]])                   # the dealt pods in another order
def test_a_block_a_launch_that_departs_from_the_plan_refuses(w, launches):
    """Round 3a point 3: under the recorded plan (here the kit default recorded at S1-0), block A refuses another
    order, more pods in a launch, a pod with a larger cap, a larger judge launch or a job the launch does not hold."""
    _default_after_s1_0(w)
    with pytest.raises(SystemExit, match="departs from the recorded block-A plan"):
        w.init("A", launches, dry_run=True)


@pytest.mark.parametrize("launches", [
    DEFAULT_A_FULL,
    [{"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]}],                                      # parts left out
    [{"hosts": [DIAG_POD]}, {"deal": [0]}, {"deal": [1]}, {"deal": [2, 3]}, {"deal": [4]}, GR26],  # 1 + 1 + 2 + 1
    [{"hosts": [ln12_pod(A0U, theta0=True)]}, {"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]},
     {"judge": {"arms": 20}}]])                                            # a smaller LN-12 pod and Granite judge
def test_block_a_launches_inside_the_plan_are_planned(w, launches):
    """Leaving a planned launch out or spreading a launch's pods over consecutive launches never raises a term of the
    need (a pod's spend is below $1.85 x its cap), so it is allowed; the need never exceeds S1-0's."""
    _default_after_s1_0(w)
    out = w.init("A", launches, dry_run=True)
    assert out["need_usd"] <= 130.59


def test_the_cert_pod_after_block_a_departs_from_the_default_order(w):
    _default_after_s1_0(w)
    w.init("A", DEFAULT_A_FULL[2:5])
    w.cert_records()
    with pytest.raises(SystemExit, match="orders it before a part that is already planned"):
        w.init("cert", [{"hosts": [CERT_POD]}], dry_run=True)


def test_a_plan_b_record_after_a_plan_a_plan_refuses_block_a_until_a_replan(w):
    w.auto_plan = False
    w.s10(branch="full")
    w.gateb(sigma=5.0)                                                  # plan B after S1-0's plan-A default
    w.sealed()
    with pytest.raises(SystemExit, match="the block-A plan is for plan A"):
        w.init("A", [{"deal": [0, 1]}, {"deal": [2, 3]}], dry_run=True)
    doc, _ = w.tool.default_block_a_plan(w.tool.load(), recorded_by="test")   # plan B's default: 2 + 2, 21 units
    assert doc["plan_code"] == "B" and doc["launches"][-1]["judge"]["arms"] == 14 + 7
    w.tool.record_block_a_plan(*w.record(doc), replan=True)
    assert w.init("A", [{"deal": [0, 1]}, {"deal": [2, 3]}], dry_run=True)["need_usd"] <= 130.59


def test_a_replan_must_fit_what_is_planned_and_be_covered_by_the_same_funding_record(w):
    """Round 3a point 3: a re-plan is recorded only if every planned part fits it and the group's first funding record
    covers its need. S1-0 funded at $130.59: the 5-in-one-launch plan ($141.63) refuses; 3 + 2 ($130.59) records."""
    w.auto_plan = False
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], amount=130.59)
    _branch_full(w)
    w.gateb()
    w.sealed()
    five = w.tool.default_block_a_doc("A", True, (5,), "2026-10-23T00:00:00Z", "test")
    with pytest.raises(SystemExit, match=r"needs \$141.63; the group's funding record .* is \$130.59"):
        w.tool.record_block_a_plan(*w.record(five), replan=True)
    with pytest.raises(SystemExit, match="departs from the recorded block-A plan"):
        w.init("A", [{"deal": [0, 1, 2]}, {"deal": [3, 4]}], amount=130.59)
    three_two = w.tool.default_block_a_doc("A", True, (3, 2), "2026-10-23T00:00:00Z", "test")
    assert w.tool.record_block_a_plan(*w.record(three_two), replan=True)["need_usd"] == 130.59
    w.init("A", [{"deal": [0, 1, 2]}, {"deal": [3, 4]}], amount=130.59)
    no_s10 = dict(three_two, launches=[x for x in three_two["launches"]])
    no_s10["launches"][0] = {"role": "s1_0", "hosts": [[{"kind": "w1_18"}, {"kind": "w1_18"}]]}
    with pytest.raises(SystemExit):
        w.tool.record_block_a_plan(*w.record(no_s10), replan=True)


def _two_ln12_pods(w, split):
    """The default plan with c0 moved off the one LN-12 pod onto a second LN-12 pod of its own (c0 is that pod's last
    job and no job links to it, so no regen_source changes)."""
    doc = w.tool.default_block_a_doc("A", True, split, "2026-10-23T00:00:00Z", "test")
    ln12 = [x for x in doc["launches"] if x["role"] == "ln12"][0]
    assert len(ln12["hosts"]) == 1 and ln12["hosts"][0][-1]["kind"] == "c0"
    ln12["hosts"] = [ln12["hosts"][0][:-1], [dict(w.tool.C0_JOB)]]
    return doc


def test_a_142_top_up_covers_two_ln12_pods_only_without_the_five_in_one_arm_launch(w):
    """Fix round (VP3b-1, a stated limit, not a code defect): the $142 top-up (the worst split of the ONE-LN-12-pod
    default, $141.63) does not cover every re-plan. c0 on a second LN-12 pod adds one 42-min overhead (2,520 s x
    179/3,600 = 125.30 cents) to the spend before the arms: 2+2+1 needs $132.16 (covered, recorded); with all five arm
    pods in one launch the arm term is 11,329.50 + 125.30 = 11,454.80 -> base 11,455 -> 1.25 x = 14,318.75 -> $143.19,
    which the kit refuses against S1-0's $142 record. Money is never at risk; the plan is the limit."""
    w.auto_plan = False
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], amount=142.0)
    _branch_full(w)
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match=r"needs \$143.19; the group's funding record .* is \$142.00"):
        w.tool.record_block_a_plan(*w.record(_two_ln12_pods(w, (5,))), replan=True)
    assert w.tool.record_block_a_plan(*w.record(_two_ln12_pods(w, (2, 2, 1))), replan=True)["need_usd"] == 132.16
    one_pod_five = w.tool.default_block_a_doc("A", True, (5,), "2026-10-23T00:00:00Z", "test")
    assert w.tool.record_block_a_plan(*w.record(one_pod_five), replan=True)["need_usd"] == 141.63


def test_a_replan_that_the_planned_cert_pod_does_not_fit_refuses(w):
    w.auto_plan = False
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    _branch_full(w)
    w.gateb()
    w.cert_records()
    w.init("cert", [{"hosts": [CERT_POD]}])
    no_c3 = w.tool.default_block_a_doc("A", False, (2, 2, 1), "2026-10-23T00:00:00Z", "test")
    with pytest.raises(SystemExit, match="leaves out block A's required jobs"):   # fix round: C3 is G4/G5 content
        w.tool.record_block_a_plan(*w.record(no_c3), replan=True)


def test_a_replan_that_a_planned_larger_cert_pod_does_not_fit_refuses(w):
    """Round 3b (c0 left the cert pod, so every cert pod of the default's content is at least the default's 3.25 h):
    a lead plan whose cert pod runs C3 first (by hand: C3 at 0, 2,520 + 3,600 = 6,120; C1 at 1,800, 2,520 + 1,800 +
    8,350.38 = 12,670.38; C2 at 4,920, 2,520 + 4,920 + 5,150.50 = 12,590.50: 12,670.38 s -> 3.75 h) is recorded and the
    cert pod planned so; a re-plan back to the kit default (cert 3.25 h) does not fit the planned 3.75 h pod."""
    w.auto_plan = False
    lead = w.tool.default_block_a_doc("A", True, (2, 2, 1), "2026-10-23T00:00:00Z", "test")
    pod = lead["launches"][1]["hosts"][0]
    pod.insert(0, pod.pop())                                        # C3, C1, C2
    assert w.tool.plan_launches(w.tool.load(), lead)[1]["pods"][0]["cap_hours"] == 3.75
    w.tool.record_block_a_plan(*w.record(lead))
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}])
    _branch_full(w)
    w.gateb()
    w.cert_records()
    assert w.init("cert", [{"hosts": [[CERT_POD[2], CERT_POD[0], CERT_POD[1]]]}])["pods"][0]["cap_hours"] == 3.75
    default = w.tool.default_block_a_doc("A", True, (2, 2, 1), "2026-10-23T00:00:00Z", "test")
    with pytest.raises(SystemExit, match="block cert: launch 0 departs"):
        w.tool.record_block_a_plan(*w.record(default), replan=True)


@pytest.mark.parametrize("edit", ["default doc", "default inputs", "lead file changed", "lead file deleted",
                                  "lead file reformatted", "plan.json copy"])
def test_a_hand_edited_or_changed_block_a_plan_refuses_init_and_release(w, edit):
    """The recorded plan is re-derived at every init-block and release in the group: the kit default from its
    recorded inputs, a lead's file by its SHA-256 (and plan.json's copy must be the file's)."""
    w.auto_plan = False
    if edit.startswith("lead") or edit == "plan.json copy":
        p, h = w.record(_plan_doc(w))
        w.tool.record_block_a_plan(p, h)
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    w.init("A", DEFAULT_A_FULL)
    w.done("a-1")
    w.cert_records()
    plan = w.plan()
    rec = plan["records"]["block_a_plan"]
    if edit == "default doc":
        rec["doc"]["launches"][-1]["judge"]["arms"] = 40
    elif edit == "default inputs":
        rec["default"]["split"] = [5]
    elif edit == "lead file changed":
        Path(rec["path"]).write_text(json.dumps({**rec["doc"], "recorded_by": "someone else"}))
    elif edit == "lead file deleted":
        Path(rec["path"]).unlink()
    elif edit == "lead file reformatted":                       # the same JSON, other bytes: only the SHA-256 sees it
        Path(rec["path"]).write_text(json.dumps(rec["doc"]))
    else:
        rec["doc"]["launches"][-1]["judge"]["arms"] = 40
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="block-A plan"):
        w.tool.release("A")
    with pytest.raises(SystemExit, match="block-A plan"):
        w.init("cert", [{"hosts": [CERT_POD]}], dry_run=True)


def test_release_refuses_a_launch_whose_host_was_edited_past_the_plan(w):
    """Release re-checks the block's planned launches against the plan: a pending pod whose cap was raised by hand
    in plan.json refuses."""
    _default_after_s1_0(w)
    w.init("A", DEFAULT_A_FULL)
    w.done("a-1")
    plan = w.plan()
    plan["blocks"]["A"]["pending"]["a-2"]["cap_hours"] = 14.0              # the LN-12 plan pod is 13.5 h
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="block A: launch 1 departs"):
        w.tool.release("A")



def test_conform_part_compares_each_pod_by_cap_spend_deal_judge_and_the_launchs_jobs(w):
    """conform_part on synthetic shapes: a pod fits a plan pod only with no larger cap AND no larger spend; a dealt pod
    only the same deal pod; a judge only the same judge with no more units; a hosts launch only with jobs its plan
    launch holds; pods are matched one to one."""
    c = w.tool.conform_part
    k1, k2 = ("rep_pass", None, None, "X", None, None), ("l1_scan", None, None, "X", None, None)
    plan = [{"part": "A", "type": "hosts", "jobs": {k1: 1, k2: 1}, "pods": [{"cap_hours": 3.0, "spend_usd": 1.0},
                                                                           {"cap_hours": 2.0, "spend_usd": 2.0}]},
            {"part": "A", "type": "deal", "pods": [{"deal": 0, "cap_hours": 7.5, "spend_usd": 10.0},
                                                   {"deal": 1, "cap_hours": 7.5, "spend_usd": 10.0}]},
            {"part": "A", "type": "judge", "pods": [{"judge": "granite", "arms": 26, "cap_hours": 1.5,
                                                     "spend_usd": 2.685}]}]
    hosts = lambda *pods: {"type": "hosts", "pods": [{"jobs": j, "cap_hours": cap, "spend_usd": s, "deal": None}
                                                     for j, cap, s in pods]}
    deal = lambda *idx: {"type": "deal", "pods": [{"deal": i, "cap_hours": 7.5, "spend_usd": 10.0, "jobs": []}
                                                  for i in idx]}
    judge = lambda kind, arms: {"type": "judge", "pods": [{"judge": kind, "arms": arms, "cap_hours": 1.5,
                                                           "spend_usd": 2.685}]}
    assert c([hosts(([k1], 3.0, 1.0), ([k2], 2.0, 2.0)), deal(1), deal(0), judge("granite", 20)], plan, "A") == \
        [0, 1, 1, 2]
    assert c([hosts(([k1], 2.0, 2.0)), hosts(([k2], 3.0, 1.0))], plan, "A") == [0, 0]     # spread over two launches
    for bad in ([hosts(([k1], 3.0, 1.5))],                       # cap fits the 3.0 pod, spend only the 2.0 pod's cap
                [hosts(([k1], 3.25, 0.5))],                      # a larger cap
                [hosts(([k1, k1], 2.0, 1.0))],                   # a job the launch holds once
                [hosts(([("arm", "A1", 1102, "X", None, None)], 1.0, 0.5))],
                [hosts(([k1], 1.0, 0.5), ([k2], 1.0, 0.5), ([k2], 1.0, 0.5))],   # three pods
                [deal(0, 1, 1)], [{"type": "deal", "pods": [{"deal": 2, "cap_hours": 1.0, "spend_usd": 1.0}]}],
                [judge("granite", 27)], [judge("harmbench", 1)], [deal(0), hosts(([k1], 1.0, 0.5))]):
        with pytest.raises(SystemExit, match="departs"):
            c(bad, plan, "A")


def test_an_ln_14_pod_that_exists_only_under_branch_128_is_counted_and_fits_under_128(w):
    """A plan pod that holds only theta0's LN-14 transfer report has no Branch-full form; the frozen numbers take its
    Branch-128 cap and spend (each pod's larger), so S1-0's need counts it. By hand: J4 measured 1,408 s, upper
    1,408 + 1,900 = 3,308, start 5,108: cap 2,520 + 5,108 = 7,628 s -> 2.25 h; spend (2,520 + 1,408) s x $1.79/h.
    The default's LN-12 pod keeps its numbers; that launch's caps rise by 2.25 h and every later term by the spend:
    Granite's 10,447.2421 + 195.3089 = 10,642.551 cents -> 1.25 x 106.43 = 133.0375 -> $133.04."""
    w.auto_plan = False
    doc, _ = w.tool.default_block_a_plan(w.tool.load(), recorded_by="test")
    pod = doc["launches"][3]["hosts"][0]
    pod.remove({"kind": "transfer_report", "arm": "theta0"})
    doc["launches"][3]["hosts"].append([{"kind": "transfer_report", "arm": "theta0"}])
    frozen = w.tool.plan_launches(w.tool.load(), doc)
    assert [(p["cap_hours"], round(p["spend_usd"], 9)) for p in frozen[3]["pods"]] == [
        (13.5, round(44401.75 / 3600 * 1.79, 9)), (2.25, round(3928 / 3600 * 1.79, 9))]
    terms, _, _ = hand_default_need("full", (2, 2, 1))
    extra = 3928 / 3600 * 1.79
    hand = terms[:3] + [terms[3] + 1.85 * 2.25] + [t + extra for t in terms[4:]]
    need = w.tool.need_of(frozen)
    assert need["terms_usd"] == pytest.approx(hand, abs=1e-9)
    assert need["need_usd"] == times_125(cents(max(hand))) == 133.04
    p, h = w.record(doc)
    w.tool.record_block_a_plan(p, h)
    w.s10(branch="128")
    w.gateb()
    w.sealed()
    split = [{"hosts": [DIAG_POD]}, {"hosts": [ln12_pod(A0U + RU, theta0=True), [{"kind": "transfer_report",
                                                                                 "arm": "theta0"}]]},
             {"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]}]
    assert w.init("A", split, dry_run=True)["dry_run"] is True


# ----- B15 round 3a FIX: the verifiers' findings (notes/b15r3a-verify-gates.json, notes/b15r3a-verify-money.json) ----

ONE_S10 = [{"hosts": [[{"kind": "w1_18"}]]}]


def _ln12_without(drop=(), keep_o=True, theta0=True, ln14=True, rescore=True, c0=True) -> list[dict]:
    """The default LN-12 pod with some units left out (their J2 and J3), or with no J3s / no theta0 passes, or
    (round 3b) without LN-15e's pairs or c0."""
    units = [u for u in A0U + RU if u not in drop]
    pod = ln12_pod(units) if keep_o else [{"kind": "regenerate", "arm": a, "seed": s} for a, s in units]
    pod = with_rescore(pod) if rescore else pod
    return pod + ([{"kind": "o_only", "arm": "theta0"}] if theta0 else []) + \
        ([{"kind": "transfer_report", "arm": "theta0"}] if ln14 else []) + ([C0] if c0 else [])


def _set_ln12(pod):
    def edit(doc):
        doc["launches"][3]["hosts"] = [pod]
        return doc
    return edit


def _drop(launch: int, kind: str):
    def edit(doc):
        doc["launches"][launch]["hosts"][0] = [j for j in doc["launches"][launch]["hosts"][0] if j["kind"] != kind]
        return doc
    return edit


def _judges(hb: int, gr: int):
    def edit(doc):
        doc["launches"][-2]["judge"]["arms"], doc["launches"][-1]["judge"]["arms"] = hb, gr
        return doc
    return edit


@pytest.mark.parametrize("edit, match", [
    (_drop(3, "c0"), "required jobs .*: c0"),                                   # J11, round 3b on the LN-12 pod
    (_set_ln12(_ln12_without(rescore=False)), "required jobs .*: retrain a0 1102, a1_rescore a0 1102, retrain a0 "
                                              "1103, a1_rescore a0 1103"),       # LN-15e (round 3b)
    (_drop(3, "a1_rescore"), "required jobs .*: a1_rescore a0 1102, a1_rescore a0 1103"),
    (_drop(1, "cert_c3"), "required jobs .*: cert_c3"),                         # C3 without its fallback record
    (_drop(2, "l1_scan"), "required jobs .*: l1_scan"),                         # J7
    (_drop(2, "classifier"), "required jobs .*: classifier"),                   # J8
    (_drop(2, "rep_pass"), "required jobs .*: rep_pass"),                       # J5
    (_set_ln12(_ln12_without(drop=[("a0", 1102)])), "regenerate a0 1102, o_only a0 1102"),
    (_set_ln12(_ln12_without(drop=[("R", 1101), ("R", 1102), ("R", 1103)])), "regenerate R 1101"),
    (_set_ln12(_ln12_without(keep_o=False)), "o_only a0 1101"),                  # J2s without their J3s
    (_set_ln12(_ln12_without(theta0=False)), "o_only theta0"),
    (_set_ln12(_ln12_without(ln14=False)), "transfer_report theta0"),           # LN-14 (counted only under 128)
    (_judges(26, 27), "at least 27 units"), (_judges(27, 20), "at least 27 units")])   # §25 point 2
def test_a_block_a_plan_that_leaves_out_block_a_content_refuses(w, edit, match):
    """VG3-1 (should_fix): the plan's CONTENT is checked against brief §4 G5 (c0, C3, J5-J8, the six J2/J3 pairs,
    theta0's J3, LN-14) and §17 Q14 (judges over the 20 new + 6 re-judged units). Before the fix such a plan was
    recorded and lowered S1-0's floor (the verifier's plan without c0, J7, J8, the pairs, LN-14 and with 20-unit
    judges: S1-0 on $99.98, then block A stuck)."""
    w.auto_plan = False
    doc = edit(_plan_doc(w))
    with pytest.raises(SystemExit, match=match):
        w.tool.record_block_a_plan(*w.record(doc))
    assert w.tool.load()["records"]["block_a_plan"] is None


def test_the_verifiers_incomplete_plan_refuses_and_fallbacks_relax_only_their_own_jobs(w):
    w.auto_plan = False
    doc = _plan_doc(w)
    L = doc["launches"]
    L[1]["hosts"][0] = [j for j in L[1]["hosts"][0] if j["kind"] != "c0"]
    L[2]["hosts"][0] = [{"kind": "untuned_answers"}, {"kind": "rep_pass"}]
    L[3]["hosts"][0] = [{"kind": "o_only", "arm": "theta0"}]
    L[-2]["judge"]["arms"] = L[-1]["judge"]["arms"] = 20
    with pytest.raises(SystemExit, match="required jobs .*: l1_scan, classifier, c0, retrain a0 1102, a1_rescore a0 "
                                         "1102, retrain a0 1103, a1_rescore a0 1103, regenerate a0 1101"):
        w.tool.record_block_a_plan(*w.record(doc))
    # the O-ext fallback (c): no J3 and no LN-14 runs, so a plan without them is complete; J2 is still required
    w.tool.record_simple("oext_fallback", *w.record({"kind": "stage1 oext fallback", "status": "dev100_recipe_cap",
                                                     "reason": "synthetic", "utc": "u", "recorded_by": "t"}))
    no_o = _set_ln12(_ln12_without(keep_o=False, theta0=False, ln14=False))(_plan_doc(w))
    assert w.tool.record_block_a_plan(*w.record(no_o))["recorded"] == "block_a_plan"
    with pytest.raises(SystemExit, match="regenerate a0 1103"):
        w.tool.record_block_a_plan(*w.record(_set_ln12(_ln12_without(drop=[("a0", 1103)], keep_o=False, theta0=False,
                                                                     ln14=False))(_plan_doc(w))))


def test_a_c3_fallback_plan_without_c3_records(w):
    w.auto_plan = False
    w.tool.record_simple("c3_fallback", *w.record({"kind": "stage1 c3 fallback", "status": "dropped",
                                                   "reason": "synthetic", "utc": "u", "recorded_by": "t"}))
    assert w.tool.record_block_a_plan(*w.record(_drop(1, "cert_c3")(_plan_doc(w))))["need_usd"] == 129.48


def _two_ln12_pods_world(w):
    """World's broad test plan (two LN-12 pods) recorded at S1-0; block A planned as diagnostics, the two LN-12 pods
    (a0 pairs + theta0 | R pairs), all five dealt pods."""
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    a0 = ln12_pod(A0U, theta0=True)
    w.init("A", [{"hosts": [DIAG_POD]}, {"hosts": [a0, ln12_pod(RU)]}, {"deal": [0, 1, 2, 3, 4]}])
    w.done("a-1")
    assert w.tool.release("A")["released"] == ["a-2", "a-3"]


def test_a_contingency_paid_deferral_into_a_sibling_pod_does_not_block_block_a(w):
    """VG3-2 (should_fix): a-2's crashed J2 (with its J3) is deferred into its unlaunched sibling a-3 of the same
    planned launch (paid from the contingency, outside the plan). Before the fix every later release refused ('launch 1
    departs': a-3 now held a job and a cap the plan pod did not); round 2's kit released normally. The sibling is now
    checked as it was planned (its plan_shape), so the arm launch releases."""
    _two_ln12_pods_world(w)
    planned = w.plan()["hosts"]["a-3"]
    w.done("a-2", statuses={0: "crashed", 1: "not_started"})
    moved = w.tool.defer("a-2")
    assert moved["to"] == "a-3"
    h = w.plan()["hosts"]["a-3"]
    assert h["plan_shape"]["cap_hours"] == planned["cap_hours"] and h["cap_hours"] > planned["cap_hours"]
    assert [j["kind"] for j in h["plan_shape"]["jobs"]] == [j["kind"] for j in planned["jobs"]]
    w.done("a-3")
    assert w.tool.release("A")["released"] == ["a-4", "a-5", "a-6", "a-7", "a-8"]


def test_a_host_edited_past_its_plan_shape_still_refuses(w):
    """The plan_shape is the host as planned: raising it by hand past the plan pod refuses at release."""
    _two_ln12_pods_world(w)
    w.done("a-2", statuses={0: "crashed", 1: "not_started"})
    w.tool.defer("a-2")
    w.done("a-3")
    plan = w.plan()
    plan["hosts"]["a-3"]["plan_shape"]["cap_hours"] = 14.0            # above both LN-12 plan pods (round 3b)
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="launch 1 departs"):
        w.tool.release("A")


def test_the_groups_parts_are_read_in_planning_order_and_a_replan_after_block_a_works(w):
    """VG3-3 (should_fix): plan.json is saved with sort_keys, so plan["blocks"] reads back A, S1-0, cert. The parts
    are now read by each record's seq. Before the fix group_launches put A's diagnostics pod (6.25 h) first and every
    re-plan after A refused ('orders the planned parts otherwise'), so the cert-last route (LS-03 (a)) was closed.

    By hand (round 3b), the cert-last re-plan's need (cents; pods from hand_default_need's worked example): terms
    S1-0 923.75; diagnostics 214.80 + 600 + 1,156.25 = 1,971.05; LN-12 1,174.0411 + 600 + 2,497.5 = 4,271.5411; arms
    [0,1] 3,381.7948 + 600 + 2,775 = 6,756.7948; arms [2,3] 5,476.8904 + 3,375 = 8,851.8904; arms [4] 7,571.986 +
    600 + 1,387.5 = 9,559.486; HarmBench 8,619.5338 + 600 + 462.5 = 9,682.0338; Granite 9,067.0338 + 600 + 370 =
    10,037.0338; cert 9,425.0338 + 600 + 601.25 = 10,626.2838. base 10,626 cents; need 1.25 x 106.26 = 132.825 ->
    $132.83."""
    w.auto_plan = False
    w.init("S1-0", ONE_S10, amount=150.0)
    _branch_full(w)
    w.gateb()
    w.sealed()
    w.init("A", DEFAULT_A_FULL, amount=150.0)
    plan = w.tool.load()
    assert list(plan["blocks"]) == ["A", "S1-0"]                       # sorted on disk
    assert w.tool.planned_parts(plan, "A") == ["S1-0", "A"]
    assert w.tool.group_launches(plan, "A")[0][0]["cap_hours"] == 1.75   # S1-0's pod first
    same = w.tool.default_block_a_doc("A", True, (2, 2, 1), "2026-10-23T00:00:00Z", "lead")
    assert w.tool.record_block_a_plan(*w.record(same), replan=True)["replan"] is True
    last = dict(same, launches=[same["launches"][0]] + same["launches"][2:] + [same["launches"][1]])
    assert w.tool.record_block_a_plan(*w.record(last), replan=True)["need_usd"] == 132.83
    w.cert_records()
    got = w.init("cert", [{"hosts": [CERT_POD]}], amount=150.0)
    assert got["need_usd"] == 132.83 and got["terms_cents"][-1] == pytest.approx(10626.2838, abs=1e-3)


def test_a_replan_that_reorders_parts_already_planned_refuses(w):
    """With S1-0, the cert pod and A planned in that order, a cert-last re-plan orders the planned parts otherwise and
    refuses; the same plan re-recorded is accepted (it fails before the fix: the parts read A, S1-0, cert)."""
    w.auto_plan = False
    w.init("S1-0", ONE_S10, amount=150.0)
    _branch_full(w)
    w.gateb()
    w.cert_records()
    w.init("cert", [{"hosts": [CERT_POD]}], amount=150.0)
    w.sealed()
    w.init("A", DEFAULT_A_FULL, amount=150.0)
    same = w.tool.default_block_a_doc("A", True, (2, 2, 1), "2026-10-23T00:00:00Z", "lead")
    assert w.tool.record_block_a_plan(*w.record(same), replan=True)["need_usd"] == 130.59
    last = dict(same, launches=[same["launches"][0]] + same["launches"][2:] + [same["launches"][1]])
    with pytest.raises(SystemExit, match="orders the planned parts otherwise"):
        w.tool.record_block_a_plan(*w.record(last), replan=True)


def _default_s10_at(w, amount=130.59):
    w.auto_plan = False
    w.init("S1-0", ONE_S10, amount=amount)
    _branch_full(w)
    w.gateb()
    w.sealed()


def test_a_coherent_edit_of_the_default_record_refuses(w):
    """VG3-4 (should_fix): the kit default's recorded inputs must be the kit's own (split = DEFAULT_SPLIT[code]); a
    coherent edit of inputs, doc and SHA-256 to the 5-in-one split refuses."""
    _default_s10_at(w)
    plan = w.plan()
    rec = plan["records"]["block_a_plan"]
    doc = w.tool.default_block_a_doc("A", True, [5], rec["doc"]["utc"], rec["doc"]["recorded_by"])
    rec.update(doc=doc, default={**rec["default"], "split": [5]}, sha256=w.tool.hashlib_sha(w.tool.canonical(doc)))
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not the default rebuilt"):
        w.tool.block_a_plan_checked(w.tool.load())


def test_every_later_group_a_init_is_covered_by_s1_0s_funding_record(w):
    """VG3-4: a lead record re-pointed coherently at a 5-in-one plan file passes the re-derivation (the stated limit),
    but all of block A with its arms in one launch (the cert pod left out) then needs $136.49 and S1-0's funding
    record is $130.59: block A refuses even on another, larger $150 'block A' record. Before the fix it was accepted.
    By hand (round 3b; cents): S1-0 923.75; diagnostics 214.80 + 600 + 1,156.25 = 1,971.05; LN-12 1,174.0411 + 600 +
    2,497.5 = 4,271.5411; the 5 arm pods 3,381.7948 + 600 + 185 x 37.5 = 10,919.2948; HarmBench 8,619.5338 + 600 +
    462.5 = 9,682.0338; Granite 9,067.0338 + 600 + 370 = 10,037.0338; base 109.19 -> 1.25 x 109.19 = 136.4875 ->
    $136.49.
    The arms alone (S1-0 + one 5-pod launch: 214.80 + 600 + 185 x 37.5 =
    7,752.30 cents -> 1.25 x 77.52 = $96.90) are covered by S1-0's record and plan."""
    w.auto_plan = False
    w.tool.record_block_a_plan(*w.record(_plan_doc(w)))
    _default_s10_at(w)
    five = w.tool.default_block_a_doc("A", True, [5], "2026-10-23T00:00:00Z", "someone")
    p5, h5 = w.record(five)
    plan = w.plan()
    plan["records"]["block_a_plan"].update(path=p5, sha256=h5, doc=five)
    w.mac.save_plan(plan)
    assert w.tool.block_a_plan_checked(w.tool.load()) == five
    full5 = DEFAULT_A_FULL[:2] + [{"deal": [0, 1, 2, 3, 4]}, HB26, GR26]   # all of block A, the arms in one launch
    with pytest.raises(SystemExit, match=r"need \$136.49 is above block A's first funding record \(\$130.59"):
        w.init("A", full5, amount=150.0)
    assert "A" not in w.plan()["blocks"]
    assert w.init("A", [{"deal": [0, 1, 2, 3, 4]}], amount=150.0)["need_usd"] == 96.90   # the arms alone fit $130.59


def test_a_plan_record_removed_after_s1_0_refuses_the_next_init(w):
    """VG3-4: with S1-0 planned and the plan record set to null, the cert init used to record the kit default
    silently; it now refuses until a re-plan is recorded (which the same funding record must cover)."""
    w.auto_plan = False
    w.tool.record_block_a_plan(*w.record(w.tool.default_block_a_doc("A", True, (3, 2), "2026-10-23T00:00:00Z",
                                                                    "lead")))
    _default_s10_at(w)
    plan = w.plan()
    plan["records"]["block_a_plan"] = None
    w.mac.save_plan(plan)
    w.cert_records()
    with pytest.raises(SystemExit, match="no block-A plan is recorded"):
        w.init("cert", [{"hosts": [CERT_POD]}], amount=130.59)
    w.tool.record_block_a_plan(*w.record(_plan_doc(w)), replan=True)
    assert w.init("cert", [{"hosts": [CERT_POD]}], amount=130.59)["need_usd"] == 130.59


def test_s1_0s_funding_record_must_stay_unchanged(w):
    """The anchor is re-hashed from its file at every later init in the group."""
    _default_s10_at(w)
    w.cert_records()
    f = Path(w.plan()["blocks"]["S1-0"]["funding"]["path"])
    body = f.read_text()
    write_json(f, {**json.loads(body), "user_words": "other words"})          # seen only by the SHA-256
    with pytest.raises(SystemExit, match="first funding record .* differs"):
        w.init("cert", [{"hosts": [CERT_POD]}], amount=999.0)
    write_json(f, {**json.loads(body), "amount_usd": 999.0})
    with pytest.raises(SystemExit, match="first funding record .* differs"):
        w.init("cert", [{"hosts": [CERT_POD]}], amount=999.0)
    f.write_text(body)
    assert w.init("cert", [{"hosts": [CERT_POD]}], amount=130.59)["need_usd"] == 130.59


def test_a_replan_is_anchored_to_s1_0s_record_even_after_a_larger_cert_record(w):
    """VG3-5: the cert pod cites another, larger $200 'block A' record; a 5-in-one re-plan ($141.63) still refuses
    against S1-0's $130.59, and a 3 + 2 re-plan ($130.59) records (kills VG3-replan-anchor-last)."""
    _default_s10_at(w)
    w.cert_records()
    w.init("cert", [{"hosts": [CERT_POD]}], amount=200.0)
    five = w.tool.default_block_a_doc("A", True, (5,), "2026-10-23T00:00:00Z", "test")
    with pytest.raises(SystemExit, match=r"needs \$141.63; the group's funding record .* is \$130.59"):
        w.tool.record_block_a_plan(*w.record(five), replan=True)
    three_two = w.tool.default_block_a_doc("A", True, (3, 2), "2026-10-23T00:00:00Z", "test")
    assert w.tool.record_block_a_plan(*w.record(three_two), replan=True)["need_usd"] == 130.59


def test_the_c3_fallback_default_is_recorded_and_re_derived_at_the_cert_and_a_inits(w):
    """VG3-5: under C3's fallback the kit default (c3 false) is recorded at S1-0 ($129.48) and re-derived from its
    inputs at the cert init (C1, C2, c0) and block A's init (kills VG3-default-c3-forced)."""
    w.auto_plan = False
    w.tool.record_simple("c3_fallback", *w.record({"kind": "stage1 c3 fallback", "status": "dropped",
                                                   "reason": "synthetic", "utc": "u", "recorded_by": "t"}))
    w.init("S1-0", ONE_S10, amount=129.48)
    assert w.plan()["records"]["block_a_plan"]["default"]["c3"] is False
    _branch_full(w)
    w.gateb()
    w.thresholds()
    got = w.init("cert", [{"hosts": [[CERT_POD[0], CERT_POD[1]]]}], amount=129.48)
    assert got["need_usd"] == 129.48
    w.sealed()
    assert w.init("A", DEFAULT_A_FULL, amount=129.48)["need_usd"] == 129.48


def test_conform_part_tolerance_and_the_pooled_job_count(w):
    """VG3-5: a pod one cent over its plan pod's spend refuses (kills VG3-plan-tol-loose); a job the plan launch holds
    once, spread over two actual launches, refuses (kills VG3-jobs-pool-reset)."""
    c = w.tool.conform_part
    k1 = ("rep_pass", None, None, "X", None, None)
    plan = [{"part": "A", "type": "hosts", "jobs": {k1: 1}, "pods": [{"cap_hours": 3.0, "spend_usd": 1.0},
                                                                    {"cap_hours": 2.0, "spend_usd": 2.0}]}]
    hosts = lambda *pods: {"type": "hosts", "pods": [{"jobs": j, "cap_hours": cap, "spend_usd": s, "deal": None}
                                                     for j, cap, s in pods]}
    assert c([hosts(([k1], 3.0, 1.0))], plan, "A") == [0]
    with pytest.raises(SystemExit, match="departs"):
        c([hosts(([k1], 3.0, 1.01))], plan, "A")
    with pytest.raises(SystemExit, match="departs"):
        c([hosts(([k1], 2.0, 2.0)), hosts(([k1], 3.0, 1.0))], plan, "A")


def test_the_block_a_need_report_and_the_init_summary_print_ln_15e_in_the_plan_and_v2a_on_its_fallback(w, capsys):
    """Round 3b (addendum §25 point 1; was VMR3-1): LN-15e's re-score is in the plan (its retrain and re-score jobs on
    the LN-12 pod, priced in the need); V2a has no script and stays on its fallback (FO-04's figures as the limit),
    recorded in the plan doc's not_in_plan and printed by block-a-need and S1-0's init summary; the judges are over
    27 units (§25 point 2)."""
    w.auto_plan = False
    assert w.tool.main(["block-a-need"]) == 0
    rep = json.loads(capsys.readouterr().out)
    assert [x["job"].split(":")[0] for x in rep["not_in_plan"]] == ["V2a"] and "FO-04" in rep["not_in_plan"][0]["why"]
    assert rep["ln15e"]["units"].startswith("a0 retrains at 1102 and 1103") and "Kendall tau" in rep["ln15e"]["outputs"]
    assert rep["judge_units"] == {"harmbench": 27, "granite": 27}
    ln12 = [x for x in rep["full"]["launches"] if x["role"] == "ln12"][0]["pods"][0]
    assert ln12["cap_hours"] == 13.5 and "a1_rescore" in ln12["unmeasured"]
    doc, _ = w.tool.default_block_a_plan(w.tool.load(), recorded_by="test")
    assert doc["not_in_plan"] == rep["not_in_plan"]                     # recorded in the plan itself
    got = w.init("S1-0", ONE_S10, dry_run=True)
    assert got["block_a_plan"]["not_in_plan"] == rep["not_in_plan"] and got["block_a_plan"]["ln15e"] == rep["ln15e"]
    for bad in ([], [{"job": "V2a", "why": "built"}]):                  # a plan that drops or rewrites the record
        with pytest.raises(SystemExit, match="not_in_plan must record"):
            w.tool.record_block_a_plan(*w.record({**doc, "not_in_plan": bad}))


def test_a_plan_file_recorded_by_a_relative_path_is_re_hashed_from_anywhere(w, monkeypatch):
    """VG3-7 (note): the plan file's path is stored resolved, so a later init from another working directory still
    finds it."""
    w.auto_plan = False
    p, h = w.record(_plan_doc(w))
    monkeypatch.chdir(w.repo)
    w.tool.record_block_a_plan(str(Path(p).relative_to(w.repo)), h)
    elsewhere = w.repo / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    assert Path(w.tool.load()["records"]["block_a_plan"]["path"]).is_absolute()
    assert w.tool.block_a_plan_checked(w.tool.load()) is not None


# ----- B15 round 3b (addendum §24-§26; notes/b15r3b-build.json) -------------------------------------------------------


def test_c0_runs_on_engine_x_in_block_a_and_never_on_the_cert_pod(w):
    """Item 6 (addendum §26): c0 (J11) evaluates an engine-X unit with B17's verified X pin, so it is block A's job on
    engine X: on the cert pod it refuses (not block cert's kind); on engine Y in block A it refuses; on the LN-12 pod
    it plans on X; the cert pod's content no longer needs it, the LN-12 pod's does (test_a_block_a_plan_that_leaves_
    out_block_a_content_refuses)."""
    w.s10()
    w.gateb()
    w.cert_records()
    with pytest.raises(SystemExit, match="c0 job does not belong to block cert"):
        w.init("cert", [{"hosts": [CERT_POD + [C0]]}], dry_run=True)
    w.sealed()
    with pytest.raises(SystemExit, match="c0 runs on engine X"):
        w.init("A", [{"hosts": [[{**C0, "engine": "Y"}]]}] + A_LAUNCHES, dry_run=True)
    w.init("A", [{"hosts": [ln12_pod(RU) + [C0]]}] + A_LAUNCHES)
    jobs = w.plan()["hosts"]["a-1"]["jobs"]
    assert jobs[-1]["kind"] == "c0" and jobs[-1]["engine"] == "X" and jobs[-1]["recipe"] == "S"
    assert w.plan()["hosts"]["a-1"]["engine"] == "X" and "c0" not in w.rules.BLOCK_KINDS["cert"]
    doc, _ = w.tool.default_block_a_plan(w.tool.load())
    assert [j["kind"] for j in doc["launches"][1]["hosts"][0]] == ["cert_c1", "cert_c2", "cert_c3"]
    assert doc["launches"][3]["hosts"][0][-1] == C0


@pytest.mark.parametrize("pod, match", [
    ([{"kind": "retrain", "arm": "a0", "seed": 1104}], "a0 at \\[1102, 1103\\]"),
    ([{"kind": "retrain", "arm": "R", "seed": 1102}], "a0 at \\[1102, 1103\\]"),
    ([{"kind": "retrain", "arm": "a0", "seed": 1102, "engine": "Y"}], "LN-15e runs on engine X"),
    ([{"kind": "a1_rescore", "arm": "a0", "seed": 1102, "regen_source": 0}], "must name its retrain"),
    ([{"kind": "retrain", "arm": "a0", "seed": 1103},
      {"kind": "a1_rescore", "arm": "a0", "seed": 1102, "regen_source": 0}], "must name its retrain"),
    ([{"kind": "regenerate", "arm": "a0", "seed": 1102},
      {"kind": "a1_rescore", "arm": "a0", "seed": 1102, "regen_source": 0}], "must name its retrain"),
    ([{"kind": "retrain", "arm": "a0", "seed": 1102}, {"kind": "retrain", "arm": "a0", "seed": 1102}],
     "planned twice")])
def test_ln_15e_jobs_follow_their_rules(w, pod, match):
    """Item 4 (REV4 LN-15e): the retrain is a0 at 1102 or 1103 on engine X; the re-score names its retrain (same
    seed) earlier on the same pod; nothing is planned twice."""
    w.s10()
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match=match):
        w.init("A", [{"hosts": [pod]}] + A_LAUNCHES, dry_run=True)


def test_ln_15e_plans_on_the_ln_12_pod_with_gate_bs_8_unit_groups(w):
    """Item 4: the re-score job in plan.json carries Gate B's 8 unit groups from its sealed MANIFEST (by its pin);
    caps by hand (Branch 128 here: W1-18's record): the pair alone, 2,520 + 18,756 = 21,276 s -> 6.0 h; spend (2,520 +
    540 + 10,944) s x $1.79/h = $6.9631."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", [{"hosts": [RESCORE[:2]]}] + A_LAUNCHES)
    h = w.plan()["hosts"]["a-1"]
    assert [j["kind"] for j in h["jobs"]] == ["retrain", "a1_rescore"] and h["jobs"][1]["regen_source"] == 0
    assert h["jobs"][1]["groups"] == [f"unit-{u}" for u in range(1, 9)] and h["jobs"][1]["unmeasured"] is True
    assert h["jobs"][0]["steps"] == 38 and h["jobs"][0]["recipe"] == h["jobs"][1]["recipe"] == "S"
    assert h["cap_hours"] == quarter_up(2520 + 540 + 1.5 * 3.04 * 3600 + 1800) == 6.0
    assert h["spend_upper_usd"] == pytest.approx((2520 + 540 + 3.04 * 3600) / 3600 * 1.79)


@pytest.mark.parametrize("change", ["unit-8 dropped", "unit-8 renamed unit-7"])
def test_ln_15e_needs_exactly_8_unit_groups_in_gate_bs_manifest(w, change):
    """Item 4; fix round (F4): 7 groups, or 8 entries naming only 7 distinct groups, refuse LN-15e's planning."""
    w.s10()
    w.gateb()
    w.sealed()
    man = json.loads((w.repo / w.rules.MAN_PATH).read_text())
    if change == "unit-8 dropped":
        man["files"] = [e for e in man["files"] if e.get("unit") != "unit-8"]
    else:
        man["files"] = [{**e, "unit": "unit-7"} if e.get("unit") == "unit-8" else e for e in man["files"]]
        assert sum(e.get("family") == "unit" for e in man["files"]) == 8
    w.mp.setattr(w.rules, "MAN_SHA256", sha(write_json(w.repo / w.rules.MAN_PATH, man)))
    with pytest.raises(SystemExit, match="exactly 8 unit groups"):
        w.init("A", [{"hosts": [RESCORE[:2]]}] + A_LAUNCHES, dry_run=True)


def test_a_stranded_retrain_is_requeued_in_front_of_its_re_score(w):
    """Item 4: Gate B's stranded exception holds for LN-15e's pair: a deferred re-score whose retrain completed moves
    with the retrain re-queued in front of it; a crashed re-score never moves without its retrain."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", [{"hosts": [RESCORE[:2]]}] + A_LAUNCHES)
    w.done("a-1", statuses={1: "deferred"})
    out = w.tool.defer("a-1")
    moved = w.plan()["hosts"][out["to"]]["jobs"][:2]
    assert [(j["kind"], j.get("reason")) for j in moved] == [("retrain", "stranded-regenerate"), ("a1_rescore", None)]
    assert moved[1]["regen_source"] == 0


def test_the_judges_run_over_27_units_under_plan_a(w):
    """Item 5 (addendum §25 point 2): 20 new + the 6 reused a0/R units + theta0's unit = 27 under plan A (plan B:
    14 + 7 = 21); a 26-unit plan refuses. By hand: HarmBench 27 x 800 = 21,600 answers, (1,800 + 5,400 + 900) / 3,600
    = 2.25 h -> 2.5 h; Granite 27 x 200 + 200 = 5,600, (1,800 + 2,800 + 900) / 3,600 = 1.53 h -> 2.0 h."""
    assert len(w.tool.REJUDGED_UNITS) == 7 and ("theta0", None) in w.tool.REJUDGED_UNITS
    doc, _ = w.tool.default_block_a_plan(w.tool.load())
    assert [x["judge"]["arms"] for x in doc["launches"] if x["role"] == "judge"] == [27, 27]
    frozen = w.tool.plan_launches(w.tool.load(), doc)
    assert [x["pods"][0]["cap_hours"] for x in frozen if x["role"] == "judge"] == [2.5, 2.0]
    with pytest.raises(SystemExit, match="at least 27 units"):
        w.tool.record_block_a_plan(*w.record(_judges(26, 26)(doc)))


def test_the_round_3b_funding_report_from_the_kits_own_functions(w):
    """Item 7 (addendum §25 point 3): plan A, the default (2+2+1) and the worst case (all five arm pods in one launch),
    Branch full and Branch 128, from block-a-need's report (hand values in hand_default_need's worked example). The
    top-up the lead asks of the user = the worst-case Branch-full need rounded up to the dollar: $141.63 -> $142
    (round 3b's top-up; round 3c's is $144: test_a_144_top_up_covers_the_two_ln12_pod_five_in_one_replan_...)."""
    rep = {split: w.tool.plan_report(w.tool.load(), w.tool.default_block_a_doc("A", True, split, "u", "t"))
           for split in ((2, 2, 1), (5,))}
    assert [(rep[s][b]["base_need_usd"], rep[s][b]["need_usd"]) for s in ((2, 2, 1), (5,)) for b in ("full", "128")] \
        == [(104.47, 130.59), (98.13, 122.66), (113.30, 141.63), (107.23, 134.04)]
    assert rep[(5,)]["frozen"]["need_usd"] == rep[(5,)]["full"]["need_usd"]
    assert math.ceil(rep[(5,)]["full"]["need_usd"]) == 142
    worst = max(w.tool.need_of(w.tool.plan_launches(w.tool.load(), w.tool.default_block_a_doc(
        "A", True, split, "u", "t")))["need_usd"] for split in ((5,), (1, 4), (2, 3), (4, 1), (2, 2, 1), (1, 1, 1, 1, 1)))
    assert worst == 141.63


@pytest.mark.parametrize("pool", ["plant", "decoy"])
def test_a_filled_pins_file_whose_pool_hash_differs_refuses_even_when_req8_agrees(w, pool):
    """Round 3b item 3, survivor B15-2-d2-req8-pool (round 2's spec): the filled pins file (pinned by its own SHA-256)
    must name the D-2 pool pin itself; REQ-8's record agreeing is not enough. A filled file re-pinned with another
    plant (or decoy) hash refuses J5's planning, so a kit whose D2_POOL_PINS and D2_POOLS disagree never plans J5."""
    w.s10()
    w.gateb()
    w.sealed()
    path = w.repo / w.rules.D2_POOL_PINS["path"]
    doc = json.loads(path.read_text())
    doc["pools"][pool]["sha256"] = "0" * 64
    w.mp.setattr(w.rules, "D2_POOL_PINS", {"path": w.rules.D2_POOL_PINS["path"], "sha256": sha(write_json(path, doc))})
    with pytest.raises(SystemExit, match=f"the {pool} pool's SHA-256 in the filled pins or REQ-8's record"):
        w.init("A", [{"hosts": [DIAG_POD]}] + A_LAUNCHES, dry_run=True)


# ===== Round 3c (notes/b15r3c-build.json): block A completes against its plan; the $144 top-up ======================

NOT_RUN = "stage1 block-a not-run decision"
DEAL_RUNS = [(a, s) for a in ("A1", "L1", "H1", "S1", "S3", "S4") for s in (1102, 1103, 1104)] + [("a0", 1104),
                                                                                                   ("R", 1104)]


def _decision(w, jobs, reason="lead: synthetic decision", **change) -> tuple[str, str]:
    return w.record({"kind": NOT_RUN, "jobs": jobs, "reason": reason, "utc": "2026-10-24T08:00:00Z",
                     "recorded_by": "test", **change})


@pytest.mark.parametrize("branch, fallback, n, has, lacks", [
    ("128", False, 45, ["transfer_report theta0", "o_only theta0", "o_only R 1103", "c0 R 1101"], []),
    ("full", False, 44, ["o_only theta0", "retrain a0 1103", "a1_rescore a0 1102"], ["transfer_report theta0"]),
    ("full", True, 37, ["regenerate R 1103", "c0 R 1101", "retrain a0 1103"],
     ["o_only theta0", "o_only a0 1101", "transfer_report theta0"])])
def test_block_as_required_jobs_follow_the_plan_the_branch_and_the_o_ext_fallback(w, branch, fallback, n, has, lacks):
    """Round 3c item 2 (VP3b-3): the jobs World's recorded test plan requires for block A, by hand: 4 diagnostics
    jobs; the LN-12 pods (a0 pairs 6, LN-15e pairs 4, theta0's J3, theta0's LN-14 report under Branch 128 only | R
    pairs 6, c0); the 20 dealt arm runs (one arm launch, pods 0-4 in order, run i of the deal on pod i mod 5); the two
    judge launches over 27 units each. Branch 128: 4 + 12 + 7 + 20 + 2 = 45; Branch full: 44; full under fallback (c)
    (no O-only pass): 4 + 7 + 4 + 20 + 2 = 37."""
    w.s10(branch=branch)
    if fallback:
        w.tool.record_simple("oext_fallback", *w.record({"kind": "stage1 oext fallback", "status": "dev100_recipe_cap",
                                                         "reason": "r", "utc": "u", "recorded_by": "t"}))
    plan = w.plan()
    req = w.tool.block_a_required(plan, w.tool.block_a_plan_checked(plan))
    assert len(req) == n and all(x in req for x in has) and not any(x in req for x in lacks)
    assert list(req)[:4] == ["untuned_answers", "rep_pass", "l1_scan", "classifier"]
    arms = [x for x in req if x.startswith(("arm ", "a0_arm "))]
    hand = [DEAL_RUNS[i] for p in range(5) for i in range(p, 20, 5)]
    assert arms == [f"{'a0_arm' if a == 'a0' else 'arm'} {a} {s}" for a, s in hand]
    assert arms[:4] == ["arm A1 1102", "arm L1 1104", "arm S1 1103", "arm S4 1102"]
    assert list(req)[-2:] == ["judge harmbench", "judge granite"] and req["judge harmbench"] == req["judge granite"] \
        == 27 and req["c0 R 1101"] == 0


def test_block_a_completes_only_when_every_planned_job_ran_or_a_decision_names_it(w, capsys):
    """Round 3c item 2 (VP3b-3): block A launches every planned job but LN-15e's 1103 pair and c0 (a launch may leave
    planned jobs out). Every host completes and both judge launches are released and filed, yet seal.py block A and
    block B's init refuse, naming exactly those 3 jobs. The lead's not-run decision (record-block-a-not-run) refuses a
    job outside the plan, one that ran, one still planned, a repeat and a malformed record; once it names the 3 with
    a reason, block A seals and the seal lists them with the decision's SHA-256. A decision file changed after
    recording refuses the seal."""
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    with pytest.raises(SystemExit, match="block A is not planned"):
        w.tool.record_block_a_not_run(*_decision(w, ["c0 R 1101"]))
    pod1 = ln12_pod(A0U) + [{"kind": "retrain", "arm": "a0", "seed": 1102},
                            {"kind": "a1_rescore", "arm": "a0", "seed": 1102, "regen_source": 6},
                            {"kind": "o_only", "arm": "theta0"}]
    w.init("A", [{"hosts": [DIAG_POD]}, {"hosts": [pod1, ln12_pod(RU)]}, {"deal": [0, 1, 2, 3, 4]}, HB27, GR27])
    for jobs, match in ((["untuned_answers"], r"still planned in block A \(host a-1\)"),
                        (["o_only R 1101"], r"still planned in block A \(host a-3\)"),     # a pending host
                        (["judge granite"], r"still planned in block A \(launch 4, not released\)"),
                        (["transfer_report theta0"], "is not a job the recorded block-A plan requires"),   # full
                        (["arm A1 9999"], "is not a job the recorded block-A plan requires")):
        with pytest.raises(SystemExit, match=match):
            w.tool.record_block_a_not_run(*_decision(w, jobs))
    w.done("a-1")
    w.tool.release("A")
    for host in ("a-2", "a-3"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-4", "a-5", "a-6", "a-7", "a-8"):
        w.done(host)
    assert w.tool.release("A")["launches_released"] == 5                 # both judge launches released
    assert w.tool.block_a_open(w.plan())[-2:] == ["judge harmbench", "judge granite"]   # round 30: not done yet
    w.tool.record_judges("A", *w.file_judges())                          # round 30 (R2): the judges' record
    assert w.tool.block_a_open(w.plan()) == ["retrain a0 1103", "a1_rescore a0 1103", "c0 R 1101"]
    left = ("3 job(s) the block-A plan requires have no completion record and no not-run decision: retrain a0 1103, "
            "a1_rescore a0 1103, c0 R 1101 (record-block-a-not-run")
    with pytest.raises(SystemExit, match=re.escape(f"block A is not complete; {left}")):
        w.seal.seal_block("A")
    with pytest.raises(SystemExit, match=re.escape(f"block B: block A is not complete (G5); {left}")):
        w.init("B", [{"deal": [0, 1, 2, 3, 4, 5]}])
    assert not (w.root / "seals").exists()
    for jobs, change, match in ((["regenerate a0 1101"], {}, "has a completion record"),
                                (["judge harmbench"], {}, "has a completion record"),     # recorded over 27 units
                                (["c0 R 1101", "c0 R 1101"], {}, "not a block-A not-run decision"),
                                ([], {}, "not a block-A not-run decision"),
                                (["c0 R 1101"], {"kind": "stage1 d2 fallback"}, "not a block-A not-run decision"),
                                (["c0 R 1101"], {"reason": "  "}, "needs its reason"),
                                (["c0 R 1101"], {"recorded_by": ""}, "must hold")):
        with pytest.raises(SystemExit, match=match):
            w.tool.record_block_a_not_run(*_decision(w, jobs, **change))
    assert w.plan()["records"]["block_a_not_run"] == []
    path, digest = _decision(w, ["retrain a0 1103", "a1_rescore a0 1103", "c0 R 1101"],
                             reason="lead: LN-15e's 1103 pair and c0 left out of the LN-12 launch")
    assert w.tool.main(["record-block-a-not-run", path, "--sha256", digest]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"recorded": "block_a_not_run", "sha256": digest, "open": [],
                   "jobs": ["retrain a0 1103", "a1_rescore a0 1103", "c0 R 1101"]}
    with pytest.raises(SystemExit, match="already named by a recorded not-run decision"):
        w.tool.record_block_a_not_run(*_decision(w, ["c0 R 1101"]))
    original = Path(path).read_bytes()
    Path(path).write_bytes(original + b" ")                              # changed after recording
    with pytest.raises(SystemExit, match="not-run decision of block A is missing or differs"):
        w.seal.seal_block("A")
    Path(path).write_bytes(original)
    assert w.tool.block_complete(w.plan(), "A") is True
    w.seal.seal_block("A")
    record = json.loads((w.root / "seals" / "block-A.json").read_text())
    assert record["not_run"] == [{"job": j, "decision_sha256": digest}
                                 for j in ("a1_rescore a0 1103", "c0 R 1101", "retrain a0 1103")]
    with pytest.raises(SystemExit, match="block A is sealed"):
        w.tool.record_block_a_not_run(*_decision(w, ["c0 R 1101"]))


def test_a_dealt_arm_run_the_contingency_cannot_re_run_keeps_block_a_open_until_a_decision_names_it(w):
    """Round 3c item 2: every dealt arm run is required. a-4 (deal pod 3: L1 1102, H1 1104, S3 1103, a0 1104 by the
    deal rule) crashes its first arm; with block A's contingency at $0 its defer re-runs nothing ('not re-run'), so
    a-4 counts as moved and, before round 3c, block A could complete without arm L1 1102. Now that run stays open:
    a decision naming it while a-4 still holds it refuses; after the defer it is accepted."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    w.tool.release("A")
    assert [(j["arm"], j["seed"]) for j in w.plan()["hosts"]["a-4"]["jobs"]] == [DEAL_RUNS[i] for i in (3, 8, 13, 18)]
    w.done("a-4", statuses={0: "crashed"})
    w.done("a-5")
    with pytest.raises(SystemExit, match=r"'arm L1 1102' is still planned in block A \(host a-4\)"):
        w.tool.record_block_a_not_run(*_decision(w, ["arm L1 1102"]))
    plan = w.plan()
    plan["contingency"]["A"]["remaining_usd"] = 0.0
    w.mac.save_plan(plan)
    assert w.tool.defer("a-4") == {"from": "a-4", "to": None, "jobs": 0, "not_rerun": 1}
    left = w.tool.block_a_open(w.plan())
    assert [x for x in left if x.startswith(("arm ", "a0_arm "))] == ["arm L1 1102"]
    assert len(left) == 4 + 19 + 1 + 2                                     # Branch 128: diagnostics, LN-12, arm, judges
    w.not_run(["arm L1 1102"], reason="lead: the contingency could not pay the re-run")
    w.not_run()
    assert w.tool.block_a_open(w.plan()) == [] and w.tool.block_complete(w.plan(), "A") is True


def test_a_144_top_up_covers_the_two_ln12_pod_five_in_one_replan_but_not_the_ln14_report_apart(w):
    """Round 3c item 3: the top-up asked of the user is $144 = VP3b-1's $143.19 (two LN-12 pods, c0 alone on the
    second, all five arm pods in one launch) rounded up to the dollar. By hand (cents): the one-pod 5-in-one arm term
    11,329.5031 (round 3b's funding report) + one 42-min overhead 2,520 x 179/3,600 = 11,454.80 -> base $114.55 ->
    1.25 x = $143.1875 -> $143.19; recorded under a $144 S1-0 record. LIMIT (stated in the README): a valid two-pod
    layout that puts theta0's LN-14 report on a pod of its own (it exists only under Branch 128; each pod is priced at
    the larger of its two branch figures) adds its overhead and its 1,408 s: 11,329.5031 + 3,928 x 179/3,600 =
    11,524.81 -> $115.25 -> 1.25 x = $144.0625 -> $144.06, above $144, and the kit refuses it. Needs unchanged."""
    assert math.ceil(times_125(cents((11329.5031 + 2520 * 179 / 3600) / 100))) == 144
    assert times_125(cents((11329.5031 + 2520 * 179 / 3600) / 100)) == 143.19
    assert times_125(cents((11329.5031 + (2520 + 1408) * 179 / 3600) / 100)) == 144.06
    w.auto_plan = False
    w.init("S1-0", [{"hosts": [[{"kind": "w1_18"}]]}], amount=144.0)
    _branch_full(w)
    w.gateb()
    w.sealed()
    assert w.tool.record_block_a_plan(*w.record(_two_ln12_pods(w, (5,))), replan=True)["need_usd"] == 143.19
    apart = w.tool.default_block_a_doc("A", True, (5,), "2026-10-24T00:00:00Z", "test")
    ln12 = [x for x in apart["launches"] if x["role"] == "ln12"][0]
    assert ln12["hosts"][0][-2]["kind"] == "transfer_report"
    ln12["hosts"] = [ln12["hosts"][0][:-2] + ln12["hosts"][0][-1:], [ln12["hosts"][0][-2]]]
    with pytest.raises(SystemExit, match=r"needs \$144.06; the group's funding record .* is \$144.00"):
        w.tool.record_block_a_plan(*w.record(apart), replan=True)



# ===== Addendum §28: launches in parallel while the budget guard is off ==============================================


def _operator_log(w) -> list[dict]:
    return [json.loads(line) for line in w.mac.OPERATOR_LOG.read_text().splitlines()]


def _guard_off_recorded(w) -> str:
    p, h = _guard_off(w)
    w.tool.record_simple("guard_off", p, h)
    assert w.rules.guard_off_record(w.root)["sha256"] == h
    return h


def test_with_the_guard_off_release_does_not_wait_for_the_launch_before_it(w):
    """§28: while the user's guard-off decision is recorded, release releases block A's launch 1 while launch 0's
    three hosts are running, and records it (the launch, the open hosts, the decision's SHA-256, UTC) in the block and
    in the operator log. The order stays: one launch per release, and then nothing is left."""
    w.s10()
    w.gateb()
    w.sealed()
    h = _guard_off_recorded(w)
    w.init("A", A_LAUNCHES)
    out = w.tool.release("A")
    assert out["released"] == ["a-4", "a-5"] and out["launches_released"] == 2
    assert [{k: e[k] for k in ("launch", "open_hosts", "guard_off_sha256")} for e in out["released_early"]] == \
        [{"launch": 1, "open_hosts": ["a-1", "a-2", "a-3"], "guard_off_sha256": h}]
    assert dt.datetime.fromisoformat(out["released_early"][0]["utc"]).utcoffset() == dt.timedelta(0)
    plan = w.plan()
    assert plan["blocks"]["A"]["released_early"] == out["released_early"]
    assert sorted(n for n in plan["hosts"] if n.startswith("a-")) == ["a-1", "a-2", "a-3", "a-4", "a-5"]
    assert not any(plan["hosts"][n].get("done") for n in ("a-1", "a-2", "a-3"))
    last = _operator_log(w)[-1]
    assert last["action"] == "release" and last["hosts"] == ["a-4", "a-5"] and last["released_early"] == out["released_early"]
    with pytest.raises(SystemExit, match="no launch left to release"):
        w.tool.release("A")


def test_with_the_guard_off_a_launch_whose_hosts_are_done_is_released_as_before(w):
    w.s10()
    w.gateb()
    w.sealed()
    _guard_off_recorded(w)
    w.init("A", A_LAUNCHES)
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    out = w.tool.release("A")
    assert out == {"block": "A", "released": ["a-4", "a-5"], "launches_released": 2}
    assert "released_early" not in w.plan()["blocks"]["A"] and "released_early" not in _operator_log(w)[-1]


@pytest.mark.parametrize("change", ["file changed", "file deleted", "record removed"])
def test_without_a_valid_guard_off_record_release_waits_exactly_as_before(w, change):
    """No record, or a record whose file changed or is gone (re-hashed at every release): the old rule."""
    w.s10()
    w.gateb()
    w.sealed()
    p, h = _guard_off(w)
    w.tool.record_simple("guard_off", p, h)
    if change == "file changed":
        Path(p).write_text(Path(p).read_text().replace("test", "tset"))
    elif change == "file deleted":
        Path(p).unlink()
    else:
        plan = w.plan()
        plan["records"]["guard_off"] = None
        w.mac.save_plan(plan)
    w.init("A", A_LAUNCHES)
    with pytest.raises(SystemExit, match=r"block A: launch 0's hosts are not done \(a-1\)"):
        w.tool.release("A")
    plan = w.plan()
    assert plan["blocks"]["A"]["released"] == 1 and "released_early" not in plan["blocks"]["A"]
    assert sorted(n for n in plan["hosts"] if n.startswith("a-")) == ["a-1", "a-2", "a-3"]


def test_with_the_guard_off_the_block_a_plan_check_at_release_stays(w):
    """The plan conformance stays: with launch 0 still running, a pending pod raised by hand past the plan refuses."""
    _default_after_s1_0(w)
    _guard_off_recorded(w)
    w.init("A", DEFAULT_A_FULL)
    plan = w.plan()
    plan["blocks"]["A"]["pending"]["a-2"]["cap_hours"] = 14.0              # the LN-12 plan pod is 13.5 h
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="block A: launch 1 departs"):
        w.tool.release("A")
    assert "a-2" not in w.plan()["hosts"]


def test_with_the_guard_off_the_release_gates_stay(w):
    """Every gate of release_hosts stays: with launch 0 still running, a hand-edited plan-A/B record refuses the next
    launch; the restored record releases it early."""
    w.s10()
    w.gateb(sigma=3.9)
    w.sealed()
    _guard_off_recorded(w)
    w.init("A", A_LAUNCHES)
    plan = w.plan()
    good = dict(plan["records"]["plan_ab"])
    plan["records"]["plan_ab"].update(sigma_pp=5.0, code="B")
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="not the one derived"):
        w.tool.release("A")
    plan = w.plan()
    assert "a-4" not in plan["hosts"] and "released_early" not in plan["blocks"]["A"]
    plan["records"]["plan_ab"] = good
    w.mac.save_plan(plan)
    assert w.tool.release("A")["released_early"][0]["open_hosts"] == ["a-1", "a-2", "a-3"]


def test_with_the_guard_off_a_judge_launch_still_waits_for_every_earlier_launch(w):
    """Hosts launches go in parallel; a judge launch judges their units, so it waits until every earlier launch's
    hosts are done or moved - also those of a launch before the one just before it (released early)."""
    w.s10(branch="full")
    w.gateb()
    w.sealed()
    _guard_off_recorded(w)
    pod1 = ln12_pod(A0U) + [{"kind": "retrain", "arm": "a0", "seed": 1102},
                            {"kind": "a1_rescore", "arm": "a0", "seed": 1102, "regen_source": 6},
                            {"kind": "o_only", "arm": "theta0"}]
    w.init("A", [{"hosts": [DIAG_POD]}, {"hosts": [pod1, ln12_pod(RU)]}, {"deal": [0, 1, 2, 3, 4]}, HB27, GR27])
    assert w.tool.release("A")["released"] == ["a-2", "a-3"]                    # a-1 running
    second = w.tool.release("A")
    assert second["released"] == ["a-4", "a-5", "a-6", "a-7", "a-8"]
    assert [(e["launch"], e["open_hosts"]) for e in second["released_early"]] == [(2, ["a-2", "a-3"])]
    with pytest.raises(SystemExit, match=r"launch 3 is a judge launch; it waits until every earlier launch's hosts are "
                                         r"done, with the budget guard off too \(a-1\)"):
        w.tool.release("A")
    for host in ("a-2", "a-3", "a-4", "a-5", "a-6", "a-7", "a-8"):
        w.done(host)
    with pytest.raises(SystemExit, match=r"launch 3 is a judge launch.*\(a-1\)"):    # launch 2 is done, launch 0 is not
        w.tool.release("A")
    assert w.plan()["blocks"]["A"]["released"] == 3
    w.done("a-1")
    out = w.tool.release("A")
    assert out["launches_released"] == 5 and out["released"] == [] and "released_early" not in out
    assert [e["launch"] for e in w.plan()["blocks"]["A"]["released_early"]] == [1, 2]


def test_with_the_guard_off_block_order_stays(w):
    """The guard-off rule is inside a block: block B still refuses before block A is complete and sealed."""
    w.s10()
    w.gateb()
    w.sealed()
    _guard_off_recorded(w)
    w.init("A", A_LAUNCHES)
    w.tool.release("A")
    with pytest.raises(SystemExit, match="block A is not complete"):
        w.init("B", [{"deal": [0, 1, 2, 3, 4, 5]}])


def test_with_the_guard_off_a_moved_host_does_not_hold_a_judge_launch(w):
    """A host that was moved before its job started (requeue: not done, its jobs on a new host) counts as finished for
    the judge launch's wait, as it does for the old rule's wait."""
    w.s10()
    w.gateb()
    w.sealed()
    _guard_off_recorded(w)
    w.init("A", A_LAUNCHES + [HB27, GR27])
    assert w.tool.release("A")["released_early"][0]["open_hosts"] == ["a-1", "a-2", "a-3"]
    for host in ("a-1", "a-2", "a-3", "a-4", "a-5"):
        _launch(w, host)
    _log(w, "a-1", "pre-job-failed", "pre-job-stop")
    assert w.tool.requeue("a-1")["to"] == "a-6"
    for host in ("a-2", "a-3", "a-4", "a-5"):
        w.done(host)
    assert not w.plan()["hosts"]["a-1"].get("done")
    out = w.tool.release("A")
    assert out["launches_released"] == 4 and out["released"] == [] and "released_early" not in out


# ===== Addendum §29 (round 29, 26 Oct): the unpulled re-score units and the user's re-run payment ====================
# Real-shaped synthetic fixtures from the live kit's records (plan.json, hosts/, retrieved/a-2/tree/job-done/; no data
# text): pod a-2 is block A's LN-12 pod with 19 jobs (the a0 and R pairs 0-11, LN-15e's retrain and re-score pairs at
# 12-15, theta0's J3 and LN-14 report 16-17, c0 18) under Branch 128; its jobs 12-15 wrote their units to rescore/,
# which the light pull did not fetch, and c0's outputs list 8 model-state files that the light pull leaves on the pod.
# Pod a-7 (deal pod 4: L1 1103, S1 1102, S3 1104, R 1104) stopped before its job; the contingency could not pay its
# unit, so the four runs are held as not re-run.

UNPULLED = "stage1 unpulled outputs decision"
PAYMENT = "stage1 user decision: pay re-runs beyond the contingency"
LN12_128 = with_rescore(ln12_pod(A0U + RU)) + [{"kind": "o_only", "arm": "theta0"},
                                               {"kind": "transfer_report", "arm": "theta0"}, C0]
DEFAULT_A_128 = [{"hosts": [DIAG_POD]}, {"hosts": [LN12_128]}, {"deal": [0, 1]}, {"deal": [2, 3]}, {"deal": [4]},
                 HB27, GR27]
C0_STATES = ("e1/adapter.safetensors", "e1/optimizer.safetensors", "e1/rng.safetensors", "init/adapter.safetensors",
             "init/rng.safetensors", "q/adapter.safetensors", "q/optimizer.safetensors", "q/rng.safetensors")
RESCORE_UNITS = {12: "rescore/1102-a0-retrain-a1", 13: "rescore/1102-attributes-a1",
                 14: "rescore/1103-a0-retrain-a1", 15: "rescore/1103-attributes-a1"}
A7_RUNS = [("L1", 1103), ("S1", 1102), ("S3", 1104), ("R", 1104)]


def _block_a_128(w):
    """Block A under Branch 128 with the kit's default block-A plan (split 2+2+1, one LN-12 pod), as the live kit
    holds it: a-1 diagnostics, a-2 LN-12 (19 jobs), a-3/a-4, a-5/a-6, a-7 the dealt arm pods, then both judges."""
    w.auto_plan = False
    w.s10(branch="128")
    w.gateb()
    w.sealed()
    w.init("A", DEFAULT_A_128)
    w.done("a-1")
    w.tool.release("A")
    jobs = w.plan()["hosts"]["a-2"]["jobs"]
    assert [job_label(j) for j in jobs[12:16]] == ["retrain a0 1102", "a1_rescore a0 1102", "retrain a0 1103",
                                                   "a1_rescore a0 1103"] and len(jobs) == 19


def job_label(j: dict) -> str:
    return " ".join(str(x) for x in (j["kind"], j.get("arm"), j.get("seed")) if x is not None)


def _a2_light_pull(w, host: str = "a-2") -> Path:
    """a-2's pulled tree after the light pull: every job complete; the regenerations' units under round1/ (pulled);
    LN-15e's four units under rescore/ only on the pod (their COMPLETE.json SHA-256 known from JOB-DONE.json); c0's
    outputs list its 8 .safetensors states, absent here; every job's cost ledger under job-I/ (pulled)."""
    tree = w.root / "retrieved" / host / "tree"
    recs = []
    for i, job in enumerate(w.plan()["hosts"][host]["jobs"]):
        r = {"index": i, "kind": job["kind"], "arm": job["arm"], "seed": job["seed"], "status": "complete",
             "engine": "X", "engine_sha256": X}
        ledger = f"job-{i}/cost-ledger.json"
        outputs = {ledger: sha(write_json(tree / ledger, {"stages_s": {"training": 1.0}, "i": i}))}
        if i in RESCORE_UNITS:
            r.update(unit=RESCORE_UNITS[i], complete_sha256=hashlib.sha256(f"pod-only {i}".encode()).hexdigest())
        elif job["kind"] == "regenerate":
            unit = f"round1/{job['seed']}-{job['arm']}-regen-a1"
            write_json(tree / unit / "eval" / "e1" / "summary.json", {"u": float(SENTINELS[0])})
            r.update(unit=unit, complete_sha256=sha(write_json(tree / unit / "COMPLETE.json", {"i": i})))
        else:
            rel = f"job-{i}/{job['kind']}.json"
            outputs[rel] = sha(write_json(tree / rel, {"kind": job["kind"], "value": SENTINELS[1]}))
            if job["kind"] == "c0":
                for s in C0_STATES:
                    outputs[f"job-{i}/c0/train/states/{s}"] = hashlib.sha256(s.encode()).hexdigest()
        r["outputs"] = outputs
        recs.append(r)
    write_json(tree / "JOB-DONE.json", {"host": host, "jobs": recs, "ok": True, "stopped": None})
    return tree


def _unpulled(w, jobs, host="a-2", **change) -> tuple[str, str]:
    body = {"kind": UNPULLED, "host": host, "jobs": jobs, "reason": "lead: addendum §29; the light pull did not fetch "
            "rescore/ and a-2 is never restarted", "utc": "2026-10-26T06:41:00Z", "recorded_by": "test", **change}
    return w.record({k: v for k, v in body.items() if v is not None})


@pytest.mark.parametrize("change, match", [
    ({"kind": "stage1 block-a not-run decision"}, "its kind is not"),
    ({"extra": "x"}, "must hold exactly"),
    ({"reason": None}, "must hold exactly"),
    ({"jobs": []}, "non-empty list of distinct job indices"),
    ({"jobs": [12, 12]}, "non-empty list of distinct job indices"),
    ({"jobs": ["12"]}, "non-empty list of distinct job indices"),
    ({"jobs": [True]}, "non-empty list of distinct job indices"),
    ({"reason": " "}, "must be non-empty texts"),
    ({"utc": "2026-10-26T06:41:00+05:30"}, "not a UTC time"),
    ({"utc": "2099-01-01T00:00:00Z"}, "in the future"),
    ({"host": "a-99"}, "a-99 is not a host"),
    ({"jobs": [19]}, "job 19 is not a job of this host"),
    ({"jobs": [0]}, "job 0's unit is in the pulled tree"),              # a regeneration whose unit was pulled
    ({"jobs": [1]}, "job 1 is not a complete unit job"),                # an O-only pass: no unit at all
    ({"jobs": [12, 16]}, "job 16 is not a complete unit job")])
def test_an_unpulled_decision_names_only_complete_units_the_pull_did_not_fetch(w, change, match):
    """§29 point 3: record-unpulled takes the lead's decision {kind, host, jobs, reason, utc, recorded_by} (exactly),
    and only for jobs complete on the pod with a unit whose COMPLETE.json is absent from the pulled tree."""
    _block_a_128(w)
    _a2_light_pull(w)
    change = dict(change)
    args = _unpulled(w, change.pop("jobs", [12, 13, 14, 15]), **change)
    with pytest.raises(SystemExit, match=match):
        w.tool.record_unpulled(*args)
    assert w.plan()["records"].get("unpulled") in (None, [])


def test_record_done_records_jobs_12_to_15_complete_not_pulled_under_the_leads_decision(w, capsys):
    """§29 points 1-3, the a-2 case by hand. Without a decision, record-done a-2 refuses at job 12 (its COMPLETE.json is
    not in the pulled tree) and says what to record. c0's 8 .safetensors outputs that the light pull leaves on the pod
    are accepted as states on the pod, but a state file that is present must hash as recorded and a missing output
    that is not a state still refuses. With the decision
    (jobs 12-15), record-done records all 19 complete, jobs 12-15 with pulled false and the decision's SHA-256, and
    nothing else changes: the other 15 jobs keep their units or outputs and carry no such mark; a second decision
    naming job 12, or one after record-done, refuses; a changed decision file refuses record-done."""
    _block_a_128(w)
    tree = _a2_light_pull(w)
    with pytest.raises(SystemExit, match=r"a-2: job 12's COMPLETE.json is missing from the pulled tree or differs; if "
                                         r"the light pull did not fetch its unit, record the lead's decision first"):
        w.tool.record_done("a-2")
    path, digest = _unpulled(w, [15, 13, 12, 14])
    assert w.tool.main(["record-unpulled", path, "--sha256", digest]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"recorded": "unpulled", "sha256": digest, "host": "a-2", "jobs": [12, 13, 14, 15],
                   "labels": ["retrain a0 1102", "a1_rescore a0 1102", "retrain a0 1103", "a1_rescore a0 1103"]}
    with pytest.raises(SystemExit, match="already named by a recorded unpulled outputs decision"):
        w.tool.record_unpulled(*_unpulled(w, [12]))
    c0_out = tree / "job-18" / "c0.json"
    kept = c0_out.read_bytes()
    c0_out.unlink()                                                       # a missing output that is not a state
    with pytest.raises(SystemExit, match="job 18's output is missing from the pulled tree or differs"):
        w.tool.record_done("a-2")
    c0_out.write_bytes(kept)
    state = tree / "job-18" / "c0" / "train" / "states" / "e1" / "adapter.safetensors"
    state.parent.mkdir(parents=True)
    state.write_bytes(b"a state file pulled by a full pull, changed")       # present: it must hash as recorded
    with pytest.raises(SystemExit, match="job 18's output is missing from the pulled tree or differs"):
        w.tool.record_done("a-2")
    state.unlink()
    original = Path(path).read_bytes()
    Path(path).write_bytes(original + b"\n")
    with pytest.raises(SystemExit, match="unpulled outputs decision is missing or differs"):
        w.tool.record_done("a-2")
    Path(path).write_bytes(original)
    got = w.tool.record_done("a-2")
    assert got == {"host": "a-2", "statuses": ["complete"] * 19, "not_pulled": [12, 13, 14, 15]}
    jobs = w.plan()["hosts"]["a-2"]["jobs"]
    for i, j in enumerate(jobs):
        if i in RESCORE_UNITS:
            assert (j["pulled"], j["unpulled_decision_sha256"], j["unit"]) == (False, digest, RESCORE_UNITS[i])
            assert j["complete_sha256"] == hashlib.sha256(f"pod-only {i}".encode()).hexdigest()
        else:
            assert "pulled" not in j and "unpulled_decision_sha256" not in j
    assert jobs[18]["states_on_pod"] == 8 and all("states_on_pod" not in j for j in jobs[:18])
    log = [json.loads(line) for line in w.mac.OPERATOR_LOG.read_text().splitlines()]
    assert [e["action"] for e in log[-2:]] == ["record-unpulled", "record-done"] and log[-1]["not_pulled"] == [12, 13,
                                                                                                             14, 15]
    with pytest.raises(SystemExit, match="a-2 is recorded done"):
        w.tool.record_unpulled(*_unpulled(w, [16]))


def test_without_a_decision_a_pulled_rescore_unit_records_as_before(w):
    """The other way: when the pull fetched rescore/ (the new pull list), record-done a-2 needs no decision and marks
    no job not pulled; the completion check counts the four LN-15e jobs as done."""
    _block_a_128(w)
    tree = _a2_light_pull(w)
    done = json.loads((tree / "JOB-DONE.json").read_text())
    for r in done["jobs"]:
        if r["index"] in RESCORE_UNITS:
            r["complete_sha256"] = sha(write_json(tree / r["unit"] / "COMPLETE.json", {"i": r["index"]}))
    write_json(tree / "JOB-DONE.json", done)
    assert "not_pulled" not in w.tool.record_done("a-2")
    plan = w.plan()
    assert all("pulled" not in j for j in plan["hosts"]["a-2"]["jobs"])
    done_labels = w.tool.block_a_done(plan, w.tool.block_a_required(plan, w.tool.block_a_plan_checked(plan)))
    assert {"retrain a0 1102", "a1_rescore a0 1102", "retrain a0 1103", "a1_rescore a0 1103"} <= done_labels
    assert w.tool.block_a_unpulled(plan) == {}
    with pytest.raises(SystemExit, match="job 12's unit is in the pulled tree"):
        w.tool.unit_problem(tree, done["jobs"][12], 12, "a-2")


def test_block_a_counts_not_pulled_jobs_as_decided_and_the_seal_lists_them_without_hashes(w):
    """§29 point 3: after record-done under the decision, block A's completion check counts jobs 12-15 as decided by
    it (not as done), re-hashing the decision at every use; with every other job of the plan done (45 under Branch 128:
    4 + 19 + 20 + 2), block A seals, and the seal lists the four by host, index, name, unit path and the decision's
    SHA-256, with no file hash, and holds no file under rescore/. A changed decision file refuses the completion check
    and the seal."""
    _block_a_128(w)
    _a2_light_pull(w)
    path, digest = _unpulled(w, [12, 13, 14, 15])
    w.tool.record_unpulled(path, digest)
    w.tool.record_done("a-2")
    plan = w.plan()
    labels = ["retrain a0 1102", "a1_rescore a0 1102", "retrain a0 1103", "a1_rescore a0 1103"]
    required = w.tool.block_a_required(plan, w.tool.block_a_plan_checked(plan))
    assert len(required) == 45 and all(x in required for x in labels)
    assert not set(labels) & w.tool.block_a_done(plan, required)
    assert w.tool.block_a_unpulled(plan) == {x: digest for x in labels}
    assert not set(labels) & set(w.tool.block_a_open(plan))
    w.tool.release("A")
    for host in ("a-3", "a-4"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-5", "a-6"):
        w.done(host)
    w.tool.release("A")
    w.done("a-7")
    assert w.tool.release("A")["launches_released"] == 7
    w.tool.record_judges("A", *w.file_judges())                          # round 30 (R2)
    assert w.tool.block_a_open(w.plan()) == [] and w.tool.block_complete(w.plan(), "A") is True
    original = Path(path).read_bytes()
    Path(path).write_bytes(original.replace(b"lead:", b"lead :"))
    for call in (lambda: w.tool.block_a_open(w.plan()), lambda: w.seal.seal_block("A")):
        with pytest.raises(SystemExit, match="unpulled outputs decision is missing or differs"):
            call()
    Path(path).write_bytes(original)
    w.seal.seal_block("A")
    record = json.loads((w.root / "seals" / "block-A.json").read_text())
    assert record["not_pulled"] == [{"host": "a-2", "index": i, "job": x, "unit": RESCORE_UNITS[i],
                                     "decision_sha256": digest} for i, x in zip((12, 13, 14, 15), labels)]
    assert not any(f["path"].startswith("rescore/") for f in record["files"]) and record["not_run"] == []
    with pytest.raises(SystemExit, match="block A is sealed"):
        w.tool.record_unpulled(*_unpulled(w, [16], host="a-2"))


def _a7_held(w):
    """a-1 to a-6 done; a-7 released, created, stopped before its job (pre-job-failed, then a confirmed stop); block A's
    contingency at $2.95 (the live kit's remaining_usd, less than one arm's $3.31), so requeue a-7 holds its four runs
    as not re-run (the live kit's a-7 entries)."""
    _block_a_128(w)
    w.done("a-2")
    w.tool.release("A")
    for host in ("a-3", "a-4"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-5", "a-6"):
        w.done(host)
    assert w.tool.release("A")["released"] == ["a-7"]
    assert [(j["arm"], j["seed"]) for j in w.plan()["hosts"]["a-7"]["jobs"]] == A7_RUNS
    _launch(w, "a-7")
    _log(w, "a-7", "pre-job-failed", "pre-job-stop")
    plan = w.plan()
    plan["contingency"]["A"]["remaining_usd"] = 2.9470888888888886
    w.mac.save_plan(plan)
    assert w.tool.requeue("a-7") == {"from": "a-7", "to": None, "jobs": 0, "not_rerun": 4}
    held = w.plan()["contingency"]["A"]["not_rerun"]
    one = (52 * 60 + 1024 + 42 * 60) / 3600 * 1.79              # by hand: an arm's Branch-128 upper + a new pod
    assert [(e["arm"], e["seed"], e["where"]) for e in held] == [(a, s, "requeue a-7") for a, s in A7_RUNS]
    assert all(e["cost_usd"] == pytest.approx(one) for e in held) and round(one, 2) == 3.31


def _payment(w, runs=None, amount=9.49, **change) -> tuple[str, str]:
    body = {"kind": PAYMENT, "user_words": "Yes: pay a-7's four re-runs from the balance beyond block A's contingency.",
            "block": "A", "jobs": [{"arm": a, "seed": s} for a, s in (A7_RUNS if runs is None else runs)],
            "amount_usd": amount, "utc": "2026-10-26T14:44:00Z", "recorded_by": "test", **change}
    return w.record({k: v for k, v in body.items() if v is not None})


@pytest.mark.parametrize("change, match", [
    ({"kind": "stage1 user decision: budget guard off"}, "its kind is not"),
    ({"user_words": None}, "must hold exactly"),
    ({"note": "x"}, "must hold exactly"),
    ({"user_words": ""}, "must be non-empty texts"),
    ({"amount_usd": 0}, "a finite number above 0"),
    ({"amount_usd": True}, "a finite number above 0"),
    ({"amount_usd": "9.49"}, "a finite number above 0"),
    ({"jobs": []}, "distinct {arm, seed}"),
    ({"jobs": [{"arm": "L1", "seed": "1103"}]}, "distinct {arm, seed}"),
    ({"jobs": [{"arm": "L1", "seed": 1103, "kind": "arm"}]}, "distinct {arm, seed}"),
    ({"jobs": [{"arm": "L1", "seed": 1103}, {"arm": "L1", "seed": 1103}]}, "distinct {arm, seed}"),
    ({"utc": "2099-01-01T00:00:00Z"}, "in the future"),
    ({"block": "B"}, "not a funding group with a contingency"),
    ({"jobs": [{"arm": "A1", "seed": 1102}]}, "A1 at 1102: not held by block A's contingency as not re-run")])
def test_the_users_re_run_payment_record_is_exact_and_names_only_held_runs(w, change, match):
    _a7_held(w)
    with pytest.raises(SystemExit, match=match):
        w.tool.record_rerun_payment(*_payment(w, **change))
    assert w.plan()["records"].get("rerun_payments") in (None, [])


def test_requeue_pays_a7s_four_runs_beyond_the_contingency_under_the_users_record_and_nothing_else(w, capsys):
    """The user's 26 Oct decision, by hand. Without the record, requeue a-7 refuses as before (already deferred) and
    the four runs stay open in block A. With it (amount $9.49), requeue a-7 moves exactly the four, in order, to a new
    arm pod a-8 (launch 4, cap 7.0 h) and pays them as one unit, $9.4950 = (2,520 + 4 x 4,144) s x $1.79/h, $9.49 in
    cents, recorded under contingency.user_paid and logged; the contingency's remaining_usd ($2.95), spent and
    not_rerun stay exactly as they were. A second requeue pays nothing (already deferred); another record naming one
    of the four refuses; a-8's runs complete block A's arms."""
    _a7_held(w)
    before = json.loads(json.dumps(w.plan()["contingency"]["A"]))
    with pytest.raises(SystemExit, match="a-7 was already deferred"):
        w.tool.requeue("a-7")
    assert [x for x in w.tool.block_a_open(w.plan()) if x.startswith("arm ")] == [f"arm {a} {s}" for a, s in A7_RUNS]
    path, digest = _payment(w)
    assert w.tool.main(["record-rerun-payment", path, "--sha256", digest]) == 0
    assert json.loads(capsys.readouterr().out) == {"recorded": "rerun_payment", "sha256": digest, "block": "A",
                                                   "jobs": [{"arm": a, "seed": s} for a, s in A7_RUNS],
                                                   "amount_usd": 9.49}
    out = w.tool.requeue("a-7")
    assert out == {"from": "a-7", "to": "a-8", "jobs": 4, "cap_hours": 7.0, "role": "arms"}
    plan = w.plan()
    c = plan["contingency"]["A"]
    assert {k: c[k] for k in before} == before                         # remaining, spent and not_rerun unchanged
    unit = (2520 + 4 * 4144) / 3600 * 1.79
    assert len(c["user_paid"]) == 1 and c["user_paid"][0]["cost_usd"] == pytest.approx(unit)
    assert {k: v for k, v in c["user_paid"][0].items() if k not in ("cost_usd", "utc")} == {
        "unit": [{"kind": "arm", "arm": a, "seed": s} for a, s in A7_RUNS], "new_pod": True, "cost_cents_usd": 9.49,
        "amount_usd": 9.49, "where": "requeue a-7", "decision_sha256": digest}
    a8 = plan["hosts"]["a-8"]
    assert (a8["block"], a8["launch"], a8["role"], a8["engine"], a8["done"]) == ("A", 4, "arms", "X", False)
    assert [(j["arm"], j["seed"], j["status"], j["deferred_from"], j["rerun_payment_sha256"]) for j in a8["jobs"]] == [
        (a, s, "planned", "a-7", digest) for a, s in A7_RUNS]
    assert plan["deferrals"][-1] == {"from": "a-7", "to": "a-8", "from_indices": [0, 1, 2, 3],
                                     "to_indices": [0, 1, 2, 3], "stranded": None, "reason": "user-paid-rerun",
                                     "rerun_payment_sha256": digest}
    paid = [json.loads(line) for line in w.mac.OPERATOR_LOG.read_text().splitlines()
            if json.loads(line)["action"] == "rerun-user-paid"]
    assert len(paid) == 1 and paid[0]["contingency_remaining_usd"] == pytest.approx(2.9470888888888886)
    with pytest.raises(SystemExit, match="a-7 was already deferred"):
        w.tool.requeue("a-7")
    assert len(w.plan()["contingency"]["A"]["user_paid"]) == 1
    with pytest.raises(SystemExit, match="L1 at 1103: already paid by a recorded re-run payment"):
        w.tool.record_rerun_payment(*_payment(w, runs=[("L1", 1103)]))
    w.done("a-8")
    assert not [x for x in w.tool.block_a_open(w.plan()) if x.startswith("arm ")]


def test_a_payment_covers_only_the_runs_it_names_and_never_more_than_its_amount(w):
    """The other ways: a record naming two of the four moves those two only (the other two stay held and open); the
    unit (2,520 + 2 x 4,144) s x $1.79/h = $5.3740, $5.37 in cents, is refused under a $5.36 record; the user's new
    decision ($5.37, recorded as a new file: a recorded file is never edited) supersedes it for those two and pays
    them; a payment file changed after recording refuses the requeue."""
    _a7_held(w)
    low = _payment(w, runs=A7_RUNS[:2], amount=5.36)
    w.tool.record_rerun_payment(*low)
    with pytest.raises(SystemExit, match=r"the re-run unit costs \$5.37 \(the kit's figure\), more than the \$5.36"):
        w.tool.requeue("a-7")
    assert "a-8" not in w.plan()["hosts"] and not w.plan()["contingency"]["A"].get("user_paid")
    path, digest = _payment(w, runs=A7_RUNS[:2], amount=5.37)
    w.tool.record_rerun_payment(path, digest)
    original = Path(path).read_bytes()
    Path(path).write_bytes(original.replace(b"5.37", b"9.37"))
    with pytest.raises(SystemExit, match="re-run payment decision is missing or differs"):
        w.tool.requeue("a-7")
    Path(path).write_bytes(original)
    assert w.tool.requeue("a-7")["jobs"] == 2
    plan = w.plan()
    assert [(j["arm"], j["seed"]) for j in plan["hosts"]["a-8"]["jobs"]] == A7_RUNS[:2]
    assert plan["contingency"]["A"]["user_paid"][0]["cost_usd"] == pytest.approx((2520 + 2 * 4144) / 3600 * 1.79)
    assert plan["contingency"]["A"]["user_paid"][0]["decision_sha256"] == digest != low[1]
    assert len(plan["records"]["rerun_payments"]) == 2
    planned = w.tool.block_a_planned(plan, w.tool.block_a_required(plan, w.tool.block_a_plan_checked(plan)))
    assert [planned.get(f"arm {a} {s}") for a, s in A7_RUNS] == ["host a-8", "host a-8", None, None]   # two held
    assert [j["status"] for j in plan["hosts"]["a-7"]["jobs"]] == ["not_started"] * 4


# ===== Round 30 (27 Oct; notes/kit-round-30.json): addendum §30, the judge gaps 1, 2, 5 (R2, R3), the moved hosts in
# the seal and the backup (R6) and the cost of a pod stopped without a finisher record (R7) =========================
# Every judge file, index, judge-pod result and run record below is synthetic (World.file_judges); the counts in them
# are the sentinel JUDGE_SENTINEL, which no printed line or kit record may hold.

JR = "stage1 judge completion record"


def _judged_block_a(w) -> None:
    """Block A with every host done and both judge launches (HarmBench, Granite over 27 units) released; the plan's
    diagnostics and LN-12 jobs (not launched here) named by a not-run decision; the judges still open (no record)."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES + [HB27, GR27])
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-4", "a-5"):
        w.done(host)
    assert w.tool.release("A")["launches_released"] == 4
    w.not_run([x for x in w.tool.block_a_open(w.plan()) if not x.startswith("judge ")])
    assert w.tool.block_a_open(w.plan()) == ["judge harmbench", "judge granite"]       # gap 1: released, not done


def _rewrite(path: str, change) -> tuple[str, str]:
    """A record file rewritten with ``change(doc)`` applied (a new file content; returns its path and new SHA-256)."""
    doc = json.loads(Path(path).read_text())
    change(doc)
    write_json(Path(path), doc)
    return path, sha(path)


def _reindex(w, block: str = "A", drop=None) -> str:
    """judges/BLOCK/judge-files-index.json rewritten from the files on disk (Gate B's entry keys), leaving out the
    files whose name starts with ``drop``; returns the new index SHA-256."""
    index = w.root / "judges" / block / "judge-files-index.json"
    doc = json.loads(index.read_text())
    doc["files"] = [dict(e, sha256=sha(index.parent / e["file"])) for e in doc["files"]
                    if not (drop and e["file"].startswith(drop))]
    write_json(index, doc)
    return sha(index)


def test_a_released_judge_launch_is_done_only_while_a_valid_judge_completion_record_names_it(w, capsys):
    """R2 both ways: released judge launches stay open; record-judges refuses a wrong hash, a record with a count or
    any key outside the schema, a failed launch (exit 6), an incomplete one, a Granite whose gate did not pass, a bad
    tag, another block, a future time, a launch result that differs from the record or does not exist, an index
    whose SHA-256 is not the record's; it accepts the good record (by the CLI), once; both judges are then done and
    block A complete. At every later use the record file, the index and each judge file are re-hashed: a change of
    any refuses the completion check, and the status line says INVALID. No printed line or kit record holds a count."""
    _judged_block_a(w)
    path, digest = w.file_judges()
    record = json.loads(Path(path).read_text())
    hb, gr = record["judges"]["harmbench"], record["judges"]["granite"]
    assert hb["judged"] == 27 * 800 and gr["judged"] == 27 * 200 and set(gr) - set(hb) == {"known_answer_passed"}
    with pytest.raises(SystemExit, match="differs from the one given"):
        w.tool.record_judges("A", path, "0" * 64)
    bad = [(lambda d: d["judges"]["harmbench"].update(harm=JUDGE_SENTINEL), "must hold exactly"),
           (lambda d: d.update(yes=JUDGE_SENTINEL), "must hold exactly"),
           (lambda d: d["judges"]["harmbench"].update(exit=6), "exit 0 only"),
           (lambda d: d["judges"]["harmbench"].update(complete=False), "complete true"),
           (lambda d: d["judges"]["granite"].update(known_answer_passed=False), "known-answer gate must have passed"),
           (lambda d: d["judges"]["granite"].pop("known_answer_passed"), "must hold exactly"),
           (lambda d: d["judges"]["harmbench"].update(tag="S1A_HB"), "launch tag"),
           (lambda d: d["judges"]["granite"].update(tag=d["judges"]["harmbench"]["tag"]), "its own launch tag"),
           (lambda d: d.update(block="B"), "its block is not A"),
           (lambda d: d.update(utc="2099-01-01T00:00:00Z"), "in the future"),
           (lambda d: d["judges"]["harmbench"].update(judged=27 * 800 - 1), r"differs from the record \(judged\)"),
           (lambda d: d["judges"]["harmbench"].update(result_sha256="a" * 64), "missing or its SHA-256 is not"),
           (lambda d: d["judges"]["granite"].update(tag="s1a-granite-9"), "missing or its SHA-256 is not"),
           (lambda d: d.update(index_sha256="b" * 64), "not the judge-completion record's index_sha256")]
    original = Path(path).read_text()
    for change, match in bad:
        Path(path).write_text(original)
        with pytest.raises(SystemExit, match=match):
            w.tool.record_judges("A", *_rewrite(path, change))
    Path(path).write_text(original)
    run_record = w.repo / "tmp" / "judge-pod" / hb["tag"] / "fetched" / "out" / "run-record.json"
    keep = run_record.read_bytes()
    run_record.write_bytes(keep + b" ")                                  # the fetched run record changed
    with pytest.raises(SystemExit, match="fetched/out/run-record.json is missing or not run_record_sha256"):
        w.tool.record_judges("A", path, digest)
    run_record.write_bytes(keep)
    assert w.plan()["records"].get("judges") is None and w.tool.block_a_open(w.plan())[-1] == "judge granite"
    capsys.readouterr()
    assert w.tool.main(["record-judges", "A", path, "--sha256", digest]) == 0
    printed = capsys.readouterr().out
    out = json.loads(printed)
    assert out["tags"] == {"granite": "s1a-granite-1", "harmbench": "s1a-harmbench-1"} and out["units"] == 27 and \
        out["files"] == 54 and out["other_files"] == 0 and out["open"] == [] and out["sha256"] == digest
    assert w.tool.block_complete(w.plan(), "A") is True
    with pytest.raises(SystemExit, match="already has a judge-completion record"):
        w.tool.record_judges("A", path, digest)
    assert w.seal.main(["status"]) == 0
    printed += capsys.readouterr().out
    assert f"judges A: record {digest[:16]}, granite s1a-granite-1 exit 0 judged 5400 known-answer gate passed, " \
           f"harmbench s1a-harmbench-1 exit 0 judged 21600; index " in printed and \
           "valid: 27 required units, 54 indexed files" in printed
    for text in (printed, (w.root / "plan.json").read_text(), (w.root / "operator-actions.jsonl").read_text()):
        assert not re.search(rf"(?<![0-9A-Za-z]){JUDGE_SENTINEL}(?![0-9A-Za-z])", text)
    folder = w.root / "judges" / "A"
    one = sorted(folder.glob("granite--*.json"))[0]
    for target, match in ((Path(path), "judge-completion record is missing or differs"),
                          (folder / "judge-files-index.json", "not the judge-completion record's index_sha256"),
                          (one, "differs from its indexed SHA-256")):
        keep = target.read_bytes()
        target.write_bytes(keep + b" ")
        with pytest.raises(SystemExit, match=match):
            w.tool.block_a_open(w.plan())
        w.seal.main(["status"])
        assert "; INVALID: " in capsys.readouterr().out
        target.write_bytes(keep)
    assert w.tool.block_a_open(w.plan()) == []


def test_the_judge_files_check_wants_one_file_per_judge_for_each_of_the_27_units(w):
    """R3 both ways (plan_tool.judge_files_check, which the record and the seal use): the required set by hand is the
    20 COMPLETE.json SHA-256 of block A's arm runs in plan.json plus the 7 pins; an index without one unit's Granite
    file, an unindexed judge-named file, an index entry named for another unit, a second file of one (judge, unit), a
    missing listed file and an index that is not Gate B's each refuse; a non-judge file at the top (.DS_Store) and a
    pods/ subfolder are allowed; a file of a unit outside the set is counted, not refused."""
    _judged_block_a(w)
    plan = w.plan()
    want = w.judge_units()
    required = w.tool.judge_required_units(plan, "A")
    assert sorted(required) == sorted(want) and len(want) == len(set(want)) == 27
    assert [required[p["complete_sha256"]] for p in w.rules.REJUDGED_PINS["A"]][-1] == "re-judged theta0 (untuned, Gate A)"
    w.file_judges()
    folder = w.root / "judges" / "A"
    both = {"harmbench", "granite"}
    assert w.tool.judge_files_check(plan, "A", both)["units"] == 27
    write_json(folder / ".DS_Store", {"finder": 1})
    write_json(folder / "pods" / "t" / "harmbench--x--y--0123456789ab.json", {"subfolder": True})
    assert w.tool.judge_files_check(plan, "A", both)["files"] == 54
    theta0 = want[-1][:12]
    gone = next(folder.glob(f"granite--*--{theta0}.json"))
    index_keep = (folder / "judge-files-index.json").read_bytes()
    keep = gone.read_bytes()
    gone.unlink()
    with pytest.raises(SystemExit, match="is missing or differs from its indexed SHA-256"):
        w.tool.judge_files_check(plan, "A", both)
    _reindex(w, drop=gone.name)
    with pytest.raises(SystemExit, match=r"1 required unit\(s\) have no granite judge file .*re-judged theta0"):
        w.tool.judge_files_check(plan, "A", both)
    assert w.tool.judge_files_check(plan, "A", {"harmbench"})["files"] == 53     # HarmBench alone still complete
    gone.write_bytes(keep)
    with pytest.raises(SystemExit, match="1 judge-named file.* not in its index"):
        w.tool.judge_files_check(plan, "A", both)
    (folder / "judge-files-index.json").write_bytes(index_keep)
    other = write_json(folder / f"harmbench--h--extra--{'c' * 12}.json", {"n": 1})
    with pytest.raises(SystemExit, match="not in its index"):
        w.tool.judge_files_check(plan, "A", both)
    index = folder / "judge-files-index.json"
    doc = json.loads(index.read_text())
    doc["files"].append({**doc["files"][0], "file": other.name, "sha256": sha(other), "complete_sha256": "c" * 64,
                         "judge": "cais/HarmBench-Mistral-7b-val-cls"})
    write_json(index, doc)
    assert w.tool.judge_files_check(plan, "A", both)["other_files"] == 1          # a unit outside the set: counted
    for change, match in ((lambda d: d["files"][0].update(complete_sha256="d" * 64), "not a judge file named for"),
                          (lambda d: d["files"].append(dict(d["files"][1])), "twice"),
                          (lambda d: d["files"][0].update(extra=1), "exactly Gate B's index keys"),
                          (lambda d: d.update(kind="something else"), "not Gate B's judge files index"),
                          (lambda d: d["files"].append({**d["files"][1], "file": d["files"][1]["file"].replace(
                              "--unit", "--unitb")}), "missing or differs")):
        doc2 = json.loads(json.dumps(doc))
        change(doc2)
        write_json(index, doc2)
        with pytest.raises(SystemExit, match=match):
            w.tool.judge_files_check(plan, "A", both)
    write_json(index, doc)
    p = sorted(folder.glob("harmbench--host1--*.json"))[0]
    twin = write_json(folder / p.name.replace("host1--unit1", "hostx--unitx"), json.loads(p.read_text()))
    doc3 = json.loads(json.dumps(doc))
    doc3["files"].append({**next(e for e in doc["files"] if e["file"] == p.name), "file": twin.name, "sha256": sha(twin)})
    write_json(index, doc3)
    with pytest.raises(SystemExit, match="two harmbench files for the unit"):
        w.tool.judge_files_check(plan, "A", both)


def test_a_failed_granite_is_recorded_after_block_as_old_seal_and_record_judges_changes_no_seal(w):
    """R2 for a block sealed before round 30 (block A, by the old seal.py, its judges released and filed): after the
    seal a not-run decision may name only a judge launch, and only one without a record; record-judges A (HarmBench
    only, Granite failed) adds the record and changes no seal; it refuses while the index is not the one the seal
    hashed; Granite's not-run decision then completes block A. A recorded judge cannot be named not run."""
    _judged_block_a(w)
    path, digest = w.file_judges(judges=("harmbench",))
    seal = w.old_seal("A")
    seal_bytes = (w.root / "seals" / "block-A.json").read_bytes()
    with pytest.raises(SystemExit, match="block A is sealed: a not-run decision is recorded before its seal"):
        w.tool.record_block_a_not_run(*_decision(w, ["judge granite", "c0 R 1101"]))
    index = w.root / "judges" / "A" / "judge-files-index.json"
    keep = index.read_bytes()
    doc = json.loads(keep)
    doc["complete_allowlist"] = ["e" * 64]                                 # another index than the sealed one
    write_json(index, doc)
    with pytest.raises(SystemExit, match="seal does not hold judges/A/judge-files-index.json with the record's"):
        w.tool.record_judges("A", *_rewrite(path, lambda d: d.update(index_sha256=sha(index))))
    index.write_bytes(keep)
    path, digest = _rewrite(path, lambda d: d.update(index_sha256=sha(index)))
    out = w.tool.record_judges("A", path, digest)
    assert out["judges"] == ["harmbench"] and out["open"] == ["judge granite"]
    assert w.plan()["seals"]["A"] == seal and (w.root / "seals" / "block-A.json").read_bytes() == seal_bytes
    with pytest.raises(SystemExit, match="'judge harmbench' has a completion record"):
        w.tool.record_block_a_not_run(*_decision(w, ["judge harmbench"]))
    w.tool.record_block_a_not_run(*_decision(w, ["judge granite"], reason="lead: Granite's gate failed (exit 8)"))
    assert w.tool.block_a_open(w.plan()) == [] and w.tool.block_complete(w.plan(), "A") is True
    assert w.tool.judges_needed(w.plan(), "A") == ["harmbench"]
    assert w.plan()["seals"]["A"] == seal


def test_record_judges_refuses_a_judge_without_a_released_launch_or_named_not_run(w):
    """R2: a record names only a released judge launch of the block that no not-run decision names."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES + [HB27, GR27])
    for host in ("a-1", "a-2", "a-3"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-4", "a-5"):
        w.done(host)
    path, digest = w.file_judges()
    with pytest.raises(SystemExit, match="block A has no released granite judge launch"):
        w.tool.record_judges("A", path, digest)                          # launches 2 and 3 are not released yet
    w.tool.release("A")
    w.not_run(["judge granite"])                                         # released, no record: a not-run decision
    with pytest.raises(SystemExit, match="'judge granite' is named by a recorded not-run decision"):
        w.tool.record_judges("A", path, digest)
    with pytest.raises(SystemExit, match="block B is not planned"):
        w.tool.record_judges("B", *_rewrite(path, lambda d: d.update(block="B")))


def test_the_new_seal_needs_the_judge_record_first_and_lists_it(w):
    """R3 in seal.py and the lead's order (record-judges A, then seal.py block A): without the record block A is not
    complete and does not seal; with it the seal holds every judge file, the index and the record's SHA-256."""
    _judged_block_a(w)
    path, digest = w.file_judges()
    with pytest.raises(SystemExit, match="block A is not complete"):
        w.seal.seal_block("A")
    w.tool.record_judges("A", path, digest)
    out = w.seal.seal_block("A")
    record = json.loads((w.root / "seals" / "block-A.json").read_text())
    assert record["judge_record"] == {"record_sha256": digest, "index_sha256": sha(w.root / "judges/A/judge-files-index.json"),
                                      "judges": ["granite", "harmbench"], "units": 27, "files": 54, "other_files": 0}
    assert out["files"] == 65 + 55 and record["moved"] == []


def test_the_seal_checks_the_judge_record_itself(w, monkeypatch):
    """R3: seal.py refuses on its own when the record does not name a needed judge (block_complete bypassed here, so
    the seal's own check is what refuses)."""
    _judged_block_a(w)
    w.tool.record_judges("A", *w.file_judges())
    monkeypatch.setattr(w.tool, "judges_needed", lambda plan, block: ["harmbench", "granite", "other"])
    with pytest.raises(SystemExit, match="no valid judge-completion record names harmbench, granite, other"):
        w.seal.seal_block("A")
    monkeypatch.setattr(w.tool, "judge_record_checked", lambda plan, block: None)
    monkeypatch.setattr(w.tool, "block_complete", lambda plan, block: True)
    with pytest.raises(SystemExit, match="no valid judge-completion record names"):
        w.seal.seal_block("A")
    assert not (w.root / "seals").exists()


def test_block_as_seven_rejudged_pins_are_the_reuse_spec_sources_and_the_untuned_unit(w):
    """Gap 5: the 7 pins by hand (runbook §2b, M: shasum -a 256 of each COMPLETE.json on disk, 27 Oct) and, when this
    repository holds them, equal to reuse_spec.json jobs[0..5].source and the untuned unit of the limits settings
    (paths under tmp/); they are the plan's REJUDGED_UNITS (6 reused a0/R + theta0)."""
    pins = w.rules.REJUDGED_PINS["A"]
    assert [p["complete_sha256"][:16] for p in pins] == [
        "8f0fa83a42ccc5ed", "857f78bc0f49cc8a", "7be58eaa9c5be7b8", "391d067ca6569a04", "1cef324df66f0b46",
        "d34e33f2e3b90b56", "b5083ce9d9f26efe"]
    assert [(p["arm"][:12], p["seed"], p["target"]) for p in pins] == [
        ("a0", 1101, "e1"), ("a0", 1102, "e1"), ("a0", 1103, "e1"), ("edit-f7d7eb8", 1101, "e1"),
        ("edit-913b736", 1102, "e1"), ("edit-cd8d332", 1103, "e1"), ("a0", 1101, "init")]
    assert len(w.tool.REJUDGED_UNITS) == len(pins) == 7 and w.rules.REJUDGED_PINS.get("B", ()) == ()
    repo = KIT.parents[1]
    spec = repo / ".ai/inputs/stage1-post-w1-20261023/block-a/reuse/reuse_spec.json"
    limits = repo / "scripts/stage1/settings/limits_overrefusal_checks.json"
    if not (spec.is_file() and limits.is_file()):
        pytest.skip("reuse_spec.json or the limits settings are not in this repository")
    sources = [j["source"] for j in json.loads(spec.read_text())["jobs"][:6]]
    untuned = json.loads(limits.read_text())["units"]["untuned"]
    assert [{"path": "tmp/" + s["path"], "complete_sha256": s["complete_sha256"], "job_sha256": s["job_sha256"]}
            for s in sources] + [{"path": "tmp/" + untuned["path"], "complete_sha256": untuned["complete_sha256"],
                                  "job_sha256": untuned["job_sha256"]}] == \
        [{k: p[k] for k in ("path", "complete_sha256", "job_sha256")} for p in pins]


def test_the_judge_constants_are_gate_bs(w):
    """The kit's copies of Gate B's judge-file names, index and tag rule equal Gate B's (scripts/gate_b_mac_judges,
    read as code, unchanged)."""
    gb = KIT.parents[1] / "scripts" / "gate_b_mac_judges"
    text = (gb / "write_files.py").read_text()
    assert f'FILE_NAME = re.compile(r"{w.rules.JUDGE_FILE_PATTERN}")' in text
    assert f'INDEX = "{w.rules.JUDGE_INDEX}"' in text and f'INDEX_KIND = "{w.rules.JUDGE_INDEX_KIND}"' in text
    assert f"INDEX_VERSION = {w.rules.JUDGE_INDEX_VERSION}" in text
    keys = re.search(r"ENTRY_KEYS = frozenset\(\{(.*?)\}\)", text, re.S).group(1)
    assert set(re.findall(r'"([a-z_0-9]+)"', keys)) == set(w.rules.JUDGE_INDEX_ENTRY_KEYS)
    common = (gb / "common.py").read_text()
    assert f'"name": "{w.rules.JUDGE_NAMES["harmbench"]}"' in common
    assert f'GRANITE = {{"name": "{w.rules.JUDGE_NAMES["granite"]}"' in common
    assert f'TAG_RE = re.compile(r"{w.rules.JUDGE_TAG_PATTERN}")' in (gb / "pod" / "podhost.py").read_text()


def test_block_bs_required_units_hold_every_b10_unit_that_record_done_keeps(w):
    """R3 for block B (no pinned re-judged unit): the arm runs and each B10 unit of a complete ref_eval or safe_lora
    job (JOB-DONE.json's units list, kept by record-done); never a regeneration, a crashed job or a job recorded not
    pulled; a complete B10 job without its units list refuses. record-done keeps each listed unit after checking its
    COMPLETE.json, and refuses a unit whose COMPLETE.json differs, a path outside the run folder or a unit twice."""
    h = hashlib.sha256
    x, y1, y2, z = (h(s.encode()).hexdigest() for s in "x y1 y2 z".split())
    plan = {"hosts": {"b-1": {"block": "B", "jobs": [
        {"kind": "arm", "arm": "A1", "seed": 1105, "status": "complete", "complete_sha256": x},
        {"kind": "safe_lora", "arm": "a0", "seed": 1105, "status": "complete", "complete_sha256": y1,
         "units": [{"unit": "job-1/eval-default", "complete_sha256": y1},
                   {"unit": "job-1/eval-conditional", "complete_sha256": y2}]},
        {"kind": "regenerate", "arm": "a0", "seed": 1105, "status": "complete", "complete_sha256": z},
        {"kind": "a0_arm", "arm": "a0", "seed": 1106, "status": "crashed"},
        {"kind": "arm", "arm": "H1", "seed": 1105, "status": "complete", "complete_sha256": z, "pulled": False}]},
        "a-3": {"block": "A", "jobs": [{"kind": "arm", "arm": "A1", "seed": 1102, "status": "complete",
                                        "complete_sha256": "f" * 64}]}}}
    assert set(w.tool.judge_required_units(plan, "B")) == {x, y1, y2}
    del plan["hosts"]["b-1"]["jobs"][1]["units"]
    with pytest.raises(SystemExit, match="holds no list of its B10 units"):
        w.tool.judge_required_units(plan, "B")
    w.s10()
    w.gateb()
    w.sealed()
    _finish_block_a(w)
    w.seal.seal_block("A")
    w.init("certify", [{"hosts": [[{"kind": "b10_certify", "arm": "a0", "seed": 1101,
                                    "points": ["certify", "scale:0"]}]]}])
    tree = w.root / "retrieved" / "cfy-1" / "tree"
    done_file = tree / "JOB-DONE.json"
    real_record_done = w.tool.record_done
    w.mp.setattr(w.tool, "record_done", lambda host: None)               # write JOB-DONE.json only
    w.done("cfy-1")
    w.mp.setattr(w.tool, "record_done", real_record_done)
    good = json.loads(done_file.read_text())
    units = good["jobs"][0]["units"]
    assert [u["unit"] for u in units] == ["units/job-0", "units/job-0-p1"]
    for change, match in ((lambda u: u[1].update(complete_sha256="a" * 64), "missing from the pulled tree or its"),
                          (lambda u: u[1].update(unit="../outside"), "without a plain path"),
                          (lambda u: u.append(dict(u[0])), "names one unit twice"),
                          (lambda u: u.clear(), "empty or not a list")):
        doc = json.loads(json.dumps(good))
        change(doc["jobs"][0]["units"])
        write_json(done_file, doc)
        with pytest.raises(SystemExit, match=match):
            w.tool.record_done("cfy-1")
    write_json(done_file, good)
    w.tool.record_done("cfy-1")
    assert w.plan()["hosts"]["cfy-1"]["jobs"][0]["units"] == [{"unit": u["unit"], "complete_sha256": u["complete_sha256"]}
                                                              for u in units]


def _moved_block_a(w) -> None:
    """Block A where a-1 (deal pods 0) failed before its job and was requeued (moved, never done, never pulled), as
    a-5, a-6 and a-7 were on 25 Oct; its jobs ran on a-6; both judges released and recorded."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES + [HB27, GR27])
    _launch(w, "a-1")
    _log(w, "a-1", "pre-job-failed", "pre-job-stop")
    for other in ("a-2", "a-3"):
        _launch(w, other)
    assert w.tool.requeue("a-1")["to"] == "a-6"
    for host in ("a-2", "a-3", "a-6"):
        w.done(host)
    w.tool.release("A")
    for host in ("a-4", "a-5"):
        w.done(host)
    w.tool.release("A")
    w.not_run([x for x in w.tool.block_a_open(w.plan()) if not x.startswith("judge ")])
    w.tool.record_judges("A", *w.file_judges())


def test_the_seal_skips_a_moved_never_pulled_host_and_lists_it_and_still_refuses_an_unmoved_undone_one(w):
    """R6 (D3) both ways: a-1 is moved (requeue -> a-6), not done and has no pulled tree; block_complete skips it, and
    now so does the seal, listing it as moved with its target. A host that is not done and not moved still refuses
    ('record-done first'). The lead's order, record-judges A then seal.py block A, works over the 27 units."""
    _moved_block_a(w)
    plan = w.plan()
    assert not plan["hosts"]["a-1"].get("done") and not (w.root / "retrieved" / "a-1").exists()
    assert w.tool.moved_hosts(plan) == {"a-1": ["a-6"]} and w.tool.block_complete(plan, "A") is True
    plan["hosts"]["a-2"]["done"] = False                                 # not moved, not done (hand-edited)
    w.mac.save_plan(plan)
    with pytest.raises(SystemExit, match="a-2: record-done first"):
        w.seal.seal_block("A")
    plan["hosts"]["a-2"]["done"] = True
    w.mac.save_plan(plan)
    out = w.seal.seal_block("A")
    record = json.loads((w.root / "seals" / "block-A.json").read_text())
    assert record["moved"] == [{"host": "a-1", "to": ["a-6"], "pulled_tree": False}]
    assert "a-1" in record["hosts"] and not any(f["host"] == "a-1" for f in record["files"])
    assert record["judge_record"]["units"] == 27 and out["files"] == 5 * 13 + 55


def test_the_backup_does_not_require_a_moved_never_pulled_hosts_tree_or_finisher_record(w):
    """R6 for backup_records_stage1.py (the same defect): a-1 (moved, not done, never pulled) is listed under "moved"
    and needs no retrieved/a-1/tree and no finished.json; an unmoved host's missing tree and finished.json are still
    reported missing."""
    _moved_block_a(w)
    w.seal.seal_block("A")
    spec = importlib.util.spec_from_file_location("s1_backup_r6", w.root / "backup_records_stage1.py")
    backup = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(backup)
    hosts = sorted(n for n, h in w.plan()["hosts"].items() if h["block"] == "A")
    sel = backup.select(w.plan(), hosts, 1 << 30)
    assert sel["moved"] == {"a-1": ["a-6"]}
    assert "retrieved/a-1/tree" not in sel["missing"] and "hosts/a-1/finished.json" not in sel["missing"]
    assert "hosts/a-2/finished.json" in sel["missing"]                   # the World writes no finisher record
    shutil.rmtree(w.root / "retrieved" / "a-2" / "tree")
    assert "retrieved/a-2/tree" in backup.select(w.plan(), hosts, 1 << 30)["missing"]


def test_status_ends_a_pods_time_at_its_first_confirmed_stop_or_its_finisher_record(w, capsys):
    """R7 (D10) both ways, by hand: a-1 was created 17:08:48 and its stop confirmed 17:12:48 (no finished.json): 4 min,
    0.07 h, $0.12; a-2 has finished.json 2 h after creation and a later confirmed stop: 2.00 h; an unconfirmed stop
    and a confirmed stop logged before the pod's creation (an earlier attempt) do not end a-3's time, which runs
    until now. Total of a-1 and a-2: (4/60 + 2) x $1.79 = $3.70."""
    w.s10()
    w.gateb()
    w.sealed()
    w.init("A", A_LAUNCHES)
    def pod(host, created):
        write_json(w.root / "hosts" / host / "pod.json", {"created_utc": created, "costPerHr": 1.79, "id": host})
    def stops(host, *lines):
        (w.root / "hosts" / host / "stops.jsonl").write_text("".join(json.dumps(x) + "\n" for x in lines) + "not json\n")
    pod("a-1", "2026-10-25T17:08:48+00:00")
    stops("a-1", {"utc": "2026-10-25T17:10:00+00:00", "desiredStatus": "RUNNING", "confirmed": False},
          {"utc": "2026-10-25T17:12:48+00:00", "desiredStatus": "EXITED", "confirmed": True},
          {"utc": "2026-10-25T18:00:00+00:00", "desiredStatus": "EXITED", "confirmed": True})
    pod("a-2", "2026-10-25T10:00:00+00:00")
    write_json(w.root / "hosts" / "a-2" / "finished.json", {"utc": "2026-10-25T12:00:00+00:00", "status": "stopped"})
    stops("a-2", {"utc": "2026-10-25T13:00:00Z", "desiredStatus": "EXITED", "confirmed": True})
    capsys.readouterr()
    assert w.seal.main(["status"]) == 0
    rows = capsys.readouterr().out.splitlines()
    hours = {r.split()[0]: float(re.search(r"cap\s+[\d.]+ h\s+([\d.]+) h", r).group(1)) for r in rows if r.startswith("a-")}
    assert hours["a-1"] == 0.07 and hours["a-2"] == 2.0 and hours["a-3"] == 0.0
    assert next(r for r in rows if r.startswith("a-1")).endswith("stopped (confirmed)")
    assert rows[-1] == "estimated pod cost so far (this stage-1 kit): $3.70"
    pod("a-3", "2026-10-25T17:08:48+00:00")
    stops("a-3", {"utc": "2026-10-25T17:12:48+00:00", "desiredStatus": "RUNNING", "confirmed": False},
          {"utc": "2026-10-24T09:00:00+00:00", "desiredStatus": "EXITED", "confirmed": True})
    w.seal.main(["status"])
    rows = capsys.readouterr().out.splitlines()
    running = float(re.search(r"cap\s+[\d.]+ h\s+([\d.]+) h", next(r for r in rows if r.startswith("a-3"))).group(1))
    assert running > 40.0                                                # until now (27 Oct or later)


# ===== Kit round 32 (29 Oct 2026; addendum §34 points 5-7; block B's pre-flight G4, G6, G8, G11, G13) ===============
# K1 block B's second reference phase; K2 a not-run decision for any block but A; K3 a failed B10 certification;
# K4 block B's group on one funding record; K5 a block's judged units from plan.json. Hand values in each test.

CERTIFY_JOBS = [{"hosts": [[{"kind": "b10_certify", "arm": "a0", "seed": 1101, "points": ["certify"]}]]}]
REF1104 = {"kind": "ref_eval", "arm": "a0", "seed": 1104, "points": ["scale:0.75"]}
REF1105 = {"kind": "ref_eval", "arm": "a0", "seed": 1105, "points": ["scale:0.75"]}
SAFE1105 = {"kind": "safe_lora", "arm": "a0", "seed": 1105, "points": ["default"]}
SAFE1106 = {"kind": "safe_lora", "arm": "a0", "seed": 1106, "points": ["default"]}
PHASE2 = {"second_phase": [[REF1105, SAFE1105], [SAFE1106]]}
B_PHASED = B_DEAL + [{"hosts": [[REF1104]]}, PHASE2]     # 24 runs, the 1104 reference, the second phase: 28 units
B_HOSTS = ("b-1", "b-2", "b-3", "b-4", "b-5", "b-6")


def _certified(w, gate: str = "passed", passed: bool = True, rest=None, ready: bool = True) -> None:
    """Block A sealed (``ready``); the certify pod planned (block B's jobs ``rest`` counted, K4), run with B10's gate
    ``gate`` and recorded with ``passed``, the comparison file as its evidence."""
    if ready:
        _block_b_ready(w, passed=True)
    w.init("certify", CERTIFY_JOBS, group_jobs={"B": B_PHASED if rest is None else rest})
    w.done("cfy-1", gate=gate)
    rel = "job-0/evals/1101-certify.compare.json"
    ev = w.root / "retrieved" / "cfy-1" / "tree" / rel
    w.tool.record_simple("certification", *w.record({"kind": "stage1 b10 certification", "pass": passed,
                                                     "host": "cfy-1", "utc": "u", "recorded_by": "t",
                                                     "evidence": [{"path": rel, "sha256": sha(ev)}]}))


def _a0_runs(w, seeds=(1105, 1106)) -> dict:
    """seed -> the COMPLETE.json SHA-256 plan.json records for block B's own a0 run (read back by hand)."""
    plan = w.plan()
    return {s: next(j["complete_sha256"] for h in plan["hosts"].values() if h["block"] == "B" for j in h["jobs"]
                    if j["kind"] == "a0_arm" and j["seed"] == s and j.get("status") == "complete") for s in seeds}


def _a0_fp(w, seed: int) -> str:
    """The e1 fingerprint of block B's a0 run at SEED from its readable record (K6), read back by hand."""
    plan = w.plan()
    host, i = next((n, i) for n, h in plan["hosts"].items() if h["block"] == "B" for i, j in enumerate(h["jobs"])
                   if j["kind"] == "a0_arm" and j["seed"] == seed and j.get("status") == "complete")
    record = w.root / "retrieved" / host / "tree" / f"job-{i}" / "a0-adapter-fingerprint.json"
    return json.loads(record.read_text())["checkpoints"]["e1"]


def _repin(w, runs: dict, b11: dict | None = None, fps: dict | None = None) -> None:
    """The B10/B11 re-pin, synthetic, as the re-pin tool makes it from the K6 records: B10's and B11's settings at their
    S1_CODE paths in this checkout, B10 naming each a0 run (seed -> COMPLETE.json SHA-256) with the first 16 hex of its
    record's e1 fingerprint as its e1 prefix (``fps``: seed -> another e1), B11 accepting that e1 (``b11`` replaces
    B11's accepted map); stage1_rules.S1_CODE pinned to these bytes for this test."""
    r = w.rules
    fps = {s: _a0_fp(w, s) for s in runs} if fps is None else fps
    b10 = write_json(w.repo / r.B10_SETTINGS, {"reference_units": {
        str(s): {"complete_sha256": c, "fingerprint_prefixes": {"e1": fps[s][:16], "q": None}} for s, c in runs.items()}})
    accepted = b11 if b11 is not None else {str(s): {"fingerprint": fps[s]} for s in runs}
    settings = write_json(w.repo / r.B11_SETTINGS, {"adapter": {"accepted": accepted}})
    w.mp.setitem(r.S1_CODE, r.B10_SETTINGS, sha(b10))
    w.mp.setitem(r.S1_CODE, r.B11_SETTINGS, sha(settings))


def _repack(w, inputs: dict, files: dict | None = None) -> str:
    """Engine X re-packed, synthetic: sealed-files.json holds gate_a_complete:SEED at the given SHA-256 and B10's and
    B11's four files at their S1_CODE pins (``files`` overrides); the receipt names its SHA-256."""
    r = w.rules
    sealed = {rel: r.S1_CODE[rel] for rel in r.B10_B11_FILES}
    names = {}
    for s, digest in inputs.items():
        sealed[f"inputs/gate_a_complete-{s}/COMPLETE.json"] = digest
        names[f"gate_a_complete:{s}"] = f"inputs/gate_a_complete-{s}/COMPLETE.json"
    sealed.update(files or {})
    packed = w.root / "setup" / "packed-stage1-X"
    doc = write_json(packed / "sealed-files.json", {"files": sealed, "inputs": names})
    write_json(packed / "setup-receipt.json", {"engine_sha256": X, "sealed_files_sha256": sha(doc)})
    return sha(doc)


def _not_run(w, jobs, block: str = "B", reason: str = "lead: synthetic: B10 refuses this seed on the pod",
             **change) -> tuple[str, str]:
    body = {"kind": "stage1 not-run decision", "block": block, "jobs": jobs, "reason": reason,
            "utc": "2026-10-29T12:00:00Z", "recorded_by": "test", **change}
    return w.record({k: v for k, v in body.items() if v is not None})


def test_k1_the_second_phase_holds_the_references_on_block_bs_own_a0_runs_priced_by_hand(w):
    """K1 at init, both ways: a reference on a0 at 1105 outside a second phase, a second-phase reference at 1104 (block
    A's a0), a training job in the phase, the phase before the deal and a judge launch before the phase refuse, and a
    second phase outside block B; the good layout is planned with its launch marked, its two hosts pending, and their
    caps by hand (Branch 128: O500 1,024 s): b-8 = ref_eval (540 + 2,728.62 + 1,024 = 4,292.62 s) then safe_lora
    (540 + 88.02 + 600 + 3,752.62 = 4,980.64 s): 2,520 + 4,292.62 + 4,980.64 + 1,900 + 1,800 = 15,493.26 s -> 4.5 h;
    b-9 = safe_lora alone: 2,520 + 6,880.64 + 1,800 = 11,200.64 s -> 3.25 h. Their need terms are block B's."""
    _certified(w)
    g1105 = {"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1105}
    bad = [(B_DEAL + [{"hosts": [[REF1105]]}], 'plan it in a {"second_phase": [...]} launch'),
           (B_DEAL + [{"second_phase": [[REF1104]]}], "evaluates block B's own a0 runs only (seeds [1105, 1106, 1107])"),
           (B_DEAL + [{"second_phase": [[g1105]]}], "evaluation-only references only (ref_eval, safe_lora), not ref_train"),
           ([PHASE2] + B_DEAL, "comes after every deal launch"),
           (B_DEAL + [{"judge": {"judge": "harmbench", "arms": 27}}, PHASE2], "comes before every judge launch")]
    for launches, match in bad:
        with pytest.raises(SystemExit, match=re.escape(match)):
            w.init("B", launches, dry_run=True)
    with pytest.raises(SystemExit, match="a second reference phase belongs to block B"):
        w.tool.build_block(w.plan(), "certify", {"launches": [PHASE2]})
    out = w.init("B", B_PHASED)
    assert out["second_phase_launches"] == [2] and out["released"] == list(B_HOSTS)
    b = w.plan()["blocks"]["B"]
    assert b["launches"][1] == {"hosts": ["b-7"]} and b["launches"][2] == {"hosts": ["b-8", "b-9"], "second_phase": True}
    assert sorted(b["pending"]) == ["b-7", "b-8", "b-9"] and b["released"] == 1
    assert b["pending"]["b-8"]["cap_hours"] == quarter_up(2520 + 4292.62 + 4980.64 + 1900 + 1800) == 4.5
    assert b["pending"]["b-9"]["cap_hours"] == quarter_up(2520 + 4980.64 + 1900 + 1800) == 3.25
    assert b["need_launches"][2] == [
        {"cap_hours": 4.5, "spend_usd": pytest.approx((2520 + 4292.62 + 4980.64) / 3600 * 1.79)},
        {"cap_hours": 3.25, "spend_usd": pytest.approx((2520 + 4980.64) / 3600 * 1.79)}]
    assert "b-8:0 (ref_eval a0 1105)" in w.tool.block_open_jobs(w.plan(), "B")
    assert w.tool.block_complete(w.plan(), "B") is False


def test_k1_the_second_phase_is_released_only_after_the_a0_runs_the_b10_b11_repin_and_the_repack(w):
    """K1 (with K6) at release, both ways and in order, the guard off too: the a0 runs not recorded (the guard-off
    record releases launch 1 early, never the phase); B10's settings not at their S1_CODE pin; B10 naming another
    COMPLETE.json at 1105; B11 not accepting 1106's e1 from its K6 record; B10's e1 prefix not the record's; an X pack
    without gate_a_complete:1105, with 1106's at another SHA-256, or sealing B10's settings at their old pin; two
    complete a0 runs at one seed; no K6 record among the a0 job's outputs, a record naming another unit, a record
    whose bytes changed. Then the phase is released, bound to the re-pack, and block B completes and is sealed with
    its hosts."""
    _certified(w)
    w.init("B", B_PHASED)
    w.tool.record_simple("guard_off", *_guard_off(w))
    assert w.tool.release("B")["released"] == ["b-7"]                    # launch 1 early, under the user's decision
    with pytest.raises(SystemExit, match="waits: block B's a0 run at 1105 is not recorded complete"):
        w.tool.release("B")                                             # the guard off never releases it early
    for host in (*B_HOSTS, "b-7"):
        w.done(host)
    runs = _a0_runs(w)
    with pytest.raises(SystemExit, match="scripts/stage1_s1/settings/eval_adapter.json at its stage1_rules.S1_CODE pin"):
        w.tool.release("B")
    _repin(w, {1105: "0" * 64, 1106: runs[1106]}, fps={1105: _a0_fp(w, 1105), 1106: _a0_fp(w, 1106)})
    with pytest.raises(SystemExit, match="waits for the B10/B11 re-pin: .*names no reference unit for a0 1105"):
        w.tool.release("B")
    _repin(w, runs, b11={"1105": {"fingerprint": _a0_fp(w, 1105)}, "1106": {"fingerprint": _a0_fp(w, 1106)[:63] + "f"}})
    with pytest.raises(SystemExit, match="does not accept a0 1106's e1 fingerprint from its readable record"):
        w.tool.release("B")
    _repin(w, runs, fps={1105: "c" * 64, 1106: _a0_fp(w, 1106)})
    with pytest.raises(SystemExit, match="fingerprint prefixes for a0 1105 are not those of the run's readable"):
        w.tool.release("B")
    _repin(w, runs)
    _repack(w, {})
    with pytest.raises(SystemExit, match="waits for the re-pack: the packed stage1-X holds no gate_a_complete:1105"):
        w.tool.release("B")
    _repack(w, {1105: runs[1105], 1106: "0" * 64})
    with pytest.raises(SystemExit, match="holds no gate_a_complete:1106 at the a0 run's"):
        w.tool.release("B")
    _repack(w, runs, files={w.rules.B10_SETTINGS: "0" * 64})
    with pytest.raises(SystemExit, match="seals scripts/stage1_s1/settings/eval_adapter.json at another SHA-256"):
        w.tool.release("B")
    digest = _repack(w, runs)
    hosts = [w.plan()["blocks"]["B"]["pending"][n] for n in ("b-8", "b-9")]
    twice = w.plan()
    twice["hosts"]["b-7"]["jobs"].append({**twice["hosts"]["b-1"]["jobs"][3]})   # a second complete a0 at 1105
    with pytest.raises(SystemExit, match="two complete a0 runs at 1105"):
        w.tool.second_phase_gate(twice, "B", hosts)
    record = w.root / "retrieved" / "b-1" / "tree" / "job-3" / "a0-adapter-fingerprint.json"   # K6, a0 at 1105
    no_record = w.plan()
    no_record["hosts"]["b-1"]["jobs"][3]["outputs"] = {}
    with pytest.raises(SystemExit, match="lists no readable fingerprint record job-3/a0-adapter-fingerprint.json"):
        w.tool.second_phase_gate(no_record, "B", hosts)
    other = w.plan()
    other["hosts"]["b-1"]["jobs"][3]["unit"] = "units/another"
    with pytest.raises(SystemExit, match="is not this a0 run's fingerprint record"):
        w.tool.second_phase_gate(other, "B", hosts)
    kept = record.read_text()
    record.write_text(kept.replace('"version": 1', '"version": 2'))
    with pytest.raises(SystemExit, match="differs from its recorded SHA-256"):
        w.tool.second_phase_gate(w.plan(), "B", hosts)
    record.write_text(kept)
    assert w.tool.second_phase_gate(w.plan(), "B", hosts) == runs
    out = w.tool.release("B")
    assert out["released"] == ["b-8", "b-9"] and "released_early" not in out
    assert {w.plan()["hosts"][n]["sealed_files_sha256"] for n in ("b-8", "b-9")} == {digest}
    assert w.tool.block_complete(w.plan(), "B") is False
    w.done("b-8")
    w.done("b-9")
    assert w.tool.block_complete(w.plan(), "B") is True and w.tool.block_open_jobs(w.plan(), "B") == []
    sealed = w.seal.seal_block("B")
    record = json.loads((w.root / "seals" / "block-B.json").read_text())
    assert record["hosts"] == ["b-1", "b-2", "b-3", "b-4", "b-5", "b-6", "b-7", "b-8", "b-9"] and sealed["files"] > 0


def test_k1_b10s_and_b11s_pins_are_read_from_s1_code_only(w):
    """'Leave the pins as they are, but make the code read them from one place': B10's and B11's four files are
    S1_CODE keys, the round names them by those keys only, and no kit file but stage1_rules.py holds one of their
    pins (or its first 16 hex); the second phase reads the settings at S1_CODE's pin, so a changed pin refuses the
    same bytes."""
    r = w.rules
    assert set(r.B10_B11_FILES) <= set(r.S1_CODE) and {r.B10_SETTINGS, r.B11_SETTINGS} <= set(r.B10_B11_FILES)
    pins = [r.S1_CODE[rel] for rel in r.B10_B11_FILES]
    for p in sorted(KIT.rglob("*.py")):
        if p.name == "stage1_rules.py" or "tests" in p.relative_to(KIT).parts:
            continue
        text = p.read_text()
        assert not any(pin[:16] in text for pin in pins), p.name
    path = write_json(w.repo / r.B10_SETTINGS, {"reference_units": {}})
    w.mp.setitem(r.S1_CODE, r.B10_SETTINGS, sha(path))
    assert w.tool.pinned_s1_settings(r.B10_SETTINGS) == {"reference_units": {}}
    w.mp.setitem(r.S1_CODE, r.B10_SETTINGS, "1" * 64)
    with pytest.raises(SystemExit, match="missing or differs from its pin"):
        w.tool.pinned_s1_settings(r.B10_SETTINGS)


def test_k2_a_crashed_job_decided_not_run_completes_block_b_and_the_seal_and_status_list_it(w, capsys):
    """K2 both ways: before record-done the host's job refuses; then every malformed decision, block A (its route),
    an unplanned block, an unknown host, a job index out of range and a complete job refuse; a good decision (by the
    CLI) completes block B, the seal lists it ("b-1:3" and its SHA-256) and status prints it valid; it is named once;
    defer leaves it where it is; after the seal no decision; a changed file makes status INVALID and completeness
    refuse."""
    _block_b_ready(w, passed=True)
    w.init("B", B_DEAL)
    for host in B_HOSTS[1:]:
        w.done(host)
    with pytest.raises(SystemExit, match=r"b-1:3 \(a0_arm a0 1105\): b-1 is not recorded done"):
        w.tool.record_not_run(*_not_run(w, ["b-1:3"]))
    w.done("b-1", statuses={3: "crashed"})
    assert w.tool.block_complete(w.plan(), "B") is False
    assert w.tool.block_open_jobs(w.plan(), "B") == ["b-1:3 (a0_arm a0 1105)"]
    bad = [(dict(extra=1), "exactly"), (dict(kind="stage1 block-a not-run decision"), "its kind is not"),
           (dict(jobs=[]), "distinct"), (dict(jobs=["b-1:3", "b-1:3"]), "distinct"), (dict(jobs=["b-1-3"]), "HOST:INDEX"),
           (dict(jobs=["b-1:03"]), "HOST:INDEX"), (dict(reason=" "), "non-empty"), (dict(utc="2099-01-01T00:00:00Z"),
                                                                                    "in the future"),
           (dict(block="A"), "record-block-a-not-run"), (dict(block="C"), "block C is not planned"),
           (dict(jobs=["z-1:0"]), "z-1 is not a host of block B"), (dict(jobs=["b-1:9"]), "b-1 has no job 9"),
           (dict(jobs=["b-1:0"]), r"b-1:0 \(arm A1 1105\) is complete \(it ran\)")]
    for change, match in bad:
        with pytest.raises(SystemExit, match=match):
            w.tool.record_not_run(*_not_run(w, **{"jobs": ["b-1:3"], **change}))
    assert "not_run" not in w.plan()["records"]
    path, digest = _not_run(w, ["b-1:3"])
    capsys.readouterr()
    assert w.tool.main(["record-not-run", path, "--sha256", digest]) == 0
    out = json.loads(capsys.readouterr().out)
    assert out == {"recorded": "not_run", "block": "B", "sha256": digest, "jobs": ["b-1:3"], "open": [],
                   "complete": True}
    with pytest.raises(SystemExit, match="already named by a recorded not-run decision"):
        w.tool.record_not_run(*_not_run(w, ["b-1:3"], reason="again"))
    with pytest.raises(SystemExit, match="b-1: nothing to defer"):
        w.tool.defer("b-1")
    w.seal.seal_block("B")
    record = json.loads((w.root / "seals" / "block-B.json").read_text())
    assert record["not_run"] == [{"job": "b-1:3", "decision_sha256": digest}] and record["skipped"] == []
    with pytest.raises(SystemExit, match="block B is sealed"):
        w.tool.record_not_run(*_not_run(w, ["b-2:0"]))
    w.seal.main(["status"])
    rows = capsys.readouterr().out.splitlines()
    assert f"block B not run: 1 job(s) b-1:3 by decision {digest[:16]}; valid" in rows
    Path(path).write_text(Path(path).read_text().replace("synthetic", "changed"))
    w.seal.main(["status"])
    assert any(r.startswith("block B not run: 1 job(s) b-1:3") and "INVALID" in r
               for r in capsys.readouterr().out.splitlines())
    with pytest.raises(SystemExit, match="block B: a recorded not-run decision is missing or differs"):
        w.tool.block_complete(w.plan(), "B")


@pytest.mark.parametrize("paid", [False, True])
def test_k2_a_job_a_move_left_behind_keeps_block_b_open_until_a_decision_names_it(w, paid):
    """K2: before this round a crashed job that defer could not pay (contingency exhausted) left its host moved and
    block B complete without any record of it. Now it stays open ("b-1:3") until a decision names it (a moved host's
    job that was not taken along). When the contingency pays it, the move takes it to b-7: naming b-1:3 then refuses
    (name it where it moved), and b-7's planned job stays open until b-7 is done."""
    _block_b_ready(w, passed=True)
    w.init("B", B_DEAL)
    for host in B_HOSTS[1:]:
        w.done(host)
    w.done("b-1", statuses={3: "crashed"})
    if not paid:
        plan = w.plan()
        plan["contingency"]["B"]["remaining_usd"] = 0.0
        w.mac.save_plan(plan)
    out = w.tool.defer("b-1")
    if not paid:
        assert out == {"from": "b-1", "to": None, "jobs": 0, "not_rerun": 1}
        assert w.tool.block_open_jobs(w.plan(), "B") == ["b-1:3 (a0_arm a0 1105)"]
        assert w.tool.block_complete(w.plan(), "B") is False
        w.tool.record_not_run(*_not_run(w, ["b-1:3"], reason="lead: synthetic: the contingency could not pay it"))
        assert w.tool.block_complete(w.plan(), "B") is True
        return
    assert out["to"] == "b-7" and out["jobs"] == 1
    assert w.tool.block_open_jobs(w.plan(), "B") == ["b-7:0 (a0_arm a0 1105)"]
    with pytest.raises(SystemExit, match=r"b-1:3 \(a0_arm a0 1105\): a move took it to b-7; name it where it moved"):
        w.tool.record_not_run(*_not_run(w, ["b-1:3"]))
    with pytest.raises(SystemExit, match="b-7 is not recorded done"):
        w.tool.record_not_run(*_not_run(w, ["b-7:0"]))
    w.done("b-7")
    assert w.tool.block_complete(w.plan(), "B") is True


def test_k2_a_held_launch_decided_not_run_is_skipped_and_the_judges_release(w):
    """K2 with K1: the second phase will not run (say the re-pin never lands). A decision naming one of b-8's two
    jobs refuses (a pending host's pod runs every job it holds); one naming every job of b-8 and b-9 is recorded;
    release then skips launch 2 (recorded with the decision's SHA-256) and releases both judge launches, which wait
    for b-7 as before; with the judges decided not run (round 31) block B is complete and the seal lists the three
    jobs and the skipped launch."""
    _certified(w)
    w.init("B", B_PHASED + [{"judge": {"judge": "harmbench", "arms": 28}}, {"judge": {"judge": "granite", "arms": 28}}])
    for host in B_HOSTS:
        w.done(host)
    assert w.tool.release("B")["released"] == ["b-7"]
    with pytest.raises(SystemExit, match=r"b-8 is not released: .* job\(s\) \[1\] are not named"):
        w.tool.record_not_run(*_not_run(w, ["b-8:0", "b-9:0"]))
    path, digest = _not_run(w, ["b-8:0", "b-8:1", "b-9:0"], reason="lead: synthetic: the B10/B11 re-pin did not land")
    w.tool.record_not_run(path, digest)
    with pytest.raises(SystemExit, match="launch 1's hosts are not done"):
        w.tool.release("B")                                             # the guard is on: b-7 first
    w.done("b-7")
    out = w.tool.release("B")
    assert out["released"] == [] and out["launches_released"] == 5
    assert [(x["launch"], x["hosts"], x["decisions"]) for x in out["skipped"]] == [(2, ["b-8", "b-9"], [digest])]
    assert "b-8" not in w.plan()["hosts"] and w.tool.block_open_jobs(w.plan(), "B") == []
    assert w.tool.block_complete(w.plan(), "B") is False                 # the judge launches have no record
    w.tool.record_judge_not_run(*w.record({"kind": "stage1 judge not-run decision", "block": "B",
                                           "judges": ["harmbench", "granite"], "reason": "synthetic",
                                           "utc": "2026-10-29T12:00:00Z", "recorded_by": "test"}))
    assert w.tool.block_complete(w.plan(), "B") is True
    w.seal.seal_block("B")
    record = json.loads((w.root / "seals" / "block-B.json").read_text())
    assert [x["job"] for x in record["not_run"]] == ["b-8:0", "b-8:1", "b-9:0"]
    assert [(x["launch"], x["hosts"]) for x in record["skipped"]] == [(2, ["b-8", "b-9"])]
    assert "b-8" not in record["hosts"]


def test_k2_an_unreleased_launch_that_holds_only_decided_hosts_is_settled_without_a_release(w):
    """K2: block_complete reads a trailing held launch whose every job is decided as settled (release would skip it);
    a launch with one undecided pending job, or a judge launch after it, keeps the block open."""
    b = {"released": 1, "launches": [{"hosts": ["b-1"]}, {"hosts": ["b-2", "b-3"]}, {"judge": {"judge": "granite"}}],
         "pending": {"b-2": {"jobs": [{}, {}]}, "b-3": {"jobs": [{}]}}}
    decided = {("b-2", 0): "d", ("b-2", 1): "d", ("b-3", 0): "d"}
    view = w.tool.settled_view(b, decided)
    assert view["released"] == 2 and view["pending"] == {}
    assert w.tool.settled_view(b, {k: v for k, v in decided.items() if k != ("b-2", 1)})["released"] == 1
    assert w.tool.launch_decided(b, 1, decided) is True and w.tool.launch_decided(b, 2, decided) is False


def test_k3_a_failed_certification_is_recorded_pass_false_and_every_reference_then_refuses_to_plan(w):
    """K3 (G11) both ways: B10's failed gate, as the runner records it (complete, certification_gate failed, the
    certify unit only), is recorded done; a certification record with pass true then refuses and pass false is
    recorded; init-block B then refuses any evaluation-only reference (LS-08) and plans block B without them."""
    _block_b_ready(w, passed=True)
    w.init("certify", CERTIFY_JOBS, group_jobs={"B": B_DEAL + [{"hosts": [[REF1104]]}]})
    w.done("cfy-1", gate="failed")
    job = w.plan()["hosts"]["cfy-1"]["jobs"][0]
    assert (job["status"], job["certification_gate"], job["unit"]) == ("complete", "failed", "job-0/evals/1101-certify")
    assert [u["unit"] for u in job["units"]] == ["job-0/evals/1101-certify"]
    rel = "job-0/evals/1101-certify.compare.json"
    ev = [{"path": rel, "sha256": sha(w.root / "retrieved" / "cfy-1" / "tree" / rel)}]
    body = {"kind": "stage1 b10 certification", "host": "cfy-1", "utc": "u", "recorded_by": "t", "evidence": ev}
    with pytest.raises(SystemExit, match="B10 gate is recorded failed .* pass must be false"):
        w.tool.record_simple("certification", *w.record({**body, "pass": True}))
    w.tool.record_simple("certification", *w.record({**body, "pass": False}))
    assert w.plan()["records"]["certification"]["pass"] is False
    for refs in ([[REF1104]], [[{**SAFE1105, "seed": 1104}]]):
        with pytest.raises(SystemExit, match=re.escape("a failed B10 certification is recorded (pass false): every "
                                                       "evaluation-only reference stops (LS-08)")):
            w.init("B", B_DEAL + [{"hosts": refs}], dry_run=True)
    out = w.init("B", B_DEAL)
    assert out["released"] == list(B_HOSTS)


def test_k3_a_passed_gate_may_still_be_recorded_pass_false_and_no_certification_refuses_a_reference_at_init(w):
    """K3: the lead's reading may record pass false over a passed gate (the stricter reading governs); before any
    certification a reference refuses at init-block (not only at release), with its own message."""
    _block_b_ready(w, passed=True)
    with pytest.raises(SystemExit, match=re.escape("an evaluation-only reference refuses before a passing B10 "
                                                   "certification")):
        w.init("B", B_DEAL + [{"hosts": [[REF1104]]}], dry_run=True)
    _certified(w, gate="passed", passed=False, rest=B_DEAL, ready=False)
    with pytest.raises(SystemExit, match="every evaluation-only reference stops"):
        w.init("B", B_DEAL + [{"hosts": [[REF1104]]}], dry_run=True)


def test_k3_record_done_takes_b10s_gate_only_as_the_runner_writes_it(w):
    """K3: record-done refuses a complete b10_certify record without B10's gate or with another value, a failed gate
    with a second unit, a comparison file missing from the recorded outputs, and a gate on a job that is not a
    complete b10_certify; a failed and a passed gate are each recorded."""
    _block_b_ready(w, passed=True)
    w.init("certify", CERTIFY_JOBS)
    done_file = w.root / "retrieved" / "cfy-1" / "tree" / "JOB-DONE.json"
    real = w.tool.record_done
    w.mp.setattr(w.tool, "record_done", lambda host: None)                # write JOB-DONE.json only
    w.done("cfy-1", gate="failed")
    w.mp.setattr(w.tool, "record_done", real)
    good = json.loads(done_file.read_text())
    second = {"unit": "job-0/evals/1101-scale:0", "complete_sha256": "a" * 64, "verify_exit": 0}
    for change, match in ((lambda r: r.pop("certification_gate"), "complete without B10's gate"),
                          (lambda r: r.update(certification_gate="maybe"), "complete without B10's gate"),
                          (lambda r: r["units"].append(second), "missing from the pulled tree|certify unit only"),
                          (lambda r: r.update(outputs={}), "comparison file is not among its recorded outputs"),
                          (lambda r: r.update(status="crashed"), "only a complete b10_certify job does")):
        doc = json.loads(json.dumps(good))
        change(doc["jobs"][0])
        write_json(done_file, doc)
        with pytest.raises(SystemExit, match=match):
            w.tool.record_done("cfy-1")
    write_json(done_file, good)
    assert w.tool.record_done("cfy-1") == {"host": "cfy-1", "statuses": ["complete"]}
    assert w.plan()["hosts"]["cfy-1"]["jobs"][0]["certification_gate"] == "failed"


def test_k3_a_failed_gate_with_a_second_unit_on_disk_refuses(w):
    """K3: a failed gate whose units list names a second unit (present on disk) refuses: B10 stops after the gate."""
    _block_b_ready(w, passed=True)
    w.init("certify", [{"hosts": [[{"kind": "b10_certify", "arm": "a0", "seed": 1101,
                                    "points": ["certify", "scale:0"]}]]}])
    done_file = w.root / "retrieved" / "cfy-1" / "tree" / "JOB-DONE.json"
    real = w.tool.record_done
    w.mp.setattr(w.tool, "record_done", lambda host: None)
    w.done("cfy-1", gate="failed")
    w.mp.setattr(w.tool, "record_done", real)
    doc = json.loads(done_file.read_text())
    extra = write_json(w.root / "retrieved" / "cfy-1" / "tree" / "job-0" / "evals" / "1101-scale:0" / "COMPLETE.json",
                       {"point": "scale:0"})
    doc["jobs"][0]["units"].append({"unit": "job-0/evals/1101-scale:0", "complete_sha256": sha(extra), "verify_exit": 0})
    write_json(done_file, doc)
    with pytest.raises(SystemExit, match="a failed gate leaves the certify unit only"):
        w.tool.record_done("cfy-1")


def test_k4_certify_covers_block_bs_whole_group_by_hand_on_one_funding_record(w, capsys):
    """K4 (G8; addendum §20 point 1 for block B's group) both ways, by hand under Branch 128: certify's pod (b10_certify,
    certify only: 540 + 2,728.62 = 3,268.62 s measured; cap 2,520 + 3,268.62 + 1,900 + 1,800 = 9,488.62 s -> 2.75 h)
    and block B's six arm pods in one launch (7.0 h each). Terms: 6 + 1.85 x 2.75 = 11.09; then certify's spend
    (2,520 + 3,268.62) / 3,600 x 1.79 + 6 + 1.85 x 42 = 86.58 -> need 1.25 x 86.58 = 108.23 (certify alone: 13.86).
    Certify's first init refuses without block B's jobs file, with a part given twice, with itself or C; the CLI dry
    run prints the group's need; 108.22 refuses, 108.23 plans certify; block B then refuses another funding record
    and a jobs file whose need is above the first record, and plans on it with the counted file; --group-jobs after
    the first init refuses, and outside group B too."""
    _block_b_ready(w, passed=True)
    cfy, b = w.jobs(CERTIFY_JOBS), w.jobs(B_DEAL)
    s_cfy = (2520 + 540 + 0.93 * 2934) / 3600 * 1.79
    base = cents(max(6 + 1.85 * 2.75, s_cfy + 6 + 1.85 * 6 * 7.0))
    assert base == 86.58 and times_125(base) == 108.23 and times_125(cents(6 + 1.85 * 2.75)) == 13.86

    def init(jobs, funding=None, given=None, dry_run=False, block="certify"):
        return w.tool.init_block(argparse.Namespace(block=block, jobs=jobs, funding=funding, dry_run=dry_run,
                                                    group_jobs=given))
    with pytest.raises(SystemExit, match="first init of block B's group: .*give --group-jobs B=FILE"):
        init(cfy, dry_run=True)
    for given in ([f"B={b}", f"B={b}"], [f"certify={cfy}"], [f"C={b}"], [b]):
        with pytest.raises(SystemExit, match="give PART=FILE once for each later part"):
            init(cfy, given=given, dry_run=True)
    capsys.readouterr()
    assert w.tool.main(["init-block", "certify", "--jobs", cfy, "--group-jobs", f"B={b}", "--dry-run"]) == 0
    out = json.loads(capsys.readouterr().out)
    assert (out["need_usd"], out["base_need_usd"], out["dry_run"]) == (108.23, 86.58, True)
    assert out["group"] == {"planned": [], "this": "certify", "later": {"B": {"sha256": sha(Path(b)), "pods": 6}}}
    with pytest.raises(SystemExit, match="below the need"):
        init(cfy, w.funding("B", 108.22), [f"B={b}"])
    anchor = w.funding("B", 108.23)
    assert init(cfy, anchor, [f"B={b}"])["released"] == ["cfy-1"]
    assert w.plan()["blocks"]["certify"]["group_jobs"]["B"]["sha256"] == sha(Path(b))
    with pytest.raises(SystemExit, match="one funding record .*give the first init's record"):
        init(b, w.funding("B", 500.0), block="B")
    with pytest.raises(SystemExit, match="below the need"):
        init(w.jobs(B_DEAL + [{"hosts": [[{"kind": "ref_train", "arm": "G", "recipe": "G", "seed": s}]
                                         for s in range(1102, 1108)]}]), anchor, block="B")
    with pytest.raises(SystemExit, match="give PART=FILE once for each later part of block B's group .*none here"):
        init(b, anchor, [f"B={b}"], block="B")
    out = init(b, anchor, block="B")
    assert out["need_usd"] == 108.23 and out["group"]["counted_at_first_init"] == "the same jobs file"
    with pytest.raises(SystemExit, match="--group-jobs belongs to block B's group"):
        w.tool.group_jobs(w.plan(), "A", [f"B={b}"])


def test_k5_units_of_block_lists_exactly_block_bs_judged_units_from_plan_json(w, tmp_path, capsys):
    """K5 (G13) both ways: the judge wrapper's units-of-block lists, by hand, block B's judged units from plan.json:
    23 of the 24 runs (b-2's H1 at 1106 crashed), the two B10 units of the 1104 reference (two points) and recipe G's
    unit at 1102: 26 folders, one per line, by kind; the same COMPLETE.json SHA-256 set as plan_tool's
    judge_required_units; no block-A or certify unit (a --run-root sweep would take them). It refuses an OUT file that
    exists, a unit whose COMPLETE.json changed or is gone, and a block not planned (exit 2, nothing written)."""
    _certified(w, rest=B_DEAL + [{"hosts": [[{**REF1104, "points": ["scale:0.75", "scale:0.5"]}]]},
                                  {"hosts": [[{"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1102}]]}])
    w.init("B", B_DEAL + [{"hosts": [[{**REF1104, "points": ["scale:0.75", "scale:0.5"]}]]},
                          {"hosts": [[{"kind": "ref_train", "arm": "G", "recipe": "G", "seed": 1102}]]}])
    for host in B_HOSTS:
        w.done(host, statuses={1: "crashed"} if host == "b-2" else None)
    w.tool.release("B")
    w.done("b-7")
    w.tool.release("B")
    w.done("b-8")
    spec = importlib.util.spec_from_file_location("s1_units_wrapper_k5", KIT / "judge_units_stage1.py")
    wrapper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(wrapper)
    plan = w.plan()
    expected = [w.root / "retrieved" / host / "tree" / f"units/job-{i}" for host in B_HOSTS for i in range(4)
                if (host, i) != ("b-2", 1)]
    expected += [w.root / "retrieved" / "b-7" / "tree" / u for u in ("units/job-0", "units/job-0-p1")]
    expected += [w.root / "retrieved" / "b-8" / "tree" / "units/job-0"]
    out = tmp_path / "units_b.txt"
    capsys.readouterr()
    assert wrapper.main(["units-of-block", "B", "--out", str(out), "--plan", str(w.root / "plan.json")]) == 0
    printed = json.loads(capsys.readouterr().out)
    assert out.read_text().splitlines() == [str(p) for p in expected]
    assert printed == {"block": "B", "units": 26, "by_kind": {"arm": 20, "a0_arm": 3, "ref_eval": 2, "ref_train": 1},
                       "out": str(out), "sha256": sha(out)}
    found = wrapper.block_units(plan, "B", w.root, w.repo)
    assert {u["complete_sha256"] for u in found} == set(w.tool.judge_required_units(plan, "B"))
    assert not any("/retrieved/cfy-1/" in line or "/retrieved/a-" in line for line in out.read_text().splitlines())
    assert wrapper.main(["units-of-block", "B", "--out", str(out), "--plan", str(w.root / "plan.json")]) == 2
    assert "exists; give a new file" in capsys.readouterr().err
    unit = w.root / "retrieved" / "b-7" / "tree" / "units" / "job-0-p1" / "COMPLETE.json"
    unit.write_text(unit.read_text() + " ")
    other = tmp_path / "units_b2.txt"
    assert wrapper.main(["units-of-block", "B", "--out", str(other), "--plan", str(w.root / "plan.json")]) == 2
    assert "not the SHA-256 plan.json records" in capsys.readouterr().err and not other.exists()
    unit.unlink()
    assert wrapper.main(["units-of-block", "B", "--out", str(other), "--plan", str(w.root / "plan.json")]) == 2
    assert "1 unit(s) have no COMPLETE.json" in capsys.readouterr().err and not other.exists()
    assert wrapper.main(["units-of-block", "C", "--out", str(other), "--plan", str(w.root / "plan.json")]) == 2
    assert "block C is not planned" in capsys.readouterr().err
