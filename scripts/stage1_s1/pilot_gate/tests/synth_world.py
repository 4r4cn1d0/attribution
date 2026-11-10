"""Synthetic pilot worlds in the engine's real layout (tests only; no real data; every draw is seeded), built with
the input builder's synthetic kit writers (reading_input/tests/synth_kit.py: eval_folder, complete, jbytes, write).

``make(root, counts)`` writes, under ``root``:
- ``repo/``: Gate A's three a0 units at 1101-1103 (checkpoint e1) in the engine's unit layout, the frozen coherence
  bars file (copied from this repository by its pin) and a rules module ``rules.py`` that is the kit's
  stage1_rules.py with REJUDGED_PINS replaced by pins to these units, named "a0 1101 (Gate A)" and so on;
- ``kit/``: plan.json (record-done's job records: block P's host p-1 with three complete, pulled ``arm`` jobs of
  a0_plant at 1101-1103, each with an edit record; a block-A host with a complete job the reader must ignore), and
  retrieved/p-1/tree/round1/<seed>-edit-<edit SHA-256>-e1-a1 with eval/e1/{samples, guard_samples, guard,
  generations, query_loss}.jsonl and summary.json, job.json, and COMPLETE.json last with the SHA-256 of every other
  file.

``counts`` fixes each unit's Unsafe count per prompt: {(arm, seed): {prompt id: 0..3}} for the arms "a0_plant"
(or "a0_plant75" with ``arm``) and "a0"; a missing unit is drawn. Every field that is not U holds a sentinel string
(SENTINELS): the pilot units' edit name (where the engine writes it: COMPLETE.json trajectory.edit.name), their
job.json, plan.json's edit path and host record, every summary.json, every answer and judge text. A test shows
that no sentinel reaches the reader's streams or output.
"""

from __future__ import annotations

import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import synth_kit as sk

SEEDS = (1101, 1102, 1103)
HARM = list(sk.HARM)
SENTINELS = {"edit_name": "SENTINEL-EDIT-NAME-xq7v", "edit_path": "SENTINEL-EDIT-PATH-xq7v/edits/x.json",
             "job": "SENTINEL-JOB-NOTE-xq7v", "host": "SENTINEL-HOST-NOTE-xq7v", "summary": "SENTINEL-SUMMARY-xq7v",
             "identity": "SENTINEL-IDENTITY-xq7v", "text": sk.TEXT, "other_block": "SENTINEL-OTHER-BLOCK-xq7v"}


def edit_sha(arm: str) -> str:
    return sk.sha(f"edit {arm}".encode())


def cell_of(counts: dict) -> sk.Cell:
    """A synth_kit Cell whose sampled answers hold exactly ``counts`` Unsafe answers per prompt: the first k of the 3
    answers of a prompt are Unsafe. Among the other answers, every 7th prompt's last answer is Controversial and
    every 11th prompt's last answer is invalid (over the guard's limit), so U differs from B16's two G3 variants
    (a reader that took one of them would read other values). No capped and no failing answer."""
    samples = []
    invalid, controversial, unscored = {}, {}, {}
    for n, p in enumerate(HARM):
        invalid[p] = controversial[p] = unscored[p] = 0
        for k in range(3):
            if k < counts[p]:
                guard = {"valid": True, "safety": "Unsafe", "reason": None}
            elif k == 2 and n % 7 == 0:
                guard = {"valid": True, "safety": "Controversial", "reason": None}
                controversial[p] += 1
            elif k == 2 and n % 11 == 0:
                guard = {"valid": False, "safety": None, "reason": "guard input over limit; not scored"}
                invalid[p] += 1
                unscored[p] += 1
            else:
                guard = {"valid": True, "safety": "Safe", "reason": None}
            samples.append((p, k, "eos", 50, None, False, guard))
    return sk.Cell(dict(counts), invalid, controversial, unscored, 0, 0, {q: 1.0 for q in sk.QUERIES}, {}, {}, {},
                   samples)


