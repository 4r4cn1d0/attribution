"""The pilot's inputs: the pilot-arm units of the block by key from the kit's plan.json, Gate A's a0 units through
REJUDGED_PINS["A"], and the 3 x 200 per-prompt U tables built by the input builder's own code.

**The pilot-arm units** (the input builder's practice, reading_input/build.py scan and _primary_jobs, without the
seal: the pilot needs nothing sealed to be read, addendum section 40 point 12). In plan.json, among the hosts of the
block that are recorded done (record-done), the jobs recorded complete and pulled: every one must be an ``arm`` job
of the mode's arm at one of the seeds (any other complete job in the block is an extra unit and refuses); exactly
one per seed. A host that is not done and a job recorded complete (not pulled) are not inputs (listed by name and
count only). The unit folder is retrieved/HOST/tree/<unit>; its COMPLETE.json must hash to the SHA-256 record-done
recorded (plan_tool.py record_done hashed the pulled file), be a complete marker with a file list, and name job.json
by its SHA-256; job.json must name kind run-one, the engine arm edit-<the job's edit SHA-256>, the seed, target e1
and the dev bank (the builder's _check_job_json). Every later file is read through the builder's Folder.file (listed
by COMPLETE.json at its SHA-256 and hashing to it on disk).

**Gate A's a0 units**: REJUDGED_PINS["A"] of the rules module (loaded by path, as the builder loads it), the pins
named "a0 1101 (Gate A)", "a0 1102 (Gate A)" and "a0 1103 (Gate A)" with arm a0, the seed and target e1; the folder
is opened only when its COMPLETE.json and job.json hash to the pins (the builder's pinned_folder), and job.json must
name the arm, the seed and the checkpoint.

**The tables**: per unit, items.harm on eval/e1/samples.jsonl, guard_samples.jsonl and summary.json with the
frozen coherence bars (by pin): per harm prompt the Unsafe share of its 3 sampled answers, checked against the
summary's counts; the six units must hold one sorted set of prompt ids, B16's 200 (settings endpoints.U.items).

**Messages.** Every refusal of this module is a fixed message that names the step and the unit's design key
(the arm and seed, from the code, never from a file). A refusal or any other error of the imported code is replaced
by a fixed message; its own message is withheld (it may hold a name, a path or a value). Nothing here prints.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from scripts.stage1_s1.reading.settings import Refusal, settings
from scripts.stage1_s1.reading_input import build
from scripts.stage1_s1.reading_input import items as it
from scripts.stage1_s1.reading_input.sources import (COMPLETE, Folder, Kit, _complete, is_hex64, load_rules,
                                                     pinned_folder, read_bytes, sha256_bytes)
from scripts.stage1_s1.pilot_gate.gate import ARM_OF, COMPARATOR, MODES, SEEDS

CHECKPOINT = "e1"                                            # the builder's CHECKPOINT
JOB_KIND = "arm"                                             # the kit kind of a pilot-arm job (CHECK 5.1 item 1)
GATE_A_NAME = "a0 {seed} (Gate A)"                           # REJUDGED_PINS["A"] names (stage1_rules.py)
UNIT_PATH = re.compile(r"round1/\d{4}-edit-[0-9a-f]{64}-e1-a\d+")   # job_runner_stage1: ROUND/<seed>-<engine arm>-e1-a*
EVAL = (f"eval/{CHECKPOINT}/summary.json", f"eval/{CHECKPOINT}/samples.jsonl", f"eval/{CHECKPOINT}/guard_samples.jsonl")
WITHHELD = "its message is withheld: it may hold a name, a path or a value"


@dataclass
class Unit:
    key: str                                                 # "a0_plant 1101" or "a0 1101 (Gate A)"
    arm: str                                                 # the design arm
    seed: int
    folder: Folder
    where: str                                               # "kit:HOST/<unit>" or "repo:<path>"
    u: dict = field(default_factory=dict)                    # prompt id -> Unsafe share (k / 3)
    ids: list = field(default_factory=list)

    def record(self) -> dict:
        return {"folder": self.where, "complete_sha256": self.folder.complete_sha256,
                "files": dict(sorted(self.folder.read.items()))}


def _step(what: str, fn, *args):
    """One step of imported code; any error becomes a fixed message that names the step only."""
    try:
        return fn(*args)
    except Refusal:
        raise Refusal(f"{what}: refused by a check of the imported code ({WITHHELD})") from None
    except Exception as exc:  # noqa: BLE001 - its text may hold a value
        raise Refusal(f"{what}: an unexpected {type(exc).__name__} ({WITHHELD})") from None


def _plain_hosts(kit: Kit, block: str) -> tuple[list, list]:
    """(the done hosts of the block as (name, record), the names of its hosts that are not done)."""
    done, not_done = [], []
    for name, h in sorted(kit.plan["hosts"].items()):
        if not isinstance(name, str) or not isinstance(h, dict) or h.get("block") != block:
            continue
        if h.get("done") is not True:
            not_done.append(name)
            continue
        if not isinstance(h.get("jobs"), list):
            raise Refusal(f"block {block}: a done host holds no job list")
        done.append((name, h))
    return done, not_done


def block_jobs(kit: Kit, block: str, mode: str) -> dict:
    """seed -> (host, job) of the mode's arm at each seed from the block's done hosts (module doc); the names of
    the hosts not done and the count of complete, not pulled jobs come back under "_not_done" and "_not_pulled"."""
    arm = ARM_OF[mode]
    done, not_done = _plain_hosts(kit, block)
    if not done:
        raise Refusal(f"block {block}: no host of the block is recorded done (record-done first)")
    found: dict = {}
    not_pulled = 0
    for host, h in done:
        for job in h["jobs"]:
            if not isinstance(job, dict) or job.get("status") != "complete":
                continue
            if job.get("pulled") is False:
                not_pulled += 1
                continue
            if job.get("kind") != JOB_KIND or job.get("arm") != arm or job.get("seed") not in SEEDS:
                raise Refusal(f"block {block} holds a complete job that is not {arm} at 1101-1103 (an extra unit)")
            if job["seed"] in found:
                raise Refusal(f"{arm} {job['seed']}: two complete units in block {block}")
            found[job["seed"]] = (host, job)
    missing = [j for j in SEEDS if j not in found]
    if missing:
        raise Refusal(f"{arm} {missing[0]}: no complete, pulled unit in block {block}")
    found["_not_done"] = not_done
    found["_not_pulled"] = not_pulled
    return found


def _host_name(host: str) -> str:
    if not isinstance(host, str) or not re.fullmatch(r"[a-z0-9][a-z0-9-]{0,39}", host):
        raise Refusal("a host name of plan.json is not a plain name")
    return host


def pilot_unit(kit: Kit, mode: str, seed: int, host: str, job: dict) -> Unit:
    """The pilot-arm unit of one seed: plan.json's record, COMPLETE.json at record-done's SHA-256, job.json by its
    marker and its fields (module doc)."""
    arm = ARM_OF[mode]
    key = f"{arm} {seed}"
    edit = job.get("edit")
    if not isinstance(edit, dict) or not is_hex64(edit.get("sha256")):
        raise Refusal(f"{key}: the job record names no edit SHA-256")
    rel, digest = job.get("unit"), job.get("complete_sha256")
    if not isinstance(rel, str) or not UNIT_PATH.fullmatch(rel) or not is_hex64(digest):
        raise Refusal(f"{key}: the job record has no engine run-one unit path or no COMPLETE.json SHA-256")
    root = kit.root / "retrieved" / _host_name(host) / "tree" / rel
    try:
        data = read_bytes(root / COMPLETE, key)
    except Refusal:
        raise Refusal(f"{key}: COMPLETE.json is missing or not a regular file") from None
    if sha256_bytes(data) != digest:
        raise Refusal(f"{key}: COMPLETE.json does not hash to the SHA-256 record-done recorded in plan.json")
    doc = _step(f"{key}: COMPLETE.json as a complete marker", _complete, data, key)
    folder = Folder(key, root, digest, doc, None)
    want = {"kind": "run-one", "arm": f"edit-{edit['sha256']}", "seed": seed, "target_checkpoint": CHECKPOINT,
            "evaluate_bank": "dev", "split": "dev"}
    _step(f"{key}: job.json by its marker, naming the arm, the seed, checkpoint {CHECKPOINT} and the dev bank",
          build._check_job_json, folder, want, False)
    return Unit(key, arm, seed, folder, f"kit:{host}/{rel}")


def gate_a_unit(repo: Path, rules, seed: int) -> Unit:
    """Gate A's a0 unit of one seed through REJUDGED_PINS["A"] (module doc)."""
    key = GATE_A_NAME.format(seed=seed)
    pins = [p for p in rules.REJUDGED_PINS.get("A", ()) if isinstance(p, dict) and p.get("name") == key]
    if len(pins) != 1 or pins[0].get("arm") != COMPARATOR or pins[0].get("seed") != seed \
            or pins[0].get("target") != CHECKPOINT:
        raise Refusal(f"{key}: REJUDGED_PINS['A'] holds no one pin of this name with arm a0, seed {seed}, target e1")
    pin = pins[0]
    folder = _step(f"{key}: COMPLETE.json and job.json at their pins", pinned_folder, repo, pin)
    _step(f"{key}: job.json naming arm a0, seed {seed} and checkpoint {CHECKPOINT}", build._check_job_json, folder,
          {"arm": COMPARATOR, "seed": seed, "target_checkpoint": CHECKPOINT}, True)
    return Unit(key, COMPARATOR, seed, folder, f"repo:{pin['path']}")