def write_unit(folder: Path, counts: dict, engine_arm: str, seed: int, pilot: bool) -> dict:
    """One engine run-one unit; a pilot unit's COMPLETE.json carries the edit summary with the sentinel name."""
    job = {"kind": "run-one", "arm": engine_arm, "seed": seed, "target_checkpoint": "e1", "evaluate_bank": "dev",
           "split": "dev", "role": "development", "note": SENTINELS["job"]}
    job_sha = sk.write(folder / "job.json", sk.jbytes(job))
    summary = sk.eval_folder(folder, cell_of(counts), "e1")
    summary = {**summary, "note": SENTINELS["summary"]}
    sk.write(folder / "eval" / "e1" / "summary.json", sk.jbytes(summary))
    trajectory = {"arm": engine_arm, "seed": seed, "split": "dev", "role": "development"}
    if pilot:
        trajectory["edit"] = {"edit_sha256": engine_arm[len("edit-"):], "edit_kind": "add",
                              "name": SENTINELS["edit_name"], "removed": 37, "rewritten": 0, "added": 37}
    c = sk.complete(folder, {"kind": "run-one", "identity": {"note": SENTINELS["identity"]}, "job_sha256": job_sha,
                             "target_checkpoint": "e1", "trajectory": trajectory, "evaluation": summary})
    return {"complete": c, "job": job_sha}


@dataclass
class World:
    root: Path
    kit: Path
    repo: Path
    rules: Path
    arm: str
    block: str
    counts: dict = field(default_factory=dict)      # (arm, seed) -> {prompt id: count}
    units: dict = field(default_factory=dict)       # (arm, seed) -> {complete, job, rel, host}

    def args(self, out: Path, mode: str | None = None, block: str | None = None) -> list[str]:
        return ["--mode", mode or ("re-pilot" if self.arm == "a0_plant75" else "pilot"), "--kit", str(self.kit),
                "--repo", str(self.repo), "--rules", str(self.rules), "--block", block or self.block, "--out", str(out)]

    def plan(self) -> dict:
        return json.loads((self.kit / "plan.json").read_text())

    def save_plan(self, plan: dict) -> None:
        (self.kit / "plan.json").write_bytes(sk.jbytes(plan))

    def unit_folder(self, arm: str, seed: int) -> Path:
        u = self.units[(arm, seed)]
        if arm == "a0":
            return self.repo / u["rel"]
        return self.kit / "retrieved" / u["host"] / "tree" / u["rel"]

    def job(self, plan: dict, seed: int) -> dict:
        return plan["hosts"]["p-1"]["jobs"][SEEDS.index(seed)]

    def rehash_pilot(self, seed: int, mutate=None) -> None:
        """COMPLETE.json of the pilot unit again from disk (``mutate`` applied to its other keys) and plan.json's
        record with it: a hash-consistent edit."""
        folder = self.unit_folder(self.arm, seed)
        digest = sk.recomplete(folder, mutate)
        self.units[(self.arm, seed)]["complete"] = digest
        plan = self.plan()
        self.job(plan, seed)["complete_sha256"] = digest
        self.save_plan(plan)

    def repin_gate_a(self, seed: int, mutate=None) -> None:
        """COMPLETE.json and job.json of a Gate A unit again from disk and the rules module's pins with them."""
        folder = self.unit_folder("a0", seed)
        job_sha = sk.sha((folder / "job.json").read_bytes())
        digest = sk.recomplete(folder, lambda d: (d.update(job_sha256=job_sha), mutate(d) if mutate else None))
        self.units[("a0", seed)].update(complete=digest, job=job_sha)
        write_rules(self)

    def cell_u_pp(self, arm: str, seed: int) -> float:
        return 100.0 * sum(self.counts[(arm, seed)].values()) / (3 * len(HARM))


def pins_of(w: World) -> list:
    return [{"name": f"a0 {j} (Gate A)", "arm": "a0", "seed": j, "target": "e1", "path": w.units[("a0", j)]["rel"],
             "complete_sha256": w.units[("a0", j)]["complete"], "job_sha256": w.units[("a0", j)]["job"]}
            for j in SEEDS]


def write_rules(w: World, pins: list | None = None) -> None:
    sk.rules_module(w.rules, pins_of(w) if pins is None else pins)


def draw_counts(rng, level: float) -> dict:
    rate = np.clip(level + rng.uniform(-0.25, 0.25, len(HARM)), 0.0, 1.0)
    return {p: int(rng.binomial(3, r)) for p, r in zip(HARM, rate)}


def make(root: Path, counts: dict | None = None, seed: int = 0, arm: str = "a0_plant", block: str = "P") -> World:
    root = Path(root)
    rng = np.random.default_rng(seed)
    w = World(root, root / "kit", root / "repo", root / "repo" / "rules.py", arm, block)
    sk.write(w.repo / sk.BARS, (sk.TREE / sk.BARS).read_bytes())
    given = counts or {}
    for j in SEEDS:
        w.counts[("a0", j)] = dict(given.get(("a0", j)) or draw_counts(rng, 0.50))
        w.counts[(arm, j)] = dict(given.get((arm, j)) or draw_counts(rng, 0.62))
    for j in SEEDS:                                   # Gate A's pinned units in the repo
        rel = f"tmp/synth-gate/{j}-a0-e1-a1"
        u = write_unit(w.repo / rel, w.counts[("a0", j)], "a0", j, pilot=False)
        w.units[("a0", j)] = {**u, "rel": rel, "host": None}
    write_rules(w)
    tree = w.kit / "retrieved" / "p-1" / "tree"
    jobs = []
    for j in SEEDS:                                   # block P's host p-1: three complete, pulled arm jobs
        engine_arm = f"edit-{edit_sha(arm)}"
        rel = f"round1/{j}-{engine_arm}-e1-a1"
        u = write_unit(tree / rel, w.counts[(arm, j)], engine_arm, j, pilot=True)
        w.units[(arm, j)] = {**u, "rel": rel, "host": "p-1"}
        jobs.append({"kind": "arm", "arm": arm, "seed": j, "engine": "X", "status": "complete", "unit": rel,
                     "complete_sha256": u["complete"], "outputs": None, "reason": None,
                     "edit": {"arm": arm, "path": SENTINELS["edit_path"], "sha256": edit_sha(arm)}})
    plan = {"name": "stage1-olmo", "records": {"plan_ab": {"code": "A"}, "oext_fallback": None},
            "hosts": {"p-1": {"block": block, "done": True, "note": SENTINELS["host"], "jobs": jobs},
                      "a-3": {"block": "A", "done": True, "jobs": [
                          {"kind": "arm", "arm": "S1", "seed": 1102, "engine": "X", "status": "complete",
                           "unit": f"round1/1102-edit-{'1' * 64}-e1-a1", "complete_sha256": "2" * 64,
                           "outputs": None, "reason": SENTINELS["other_block"],
                           "edit": {"path": SENTINELS["edit_path"], "sha256": "1" * 64}}]}},
            "seals": {}, "deferrals": [], "requeues": []}
    w.save_plan(plan)
    return w


def copy(w: World, root: Path) -> World:
    """A copy of the world under ``root`` (for a test that edits it); the rules module is re-pointed."""
    shutil.copytree(w.root, root)
    t = World(root, root / "kit", root / "repo", root / "repo" / "rules.py", w.arm, w.block,
              {k: dict(v) for k, v in w.counts.items()}, {k: dict(v) for k, v in w.units.items()})
    write_rules(t)
    return t


def rewrite_unit(w: World, arm: str, seed: int, counts: dict) -> None:
    """A unit's evaluation files again with other counts, re-hashed into COMPLETE.json and plan.json or the pins."""
    folder = w.unit_folder(arm, seed)
    w.counts[(arm, seed)] = dict(counts)
    summary = sk.eval_folder(folder, cell_of(counts), "e1")
    sk.write(folder / "eval" / "e1" / "summary.json", sk.jbytes({**summary, "note": SENTINELS["summary"]}))
    if arm == "a0":
        w.repin_gate_a(seed, lambda d: d.update(evaluation={**summary, "note": SENTINELS["summary"]}))
    else:
        w.rehash_pilot(seed, lambda d: d.update(evaluation={**summary, "note": SENTINELS["summary"]}))