def harm_table(unit: Unit, bar: dict) -> None:
    """The unit's per-prompt U by the builder's items.harm (U only; the other parts are dropped)."""
    def build_table():
        summary = unit.folder.json(EVAL[0])
        harm = it.harm(unit.folder.file(EVAL[1]), unit.folder.file(EVAL[2]), summary, bar, unit.key)
        return harm["ids"], harm["U"]
    unit.ids, unit.u = _step(f"{unit.key}: the per-prompt U table", build_table)


def read_units(kit_root: Path, repo: Path, rules_path: Path, mode: str, block: str) -> tuple[dict, dict]:
    """(the B16 table {(arm, seed): vector}, the inputs record): every check of the module doc."""
    if mode not in MODES:
        raise Refusal("the mode is not pilot or re-pilot")
    kit = _step("the kit's plan.json as a stage-1 plan", Kit, kit_root)
    seals = kit.plan.get("seals")
    seal = seals.get(block) if isinstance(seals, dict) else None     # a note only: the pilot needs no seal to be read
    seal_sha = seal.get("sha256") if isinstance(seal, dict) and is_hex64(seal.get("sha256")) else None
    rules, rules_sha = _step("the rules module", load_rules, rules_path)
    bar = _step("the frozen coherence bars file", lambda: it.bars(read_bytes(Path(repo) / it.BARS_PATH, "bars")))
    jobs = block_jobs(kit, block, mode)
    units = [pilot_unit(kit, mode, j, *jobs[j]) for j in SEEDS] + [gate_a_unit(Path(repo), rules, j) for j in SEEDS]
    for unit in units:
        harm_table(unit, bar)
    ids = units[0].ids
    if any(u.ids != ids for u in units[1:]):
        raise Refusal("the six units do not hold one set of harm prompt ids")
    if len(ids) != int(settings()["endpoints"]["U"]["items"]):
        raise Refusal("the units' harm prompt ids are not B16's 200")
    table = {(u.arm, u.seed): np.array([u.u[p] for p in ids], dtype=float) for u in units}
    record = {"plan_sha256": kit.plan_sha256, "block": block, "plan_json_block_seal_sha256": seal_sha,
              "hosts_not_done": jobs["_not_done"], "jobs_complete_not_pulled": jobs["_not_pulled"],
              "rules": {"path": str(rules_path), "sha256": rules_sha}, "coherence_bars_sha256": it.BARS_SHA256,
              "units": {u.key: u.record() for u in units}, "prompt_ids": list(ids),
              "per_prompt_u": {u.key: [u.u[p] for p in ids] for u in units}}
    return table, record
