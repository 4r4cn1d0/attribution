#!/usr/bin/env python3
"""Rebuild the attribution project's cloud cost ledger from its local run records.

    python3 tmp/cost-ledger/cost_ledger.py               # write the CSV and the summary page
    python3 tmp/cost-ledger/cost_ledger.py --dry-run     # build and self-check only; print totals; write nothing
    python3 tmp/cost-ledger/cost_ledger.py --now 2026-10-06T06:00:00Z   # fix the provisional end of running pods

Outputs (the only files this script writes):
    research/costs/cost-ledger.csv          one row per activity segment of every pod (and zero-length records)
    research/costs/2026-10-06-cost-ledger.md the readable summary, regenerated from the same data

Standard library only; Python 3.9 or later. Every source is opened read-only. Safe to re-run while headroom v2 is
still running: hosts that appear later under tmp/headroom-v2/hosts/ are picked up, a pod without a stop record is
billed up to the build time and its open tail is labelled in_progress (provisional).

Method in one paragraph. A pod bills from RunPod's start time (lastStartedAt / createdAt) to its stop (RunPod's
"Exited by user" status change when a refreshed record holds it, else the accepted stop request). That span starts as
"unattributed" and is painted with intervals from the records, coarse first and fine last: orchestrator log events
(second resolution), then process receipts (started_utc + elapsed_s), then the engine's per-stage ledgers
(millisecond start/end). Whatever no record covers stays "unattributed". By construction the segments of a pod add up
to its billed span; the script asserts this. Dollars are wall_hours x the pod's own costPerHr (GPU price; storage
and disk are not in the CSV, see the reconciliation in the summary).

Privacy. Pod records also hold the pod's public IP and port mappings. Only an allow-list of fields is read (name,
price, status, start/stop times, disk sizes, GPU type). SSH keys, known_hosts files and the secrets file are never
opened. No per-prompt outputs or held-out data are read: only receipts, stage ledgers, progress/step timings, pull
records and aggregate counts. Before writing, every output is scanned for IPv4 addresses and refused if one is found.

Snapshot. Four retrieved trees (SNAPSHOT_TREES) may be deleted after their private backup. The files read from them are
kept in research/costs/receipts-snapshot/ at the same path relative to tmp/ and are cited by that tmp/ path. The script
reads the snapshot only when the live tree is missing, and it stops with an error if neither exists. To test the
snapshot alone: COST_LEDGER_LIVE_ROOT=<empty folder> python3 research/costs/cost_ledger.py --dry-run
"""

from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import io
import json
import os
import pathlib
import re
import statistics
import sys
from dataclasses import dataclass, field

UTC = dt.timezone.utc
ROOT = pathlib.Path(__file__).resolve().parents[2]
TMP = ROOT / "tmp"
DEFAULT_CSV = ROOT / "research" / "costs" / "cost-ledger.csv"
DEFAULT_MD = ROOT / "research" / "costs" / "2026-10-06-cost-ledger.md"
SNAPSHOT = ROOT / "research" / "costs" / "receipts-snapshot"
SNAPSHOT_TREES = ("study-v2-20261002/retrieved-calibration", "study-v2-20261004/retrieved", "headroom-20261005/retrieved",
                  "headroom-v2/retrieved")
LIVE = pathlib.Path(os.environ.get("COST_LEDGER_LIVE_ROOT") or TMP)     # where the live trees are looked for
A100 = "NVIDIA A100-SXM4-80GB"
COLUMNS = ["date_utc", "run", "host", "role", "activity", "start_utc", "end_utc", "wall_hours", "gpu_type",
           "gpu_count", "usd_per_hour", "usd_estimate", "source_file", "notes"]
ACTIVITIES = ["pod_create_wait", "bootstrap/setup", "preflight", "training", "evaluation", "row_scoring", "rewriting",
              "edit_building", "attribution", "copy/finish", "idle", "failed_attempt", "lease_extension",
              "unattributed", "in_progress"]
RUNS = {
    "runpod-pilot-20261002": "2 Oct: minimal-safety CUDA pilot (one RTX A5000 pod, deleted after use)",
    "study-v2-20261002": "2 Oct: study-v2 calibration and dev-matrix-001 (13 A100 pods, lost in the credit incident)",
    "pod-timer-check-20261004": "4 Oct: in-pod stop-timer self-stop check (one small pod)",
    "study-v2-20261004": "4 Oct: dev-matrix-002 (13 A100 hosts x 2 jobs, plus one replaced pod)",
    "headroom-20261005": "5 Oct: headroom positive control, round 1 (10 jobs + lead; two restarts)",
    "headroom-v2": "5-6 Oct: headroom v2 (validation, calibration, lead)",
}

# Engine stages grouped for the summary (stage key -> activity).
EVAL_STAGES = ("load_guard", "query_loss", "generate", "sample", "arc_utility", "guard", "guard_samples", "harm_scores")
SETUP_STAGES = ("load_policy", "tokenize", "memory_preflight", "init_state", "restore_state")

# ----------------------------------------------------------------------------------------------------------------
# safe reading


def _guard(path: pathlib.Path) -> None:
    parts = [p.lower() for p in path.parts]
    name = path.name.lower()
    if ("ssh" in parts or ".ssh" in parts or name.startswith("known_hosts") or name.startswith("ssh_key")
            or name.endswith(".pub") or name.endswith(".env") or "secret" in name or name in ("key", "id_rsa", "id_ed25519")):
        raise PermissionError(f"refusing to open a sensitive file: {path}")


def rel(path: pathlib.Path) -> str:
    p = pathlib.Path(path).resolve()
    try:
        return str(pathlib.Path("tmp") / p.relative_to(SNAPSHOT))      # a snapshot copy is cited by its tmp/ path
    except ValueError:
        pass
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_json(path: pathlib.Path):
    _guard(path)
    return json.loads(path.read_text())


_RETRIEVED = {}


def retrieved(base: pathlib.Path, sub: str = "retrieved") -> pathlib.Path:
    """The live tree tmp/RUN/SUB, else its snapshot. Raises if both are missing, so that rows measured from receipts are
    never silently rebuilt as log-time estimates."""
    key = f"{base.name}/{sub}"
    if key not in SNAPSHOT_TREES:
        return base / sub
    if key not in _RETRIEVED:
        live, snap = LIVE / key, SNAPSHOT / key
        if live.exists():
            _RETRIEVED[key] = live
        elif snap.exists():
            check_snapshot(key)
            _RETRIEVED[key] = snap
        else:
            raise FileNotFoundError(f"{live} and its snapshot {snap} are both missing; refusing to fall back to log-time "
                                    "estimates for a run with measured rows")
    return _RETRIEVED[key]


def check_snapshot(key: str) -> None:
    """Every file MANIFEST.json lists under KEY must be present and unchanged."""
    files = [f for f in read_json(SNAPSHOT / "MANIFEST.json")["files"] if f["path"].startswith(key + "/")]
    bad = [f["path"] for f in files
           if not (SNAPSHOT / f["path"]).is_file() or hashlib.sha256((SNAPSHOT / f["path"]).read_bytes()).hexdigest() != f["sha256"]]
    if bad or not files:
        raise RuntimeError(f"snapshot {SNAPSHOT / key} is incomplete or changed: {len(bad)} of {len(files)} files fail, e.g. {bad[:3]}")


def read_jsonl(path: pathlib.Path) -> list:
    _guard(path)
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            out.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return out


POD_FIELDS = ("name", "costPerHr", "cost", "desiredStatus", "lastStartedAt", "lastStatusChange", "createdAt",
              "startedAt", "created_utc", "cap_stop_utc", "volumeInGb", "containerDiskInGb", "disk", "utc", "host")


def pod_fields(path: pathlib.Path) -> dict:
    """Allow-listed fields of a pod record (pod.json, pod-latest.json, create-result.json). Never the IP or ports."""
    raw = read_json(path)
    out = {}
    if isinstance(raw, dict) and isinstance(raw.get("pod"), dict):
        out["http_status"] = raw.get("status")
        out["result_utc"] = raw.get("utc")
        rec = raw["pod"]
        if "error" in rec:
            out["error"] = re.sub(r"\s+", " ", str(rec["error"]))[:160]
    else:
        rec = raw if isinstance(raw, dict) else {}
    for k in POD_FIELDS:
        if k in rec:
            out[k] = rec[k]
    gpu = rec.get("gpu")
    if isinstance(gpu, dict):
        out["gpu_id"] = gpu.get("id")
        out["gpu_count"] = gpu.get("count")
    return out


# ----------------------------------------------------------------------------------------------------------------
# time

RE_ISO = re.compile(r"^(\d{4})-(\d{2})-(\d{2})[T ](\d{2}):(\d{2}):(\d{2})(?:\.(\d+))?\s*(Z|UTC|[+-]\d{2}:?\d{2})?(?:\s*UTC)?$")
RE_CHANGE = re.compile(r"(Exited|Rented|Stopped|Terminated)[^:]*:\s*\w{3} (\w{3}) (\d{1,2}) (\d{4}) (\d{2}):(\d{2}):(\d{2}) GMT([+-]\d{4})")
MONTHS = {m: i + 1 for i, m in enumerate("Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}


def parse_ts(value):
    if value is None or value == "":
        return None
    if isinstance(value, (int, float)):
        return dt.datetime.fromtimestamp(float(value), UTC)
    s = str(value).strip()
    m = RE_ISO.match(s)
    if not m:
        return None
    y, mo, d, h, mi, se, frac, off = m.groups()
    t = dt.datetime(int(y), int(mo), int(d), int(h), int(mi), int(se), int((frac or "0")[:6].ljust(6, "0")), tzinfo=UTC)
    if off and off not in ("Z", "UTC"):
        digits = off[1:].replace(":", "")
        delta = dt.timedelta(hours=int(digits[:2]), minutes=int(digits[2:4]))
        t = t - delta if off[0] == "+" else t + delta
    return t


def status_change(value):
    """RunPod lastStatusChange, e.g. 'Exited by user: Mon Oct 05 2026 09:23:19 GMT+0000 (...)' -> (kind, time)."""
    m = RE_CHANGE.search(str(value or ""))
    if not m:
        return None, None
    kind, mon, day, year, h, mi, se, off = m.groups()
    t = dt.datetime(int(year), MONTHS[mon], int(day), int(h), int(mi), int(se), tzinfo=UTC)
    delta = dt.timedelta(hours=int(off[1:3]), minutes=int(off[3:5]))
    return kind, (t - delta if off[0] == "+" else t + delta)


def iso(t) -> str:
    if t is None:
        return ""
    t = t.astimezone(UTC)
    return f"{t:%Y-%m-%dT%H:%M:%S}.{t.microsecond // 1000:03d}Z"


def hms(t) -> str:
    return "" if t is None else f"{t.astimezone(UTC):%H:%M:%S}"


def hours(a, b) -> float:
    return (b - a).total_seconds() / 3600.0


def tar_stamp(name: str):
    m = re.search(r"pull-(\d{8}T\d{6}Z)", name or "")
    return dt.datetime.strptime(m.group(1), "%Y%m%dT%H%M%SZ").replace(tzinfo=UTC) if m else None


# ----------------------------------------------------------------------------------------------------------------
# model


@dataclass
class Iv:
    prio: int
    start: dt.datetime
    end: dt.datetime
    activity: str
    stage: str
    detail: str
    sources: tuple
    basis: str
    extra: tuple = ()

    def key(self):
        return (self.activity, self.stage, self.detail, self.sources, self.basis, self.extra)


@dataclass
class Pod:
    run: str
    host: str
    role: str
    pod_name: str
    gpu_type: str
    gpu_count: int
    price: float
    price_src: str
    start: dt.datetime
    start_src: str
    end: dt.datetime
    end_src: str
    end_basis: str
    running: bool = False
    disk_gb: float = 0.0       # container disk + volume, billed while the pod runs
    volume_gb: float = 0.0     # the volume, kept (and billed) after a stop until the pod is deleted
    deleted_at_end: bool = False
    note: str = ""
    ivs: list = field(default_factory=list)
    segments: list = field(default_factory=list)

    def add(self, prio, start, end, activity, stage, detail, sources, basis, **extra):
        if start is None or end is None:
            return
        if end < start:
            raise ValueError(f"{self.run}/{self.host}: interval ends before it starts: {detail} {start} {end}")
        self.ivs.append(Iv(prio, start, end, activity, stage, detail, tuple(s for s in sources if s), basis,
                           tuple((k, str(v)) for k, v in extra.items() if v not in (None, ""))))

    @property
    def key(self):
        return f"{self.run}/{self.pod_name}"


@dataclass
class Rec:
    """A zero-length record row (failed create, lease extension, failed restart)."""
    run: str
    host: str
    role: str
    activity: str
    when: dt.datetime
    stage: str
    detail: str
    sources: tuple
    basis: str
    gpu_type: str = ""
    price: float = 0.0
    extra: tuple = ()


@dataclass
class Job:
    """One training job (one engine process), for unit costs."""
    run: str
    host: str
    pod: str
    process: str
    seed: str
    arm: str
    start: dt.datetime
    end: dt.datetime
    exit: object
    price: float
    stage_s: dict = field(default_factory=dict)       # stage -> seconds (summed over units and checkpoints)
    counts: dict = field(default_factory=dict)        # stage -> items (prompts, answers, questions, steps)
    train_steps: int = 0
    step_seconds: float = 0.0                         # sum of steps.jsonl 'seconds'
    step_count: int = 0
    checkpoints: int = 0
    meta: dict = field(default_factory=dict)          # trainable parameters, attention implementation
    tokens: dict = field(default_factory=dict)        # padded / input / target tokens of the train stages
    segments: dict = field(default_factory=dict)      # train segment -> (seconds, steps)

    @property
    def elapsed(self):
        return (self.end - self.start).total_seconds()


class Ledger:
    def __init__(self, now: dt.datetime):
        self.now = now
        self.pods: list = []
        self.recs: list = []
        self.jobs: list = []
        self.lead: list = []           # dicts: scoring / rewriting stats
        self.projections: list = []    # v2 preflight evaluation-timing projections
        self.snapshots: list = []      # balance snapshots
        self.local: list = []          # local (Mac) compute rows
        self.billing: list = []        # provider billing records found locally
        self.warnings: list = []
        self.facts: dict = {}          # named measured values for the summary

    def rec(self, run, host, role, activity, when, stage, detail, sources, basis, gpu_type="", price=0.0, **extra):
        self.recs.append(Rec(run, host, role, activity, when, stage, detail, tuple(s for s in sources if s), basis,
                             gpu_type, price, tuple((k, str(v)) for k, v in extra.items() if v not in (None, ""))))

    def warn(self, msg):
        self.warnings.append(msg)


# ----------------------------------------------------------------------------------------------------------------
# receipts, engine ledgers


def receipt(folder: pathlib.Path):
    """A process_receipt.py folder -> dict(start, end, elapsed, exit, command, source) or None."""
    pr, st = folder / "process-receipt.json", folder / "started.json"
    if pr.exists():
        r = read_json(pr)
        start = parse_ts(r.get("started_utc")) or parse_ts(r.get("started_epoch"))
        el = r.get("elapsed_s")
        end = parse_ts(r.get("ended_epoch")) if r.get("ended_epoch") else None
        if end is None and start is not None and isinstance(el, (int, float)):
            end = start + dt.timedelta(seconds=el)
        return {"start": start, "end": end, "elapsed": el, "exit": r.get("exit_code"), "command": r.get("command") or [],
                "source": rel(pr), "name": folder.name}
    if st.exists():
        r = read_json(st)
        return {"start": parse_ts(r.get("started_utc")) or parse_ts(r.get("started_epoch")), "end": None, "elapsed": None,
                "exit": None, "command": r.get("command") or [], "source": rel(st), "name": folder.name}
    return None


def receipt_from_dict(r: dict, source: str, name: str):
    if not isinstance(r, dict) or "started_utc" not in r:
        return None
    start = parse_ts(r.get("started_utc"))
    el = r.get("elapsed_s")
    end = parse_ts(r.get("ended_epoch")) if r.get("ended_epoch") else (start + dt.timedelta(seconds=el) if start and el else None)
    return {"start": start, "end": end, "elapsed": el, "exit": r.get("exit_code"), "command": r.get("command") or [],
            "source": source, "name": name}


def load_stages(unit: pathlib.Path):
    """An engine ledger.jsonl -> list of dict(stage, start, end, row) with absolute times, and the unit status."""
    path = unit / "ledger.jsonl"
    rows = read_jsonl(path)
    status = read_json(unit / "status.json") if (unit / "status.json").exists() else {}
    out = []
    precise = any("." in str(r.get("start_utc", "")) for r in rows)
    t0 = None
    if not precise:      # second-resolution start_utc: place stages on the process clock (start_s / end_s)
        lo, hi = [], []
        for r in rows:
            s, rel_s = parse_ts(r.get("start_utc")), r.get("start_s")
            if s is not None and isinstance(rel_s, (int, float)):
                lo.append(s - dt.timedelta(seconds=rel_s))
                hi.append(s + dt.timedelta(seconds=1) - dt.timedelta(seconds=rel_s))
        if lo:
            a, b = max(lo), min(hi)
            t0 = a + (b - a) / 2 if b > a else a
    for r in rows:
        if t0 is not None and isinstance(r.get("start_s"), (int, float)):
            s = t0 + dt.timedelta(seconds=r["start_s"])
            e = t0 + dt.timedelta(seconds=r["end_s"]) if isinstance(r.get("end_s"), (int, float)) else None
        else:
            s, e = parse_ts(r.get("start_utc")), parse_ts(r.get("end_utc"))
        if s is None:
            continue
        if e is None and isinstance(r.get("seconds"), (int, float)):
            e = s + dt.timedelta(seconds=r["seconds"])
        if e is None or e < s:
            e = s
        out.append({"stage": r.get("stage", "?"), "start": s, "end": e, "row": r, "unit": unit.name, "source": rel(path)})
    return out, status


def fmt_int(x):
    return f"{int(x):,}" if isinstance(x, (int, float)) else "?"


def classify(stage: str, row: dict, context: str):
    """Engine ledger stage -> (activity, stage key, detail)."""
    ck = row.get("checkpoint")
    at = f" at {ck}" if ck else ""
    if context == "preflight":
        if stage in EVAL_STAGES:
            return ("preflight", "eval_timing_sample",
                    "evaluation-timing sample after two steps (80 generations, 60 samples, judging, ARC) for the evaluation projection")
        return "preflight", "fixture", "fixture and determinism checks (load, tokenize, memory, resume, batch-equality)"
    if context == "scores":
        if stage == "score_rows":
            return "row_scoring", "score_rows", f"score {fmt_int(row.get('rows'))} rows with Qwen3Guard-Gen-4B (3 label lines per row)"
        if stage == "load_guard":
            return "row_scoring", "load_model", "load Qwen3Guard-Gen-4B"
        return "row_scoring", "other", stage
    if context == "rewrites":
        if stage == "generate_rewrites":
            return ("rewriting", "generate_rewrites",
                    f"rewrite {fmt_int(row.get('rows'))} rows with Qwen2.5-7B-Instruct ({fmt_int(row.get('accepted'))} accepted)")
        if stage == "load_generator":
            return "rewriting", "load_model", "load Qwen2.5-7B-Instruct"
        if stage == "load_guard":
            return "rewriting", "load_model", "load Qwen3Guard-Gen-4B (acceptance check)"
        return "rewriting", "other", stage
    if context == "pilot":
        if stage in ("train_short", "train_continue"):
            return "training", "train", f"{stage} {row.get('arm')} seed {row.get('seed')}: steps {row.get('first_step')}-{row.get('last_step')}"
        if stage.startswith("eval_"):
            return "evaluation", "generation", f"{stage} {row.get('arm')} seed {row.get('seed')}: generation + toxic-bert score"
        if stage == "attribution":
            return "attribution", "toy", f"attribution feature, {row.get('examples')} examples (toy: 0.5B model)"
        if stage == "input_classifier":
            return "row_scoring", "score_rows", f"toxic-bert over {row.get('texts')} training texts"
        return "training", "in_job_setup", f"in-job setup: {stage}"
    if stage in SETUP_STAGES:
        if context == "evalstate":
            return "evaluation", "in_job_setup", f"re-evaluation setup: {stage}"
        return "training", "in_job_setup", f"in-job setup: {stage}"
    if stage == "train":
        return ("training", "train",
                f"train {row.get('segment')}: steps {row.get('first_step')}-{row.get('last_step')} ({fmt_int(row.get('steps'))} steps)")
    if stage == "verify_trajectory":
        return ("training", "verify",
                f"verify trajectory ({fmt_int(row.get('steps_verified'))} steps); then seal the unit (hash states, COMPLETE.json) and verify")
    if stage == "load_guard":
        return "evaluation", "judging", f"load Qwen3Guard-Gen-4B{at}"
    if stage == "query_loss":
        return "evaluation", "query_loss", f"query loss, {fmt_int(row.get('queries'))} queries{at}"
    if stage == "generate":
        return ("evaluation", "generation",
                f"greedy generation, {fmt_int(row.get('prompts'))} prompts{at} ({fmt_int(row.get('output_tokens'))} output tokens)")
    if stage == "sample":
        return ("evaluation", "sampling",
                f"sampled answers, {fmt_int(row.get('answers'))}{at} ({fmt_int(row.get('output_tokens'))} output tokens)")
    if stage == "arc_utility":
        return "evaluation", "arc", f"ARC log-likelihood, {fmt_int(row.get('questions'))} questions{at}"
    if stage == "guard":
        return "evaluation", "judging", f"judge greedy answers (Qwen3Guard), {fmt_int(row.get('items'))} items{at}"
    if stage == "guard_samples":
        return "evaluation", "judging", f"judge sampled answers (Qwen3Guard), {fmt_int(row.get('items'))} items{at}"
    if stage == "harm_scores":
        return "evaluation", "judging", f"continuous harm scores, {fmt_int(row.get('answers'))} answers{at}"
    return "training", "other", stage


def paint_units(pod: Pod, units, context: str, prio: int = 4, failed_why: str = "", **extra) -> list:
    """Paint every stage of every unit ledger; returns the stage rows (for unit costs)."""
    out = []
    for unit in units:
        rows, status = load_stages(unit)
        if not rows:
            continue
        unit_failed = bool(failed_why) or status.get("status") == "failed"
        why = (failed_why or str(status.get("error") or "").strip() or "unit failed").replace("\n", " ")
        if unit_failed:     # one window for the whole failed unit; 'was' names what it was doing
            end = parse_ts(status.get("updated_utc")) or rows[-1]["end"]
            acts = [classify(r["stage"], r["row"], context)[0] for r in rows]
            was = max(set(acts), key=acts.count)
            pod.add(prio, rows[0]["start"], max(end, rows[-1]["end"]), "failed_attempt", "unit",
                    f"unit {unit.name} did not complete ({why[:80]}); work redone later", [rel(unit / "status.json"), rel(unit / "ledger.jsonl")],
                    "measured", was=was, **extra)
            for r in rows:
                r["failed"] = True
                out.append(r)
            continue
        for r in rows:
            act, key, detail = classify(r["stage"], r["row"], context)
            if r["row"].get("status") == "error":
                err = str(r["row"].get("error", "")).replace("\n", " ")[:80]
                pod.add(prio, r["start"], r["end"], "failed_attempt", key, f"{detail} (failed: {err})", [r["source"]],
                        "measured", was=act, **extra)
            else:
                pod.add(prio, r["start"], r["end"], act, key, detail, [r["source"]], "measured", **extra)
            r["failed"] = r["row"].get("status") == "error"
            out.append(r)
    return out


def steps_timing(units) -> tuple:
    n, s = 0, 0.0
    for unit in units:
        for r in read_jsonl(unit / "steps.jsonl"):
            if isinstance(r.get("seconds"), (int, float)):
                n += 1
                s += r["seconds"]
    return n, s


def arg_after(command, flag):
    for i, a in enumerate(command or []):
        if a == flag and i + 1 < len(command):
            return command[i + 1]
    return ""


def make_job(L: Ledger, pod: Pod, rc: dict, stage_rows: list, units: list):
    if rc is None or rc.get("start") is None:
        return None
    end = rc["end"] or pod.end
    job = Job(pod.run, pod.host, pod.pod_name, rc["name"], arg_after(rc["command"], "--seeds"),
              arg_after(rc["command"], "--arms") or "a0", rc["start"], end, rc.get("exit"), pod.price)
    mine = [r for r in stage_rows if rc["start"] <= r["start"] <= end]
    for r in mine:
        sec = (r["end"] - r["start"]).total_seconds()
        st = r["stage"]
        job.stage_s[st] = job.stage_s.get(st, 0.0) + sec
        row = r["row"]
        n = row.get("steps") if st == "train" else (row.get("prompts") or row.get("answers") or row.get("items")
                                                    or row.get("questions") or row.get("queries"))
        if isinstance(n, (int, float)):
            job.counts[st] = job.counts.get(st, 0) + n
        if st == "train" and isinstance(row.get("steps"), (int, float)):
            job.train_steps += int(row["steps"])
            seg = str(row.get("segment"))
            a, b = job.segments.get(seg, (0.0, 0))
            job.segments[seg] = (a + sec, b + int(row["steps"]))
            for k in ("padded_tokens", "input_tokens", "target_tokens"):
                if isinstance(row.get(k), (int, float)):
                    job.tokens[k] = job.tokens.get(k, 0) + row[k]
        if st == "load_policy":
            job.meta.setdefault("trainable", row.get("trainable_parameters"))
            job.meta.setdefault("attn", row.get("attn_implementation"))
        if st == "generate":
            job.checkpoints += 1
    my_units = sorted({r["unit"] for r in mine})
    unit_dirs = [u for u in units if u.name in my_units]
    job.step_count, job.step_seconds = steps_timing(unit_dirs)
    L.jobs.append(job)
    return job


# ----------------------------------------------------------------------------------------------------------------
# stops and pulls


def find_stop(hd: pathlib.Path, start, latest="pod-latest.json", stops="stops.jsonl", finished="finished.json", before=None):
    """The pod's billed end: RunPod's 'Exited' status change if a refreshed record holds it, else the accepted stop
    request. Returns (time, source, basis) or (None, '', '') while the pod runs."""
    def ok(t):
        return t is not None and t >= start and (before is None or t < before)
    p = hd / latest
    if p.exists():
        f = pod_fields(p)
        kind, t = status_change(f.get("lastStatusChange"))
        if f.get("desiredStatus") == "EXITED" and kind == "Exited" and ok(t):
            return t, rel(p), "measured (RunPod lastStatusChange 'Exited')"
    for s in read_jsonl(hd / stops):
        t = parse_ts(s.get("utc"))
        if s.get("status") == 200 and ok(t):
            return t, rel(hd / stops), "measured (stop request accepted, HTTP 200)"
    p = hd / finished
    if p.exists():
        f = read_json(p)
        stop = f.get("stop")
        try:
            stop = json.loads(stop) if isinstance(stop, str) else stop
        except json.JSONDecodeError:
            stop = None
        t = parse_ts((stop or {}).get("utc")) if isinstance(stop, dict) else None
        if ok(t):
            return t, rel(p), "measured (finisher stop request)"
    return None, "", ""


def pull_windows(pulls_path: pathlib.Path, after=None, before=None):
    """[(start, end, bytes)] from pulls.jsonl; the start comes from the tar name's UTC stamp."""
    out = []
    for p in read_jsonl(pulls_path):
        s, e = tar_stamp(p.get("file", "")), parse_ts(p.get("utc"))
        if s is None or e is None:
            continue
        if after is not None and e < after:
            continue
        if before is not None and e > before:
            continue
        out.append((s, e, p.get("bytes")))
    return out


def gb(b):
    return f"{b / 1e9:.2f} GB" if isinstance(b, (int, float)) and b >= 1e8 else (f"{b / 1e6:.1f} MB" if isinstance(b, (int, float)) else "?")


def paint_finish(pod: Pod, done, done_src, pulls, pulls_src, idle_detail, verify_detail):
    """After the work: [done, first pull start) idle, pulls copy/finish, [last pull end, stop) copy/finish."""
    if done is None or pod.end is None or done >= pod.end:
        return
    if pulls:
        p0, p1 = min(p[0] for p in pulls), max(p[1] for p in pulls)
        p0 = max(p0, done)
        size = " + ".join(gb(p[2]) for p in pulls)
        pod.add(1, done, p0, "idle", "finisher_latency", idle_detail, [done_src, pulls_src], "measured")
        pod.add(1, p0, p1, "copy/finish", "pull",
                f"copy outputs off the pod ({len(pulls)} tar pull{'s' if len(pulls) > 1 else ''}, {size})", [pulls_src], "measured")
        pod.add(1, p1, pod.end, "copy/finish", "verify_and_stop", verify_detail, [pulls_src, pod.end_src], "measured")
    else:
        pod.add(1, done, pod.end, "copy/finish", "verify_and_stop", f"{idle_detail}; copy, verify and stop (no pull record)",
                [done_src, pod.end_src], "measured")


# ----------------------------------------------------------------------------------------------------------------
# headroom round 1 and v2 (same kit)

EVENT_STATE = {
    "checked": ("bootstrap/setup", "send_bundle", "send and unpack the setup bundle (orchestrator log)"),
    "bootstrap-started": ("bootstrap/setup", "bootstrap_log", "bootstrap script (orchestrator log; in round 1 it includes the two-step fixture)"),
    "bootstrap-ready": ("preflight", "fixture", "preflight (orchestrator log)"),
    "bootstrap-finished": ("idle", "orchestrator_gap", "orchestrator between bootstrap and the next step (log)"),
    "preflight-finished": ("idle", "orchestrator_gap", "orchestrator between preflight and the next step (log)"),
    "expected-fixture-recorded": ("idle", "orchestrator_gap", "orchestrator records the expected fixture (log)"),
    "fixture-matches-expected": ("idle", "orchestrator_gap", "orchestrator compares the fixture (log)"),
    "job-started": ("training", "job_log_time", "training job (log time; receipts not retrieved yet)"),
    "jobs-started": ("training", "job_log_time", "training jobs (log time; receipts not retrieved yet)"),
    "lead-started": ("row_scoring", "lead_log_time", "lead pipeline: scores, removal edits, rewrites, edits (log time; receipts not retrieved yet)"),
}


def paint_log_mode(pod: Pod, events: list, ev_src: str, create_src: str):
    """Pods without retrieved receipts: segments between orchestrator events (second resolution)."""
    evs = [(parse_ts(e.get("utc")), e.get("event")) for e in events if e.get("event") in EVENT_STATE or e.get("event") == "checked"]
    evs = [(t, n) for t, n in evs if t is not None and pod.start <= t <= pod.end]
    evs.sort()
    if not evs:
        if pod.running:
            pod.add(1, pod.start, pod.end, "in_progress", "running", "pod running; no orchestrator event yet", [create_src], "provisional")
        return
    pod.add(1, pod.start, evs[0][0], "pod_create_wait", "container_start",
            "pod start until SSH answers and the GPU/timer check passes", [create_src, ev_src], "log-time")
    for i, (t, name) in enumerate(evs):
        nxt = evs[i + 1][0] if i + 1 < len(evs) else pod.end
        act, stage, detail = EVENT_STATE[name]
        if i + 1 == len(evs) and pod.running:
            pod.add(1, t, nxt, "in_progress", "running",
                    f"after '{name}' at {hms(t)} UTC ({act}: {detail}); still running at build time", [ev_src], "provisional")
        else:
            pod.add(1, t, nxt, act, stage, detail, [ev_src], "log-time")


def headroom_run(L: Ledger, run: str, base: pathlib.Path):
    if not base.exists():
        L.warn(f"{run}: {rel(base)} not found")
        return
    plan = read_json(base / "plan.json") if (base / "plan.json").exists() else {}
    roles = {h: (v or {}).get("role", "") for h, v in (plan.get("hosts") or {}).items()}
    for hd in sorted(p for p in (base / "hosts").iterdir() if p.is_dir()):
        host = hd.name
        role = roles.get(host, "")
        for f in sorted(hd.glob("create-result-failed-*.json")):
            r = pod_fields(f)
            L.rec(run, host, role, "failed_attempt", parse_ts(r.get("result_utc")), "pod_create",
                  f"pod create refused (HTTP {r.get('http_status')}): {r.get('error', '')}; no pod, no charge",
                  [rel(f)], "measured", A100, 0.0, was="pod_create_wait")
        if (hd / "pod-attempt1.json").exists():
            headroom_attempt1(L, run, base, hd, host, role)
        if (hd / "pod.json").exists():
            headroom_pod(L, run, base, hd, host, role)


def new_pod(L: Ledger, run, host, role, podrec, rec_src, start_src, end, end_src, end_basis, gpu=A100, price_key="costPerHr"):
    start = parse_ts(podrec.get("lastStartedAt")) or parse_ts(podrec.get("createdAt")) or parse_ts(podrec.get("created_utc"))
    running = end is None
    if running:
        end, end_src, end_basis = max(L.now, start), "build time", "provisional (pod running at build time)"
        cap = parse_ts(podrec.get("cap_stop_utc"))
        for d in DOC_RECORDS:        # a recorded lease can move the stop later than the cap
            if d["run"] == run and d["host"] == host and d.get("new_stop"):
                cap = max(cap, parse_ts(d["new_stop"])) if cap else parse_ts(d["new_stop"])
        if cap is not None and cap < end:
            end, end_src = max(cap, start), "stop-timer cap (pod.json cap_stop_utc)"
            end_basis = "provisional (no stop record yet; billed to its stop-timer cap, which ends the pod at the latest)"
    price = podrec.get(price_key)
    if price is None:
        price = podrec.get("cost")
    disk = float(podrec.get("containerDiskInGb") or podrec.get("disk") or 0) + float(podrec.get("volumeInGb") or 0)
    pod = Pod(run, host, role, podrec.get("name") or host, podrec.get("gpu_id") or gpu, int(podrec.get("gpu_count") or 1),
              float(price), rec_src, start, start_src, end, end_src, end_basis, running, disk, float(podrec.get("volumeInGb") or 0))
    L.pods.append(pod)
    return pod


def headroom_pod(L: Ledger, run: str, base: pathlib.Path, hd: pathlib.Path, host: str, role: str):
    podrec = pod_fields(hd / "pod.json")
    start = parse_ts(podrec.get("lastStartedAt"))
    end, end_src, end_basis = find_stop(hd, start)
    pod = new_pod(L, run, host, role, podrec, rel(hd / "pod.json"), rel(hd / "pod.json"), end, end_src, end_basis)
    pod.pod_name = podrec.get("name", host).replace("attribution-", "")
    ev_src = rel(hd / "orchestrate.jsonl")
    events = read_jsonl(hd / "orchestrate.jsonl")
    tree = retrieved(base) / host / "tree"
    boot = receipt(tree / "worker-bootstrap-process-001") if tree.exists() else None
    if boot is None or boot["start"] is None:
        paint_log_mode(pod, events, ev_src, rel(hd / "pod.json"))
        return
    # before the first receipt
    checked = sorted(t for t in (parse_ts(e.get("utc")) for e in events if e.get("event") == "checked") if t and t >= pod.start)
    if checked:
        pod.add(1, pod.start, checked[0], "pod_create_wait", "container_start",
                "pod start until SSH answers and the GPU/timer check passes", [rel(hd / "pod.json"), ev_src], "log-time")
        pod.add(1, checked[-1], boot["start"], "bootstrap/setup", "send_bundle",
                "send and unpack the setup bundle (orchestrator)", [ev_src, boot["source"]], "log-time")
    else:
        pod.add(1, pod.start, boot["start"], "pod_create_wait", "container_start",
                "pod start, SSH and bundle transfer (no SSH-ready record)", [rel(hd / "pod.json"), boot["source"]], "measured")
    pod.add(2, boot["start"], boot["end"] or pod.end, "bootstrap/setup", "bootstrap_script", "bootstrap script", [boot["source"]],
            "measured" if boot["end"] else "provisional")
    setup = receipt(tree / "setup-001")
    dl = read_json(tree / "model-download-receipt.json").get("elapsed_s") if (tree / "model-download-receipt.json").exists() else None
    if setup:
        pod.add(3, setup["start"], setup["end"] or pod.end, "bootstrap/setup", "setup_and_fetch",
                "setup_and_fetch: venv, packages and pinned model downloads" + (f" (downloads {dl:.0f} s per model-download-receipt.json)" if dl else ""),
                [setup["source"]], "measured")
    nxt_after_boot = []      # top-level steps after the bootstrap, for the orchestrator gaps
    # preflight (round 1: inside the bootstrap; v2: its own driver)
    pf_outer = receipt(tree / "preflight-outer")
    if pf_outer:
        pod.add(2, pf_outer["start"], pf_outer["end"] or pod.end, "preflight", "driver", "preflight driver (preflight_v2.py)",
                [pf_outer["source"]], "measured")
        nxt_after_boot.append(pf_outer)
    for pdir in sorted(tree.glob("preflight-process-*")):
        rc = receipt(pdir)
        if not rc:
            continue
        cmd = rc["command"]
        out = arg_after(cmd, "--out")
        recipe = pathlib.Path(arg_after(cmd, "--recipe")).stem
        ledger_dir = tree / out if out else None
        failed = rc["exit"] not in (0, None)
        if failed:
            why = "error"
            err = (tree / out / "error.txt") if out else None
            if err and err.exists():
                txt = err.read_text(errors="replace")
                why = "CUDA out of memory" if "OutOfMemoryError" in txt else txt.strip().splitlines()[-1][:80]
            pod.add(3, rc["start"], rc["end"] or pod.end, "failed_attempt", "fixture",
                    f"preflight with recipe {recipe} failed (exit {rc['exit']}: {why})", [rc["source"]], "measured", was="preflight")
        else:
            has_ledger = bool(ledger_dir and (ledger_dir / "ledger.jsonl").exists())
            pod.add(3, rc["start"], rc["end"] or pod.end, "preflight", "process_overhead" if has_ledger else "fixture",
                    f"two-step A100 fixture and checks (recipe {recipe})", [rc["source"]], "measured")
            if has_ledger:
                paint_units(pod, [ledger_dir], "preflight")
            ver = (ledger_dir / "verification.json") if ledger_dir else None
            if ver and ver.exists():
                v = read_json(ver)
                proj = ((v.get("evaluation_timing") or {}).get("projection_to_dev_bank") or {})
                if proj:
                    L.projections.append({"run": run, "host": host, "source": rel(ver),
                                          "projected_s": proj.get("projected_evaluation_seconds"),
                                          "stages": {k: (s.get("projected_seconds"), s.get("bank_units"), s.get("sample_seconds"), s.get("sample_units"))
                                                     for k, s in (proj.get("stages") or {}).items()}})
    # job
    job_outer = receipt(tree / "job-outer")
    job_done_path = tree / "JOB-DONE.json"
    job_done = parse_ts(read_json(job_done_path).get("utc")) if job_done_path.exists() else None
    job_procs = [receipt(p) for p in sorted(tree.glob("job-process-*"))]
    job_procs = [r for r in job_procs if r]
    units = sorted(p for p in (tree / "round1").glob("*") if (p / "ledger.jsonl").exists()) if (tree / "round1").exists() else []
    done, done_src = None, ""
    if job_procs:
        first = job_outer or job_procs[0]
        nxt_after_boot.append(first)
        if job_outer:
            pod.add(2, job_outer["start"], job_outer["end"] or pod.end, "training", "runner",
                    "job runner (job_runner.py): start, then on-pod verify of the sealed unit", [job_outer["source"]], "measured")
            done, done_src = job_outer["end"], job_outer["source"]
        elif job_done:
            pod.add(2, job_procs[0]["start"], job_done, "training", "runner",
                    "job runner: on-pod verify of the sealed unit until JOB-DONE.json", [job_procs[0]["source"], rel(job_done_path)], "measured")
            done, done_src = job_done, rel(job_done_path)
        for rc in job_procs:
            pod.add(3, rc["start"], rc["end"] or pod.end, "training", "job_overhead",
                    "engine process overhead: interpreter start, state saves between segments, unit seal", [rc["source"]], "measured")
        stage_rows = paint_units(pod, units, "job")
        for rc in job_procs:
            make_job(L, pod, rc, stage_rows, units)
    # lead
    steps = [receipt(p) for p in sorted(tree.glob("lead-process-*"), key=lambda p: int(re.search(r"lead-process-(\d+)", p.name).group(1)))]
    steps = [r for r in steps if r and r["start"]]
    if steps:
        nxt_after_boot.append(steps[0])
        lead_done_path = tree / "LEAD-DONE.json"
        lead_done = parse_ts(read_json(lead_done_path).get("utc")) if lead_done_path.exists() else None
        for i, rc in enumerate(steps):
            name = rc["name"]
            nxt = steps[i + 1]["start"] if i + 1 < len(steps) else (lead_done or rc["end"] or pod.end)
            if "score" in name:
                act, stage, detail = "row_scoring", "process_overhead", "scoring process: start-up and teardown"
            elif "rewrite" in name:
                act, stage, detail = "rewriting", "process_overhead", "rewrite process: start-up and teardown"
            else:
                act, stage, detail = "edit_building", "build_edits", f"build edit files ({name.split('-', 3)[-1]})"
            pod.add(2, rc["start"], max(nxt, rc["end"] or nxt), act, stage, detail, [rc["source"]], "measured")
        done, done_src = (lead_done, rel(lead_done_path)) if lead_done else (steps[-1]["end"], steps[-1]["source"])
        for folder, ctx in (("scores-001", "scores"), ("rewrites-001", "rewrites")):
            if (tree / folder / "ledger.jsonl").exists():
                rows = paint_units(pod, [tree / folder], ctx)
                for r in rows:
                    if r["stage"] in ("score_rows", "generate_rewrites"):
                        step = next((s for s in steps if ("score" in s["name"]) == (r["stage"] == "score_rows")
                                     and ("rewrite" in s["name"]) == (r["stage"] == "generate_rewrites")), None)
                        L.lead.append({"run": run, "host": host, "pod": pod.pod_name, "stage": r["stage"],
                                       "attn": lead_attention(tree / folder, step, r["stage"]),
                                       "seconds": (r["end"] - r["start"]).total_seconds(), "rows": r["row"].get("rows"),
                                       "accepted": r["row"].get("accepted"), "price": pod.price, "source": r["source"],
                                       "process_s": next((s["elapsed"] for s in steps if (("score" in s["name"]) == (r["stage"] == "score_rows"))
                                                          and (("rewrite" in s["name"]) == (r["stage"] == "generate_rewrites"))), None)})
    # orchestrator gaps between the bootstrap and the top-level steps
    tops = [boot] + sorted(nxt_after_boot, key=lambda r: r["start"])
    for a, b in zip(tops, tops[1:]):
        if a["end"] and b["start"] and b["start"] > a["end"]:
            pod.add(1, a["end"], b["start"], "idle", "orchestrator_gap",
                    "orchestrator: poll for the done marker (60 s), fixture/edit checks, send plan and inputs",
                    [a["source"], b["source"]], "measured")
    # after the work
    if done is not None and not pod.running:
        pulls = pull_windows(retrieved(base) / host / "pulls.jsonl", after=done, before=pod.end + dt.timedelta(seconds=5))
        paint_finish(pod, done, done_src, pulls, rel(retrieved(base) / host / "pulls.jsonl"),
                     "finisher detection latency (poll interval)" + ("; then the edit files are collected" if steps else ""),
                     "local unpack and check, then the stop request")
    elif pod.running:
        last = max([r["end"] for r in [boot] + nxt_after_boot if r.get("end")] + [pod.start])
        pod.add(1, last, pod.end, "in_progress", "running", "pod running at build time after its last retrieved receipt",
                [ev_src], "provisional")


def headroom_attempt1(L: Ledger, run: str, base: pathlib.Path, hd: pathlib.Path, host: str, role: str):
    """Round 1: the first pod of a host that was replaced (no receipts were retrieved from it)."""
    podrec = pod_fields(hd / "pod-attempt1.json")
    start = parse_ts(podrec.get("lastStartedAt"))
    cur = pod_fields(hd / "pod.json") if (hd / "pod.json").exists() else {}
    before = parse_ts(cur.get("lastStartedAt"))
    end, end_src, end_basis = find_stop(hd, start, latest="pod-latest-attempt1.json", before=before)
    if end is None and (hd / "attempt-1.json").exists():
        a = read_json(hd / "attempt-1.json")
        end, end_src, end_basis = parse_ts(a.get("stopped_utc")), rel(hd / "attempt-1.json"), "measured (operator attempt record)"
    pod = new_pod(L, run, host, role, podrec, rel(hd / "pod-attempt1.json"), rel(hd / "pod-attempt1.json"), end, end_src, end_basis)
    pod.pod_name = podrec.get("name", host).replace("attribution-", "")
    why = read_json(hd / "attempt-1.json").get("why", "") if (hd / "attempt-1.json").exists() else ""
    pod.note = why
    ev_src = rel(hd / "orchestrate-attempt1.jsonl")
    ev = {e.get("event"): parse_ts(e.get("utc")) for e in read_jsonl(hd / "orchestrate-attempt1.jsonl")}
    ev_rows = read_jsonl(hd / "orchestrate-attempt1.jsonl")
    src0 = rel(hd / "create-result-attempt1.json")
    if role != "lead":
        # a discarded attempt: every billed second is a failed attempt; 'was' says what the pod was doing
        t1, t2, t3 = ev.get("checked"), ev.get("bootstrap-started"), ev.get("bootstrap-finished")
        mins = next((e.get("result") for e in ev_rows if e.get("event") == "bootstrap-finished"), "")
        pod.add(1, pod.start, t1, "failed_attempt", "container_start", "pod start until SSH and GPU/timer check (attempt 1, discarded)",
                [src0, ev_src], "log-time", was="pod_create_wait")
        pod.add(1, t1, t2, "failed_attempt", "send_bundle", "send and unpack the setup bundle (attempt 1, discarded)",
                [ev_src], "log-time", was="bootstrap/setup")
        pod.add(1, t2, t3, "failed_attempt", "bootstrap_script", f"bootstrap incl. two-step fixture ({mins}) (attempt 1, discarded)",
                [ev_src], "log-time", was="bootstrap/setup+preflight")
        pod.add(1, t3, pod.end, "failed_attempt", "waiting_for_inputs",
                "idle, waiting for the removal edit files; stopped to save money and recreated later (attempt 1)",
                [ev_src, end_src, rel(base / "decisions.jsonl")], "log-time", was="idle")
        return
    # the first lead: its scores and removal edits were used; its rewriting was lost at the cap. Receipts were not
    # retrieved, so the split is estimated from the replacement lead's measured, byte-identical steps.
    t_checked, t_bs, t_bf, t_fix = ev.get("checked"), ev.get("bootstrap-started"), ev.get("bootstrap-finished"), ev.get("expected-fixture-recorded")
    res = next((e.get("result", "") for e in ev_rows if e.get("event") == "bootstrap-finished"), "")
    m = re.search(r"min ([\d.]+)", res)
    boot_min = float(m.group(1)) if m else None
    ver = hd / "verification-attempt1.json"
    pre_s = read_json(ver).get("elapsed_s") if ver.exists() else None
    tree2 = retrieved(base) / host / "tree"
    sc = receipt(tree2 / "lead-process-1-scores")
    ed = receipt(tree2 / "lead-process-2-edits-removal")
    ev2 = {e.get("event"): parse_ts(e.get("utc")) for e in read_jsonl(hd / "orchestrate.jsonl")}
    lag = (sc["start"] - ev2["fixture-matches-expected"]).total_seconds() if sc and ev2.get("fixture-matches-expected") else 15.0
    pod.add(1, pod.start, t_checked, "pod_create_wait", "container_start", "pod start until SSH and GPU/timer check (first lead)",
            [src0, ev_src], "log-time")
    pod.add(1, t_checked, t_bs, "bootstrap/setup", "send_bundle", "send and unpack the setup bundle (first lead)", [ev_src], "log-time")
    boot_end = t_bs + dt.timedelta(minutes=boot_min) if (t_bs and boot_min) else t_bf
    pre_start = boot_end - dt.timedelta(seconds=pre_s) if pre_s else boot_end
    pod.add(1, t_bs, pre_start, "bootstrap/setup", "setup_and_fetch",
            f"bootstrap script with generator download (first lead; end = bootstrap-started + {boot_min} min reported by the probe)",
            [ev_src], "estimated")
    pod.add(1, pre_start, boot_end, "preflight", "fixture",
            f"two-step A100 fixture ({pre_s:.0f} s per verification-attempt1.json elapsed_s; placed at the end of the bootstrap)" if pre_s else "two-step A100 fixture",
            [rel(ver), ev_src], "estimated")
    pod.add(1, boot_end, t_fix, "idle", "orchestrator_gap", "orchestrator: probe interval, fetch and record the expected fixture",
            [ev_src], "estimated")
    s0 = t_fix + dt.timedelta(seconds=lag)
    pod.add(1, t_fix, s0, "idle", "orchestrator_gap",
            f"orchestrator: send plan, start the lead pipeline (start time not recorded; {lag:.0f} s as measured on the replacement lead)",
            [ev_src, sc["source"] if sc else ""], "estimated")
    if sc and ed:
        s1 = s0 + dt.timedelta(seconds=sc["elapsed"])
        s2 = s1 + dt.timedelta(seconds=(ed["end"] - sc["end"]).total_seconds())
        pod.add(1, s0, s1, "row_scoring", "score_rows",
                f"row scoring, 9,788 rows (first lead; duration = the replacement lead's measured {sc['elapsed']:.0f} s for byte-identical scores)",
                [ev_src, sc["source"]], "estimated")
        pod.add(1, s1, s2, "edit_building", "build_edits", "removal edit files (first lead; used by the removal hosts)",
                [ed["source"]], "estimated")
        pod.add(1, s2, pod.end, "failed_attempt", "generate_rewrites",
                "rewrite generation cut off by the operator-set 2.5 h stop-timer cap; partial rewrites stayed on the volume, unused",
                [rel(hd / "attempt-1.json"), rel(base / "decisions.jsonl")], "estimated", was="rewriting")
    else:
        pod.add(1, s0, pod.end, "row_scoring", "lead_log_time", "lead pipeline (no receipts; split unknown)", [ev_src], "log-time")
    rr = hd / "restart-result-attempt1.json"
    if rr.exists():
        r = read_json(rr)
        L.rec(run, host, role, "failed_attempt", parse_ts(r.get("utc")), "restart",
              f"restart of the stopped first lead with a new 4 h cap: patch HTTP {r.get('patch_status')}, start HTTP {r.get('start_status')} "
              f"(no free GPU on its machine); pod stayed stopped; no GPU charge", [rel(rr), rel(hd / "restart-intent-attempt1.json")],
              "measured", A100, 0.0, was="restart")


def lead_attention(folder: pathlib.Path, step, stage: str):
    """Attention implementation of the scoring guard (from the recipe named in the step's command) or of the rewrite
    generator (from the rewrite job's config)."""
    try:
        if stage == "generate_rewrites" and (folder / "job.json").exists():
            return ((read_json(folder / "job.json").get("config") or {}).get("generator") or {}).get("attn_implementation")
        recipe = arg_after(step["command"], "--recipe") if step else ""
        if recipe and (ROOT / recipe).exists():
            return (read_json(ROOT / recipe).get("guard") or {}).get("attn_implementation")
    except (OSError, json.JSONDecodeError, AttributeError):
        return None
    return None


def tag_repeats(pod: Pod, until: dt.datetime, reason: str):
    for i, iv in enumerate(pod.ivs):
        if iv.end <= until and iv.activity not in ("failed_attempt",):
            pod.ivs[i] = Iv(iv.prio, iv.start, iv.end, iv.activity, iv.stage, iv.detail, iv.sources, iv.basis,
                            iv.extra + (("overhead", reason),))


# ----------------------------------------------------------------------------------------------------------------
# 4 October: dev-matrix-002


def devmatrix_run(L: Ledger):
    run, base = "study-v2-20261004", TMP / "study-v2-20261004"
    if not base.exists():
        L.warn(f"{run}: not found")
        return
    for hd in sorted(p for p in (base / "hosts").iterdir() if p.is_dir()):
        host = hd.name
        for f in sorted(hd.glob("create-result-failed-*.json")):
            r = pod_fields(f)
            L.rec(run, host, "job", "failed_attempt", parse_ts(r.get("result_utc")), "pod_create",
                  f"pod create refused (HTTP {r.get('http_status')}): {r.get('error', '')}; no pod, no charge", [rel(f)],
                  "measured", A100, 0.0, was="pod_create_wait")
        a1 = hd / "attempt-1"
        if (a1 / "pod.json").exists():
            podrec = pod_fields(a1 / "pod.json")
            start = parse_ts(podrec.get("lastStartedAt"))
            end, end_src, end_basis = find_stop(a1, start)
            pod = new_pod(L, run, host, "job", podrec, rel(a1 / "pod.json"), rel(a1 / "pod.json"), end, end_src, end_basis)
            pod.pod_name = podrec.get("name", host).replace("attribution-", "")
            pod.add(1, pod.start, pod.end, "failed_attempt", "container_start",
                    "container never started (no SSH address after 20 minutes); stopped and replaced",
                    [rel(a1 / "pod.json"), end_src, "research/experiments/2026-10-04-dev-matrix-002-results.md"], "measured",
                    was="pod_create_wait")
        if not (hd / "pod.json").exists():
            continue
        podrec = pod_fields(hd / "pod.json")
        start = parse_ts(podrec.get("lastStartedAt"))
        end, end_src, end_basis = find_stop(hd, start)
        pod = new_pod(L, run, host, "job", podrec, rel(hd / "pod.json"), rel(hd / "pod.json"), end, end_src, end_basis)
        pod.pod_name = podrec.get("name", host).replace("attribution-", "")
        ev_src = rel(hd / "orchestrate.jsonl")
        events = read_jsonl(hd / "orchestrate.jsonl")
        tree = retrieved(base) / host / "tree"
        boot = receipt(tree / "worker-bootstrap-process-001")
        if boot is None:
            paint_log_mode(pod, events, ev_src, rel(hd / "pod.json"))
            continue
        checked = sorted(t for t in (parse_ts(e.get("utc")) for e in events if e.get("event") == "checked") if t)
        if checked:
            pod.add(1, pod.start, checked[0], "pod_create_wait", "container_start",
                    "pod start until SSH answers and the GPU/timer check passes", [rel(hd / "pod.json"), ev_src], "log-time")
            if len(checked) > 1:
                pod.add(1, checked[0], checked[-1], "failed_attempt", "send_bundle",
                        "first setup-bundle transfer failed; retried after a re-check", [ev_src], "log-time", was="bootstrap/setup")
            pod.add(1, checked[-1], boot["start"], "bootstrap/setup", "send_bundle", "send and unpack the setup bundle (orchestrator)",
                    [ev_src, boot["source"]], "log-time")
        else:
            pod.add(1, pod.start, boot["start"], "pod_create_wait", "container_start",
                    "pod start, SSH and bundle transfer (no SSH-ready record for this host)", [rel(hd / "pod.json"), boot["source"]], "measured")
        pod.add(2, boot["start"], boot["end"], "bootstrap/setup", "bootstrap_script", "bootstrap script (worker_bootstrap_v3.sh)",
                [boot["source"]], "measured")
        log = tree / "worker-bootstrap-process-001" / "process.log"
        for line in (log.read_text().splitlines() if log.exists() else [])[:4]:
            try:
                sub = receipt_from_dict(json.loads(line), rel(log), "sub")
            except json.JSONDecodeError:
                continue
            if not sub:
                continue
            cmd = " ".join(sub["command"])
            if "setup_and_fetch" in cmd:
                pod.add(3, sub["start"], sub["end"], "bootstrap/setup", "setup_and_fetch", "setup_and_fetch: venv, packages, model downloads",
                        [rel(log)], "measured")
            elif "cuda_preflight" in cmd:
                pod.add(3, sub["start"], sub["end"], "preflight", "fixture", "two-step A100 fixture (cuda_preflight.py)", [rel(log)], "measured")
        outer = receipt(tree / "dev-matrix-outer-002")
        if outer is None:
            continue
        hold = host == "dev05"
        pod.add(1, boot["end"], outer["start"], "idle", "hold" if hold else "orchestrator_gap",
                ("held after its bootstrap until the matrix started (first host, one-pod validation; reason not in the run records)"
                 if hold else "orchestrator: poll (60 s), send the matrix assets and runner"), [boot["source"], outer["source"]], "measured")
        pod.add(2, outer["start"], outer["end"], "training", "runner", "job runner (run_dev_matrix_v2.py): two jobs in sequence",
                [outer["source"]], "measured")
        procs = [receipt(p) for p in sorted(tree.glob("dev-matrix-process-*-002"))]
        procs = [p for p in procs if p]
        for rc in procs:
            pod.add(3, rc["start"], rc["end"], "training", "job_overhead",
                    "engine process overhead: interpreter start, state saves, unit seals", [rc["source"]], "measured")
        units = sorted(p for p in (tree / "dev-matrix-002").glob("*") if (p / "ledger.jsonl").exists())
        stage_rows = paint_units(pod, units, "job")
        for rc in procs:
            make_job(L, pod, rc, stage_rows, units)
        if not pod.running:
            pulls = pull_windows(retrieved(base) / host / "pulls.jsonl", after=outer["end"], before=pod.end + dt.timedelta(seconds=5))
            pulls = pulls[-1:] if pulls else []
            paint_finish(pod, outer["end"], outer["source"], pulls, rel(retrieved(base) / host / "pulls.jsonl"),
                         "monitor/finisher cycles (300 s) until every unit copy is verified; includes earlier monitor pulls",
                         "local unpack and engine verify, then the stop request")


# ----------------------------------------------------------------------------------------------------------------
# 2 October: pilot and study-v2 (dev-matrix-001)


def pilot_run(L: Ledger):
    run, base = "runpod-pilot-20261002", TMP / "runpod-pilot-20261002"
    if not (base / "pod.json").exists():
        L.warn(f"{run}: not found")
        return
    podrec = pod_fields(base / "pod.json")
    term = read_json(base / "termination.json") if (base / "termination.json").exists() else {}
    end = parse_ts(term.get("requested_at"))
    pod = new_pod(L, run, "pilot", "pilot", podrec, rel(base / "pod.json"), rel(base / "pod.json"), end,
                  rel(base / "termination.json"), "measured (termination request, HTTP 204; pod deleted)", gpu="NVIDIA RTX A5000", price_key="cost")
    pod.pod_name = podrec.get("name", "pilot").replace("attribution-", "")
    pod.deleted_at_end = True
    led = base / "retrieved" / "run-cuda-001"
    rows, status = load_stages(led)
    if rows:
        runner_end = read_json(led / "runner_end.json").get("elapsed_s") if (led / "runner_end.json").exists() else None
        t0 = rows[0]["start"] - dt.timedelta(seconds=rows[0]["row"].get("start_s", 0))
        t1 = t0 + dt.timedelta(seconds=runner_end) if runner_end else rows[-1]["end"]
        pod.add(1, pod.start, t0, "bootstrap/setup", "setup_and_preflight",
                "pod start, package install, model downloads (4.7 s per download-receipt.json), CUDA tests and preflight; "
                "the split is not recorded", [rel(base / "pod.json"), rel(base / "setup-evidence" / "download-receipt.json")], "estimated")
        pod.add(2, t0, t1, "training", "job_overhead", "runner overhead (absolute times from the ledger's process clock, +-0.5 s)",
                [rel(led / "runner_end.json")], "measured")
        paint_units(pod, [led], "pilot")
        pod.add(1, t1, pod.end, "copy/finish", "terminate", "retrieve results, verify artifacts, terminate (delete) the pod",
                [rel(base / "termination.json")], "measured")
    for f in ("billing-final.json", "billing-interim.json"):
        if (base / f).exists():
            b = read_json(base / f)
            L.billing.append({"run": run, "source": rel(base / f), "records": len(b.get("records") or []),
                              "total": ((b.get("metadata") or {}).get("totals") or {}).get("totalAmount")})


def study0210_run(L: Ledger):
    run, base = "study-v2-20261002", TMP / "study-v2-20261002"
    if not (base / "pod.json").exists():
        L.warn(f"{run}: not found")
        return
    statuses = sorted(base.glob("status-*.json"))
    status = read_json(statuses[-1]) if statuses else {}
    hosts = [("lead", base)] + [(d.name, d) for d in sorted((base / "workers").glob("dev*")) if (d / "pod.json").exists()]
    for host, hd in hosts:
        podrec = pod_fields(hd / "pod.json")
        rr = base / "retrieved-dev-matrix" / host / "retrieval-process-receipt.json"
        end = parse_ts(read_json(rr).get("utc")) if rr.exists() else parse_ts("2026-10-02T18:18:27Z")
        end_src = rel(rr) if rr.exists() else "research/experiments/2026-10-02-runpod-credit-incident.md"
        pod = new_pod(L, run, host, "lead" if host == "lead" else "worker", podrec, rel(hd / "pod.json"), rel(hd / "pod.json"),
                      end, end_src, "estimated (upper bound: the local retrieval found SSH closed; pods terminated when credits ran out)",
                      price_key="cost")
        pod.pod_name = podrec.get("name", host).replace("attribution-", "")
        pod.deleted_at_end = True
        lost = ("dev-matrix-001 jobs (seed 1101 q/e1 sealed, e3 running at 18:11 per " + rel(statuses[-1]) +
                "); every output lost when credits ran out; no archive retrieved") if statuses else "dev-matrix-001 jobs; outputs lost"
        tree = retrieved(base, "retrieved-calibration") / host / "tree"
        if tree.exists():
            names = ["setup-001", "worker-process-001", "calibration-process-001", "root-resume-process-002", "cap2048-process-all",
                     "cap2048-process-q", "cap2048-process-e1", "cap2048-process-e3"]
            rcs = {n: receipt(tree / n) for n in names if (tree / n).exists()}
            rcs = {n: r for n, r in rcs.items() if r and r["start"]}
            first = min(r["start"] for r in rcs.values())
            last = max(r["end"] for r in rcs.values() if r["end"])
            pod.add(1, pod.start, first, "pod_create_wait", "container_start",
                    "pod start, SSH and bundle transfer (no SSH-ready record)", [rel(hd / "pod.json")], "measured")
            if "worker-process-001" in rcs:
                r = rcs["worker-process-001"]
                pod.add(2, r["start"], r["end"], "bootstrap/setup", "worker_script", "worker script (setup, preflight, calibration)",
                        [r["source"]], "measured")
            if "setup-001" in rcs:
                r = rcs["setup-001"]
                pod.add(3, r["start"], r["end"], "bootstrap/setup", "setup_and_fetch", "setup_and_fetch: venv, packages, model downloads",
                        [r["source"]], "measured")
            if "worker-process-001" in rcs and "setup-001" in rcs and "calibration-process-001" in rcs:
                pod.add(3, rcs["setup-001"]["end"], rcs["calibration-process-001"]["start"], "preflight", "fixture",
                        "two-step CUDA fixture (cuda_preflight.py) inside the worker script; window between receipts",
                        [rcs["setup-001"]["source"], rcs["calibration-process-001"]["source"]], "measured")
                if (tree / "cuda-preflight-001" / "ledger.jsonl").exists():
                    paint_units(pod, [tree / "cuda-preflight-001"], "preflight")
            for n, detail in (("calibration-process-001", "calibration job (micro-batch 2 recipe)"),
                              ("root-resume-process-002", "guard crossover check, then the a0 calibration resumed (e1, e3)")):
                if n in rcs:
                    r = rcs[n]
                    pod.add(3, r["start"], r["end"], "training", "job_overhead", f"{detail}: process overhead" +
                            (f" (exit {r['exit']})" if r["exit"] not in (0, None) else ""), [r["source"]], "measured")
            if "cap2048-process-all" in rcs:
                r = rcs["cap2048-process-all"]
                pod.add(2, r["start"], r["end"], "evaluation", "driver", "cap-2048 re-evaluation of saved states (driver)", [r["source"]], "measured")
                for ck in ("q", "e1", "e3"):
                    if f"cap2048-process-{ck}" in rcs:
                        s = rcs[f"cap2048-process-{ck}"]
                        pod.add(3, s["start"], s["end"], "evaluation", "eval_state_overhead", f"eval-state at a 2048-token cap ({ck}): process overhead",
                                [s["source"]], "measured")
            units = sorted(p for p in (tree / "calibration-001").glob("*") if (p / "ledger.jsonl").exists()) if (tree / "calibration-001").exists() else []
            stage_rows = paint_units(pod, units, "job")
            paint_units(pod, sorted(p for p in tree.glob("cap2048-*") if (p / "ledger.jsonl").exists()), "evalstate")
            for n in ("calibration-process-001", "root-resume-process-002"):
                if n in rcs:
                    j = make_job(L, pod, rcs[n], stage_rows, units)
                    if j:
                        j.arm = "a0" if host == "lead" else "calibration"
            if host == "lead" and (base / "retrieved-cuda").exists():
                secs = []
                for f in ("preflight-verification.json", "restart-verification.json", "batch-diagnostic.json"):
                    if (base / "retrieved-cuda" / f).exists():
                        secs.append(f"{f.split('.')[0]} {read_json(base / 'retrieved-cuda' / f).get('elapsed_s', 0):.0f} s")
                if "setup-001" in rcs and "calibration-process-001" in rcs:
                    pod.add(1, rcs["setup-001"]["end"], rcs["calibration-process-001"]["start"], "unattributed", "gap",
                            "CUDA preflight and diagnostics ran in this window (" + ", ".join(secs) +
                            "; start times not recorded); the rest is operator time between steps", [rel(base / "retrieved-cuda")], "measured")
            pod.add(1, last, pod.end, "failed_attempt", "training", lost, [end_src, rel(statuses[-1]) if statuses else ""],
                    "estimated", was="training")
        else:
            st = ((status.get("hosts") or {}).get(host) or {}).get("worker-bootstrap-process-001")
            boot = receipt_from_dict(st, rel(statuses[-1]), "worker-bootstrap") if isinstance(st, dict) else None
            if boot:
                pod.add(1, pod.start, boot["start"], "failed_attempt", "container_start", "pod start, SSH and bundle transfer (pod's work later lost)",
                        [rel(hd / "pod.json"), boot["source"]], "measured", was="pod_create_wait")
                pod.add(1, boot["start"], boot["end"], "failed_attempt", "bootstrap_script", "bootstrap incl. fixture (pod's work later lost)",
                        [boot["source"]], "measured", was="bootstrap/setup")
                pod.add(1, boot["end"], pod.end, "failed_attempt", "training", lost, [end_src, boot["source"]], "estimated", was="training")
            else:
                pod.add(1, pod.start, pod.end, "failed_attempt", "training", lost, [end_src], "estimated", was="training")
        for f in sorted(hd.glob("create-intent-failed*.json")) if host != "lead" else []:
            r = read_json(f)
            when = parse_ts(r.get("epoch"))
            rc = hd / "reconciliation-before-retry.json"
            code = read_json(rc).get("prior_http_status") if rc.exists() else None
            L.rec(run, host, "worker", "failed_attempt", when, "pod_create",
                  f"pod create failed" + (f" (HTTP {code})" if code else " (status not recorded)") + "; no matching pod existed afterwards; no charge",
                  [rel(f), rel(rc) if rc.exists() else ""], "measured", A100, 0.0, was="pod_create_wait")
    b = base / "billing-latest.json"
    if b.exists():
        d = read_json(b)
        tot = (d.get("metadata") or {}).get("totals") or {}
        L.billing.append({"run": run, "source": rel(b), "records": len(d.get("records") or []), "total": tot.get("totalAmount"),
                          "gpu": tot.get("gpuAmount"), "disk": tot.get("diskAmount"), "pods": (d.get("metadata") or {}).get("uniquePodCount")})
    est = sorted(base.glob("spend-estimate-*.json"))
    if est:
        e = read_json(est[-1])
        L.facts["oct2_spend_estimate"] = (e.get("total_estimated_gpu_dollars"), e.get("utc"), rel(est[-1]))


def podtimer_run(L: Ledger):
    run, base = "pod-timer-check-20261004", TMP / "pod-timer-check-20261004"
    if not (base / "pod.json").exists():
        L.warn(f"{run}: not found")
        return
    podrec = pod_fields(base / "pod.json")
    res = read_json(base / "result.json") if (base / "result.json").exists() else {}
    kind, end = status_change(res.get("last_status_change"))
    gpu = "unknown"
    pre = read_json(base / "precheck.json") if (base / "precheck.json").exists() else {}
    match = [o.get("id") for o in pre.get("offers") or [] if o.get("secure_price") == podrec.get("costPerHr")]
    inferred = ""
    if len(match) == 1:
        gpu = match[0]
        inferred = "gpu_type inferred: the only offer at this price in precheck.json (the pod record has no GPU field)"
    pod = new_pod(L, run, "check", "check", podrec, rel(base / "pod.json"), rel(base / "pod.json"), end, rel(base / "result.json"),
                  "measured (RunPod lastStatusChange 'Exited', self-stopped at its cap)", gpu=gpu)
    pod.gpu_type = gpu
    pod.note = inferred
    pod.pod_name = podrec.get("name", "check").replace("attribution-", "")
    pod.add(1, pod.start, pod.end, "preflight", "infrastructure_check",
            "infrastructure check: the in-pod stop timer stops the pod at its 15-minute cap (the pod runs nothing else)",
            [rel(base / "pod.json"), rel(base / "result.json")], "measured")
    for f in ("precheck.json", "after.json"):
        if (base / f).exists():
            d = read_json(base / f)
            L.snapshots.append({"utc": parse_ts(d.get("utc")), "balance": d.get("client_balance"), "spend_per_hr": d.get("current_spend_per_hr"),
                                "precision": "exact", "source": rel(base / f), "running": []})


# ----------------------------------------------------------------------------------------------------------------
# records that exist only in documents (checked against the text on every run)

DOC_RECORDS = [
    {"run": "headroom-v2", "host": "val05", "role": "first", "when": "2026-10-05T19:06:17Z",
     "detail": "operator lease 20261005T190617Z-d828d9c18523cd86 moved the stop-timer stop from the 21:53 cap to 23:15:04 "
               "(no restart); the finisher still stopped the pod when the job ended",
     "source": ".ai/handoffs/2026-10-06-general-implementation.md", "quote": "extended by an operator lease to 23:15:04",
     "new_stop": "2026-10-05T23:15:04Z",
     "also": ["research/experiments/2026-10-05-headroom-v2-workplan.md", "tmp/headroom-v2/hosts/val05/pod.json"]},
    {"run": "headroom-v2", "host": "cal10", "role": "job", "when": "2026-10-05T19:32:00Z",
     "detail": "operator lease moved the stop-timer stop from the 22:07 cap to 23:40 (time to the minute, per the workplan); "
               "the finisher still stopped the pod when the job ended",
     "source": "research/experiments/2026-10-05-headroom-v2-workplan.md", "quote": "operator leases moved the stop times to 23:15 (val05) and 23:40 (cal10)",
     "new_stop": "2026-10-05T23:40:00Z",
     "also": ["tmp/headroom-v2/hosts/cal10/pod.json"]},
]


def doc_records(L: Ledger):
    for d in DOC_RECORDS:
        path = ROOT / d["source"]
        found = path.exists() and d["quote"] in path.read_text(errors="replace")
        L.rec(d["run"], d["host"], d["role"], "lease_extension", parse_ts(d["when"]), "lease",
              d["detail"] + ("" if found else " [citation text not found in the source on this build]"), [d["source"]] + d.get("also", []),
              "measured (document)" if found else "unverified", A100, 0.0)


# ----------------------------------------------------------------------------------------------------------------
# balances, local compute


def snapshots(L: Ledger):
    p = TMP / "headroom-20261005" / "account-latest.json"
    if p.exists():
        d = read_json(p)
        me = d.get("myself") or {}
        L.snapshots.append({"utc": parse_ts(d.get("utc")), "balance": me.get("clientBalance"), "spend_per_hr": me.get("currentSpendPerHr"),
                            "precision": "exact", "source": rel(p), "running": [x.get("name") for x in d.get("pods") or [] if x.get("status") == "RUNNING"],
                            "pods_listed": len(d.get("pods") or []), "volume_gb_listed": sum(float(x.get("volumeInGb") or 0) for x in d.get("pods") or [])})
    p = TMP / "headroom-v2" / "budget-checks.jsonl"
    for d in read_jsonl(p):
        L.snapshots.append({"utc": parse_ts(d.get("utc")), "balance": d.get("balance"), "spend_per_hr": d.get("spend_per_hr"),
                            "precision": "2 dp", "source": rel(p), "running": [x.get("name") for x in d.get("running") or []]})
    L.snapshots = sorted((s for s in L.snapshots if s["utc"] and s["balance"] is not None), key=lambda s: s["utc"])


def local_compute(L: Ledger):
    """The round-1 second judge on the Mac: no receipt; wall-clock is estimated from file-system times."""
    base = TMP / "headroom-20261005"
    items = base / "second-judge-items.jsonl"
    if items.exists():
        st = os.stat(items)                        # file times only; the per-item cache is never opened
        birth = getattr(st, "st_birthtime", None)
        summ = base / "second-judge-summary.json"
        n = ((read_json(summ).get("overall") or {}).get("pairs") if summ.exists() else None) or 0
        if birth:
            L.local.append({"run": "headroom-20261005", "host": "local-mac", "role": "local", "activity": "evaluation", "items": n,
                            "start": dt.datetime.fromtimestamp(birth, UTC), "end": dt.datetime.fromtimestamp(st.st_mtime, UTC),
                            "title": f"Second safety judge on the Mac ({n} round-1 answers)",
                            "detail": "Granite Guardian 3.3 8B Q4_K_M with llama.cpp on Metal; the span runs from the first to the last cached "
                                      "item, so the model load before the first item is not included",
                            "source": rel(items), "gpu": "Apple Mac (Metal), local"})
    gguf = TMP / "judge-models" / "granite-guardian-3.3-8b-Q4_K_M.gguf"
    if gguf.exists():
        st = os.stat(gguf)
        birth = getattr(st, "st_birthtime", None)
        if birth:
            L.local.append({"run": "headroom-20261005", "host": "local-mac", "role": "local", "activity": "bootstrap/setup",
                            "start": dt.datetime.fromtimestamp(birth, UTC), "end": dt.datetime.fromtimestamp(st.st_mtime, UTC),
                            "title": "Judge model download to the Mac",
                            "detail": f"Download of the {st.st_size / 1e9:.2f} GB GGUF file; download.log has no timestamps",
                            "source": rel(gguf), "gpu": "Apple Mac (local network)"})


# ----------------------------------------------------------------------------------------------------------------
# timeline


def build_segments(pod: Pod):
    base = Iv(0, pod.start, pod.end, "unattributed", "gap", "no record covers this time", (pod.start_src,), "gap")
    segs = [(pod.start, pod.end, base)]
    for iv in sorted(pod.ivs, key=lambda x: x.prio):
        s, e = max(iv.start, pod.start), min(iv.end, pod.end)
        if e <= s:
            continue
        new = []
        for a, b, lab in segs:
            if b <= s or a >= e:
                new.append((a, b, lab))
                continue
            if a < s:
                new.append((a, s, lab))
            new.append((max(a, s), min(b, e), iv))
            if b > e:
                new.append((e, b, lab))
        segs = new
    segs = coalesce([Seg(a, b, lab) for a, b, lab in segs if b > a])
    total = sum((s.end - s.start).total_seconds() for s in segs)
    span = (pod.end - pod.start).total_seconds()
    if abs(total - span) > 1e-6:
        raise AssertionError(f"{pod.key}: segments {total} s != billed span {span} s")
    for x, y in zip(segs, segs[1:]):
        if x.end != y.start:
            raise AssertionError(f"{pod.key}: segments are not contiguous at {x.end}")
    pod.segments = segs


# Stages that are short glue between the main stages of a process: merged into the neighbouring segment of the same
# activity (and basis) so the CSV stays readable. Activity totals are unchanged; the absorbed seconds are listed in the
# row's notes as includes=...
GLUE = {"job_overhead", "runner", "driver", "eval_state_overhead", "bootstrap_script", "worker_script", "in_job_setup",
        "verify", "query_loss", "arc", "load_model", "process_overhead", "other"}
ENGINE_ACTS = {"training", "evaluation", "row_scoring", "rewriting", "preflight", "edit_building"}
# glue that may join a neighbour of another activity (the gap belongs to whatever the process was doing around it)
CROSS_GLUE = {"job_overhead": ENGINE_ACTS, "eval_state_overhead": ENGINE_ACTS, "process_overhead": ENGINE_ACTS,
              "bootstrap_script": {"bootstrap/setup", "preflight"}, "worker_script": {"bootstrap/setup", "preflight", "training"},
              "driver": {"preflight", "evaluation"}}
NO_MERGE = {"train"}       # train segments (init->q, q->e1, e1->e3) stay separate rows


@dataclass
class Seg:
    start: dt.datetime
    end: dt.datetime
    iv: Iv
    details: list = field(default_factory=list)
    sources: list = field(default_factory=list)
    includes: dict = field(default_factory=dict)

    def __post_init__(self):
        if not self.details:
            self.details = [self.iv.detail]
        if not self.sources:
            self.sources = list(self.iv.sources)

    @property
    def activity(self):
        return self.iv.activity

    @property
    def stage(self):
        return self.iv.stage

    def compatible(self, other) -> bool:
        return (self.iv.activity == other.iv.activity and self.iv.basis == other.iv.basis and self.iv.extra == other.iv.extra)

    def absorb(self, other, as_glue: bool):
        self.start, self.end = min(self.start, other.start), max(self.end, other.end)
        for s in other.sources:
            if s not in self.sources:
                self.sources.append(s)
        if as_glue:
            secs = (other.end - other.start).total_seconds()
            self.includes[other.stage] = self.includes.get(other.stage, 0.0) + secs
            for k, v in other.includes.items():
                self.includes[k] = self.includes.get(k, 0.0) + v
        else:
            for d in other.details:
                if d not in self.details:
                    self.details.append(d)
            for k, v in other.includes.items():
                self.includes[k] = self.includes.get(k, 0.0) + v


def _joinable(glue: Seg, main: Seg) -> bool:
    if main.stage in GLUE or glue.iv.basis != main.iv.basis or glue.iv.extra != main.iv.extra:
        return False
    if glue.activity == main.activity:
        return True
    return main.activity in CROSS_GLUE.get(glue.stage, set()) and glue.activity in ENGINE_ACTS | {"bootstrap/setup"}


def coalesce(segs: list) -> list:
    # 1. adjacent segments with the same activity and stage (e.g. three judging stages in a row) become one
    out = []
    for s in segs:
        if (out and out[-1].compatible(s) and out[-1].stage == s.stage and out[-1].end == s.start
                and (s.stage not in NO_MERGE or out[-1].details == s.details)):
            out[-1].absorb(s, as_glue=False)
        else:
            out.append(s)
    # 2. glue joins the previous main segment it belongs with, else the next one
    changed = True
    while changed:
        changed = False
        for i, s in enumerate(out):
            if s.stage not in GLUE or s.activity in ("failed_attempt", "unattributed", "in_progress"):
                continue
            prev = out[i - 1] if i > 0 else None
            nxt = out[i + 1] if i + 1 < len(out) else None
            target = prev if (prev is not None and _joinable(s, prev)) else (nxt if (nxt is not None and _joinable(s, nxt)) else None)
            if target is not None:
                target.absorb(s, as_glue=True)
                del out[i]
                changed = True
                break
    # 3. remaining glue pieces next to each other with the same activity become one row (e.g. verify + seal + runner)
    final = []
    for s in out:
        if (final and final[-1].compatible(s) and final[-1].end == s.start
                and (final[-1].stage == s.stage and s.stage not in NO_MERGE or (final[-1].stage in GLUE and s.stage in GLUE))):
            final[-1].absorb(s, as_glue=final[-1].stage != s.stage)
        else:
            final.append(s)
    return final


def notes_for(seg: Seg, extra_note: str = "") -> str:
    iv = seg.iv
    detail = " + ".join(seg.details)
    if len(detail) > 400:
        detail = detail[:397] + "..."
    parts = [f"basis={iv.basis}", f"stage={iv.stage}", f"detail={detail}"]
    if seg.includes:
        parts.append("includes=" + ", ".join(f"{k} {v:.1f} s" for k, v in sorted(seg.includes.items(), key=lambda kv: -kv[1])))
    parts += [f"{k}={v}" for k, v in iv.extra]
    if extra_note:
        parts.append(extra_note)
    return "; ".join(p.replace("\n", " ") for p in parts)


def short_host(pod: Pod) -> str:
    """The pod name without the run prefix, so attempts stay distinct (rm10-1101 vs rm10-1101-r2)."""
    name = pod.pod_name
    for prefix in ("headroom-20261005-", "headroom-v2-", "study-v2-20261004-", "study-v2-20261002-"):
        if name.startswith(prefix):
            return name[len(prefix):]
    if name == "study-v2-20261002":
        return "lead"
    if pod.run == "runpod-pilot-20261002":
        return "pilot"
    if pod.run == "pod-timer-check-20261004":
        return "check"
    return name


def rows_of(L: Ledger) -> list:
    rows = []
    for pod in sorted(L.pods, key=lambda p: (p.start, p.run, p.host)):
        first = True
        for seg in pod.segments:
            a, b = seg.start, seg.end
            wh = hours(a, b)
            extra = ""
            if first:
                extra = (f"pod={pod.pod_name}; billed_span={iv_span(pod)}; start_from={pod.start_src}; end_from={pod.end_src} "
                         f"({pod.end_basis}); price_from={pod.price_src} costPerHr" + (f"; pod_note={pod.note}" if pod.note else ""))
                first = False
            rows.append({"date_utc": a.strftime("%Y-%m-%d"), "run": pod.run, "host": short_host(pod),
                         "role": pod.role, "activity": seg.activity, "start_utc": iso(a), "end_utc": iso(b), "wall_hours": f"{wh:.6f}",
                         "gpu_type": pod.gpu_type, "gpu_count": str(pod.gpu_count), "usd_per_hour": f"{pod.price:.2f}",
                         "usd_estimate": f"{wh * pod.price:.4f}", "source_file": " + ".join(dict.fromkeys(seg.sources)),
                         "notes": notes_for(seg, extra)})
    for r in sorted(L.recs, key=lambda r: (r.when or L.now, r.run, r.host)):
        rows.append({"date_utc": r.when.strftime("%Y-%m-%d") if r.when else "", "run": r.run, "host": r.host, "role": r.role,
                     "activity": r.activity, "start_utc": iso(r.when), "end_utc": iso(r.when), "wall_hours": "0.000000",
                     "gpu_type": r.gpu_type, "gpu_count": "1" if r.gpu_type else "", "usd_per_hour": f"{r.price:.2f}" if r.price else "",
                     "usd_estimate": "0.0000", "source_file": " + ".join(r.sources),
                     "notes": "; ".join([f"basis={r.basis}", f"stage={r.stage}", "record only (no billed time)", f"detail={r.detail}"]
                                        + [f"{k}={v}" for k, v in r.extra])})
    for x in L.local:
        wh = hours(x["start"], x["end"])
        rows.append({"date_utc": x["start"].strftime("%Y-%m-%d"), "run": x["run"], "host": x["host"], "role": x["role"],
                     "activity": x["activity"], "start_utc": iso(x["start"]), "end_utc": iso(x["end"]), "wall_hours": f"{wh:.6f}",
                     "gpu_type": x["gpu"], "gpu_count": "", "usd_per_hour": "0.00", "usd_estimate": "0.0000", "source_file": x["source"],
                     "notes": f"basis=estimated (file-system birth and modification times; no receipt); stage=local; detail={x['detail']}; "
                              "local compute: $0 cloud cost; not a pod"})
    order = {r: i for i, r in enumerate(RUNS)}
    first = {}
    for r in rows:
        k = (r["run"], r["host"].split("-r2")[0])
        if r["start_utc"] and (k not in first or r["start_utc"] < first[k]):
            first[k] = r["start_utc"]
    rows.sort(key=lambda r: (order.get(r["run"], 99), first.get((r["run"], r["host"].split("-r2")[0]), r["start_utc"]),
                             r["host"].split("-r2")[0], r["start_utc"] or "9", r["host"]))
    return rows


def iv_span(pod: Pod) -> str:
    return f"{iso(pod.start)}..{iso(pod.end)} ({hours(pod.start, pod.end):.4f} h)"


# ----------------------------------------------------------------------------------------------------------------
# build


def build(now: dt.datetime) -> Ledger:
    L = Ledger(now)
    pilot_run(L)
    study0210_run(L)
    podtimer_run(L)
    devmatrix_run(L)
    headroom_run(L, "headroom-20261005", TMP / "headroom-20261005")
    headroom_run(L, "headroom-v2", TMP / "headroom-v2")
    for pod in L.pods:      # the replacement lead of round 1 repeats the first lead's setup, scoring and removal edits
        if pod.run == "headroom-20261005" and pod.host == "lead" and pod.pod_name.endswith("-r2"):
            rw = [iv for iv in pod.ivs if iv.activity == "rewriting"]
            if rw:
                tag_repeats(pod, min(iv.start for iv in rw), "repeat-after-failure (the first lead's work redone after its cap stop)")
    doc_records(L)
    snapshots(L)
    local_compute(L)
    for pod in L.pods:
        build_segments(pod)
    return L


# ----------------------------------------------------------------------------------------------------------------
# outputs


IPV4 = re.compile(r"(?<![\d.])(?:\d{1,3}\.){3}\d{1,3}(?![\d.])")


def scan(text: str, what: str):
    bad = [m for m in IPV4.findall(text) if all(0 <= int(x) <= 255 for x in m.split("."))]
    if bad or "portMappings" in text or "publicIp" in text:
        raise SystemExit(f"refusing to write {what}: it contains a network address field or IPv4 address")


def csv_text(rows: list) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow(r)
    return buf.getvalue()


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--csv", type=pathlib.Path, default=DEFAULT_CSV)
    ap.add_argument("--md", type=pathlib.Path, default=DEFAULT_MD)
    ap.add_argument("--now", help="provisional end for running pods (default: the current UTC time)")
    ap.add_argument("--dry-run", action="store_true", help="build and check only; write nothing")
    ap.add_argument("--no-md", action="store_true", help="write the CSV only")
    args = ap.parse_args(argv)
    now = parse_ts(args.now) if args.now else dt.datetime.now(UTC).replace(microsecond=0)
    L = build(now)
    rows = rows_of(L)
    text = csv_text(rows)
    scan(text, "the CSV")
    md = render_md(L, rows) if not args.no_md else ""
    if md:
        scan(md, "the summary")
    tot = sum(float(r["usd_estimate"]) for r in rows)
    by_run = {}
    for r in rows:
        by_run[r["run"]] = by_run.get(r["run"], 0.0) + float(r["usd_estimate"])
    print(json.dumps({"rows": len(rows), "pods": len(L.pods), "usd_total": round(tot, 2),
                      "usd_by_run": {k: round(v, 2) for k, v in by_run.items()}, "warnings": L.warnings,
                      "running_pods": [p.key for p in L.pods if p.running], "build_utc": iso(now)}, indent=1))
    if args.dry_run:
        return 0
    args.csv.parent.mkdir(parents=True, exist_ok=True)
    args.csv.write_text(text)
    if md:
        args.md.parent.mkdir(parents=True, exist_ok=True)
        args.md.write_text(md)
    return 0


# ----------------------------------------------------------------------------------------------------------------
# summary page


def money(x, nd=2):
    if x is None:
        return "–"
    if abs(x) < 0.01 and x != 0 and nd <= 2:
        return f"${x:.4f}"
    return f"${x:,.{nd}f}"


def smoney(x):
    return ("−" if x < 0 else "+") + money(abs(x))


def mins(sec):
    return "–" if sec is None else f"{sec / 60:.1f}"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else None


def rng(xs, f=lambda v: f"{v:.1f}"):
    xs = [x for x in xs if x is not None]
    return f"{f(min(xs))}–{f(max(xs))}" if xs else "–"


def seg_table(pod: Pod) -> dict:
    """seconds by activity, by (activity, stage), and dollars, for one pod (coalesced segments)."""
    act, stg = {}, {}
    for s in pod.segments:
        sec = (s.end - s.start).total_seconds()
        act[s.activity] = act.get(s.activity, 0.0) + sec
        stg[(s.activity, s.stage)] = stg.get((s.activity, s.stage), 0.0) + sec
    return {"act": act, "stage": stg, "span": (pod.end - pod.start).total_seconds()}


def interval_costs(L: Ledger, a, b, r_run):
    gpu = disk = 0.0
    for p in L.pods:
        s, e = max(p.start, a), min(p.end, b)
        if e > s:
            h = hours(s, e)
            gpu += h * p.price
            disk += h * p.disk_gb * r_run
    return gpu, disk


def stopped_volume_hi(L: Ledger, a, b, rate):
    """Upper bound for the storage of our pods that stopped inside [a, b) (deletion times are not recorded)."""
    tot = 0.0
    for p in L.pods:
        if p.running or p.deleted_at_end or not (a <= p.end < b):
            continue
        tot += p.volume_gb * rate * hours(p.end, b)
    return tot


def running_at(L: Ledger, t, r_run):
    return sum(p.price + p.disk_gb * r_run for p in L.pods if p.start <= t < p.end)


def render_md(L: Ledger, rows: list) -> str:
    out = []
    w = out.append
    pods = [p for p in L.pods]
    by_run = {r: [p for p in pods if p.run == r] for r in RUNS}
    run_usd = {r: sum(hours(p.start, p.end) * p.price for p in ps) for r, ps in by_run.items()}
    total_usd = sum(run_usd.values())
    act_usd = {}
    act_run = {}
    for p in pods:
        t = seg_table(p)
        for a, sec in t["act"].items():
            act_usd[a] = act_usd.get(a, 0.0) + sec / 3600 * p.price
            act_run[(p.run, a)] = act_run.get((p.run, a), 0.0) + sec / 3600 * p.price
    running = [p for p in pods if p.running]
    n_rows = len(rows)
    repeat_usd = sum(hours(s.start, s.end) * p.price for p in pods for s in p.segments if any(k == "overhead" for k, _ in s.iv.extra))

    # ------------------------------------------------------------------ header
    w("# Cost ledger: cloud and local compute, 2–6 October 2026")
    w("")
    w(f"Generated by `tmp/cost-ledger/cost_ledger.py` from the local run records at **{iso(L.now)}** (build time). "
      "Re-run the script to refresh it; do not edit this page by hand. The full ledger is "
      f"[`research/costs/cost-ledger.csv`](cost-ledger.csv) ({n_rows} rows: one per activity segment of each pod, plus zero-length records).")
    w("")
    w("**Scope.** Every cloud run with pod records under `tmp/`: " + ", ".join(f"`{r}`" for r in RUNS) +
      ". No other folder under `tmp/` holds pod, create or stop records (searched for `pod*.json`, `create-result*.json`, "
      "`stops.jsonl`). Local Mac work is included where a time can be recovered (section 7).")
    w("")
    w("**How to read the numbers.**")
    w("- **Times are measured** unless marked. The CSV column `notes` gives each row's `basis`:")
    w("  - `measured`: process receipts (`started_utc` + `elapsed_s`), engine stage ledgers (millisecond start and end), "
      "RunPod's own start and stop times, and pull records;")
    w("  - `log-time`: orchestrator log lines (second resolution; they can lag the real event by up to one poll interval);")
    w("  - `estimated`: derived by the method that the row states;")
    w("  - `provisional`: a pod that was still running at build time.")
    w("- **Dollars are estimates:** measured wall time × the pod's own `costPerHr` (GPU price from the pod record). "
      "Disk and storage are not in the CSV; the reconciliation (section 6) adds them.")
    w("- **A pod bills from RunPod's start time to its stop.** Each pod's rows add up to that span exactly (the script checks this). "
      "Time that no record covers is `unattributed`.")
    w("- **Price check:** every A100 pod record states `costPerHr` 1.59 (Secure Cloud, A100-SXM4-80GB). "
      "The 2 Oct pilot (RTX A5000) states 0.27 and the 4 Oct timer check 0.24.")
    w("")

    # ------------------------------------------------------------------ headline
    r1 = run_usd.get("headroom-20261005", 0.0)
    dm = run_usd.get("study-v2-20261004", 0.0)
    v2 = run_usd.get("headroom-v2", 0.0)
    o2 = run_usd.get("study-v2-20261002", 0.0)
    fail_usd = act_usd.get("failed_attempt", 0.0)
    idle_usd = act_usd.get("idle", 0.0)
    w("## 1. Headline")
    w("")
    w(f"- **GPU spend in the records: {money(total_usd)}** over {len(pods)} billed pods "
      f"({sum(hours(p.start, p.end) for p in pods):.1f} pod-hours). By run: 2 Oct {money(o2 + run_usd.get('runpod-pilot-20261002', 0))}, "
      f"4 Oct {money(dm + run_usd.get('pod-timer-check-20261004', 0))}, round 1 {money(r1)}, v2 {money(v2)}"
      + (f" (v2 includes {len(running)} pod still running: provisional)." if running else "."))
    w(f"- **Round 1 reconciles with its results page:** {money(r1)} against \"about $42.3\"; job times "
      f"{rng([j.elapsed / 60 for j in L.jobs if j.run == 'headroom-20261005'])} min against \"72–102 minutes\".")
    w(f"- **Failed attempts cost {money(fail_usd)}** ({100 * fail_usd / total_usd:.0f}% of the total), most of it the 2 Oct credit incident. "
      f"**Idle time cost {money(idle_usd)}**, and the replacement lead's repeated work in round 1 cost {money(repeat_usd)} more.")
    v2jobs = [j for j in L.jobs if j.run == "headroom-v2"]
    if v2jobs:
        w(f"- **One v2 training job** (1.5B, rank-64 LoRA, 3 epochs, e3 evaluation on the v2 banks) costs about "
          f"{money(mean([j.elapsed / 3600 * j.price for j in v2jobs]))} of engine time "
          f"({mins(mean([j.elapsed for j in v2jobs]))} min), and about "
          f"{money(mean([hours(p.start, p.end) * p.price for p in pods if p.run == 'headroom-v2' and any(j.pod == p.pod_name for j in v2jobs)]))} per pod with setup, preflight and copy.")
    lead = [x for x in L.lead if x["stage"] == "score_rows"]
    rew = [x for x in L.lead if x["stage"] == "generate_rewrites"]
    for x in lead:
        w(f"- **Row scoring** with Qwen3Guard-Gen-4B: {x['seconds'] / x['rows']:.3f} s per row, "
          f"{money(x['seconds'] / x['rows'] * x['price'] / 3600 * 1000, 3)} per 1,000 rows (`{x['run']}`, {x.get('attn') or '?'} attention).")
    for x in rew:
        w(f"- **Rewriting** with Qwen2.5-7B-Instruct: {x['seconds'] / x['rows']:.2f} s per row attempted, "
          f"{money(x['seconds'] / x['rows'] * x['price'] / 3600 * 1000, 2)} per 1,000 rows (`{x['run']}`, {x.get('attn') or '?'} attention).")
    w("")

    # ------------------------------------------------------------------ totals by run
    w("## 2. Totals by run")
    w("")
    w("| Run | What ran | Pods | Pod-hours | GPU $ (est.) | Failed $ | Idle $ | Unattributed $ | Earlier figure |")
    w("|---|---|---|---|---|---|---|---|---|")
    earlier = {
        "headroom-20261005": "about $42.3 ([results](../experiments/2026-10-05-headroom-round-1-results.md))",
        "study-v2-20261004": "about $60, about $53 of it training jobs ([results](../experiments/2026-10-04-dev-matrix-002-results.md))",
        "runpod-pilot-20261002": "$0.146 estimate (`tmp/runpod-pilot-20261002/cost-estimate.json`)",
    }
    est = L.facts.get("oct2_spend_estimate")
    if est and est[0]:
        cut = parse_ts(est[1])
        upto = sum(max(0.0, hours(p.start, min(p.end, cut))) * p.price for p in by_run["study-v2-20261002"] if p.start < cut)
        earlier["study-v2-20261002"] = (f"{money(est[0])} GPU estimate at {hms(cut)} UTC (`{est[2]}`); this ledger gives "
                                        f"{money(upto)} up to the same time")
    for r, label in RUNS.items():
        ps = by_run[r]
        if not ps:
            w(f"| `{r}` | {label} | 0 | – | – | – | – | – | no pod records found |")
            continue
        label = label + ("; a pod still running (provisional)" if any(p.running for p in ps) else "")
        w(f"| `{r}` | {label} | {len(ps)} | {sum(hours(p.start, p.end) for p in ps):.2f} | {money(run_usd[r])} | "
          f"{money(act_run.get((r, 'failed_attempt'), 0))} | {money(act_run.get((r, 'idle'), 0))} | "
          f"{money(act_run.get((r, 'unattributed'), 0))} | {earlier.get(r, '–')} |")
    w(f"| **All** | | **{len(pods)}** | **{sum(hours(p.start, p.end) for p in pods):.2f}** | **{money(total_usd)}** | "
      f"**{money(fail_usd)}** | **{money(idle_usd)}** | **{money(act_usd.get('unattributed', 0))}** | |")
    w("")
    w("Notes:")
    dmseg = lambda pred: sum(hours(s.start, s.end) * p.price for p in by_run["study-v2-20261004"] for s in p.segments if pred(s))
    w(f"- **dev-matrix-002:** the ledger's {money(dm)} includes dev10's first pod that never started "
      f"({money(dmseg(lambda s: s.stage == 'container_start' and s.activity == 'failed_attempt'))}), dev07's failed bundle transfer "
      f"({money(dmseg(lambda s: s.stage == 'send_bundle' and s.activity == 'failed_attempt'))}) and dev05's 71-minute hold before the "
      f"matrix started ({money(dmseg(lambda s: s.stage == 'hold'))}). Training plus evaluation is "
      f"{money(act_run.get(('study-v2-20261004', 'training'), 0) + act_run.get(('study-v2-20261004', 'evaluation'), 0))} "
      "(the results page: about $53).")
    cut = parse_ts("2026-10-05T11:00:04Z")
    r1_upto = sum(max(0.0, hours(p.start, min(p.end, cut))) * p.price for p in by_run["headroom-20261005"] if p.start < cut)
    a1 = sum(hours(p.start, p.end) * p.price for p in by_run["headroom-20261005"] if p.role == "job" and not p.pod_name.endswith("-r2")
             and any(s.activity == "failed_attempt" for s in p.segments) and all(s.activity == "failed_attempt" for s in p.segments))
    w(f"- **Round 1 cross-checks:** the operator's running estimate \"spend so far $28.38\" at 11:00 UTC (`tmp/headroom-20261005/decisions.jsonl`) "
      f"against {money(r1_upto)} in this ledger up to the same time; the four removal hosts of attempt 1, \"$2.73\" on the results page, "
      f"against {money(a1)} here.")
    w("- **2 Oct study-v2:** the pods' end is the time the local retrieval found SSH closed (18:18:12–18:18:27 UTC); "
      "the pods were terminated when the credit ran out, so this is an upper bound. The provider's billing record "
      "for the lead pod (`tmp/study-v2-20261002/billing-latest.json`) had posted only part of the day when it was read.")
    if running:
        w(f"- **Running at build time:** {', '.join('`' + p.pod_name + '`' for p in running)}. Its rows after the last record are "
          "`in_progress` (provisional) and end at the build time.")
    w("")

    # ------------------------------------------------------------------ totals by activity
    w("## 3. Totals by activity")
    w("")
    acts = [a for a in ACTIVITIES if any(act_run.get((r, a), 0) for r in RUNS)]
    w("| Activity | " + " | ".join(f"`{r}`" for r in RUNS) + " | All | Share |")
    w("|---|" + "---|" * (len(RUNS) + 2))
    for a in acts:
        w(f"| {a} | " + " | ".join(money(act_run.get((r, a), 0)) if act_run.get((r, a), 0) else "–" for r in RUNS)
          + f" | **{money(act_usd.get(a, 0))}** | {100 * act_usd.get(a, 0) / total_usd:.1f}% |")
    w("")
    w("- `failed_attempt` rows carry `was=` (what the pod was doing). Zero-length records (failed creates, a failed restart, "
      f"lease extensions) are in the CSV with $0: {sum(1 for r in L.recs if r.activity == 'failed_attempt')} failed creates or restarts, "
      f"{sum(1 for r in L.recs if r.activity == 'lease_extension')} lease extensions.")
    w("- Short process glue (state saves between train segments, interpreter start, the unit seal) is merged into the neighbouring "
      "segment of the same process; the CSV lists it under `includes=`.")
    w("")

    # ------------------------------------------------------------------ unit costs
    w("## 4. Unit costs")
    w("")
    w("All unit costs below are **measured times × $1.59/h** (A100-SXM4-80GB). Their sources are the receipts and stage ledgers "
      "under `tmp/*/retrieved/*/tree/`.")
    w("")
    # 4.1 per job
    w("### 4.1 Per full training job")
    w("")
    w("Per job, mean (range) over the pods of each run. A dev-matrix pod ran two jobs, so its setup, preflight and other time is "
      "split over two. *Other* is idle + copy/finish + unattributed + failed time on a job pod. Minutes, then dollars.")
    w("")
    w("| Run | Jobs | Setup (create + bootstrap) | Preflight | Training | Evaluation | Other | Total per job | $ per job |")
    w("|---|---|---|---|---|---|---|---|---|")
    perjob = {}
    for r in ("study-v2-20261004", "headroom-20261005", "headroom-v2"):
        vals = []
        for p in by_run[r]:
            js = [j for j in L.jobs if j.run == r and j.pod == p.pod_name]
            if not js or p.running:
                continue
            t = seg_table(p)["act"]
            n = len(js)
            setup = t.get("pod_create_wait", 0) + t.get("bootstrap/setup", 0)
            pre = t.get("preflight", 0)
            tr, ev = t.get("training", 0), t.get("evaluation", 0)
            other = sum(t.get(k, 0) for k in ("idle", "copy/finish", "unattributed", "failed_attempt"))
            span = seg_table(p)["span"]
            vals.append((n, setup / n, pre / n, tr / n, ev / n, other / n, span / n, p))
        if not vals:
            continue
        perjob[r] = vals
        f = lambda i: f"{mins(mean([v[i] for v in vals]))} ({rng([v[i] / 60 for v in vals])})"
        usd = [v[6] / 3600 * v[7].price for v in vals]
        w(f"| `{r}` | {sum(v[0] for v in vals)} | {f(1)} | {f(2)} | {f(3)} | {f(4)} | {f(5)} | {f(6)} | "
          f"{money(mean(usd))} ({rng(usd, lambda x: f'{x:.2f}')}) |")
    w("")
    w("Basis: times measured (receipts, stage ledgers, pod records; the create wait and bundle transfer are log-time); dollars "
      "estimated (× $1.59/h).")
    w("")
    w("- **dev-matrix-002** evaluated at q, e1 and e3 (168 prompts and ARC each), on Qwen2.5-1.5B-Instruct with a small LoRA. "
      "Its *Other* includes dev05's 71-minute hold and dev07's failed transfer.")
    w("- **Round 1** evaluated once (e3, 168 prompts and ARC), with rank-64 LoRA plus trained special-token rows and eager attention. "
      "Its *Other* includes full-state pulls of 3.8 GB on five hosts and hosts queued behind them (section 5).")
    w("- **v2** evaluated once on the larger v2 banks (section 4.4), with SDPA attention, micro-batch 4 × 2, and a longer preflight "
      "that includes an evaluation-timing sample.")
    w("")
    # 4.2 per step
    w("### 4.2 Per training step")
    w("")
    w("`train` stages only (forward, backward, optimizer and progress logging; state saves excluded). The steps.jsonl column is the "
      "sum of each step's own `seconds`.")
    w("")
    w("| Run | Model and adapter | Attention | Jobs | Steps per job | s/step (stage) | s/step (steps.jsonl) | $ per 1,000 steps | Padded tokens/s |")
    w("|---|---|---|---|---|---|---|---|---|")
    model = {"study-v2-20261002": "Qwen2.5-1.5B-Instruct", "study-v2-20261004": "Qwen2.5-1.5B-Instruct",
             "headroom-20261005": "Qwen2.5-1.5B (base)", "headroom-v2": "Qwen2.5-1.5B (base)"}
    for r in ("study-v2-20261002", "study-v2-20261004", "headroom-20261005", "headroom-v2"):
        js = [j for j in L.jobs if j.run == r and j.train_steps and j.stage_s.get("train")]
        if not js:
            continue
        sps = [j.stage_s["train"] / j.train_steps for j in js]
        spj = [j.step_seconds / j.step_count for j in js if j.step_count]
        tps = [j.tokens.get("padded_tokens", 0) / j.stage_s["train"] for j in js if j.tokens.get("padded_tokens")]
        trainable = next((j.meta.get("trainable") for j in js if j.meta.get("trainable")), None)
        attn = next((j.meta.get("attn") for j in js if j.meta.get("attn")), "?")
        w(f"| `{r}` | {model.get(r, '?')}, {fmt_int(trainable)} trainable | {attn} | {len(js)} | "
          f"{fmt_int(mean([j.train_steps for j in js]))} | {mean(sps):.3f} ({rng(sps, lambda x: f'{x:.2f}')}) | "
          f"{mean(spj):.3f} | {money(mean(sps) * 1000 * 1.59 / 3600)} | {fmt_int(mean(tps)) if tps else '–'} |")
    w("")
    w("Basis: measured (engine `ledger.jsonl` train stages and `steps.jsonl`, all jobs of each run); dollars estimated.")
    w("")
    w("A step is one optimizer update on 8 rows (micro-batch 8, or 4 × 2 in v2). Steps per job differ with the data size "
      "(10,148 rows; 9,133 after a 10% removal; 10,655 and 11,163 with the v2 injections).")
    w("")
    # pilot-run proxy
    w("**Short-run proxy (the q checkpoint, about a quarter epoch).** The `init->q` train segment, measured inside the full jobs:")
    w("")
    w("| Run | Steps | Minutes | $ (training only) |")
    w("|---|---|---|---|")
    for r in ("study-v2-20261004", "headroom-20261005", "headroom-v2"):
        segs = [j.segments.get("init->q") for j in L.jobs if j.run == r and j.segments.get("init->q")]
        if segs:
            w(f"| `{r}` | {fmt_int(mean([s[1] for s in segs]))} | {mins(mean([s[0] for s in segs]))} | "
              f"{money(mean([s[0] for s in segs]) / 3600 * 1.59)} |")
    w("")
    # 4.3 scoring and rewriting
    w("### 4.3 Row scoring and rewriting (lead pods)")
    w("")
    w("| Step | Model | Rows | Stage seconds | Process seconds | s per row | $ per row | $ per 1,000 rows | Source |")
    w("|---|---|---|---|---|---|---|---|---|")
    for x in L.lead:
        nm = "Row scoring" if x["stage"] == "score_rows" else "Rewriting"
        mdl = "Qwen3Guard-Gen-4B (3 label lines per row)" if x["stage"] == "score_rows" else "Qwen2.5-7B-Instruct, greedy, ≤1,024 new tokens"
        per = x["seconds"] / x["rows"]
        w(f"| {nm} (`{x['pod']}`) | {mdl} | {fmt_int(x['rows'])}" + (f" ({fmt_int(x['accepted'])} accepted)" if x.get("accepted") else "")
          + f" | {x['seconds']:.0f} | {x['process_s']:.0f} | {per:.3f} | {money(per * x['price'] / 3600, 5)} | "
          f"{money(per * x['price'] / 3600 * 1000, 3)} | `{x['source']}` |")
    if rew and rew[-1].get("accepted"):
        x = rew[-1]
        w("")
        w(f"Per accepted rewrite: {x['seconds'] / x['accepted']:.2f} s, {money(x['seconds'] / x['accepted'] * x['price'] / 3600, 5)}.")
    w("")
    w("- **Measured** on the replacement lead (`lead-r2`). The first lead's scoring (identical, byte for byte) is in the CSV as "
      "*estimated* with the same duration, because its receipts stayed on its volume.")
    lost_rw = sum((s.end - s.start).total_seconds() for p in by_run["headroom-20261005"] for s in p.segments
                  if s.stage == "generate_rewrites" and s.activity == "failed_attempt")
    full_rw = next((x["seconds"] for x in rew if x["run"] == "headroom-20261005"), None)
    if full_rw:
        w(f"- The grant dossier's \"about 2.8 hours\" for rewrite generation is neither the measured complete run ({full_rw / 3600:.2f} h) nor "
          f"that run plus the first lead's cut-off rewriting ({(full_rw + lost_rw) / 3600:.2f} h, estimated). Use the measured {full_rw / 3600:.2f} h.")
    if not any(x["run"] == "headroom-v2" for x in L.lead):
        w("- Round 1 used **eager attention**. The v2 lead (SDPA) has no retrieved receipts yet; a re-run after its records are "
          "pulled adds its rows here.")
    w("")
    # 4.4 v2 evaluation
    w("### 4.4 One evaluation on the v2 development banks")
    w("")
    w("Per job at e3: 468 greedy prompts (200 harm + 100 over-refusal + 72 ToxicChat + 96 ARC-generation), "
      "600 sampled answers (200 harm prompts × 3), judging of 468 + 600 answers, 800 continuous harm scores, ARC log-likelihood "
      "(189 questions, 757 sequences) and the query loss (30 queries). Counts come from the stage ledgers and the aggregate "
      "`eval/e3/summary.json`.")
    w("")
    groups = [("Greedy generation", ("generate",), "prompts"), ("Sampling (3 per harm prompt)", ("sample",), "answers"),
              ("Judging (Qwen3Guard: load, greedy, samples, harm scores)", ("load_guard", "guard", "guard_samples", "harm_scores"), None),
              ("ARC log-likelihood", ("arc_utility",), "questions"), ("Query loss", ("query_loss",), "queries")]
    if v2jobs:
        w("| Part | " + " | ".join(f"`{j.host}` s" for j in v2jobs) + " | Mean $ | Units | s per unit (mean) | Preflight projection s |")
        w("|---|" + "---|" * (len(v2jobs) + 4))
        proj = next((x for x in L.projections if x["host"] == "val05"), None) or (L.projections[0] if L.projections else None)
        tot = [0.0] * len(v2jobs)
        for name, stages, unit in groups:
            secs = [sum(j.stage_s.get(s, 0) for s in stages) for j in v2jobs]
            tot = [a + b for a, b in zip(tot, secs)]
            units = v2jobs[0].counts.get(stages[0]) if unit else None
            if name.startswith("Judging"):
                units = sum(v2jobs[0].counts.get(s, 0) for s in ("guard", "guard_samples", "harm_scores"))
            per = f"{mean(secs) / units:.2f}" if units else "–"
            pj = "–"
            if proj:
                ps = [proj["stages"].get(s, (None,))[0] for s in stages if s in proj["stages"]]
                pj = f"{sum(ps):.0f}" if ps else "–"
            w(f"| {name} | " + " | ".join(f"{s:.0f}" for s in secs) + f" | {money(mean(secs) / 3600 * 1.59)} | "
              f"{fmt_int(units) if units else '–'} | {per} | {pj} |")
        w(f"| **Total** | " + " | ".join(f"**{s:.0f}**" for s in tot) + f" | **{money(mean(tot) / 3600 * 1.59)}** | | | "
          f"**{proj['projected_s']:.0f}** |" if proj else f"| **Total** | " + " | ".join(f"{s:.0f}" for s in tot) + " | | | | |")
        w("")
        w(f"- **Measured: {mins(mean(tot))} min, {money(mean(tot) / 3600 * 1.59)} per evaluation** "
          f"({' and '.join(f'{j.host} {mins(t)} min' for j, t in zip(v2jobs, tot))}).")
        if proj:
            w(f"- **The preflight's projection ({proj['projected_s'] / 60:.0f} min, `{proj['source']}`) was an upper bound** "
              "by design: after two training steps nearly every answer ran to the 2,048-token cap. The trained models stop much "
              "earlier, so generation and sampling took about a third of the projection.")
    r1jobs = [j for j in L.jobs if j.run == "headroom-20261005"]
    if r1jobs:
        ev = [sum(j.stage_s.get(s, 0) for s in EVAL_STAGES) for j in r1jobs]
        w(f"- **For comparison, round 1's evaluation** (168 greedy prompts, judging, ARC at e3): {mins(mean(ev))} min "
          f"({rng([e / 60 for e in ev])}), {money(mean(ev) / 3600 * 1.59)} per job.")
    dmj = [j for j in L.jobs if j.run == "study-v2-20261004"]
    if dmj:
        ev = [sum(j.stage_s.get(s, 0) for s in EVAL_STAGES) / max(j.checkpoints, 1) for j in dmj]
        w(f"- **dev-matrix-002, per checkpoint** (168 prompts, judging, ARC): {mins(mean(ev))} min, {money(mean(ev) / 3600 * 1.59)}; "
          "three checkpoints per job.")
    w("")
    # 4.5 judge throughput
    w("### 4.5 Judge throughput (Qwen3Guard-Gen-4B on the A100)")
    w("")
    w("Basis: measured (stage seconds ÷ items, mean over the run's jobs); dollars estimated.")
    w("")
    w("| Use | Run | Items per job | s per item | $ per 1,000 items |")
    w("|---|---|---|---|---|")
    for r, st, label in (("headroom-v2", "guard", "label greedy answers"), ("headroom-v2", "guard_samples", "label sampled answers"),
                         ("headroom-v2", "harm_scores", "continuous harm score"), ("headroom-20261005", "guard", "label greedy answers"),
                         ("study-v2-20261004", "guard", "label greedy answers")):
        js = [j for j in L.jobs if j.run == r and j.counts.get(st)]
        if js:
            per = mean([j.stage_s[st] / j.counts[st] for j in js])
            w(f"| {label} | `{r}` | {fmt_int(mean([j.counts[st] for j in js]))} | {per:.3f} | {money(per * 1.59 / 3600 * 1000, 3)} |")
    if lead:
        x = lead[-1]
        w(f"| score training rows (3 label lines each) | `headroom-20261005` | {fmt_int(x['rows'])} | {x['seconds'] / x['rows']:.3f} | "
          f"{money(x['seconds'] / x['rows'] * 1.59 / 3600 * 1000, 3)} |")
    w("")
    # 4.6 overhead fraction
    w("### 4.6 Per-pod overhead as a fraction of a job")
    w("")
    w("*Setup + preflight* is pod creation wait, bootstrap (environment, model downloads) and the preflight fixture. "
      "*All non-job time* adds idle, copy/finish, unattributed and failed time on the job pods.")
    w("")
    w("| Run | Setup + preflight per pod (min) | Training + evaluation per pod (min) | Setup + preflight ÷ job time | All non-job time ÷ billed time |")
    w("|---|---|---|---|---|")
    for r, vals in perjob.items():
        sp = [(v[1] + v[2]) * v[0] for v in vals]
        jt = [(v[3] + v[4]) * v[0] for v in vals]
        frac = [a / b for a, b in zip(sp, jt) if b]
        non = [(v[1] + v[2] + v[5]) / v[6] for v in vals if v[6]]
        w(f"| `{r}` | {mins(mean(sp))} | {mins(mean(jt))} | {100 * mean(frac):.0f}% ({rng([100 * f for f in frac], lambda x: f'{x:.0f}')}) | "
          f"{100 * mean(non):.0f}% |")
    w("")
    ets = [sum((s.end - s.start).total_seconds() for s in p.segments if s.stage == "eval_timing_sample")
           for p in by_run.get("headroom-v2", []) if not p.running]
    ets = [x for x in ets if x]
    w("A dev-matrix pod ran two jobs, so its fixed costs were shared. v2's preflight includes an evaluation-timing sample "
      f"(about {mins(mean(ets))} minutes per pod), which made the per-pod overhead larger." if ets else
      "A dev-matrix pod ran two jobs, so its fixed costs were shared.")
    w("")

    # ------------------------------------------------------------------ failure and idle
    w("## 5. Failure and idle overhead")
    w("")
    w("Each line sums CSV rows (`failed_attempt`, `idle`, `unattributed`, and rows tagged `overhead=`); the basis column gives theirs.")
    w("")
    w("| Run | Item | Hours | $ (est.) | Basis |")
    w("|---|---|---|---|---|")
    items = {}
    for p in pods:
        for s in p.segments:
            if s.activity not in ("failed_attempt", "idle", "unattributed") and not any(k == "overhead" for k, _ in s.iv.extra):
                continue
            if s.activity == "failed_attempt":
                d = s.details[0]
                if p.run == "study-v2-20261002" and s.stage != "unit":
                    key = "dev-matrix-001 work lost in the credit incident (all 13 pods' work after their last retrieved receipt)"
                elif s.stage == "unit":
                    key = "calibration unit interrupted by the operator (KeyboardInterrupt), redone"
                elif p.run == "headroom-20261005" and s.stage == "generate_rewrites":
                    key = "first lead's rewriting cut off by its 2.5 h stop-timer cap"
                elif p.run == "headroom-20261005":
                    key = "removal hosts, attempt 1: bootstrapped, then stopped idle and recreated (4 pods)"
                elif s.stage == "container_start":
                    key = "first pod never started its container (dev10), replaced"
                elif s.stage == "send_bundle":
                    key = "first setup-bundle transfer failed, retried (dev07)"
                elif s.stage == "fixture":
                    key = "preflight out of CUDA memory at micro-batch 8, retried at 4 × 2 (val05)"
                else:
                    key = d[:80]
            elif s.activity == "idle":
                key = {"orchestrator_gap": "idle: orchestrator gaps between steps (polling, transfers)",
                       "finisher_latency": "idle: finisher detection latency after the job ended",
                       "hold": "idle: dev05 held 71 minutes after its bootstrap (one-pod validation)"}.get(s.stage, f"idle: {s.stage}")
                if any(k == "overhead" for k, _ in s.iv.extra):
                    key = "replacement lead repeats the first lead's setup, preflight, scoring and removal edits"
            elif s.activity == "unattributed":
                key = "unattributed (no record covers the time)"
            else:
                key = "replacement lead repeats the first lead's setup, preflight, scoring and removal edits"
            k2 = (p.run, key)
            h0, u0, b0 = items.get(k2, (0.0, 0.0, set()))
            items[k2] = (h0 + hours(s.start, s.end), u0 + hours(s.start, s.end) * p.price, b0 | {s.iv.basis})
    for (r, key), (h, u, b) in sorted(items.items(), key=lambda kv: (list(RUNS).index(kv[0][0]), -kv[1][1])):
        w(f"| `{r}` | {key} | {h:.2f} | {money(u)} | {', '.join(sorted(b))} |")
    ov = sum(u for (h, u, b) in items.values())
    w(f"| **All** | | **{sum(h for (h, u, b) in items.values()):.2f}** | **{money(ov)}** ({100 * ov / total_usd:.0f}% of GPU spend) | |")
    w("")
    nfc = {r: sum(1 for x in L.recs if x.run == r and x.stage == "pod_create") for r in RUNS}
    w("- **Failed creates cost nothing** but delay work: " + ", ".join(f"{n} in `{r}`" for r, n in nfc.items() if n) +
      " (RunPod refused the request: no instances available, or a server error). One failed restart (round 1's first lead, no free GPU "
      "on its machine) also cost nothing.")
    big = [(p, s) for p in by_run["headroom-20261005"] for s in p.segments if s.stage == "pull" and hours(s.start, s.end) > 0.05]
    if big:
        bu = sum(hours(s.start, s.end) * p.price for p, s in big)
        w(f"- **Copying full model states off the pod** (3.8 GB tars on {len(big)} round-1 hosts, {rng([hours(s.start, s.end) * 60 for p, s in big])} min each) "
          f"cost {money(bu)}. The light pull (results and receipts only, a few MB, under 10 s) replaced it from about 10:38 UTC.")
    q = [(p, s) for p in by_run["headroom-20261005"] for s in p.segments if s.stage == "finisher_latency" and hours(s.start, s.end) > 5 / 60]
    if q:
        qu = sum(hours(s.start, s.end) * p.price for p, s in q)
        w(f"- **Round 1 finished hosts one at a time:** {len(q)} removal hosts waited "
          f"{rng([hours(s.start, s.end) * 60 for p, s in q], lambda x: f'{x:.0f}')} minutes after their jobs ended while the finisher "
          f"copied other hosts' full tars ({money(qu)} idle). The finisher was then changed to finish ready hosts in parallel "
          "(its own comment: \"so none waits billed behind another's copy\").")
    fl = [hours(s.start, s.end) * 60 for p in pods for s in p.segments if s.stage == "finisher_latency"]
    if fl:
        w(f"- **Finisher latency** (job done → copy starts) was {rng(fl)} min per pod; it is set by the finisher's poll interval "
          "(120–300 s) and, in dev-matrix-002, by waiting for every unit copy to verify.")
    w("")

    # ------------------------------------------------------------------ reconciliation
    w("## 6. Reconciliation with the account balance")
    w("")
    r_run = None
    for b in L.billing:
        if b.get("disk") and b.get("gpu"):
            r_run = b["disk"] / (b["gpu"] / 1.59) / 100.0
    r_run = r_run or 0.0
    stop_rate_hi = 0.0
    for snap in L.snapshots:
        if snap.get("volume_gb_listed"):
            stop_rate_hi = snap["spend_per_hr"] / snap["volume_gb_listed"]
    w("Snapshots of the RunPod balance exist from 4 October on (none for 2 October). The account also holds pods of other projects. "
      "Rates used (both derived, not invoiced):")
    w(f"- **Disk while a pod runs:** {r_run * 1e4:.2f} × 10⁻⁴ $/GB-hour (about ${r_run * 730:.3f}/GB-month), from the provider's "
      "2 Oct billing record of one pod (`diskAmount` ÷ GPU hours ÷ 100 GB). An A100 pod here has 60 + 20 GB, so about "
      f"${80 * r_run:.4f}/h on top of $1.59.")
    w("- **Storage of stopped pods and other projects** (the *base*): the snapshot's `currentSpendPerHr` minus the pods running then "
      "(price + running disk).")
    w(f"- **Our pods stopped inside an interval** (upper bound, because deletion times are not recorded): {stop_rate_hi * 1e4:.1f} × 10⁻⁴ $/GB-hour "
      "per 20 GB volume, that is the whole storage spend rate of `account-latest.json` divided by the volumes it lists.")
    w("")
    w("| From → to (UTC) | Observed drop | GPU (ledger) | Running disk | Base storage | Stopped volumes (≤) | Expected | Difference | Reading |")
    w("|---|---|---|---|---|---|---|---|---|")
    snaps = [s for s in L.snapshots]
    recon = []
    pairs = []
    for a, b in zip(snaps, snaps[1:]):
        if (b["utc"] - a["utc"]).total_seconds() < 60:
            continue
        pairs.append((a, b))
    if snaps:
        v2a = next((s for s in snaps if s["source"].endswith("account-latest.json")), None)
        v2b = snaps[-1]
        if v2a and v2b is not v2a:
            pairs.append((v2a, v2b))
    for a, b in pairs:
        obs = a["balance"] - b["balance"]
        gpu, disk = interval_costs(L, a["utc"], b["utc"], r_run)
        base_rate = max(0.0, (a["spend_per_hr"] or 0) - running_at(L, a["utc"], r_run))
        base = base_rate * hours(a["utc"], b["utc"])
        stop_hi = stopped_volume_hi(L, a["utc"], b["utc"], stop_rate_hi)
        lo, hi = gpu + disk + base, gpu + disk + base + stop_hi
        prec = 0.01 if "2 dp" in (a["precision"], b["precision"]) else 0.0001
        if obs < lo - prec:
            diff = smoney(obs - lo)
        elif obs > hi + prec:
            diff = smoney(obs - hi)
        else:
            diff = "within rounding"
        recon.append((a, b, obs, lo, hi))
        if obs > hi + max(prec, 0.5):
            reading = ("**not explained by this project's records.** Candidates: other projects' pods on the same account, storage "
                       "of stopped pods (deletion times unknown), billing granularity. Check RunPod's billing history.")
        elif obs < lo - max(prec, 0.05):
            reading = "the balance trails the ledger by about 4 minutes of one pod; consistent with a short debit delay (it does not grow)"
        else:
            reading = "agrees within rounding (balances in budget-checks.jsonl are rounded to cents)" if prec == 0.01 else "agrees"
        w(f"| {a['utc']:%m-%d %H:%M:%S} → {b['utc']:%m-%d %H:%M:%S} | {money(obs)} | {money(gpu)} | {money(disk)} | {money(base)} | "
          f"{money(stop_hi)} | {money(lo) if abs(hi - lo) < 0.005 else money(lo) + '–' + money(hi)} | {diff} | {reading} |")
    w("")
    big = [x for x in recon if x[2] > x[4] + 0.5]
    small = [x for x in recon if x not in big]
    if big:
        a, b, obs, lo, hi = big[0]
        w(f"**Reading.** Wherever this project's pods explain the account, the ledger agrees with the balance to within about $0.12, "
          f"and the remaining difference is a short debit delay. One interval does not reconcile: from {a['utc']:%d %b %H:%M} to "
          f"{b['utc']:%d %b %H:%M} UTC the balance fell {money(obs)}, while this project's pods, their disks and the storage explain "
          f"{money(lo)}–{money(hi)}. The {money(obs - hi)}–{money(obs - lo)} left over is **not in these records**. The account also holds "
          "other projects' pods (listed in `tmp/pod-timer-check-20261004/precheck.json`); their use in that window, or storage of stopped "
          "pods whose deletion times are unknown, would explain it. RunPod's billing history for 4–5 October can settle it.")
        w("")
    w("Snapshot sources: `tmp/pod-timer-check-20261004/precheck.json` and `after.json` (exact), "
      "`tmp/headroom-20261005/account-latest.json` (exact), `tmp/headroom-v2/budget-checks.jsonl` (rounded to cents).")
    w("")

    # ------------------------------------------------------------------ local
    w("## 7. Local compute (no cloud cost)")
    w("")
    if L.local:
        for x in L.local:
            h = hours(x["start"], x["end"])
            title = x.get("title") or x["detail"]
            w(f"- **{title}: {h:.2f} h** ({iso(x['start'])} → {iso(x['end'])}). **Estimated** from the file system's birth and "
              f"last-modification times of `{x['source']}`; no receipt exists. {x['detail'][:1].upper() + x['detail'][1:]}. $0 cloud cost.")
        judge = next((x for x in L.local if x["activity"] == "evaluation"), None)
        if judge and judge.get("items"):
            per = hours(judge["start"], judge["end"]) * 3600 / judge["items"]
            w(f"- That is at most {per:.1f} s per judged answer on the Mac (about {per / 0.175:.0f}× the A100 guard's time per answer, "
              "for a larger judge at 4 bits). The grant dossier states \"about 1.5 hours\"; the file times give the longer span, which "
              "may include pauses.")
    else:
        w("- No local compute record found.")
    w("- Other local work (analysis scripts, the ToxicBERT regrade, the noise analysis) has no timing record.")
    w("")

    # ------------------------------------------------------------------ not measured
    w("## 8. Not measured yet (needed for the decision study)")
    w("")
    j0 = next((j for j in L.jobs if j.run == "headroom-v2" and j.meta.get("trainable")), None)
    npar = j0.meta["trainable"] if j0 else 73862144
    w("- **Attribution, any method.** No attribution was computed at study scale. The only timing is a toy in the 2 Oct pilot "
      "(0.5B model, 12 examples, about 1.5 s per call on an RTX A5000). Needed per method on the same A100:")
    w("  - one-off setup (gradient features or caches, curvature fits) in GPU-seconds;")
    w("  - cost per query (per scored training row and per query set);")
    w("  - storage written and kept (GB, GB-months), and peak memory.")
    w("- **Methods to time:** the protocol's per-example LoRA-gradient features (`checkpoint_gradsim`, "
      "`adam_diag_preconditioned_dot`), RepSim/DRA, TracIn-style LoRA gradients over checkpoints, and EK-FAC/SOURCE.")
    w(f"- **Sizing arithmetic, not a measurement:** one per-example gradient of the {fmt_int(npar)} trainable values is "
      f"{npar * 4 / 1e6:.0f} MB in float32 ({npar * 8 / 1e6:.0f} MB in float64). For 10,148 rows that is "
      f"{npar * 4 * 10148 / 1e12:.1f} TB per checkpoint in float32. So these methods need projection or on-the-fly scoring; "
      "the stored size depends on the projection dimension, which is not chosen yet.")
    ep = [j.segments.get("init->q", (0, 0))[0] + j.segments.get("q->e1", (0, 0))[0] for j in L.jobs
          if j.run == "headroom-v2" and j.segments.get("q->e1") and j.segments.get("init->q")]
    w("- **Time by analogy (an estimate, not a measurement):** one forward and backward pass over every training row costs about one "
      f"epoch of training. At v2 speed one epoch (init→q plus q→e1) took {mins(mean(ep))} min ({money(mean(ep) / 3600 * 1.59)}), "
      "so a full gradient pass is of that order per checkpoint, and more if per-example gradients need smaller batches.")
    w("- **Pilot (short) runs as decision inputs:** the q checkpoint inside full jobs is measured (section 4.2), but no stand-alone pilot "
      "run has been timed, and its fixed costs (setup, preflight, evaluation) would not be shared with a full job.")
    w("- **Amortization over decisions:** cost per decision = (setup + queries × cost per query) ÷ decisions served. Neither the "
      "number of decisions per setting nor the reuse of features across decisions is recorded yet.")
    w("- **Held-out evaluation, selector seeds, human audit and API judges:** not run yet, so not costed.")
    w("- **Storage GB-months:** stopped volumes (20 GB per pod) bill until deletion, but deletion times are not recorded.")
    w("- **Larger models** (7B replication, 32B check): no runs yet; scale factors would be guesses.")
    w("")

    # ------------------------------------------------------------------ checklist
    w("## 9. Recording checklist for every future run")
    w("")
    w("Suggestions only; the run kit is not changed by this ledger. File names refer to the kit in `tmp/headroom-v2/`.")
    w("")
    w("| Record | Why | Where to log it |")
    w("|---|---|---|")
    checklist = [
        ("Pod price, GPU type, cloud type, container and volume GB at create", "dollars per pod; already logged", "`host.py create` → `pod.json` (keep)"),
        ("RunPod's own stop time (`lastStatusChange` 'Exited') after every stop", "exact billed end; today only some pods have it",
         "`host.py stop`: call `get` after the stop and save `pod-latest.json`"),
        ("Pod deletion time and the volume GB kept until then", "storage GB-months; not recorded today", "a `host.py delete` record, or a note in `finished.json`"),
        ("SSH-ready time and each transfer's start, end and bytes", "create wait vs transfer; log lines are completion-only today",
         "`orchestrate.py` `log()`: add `start_utc` and `bytes` to `checked`, `send` and `fetch` events"),
        ("Finisher detection time, pull start and end, stop result, poll interval", "idle and copy cost", "`finisher.py` `log()` (pull start is only in the tar name today)"),
        ("Process receipts for every on-pod step, including the outer drivers and the lead pipeline", "exact phase times",
         "`process_receipt.py` (already); pull `job-outer` and `lead-outer` in round-1-style kits too"),
        ("Engine stage ledger with GPU-seconds, items and tokens per stage", "unit costs per item and per step", "engine `ledger.jsonl` (already; keep `seconds`, counts and tokens)"),
        ("Attribution: per method, setup GPU-seconds, per-query GPU-seconds, bytes written, peak memory, method version and projection size",
         "cost curves per method; nothing exists yet", "new engine ledger stages (for example `attr_setup`, `attr_query`) in the same `ledger.jsonl`"),
        ("Balance and spend rate at each create, stop and lease, at full precision", "reconciliation; budget-checks rounds to cents",
         "`budget.py` (log `clientBalance` unrounded; add a periodic snapshot)"),
        ("Every lease extension (old stop, new stop, lease id)", "commitments and audit; today only in a handoff note", "`hosts/HOST/leases.jsonl`, written by the caller of `extend_cap.py`"),
        ("Failed and abandoned attempts with a machine-readable reason, and operator holds", "failure overhead; dev05's hold has no reason",
         "`hosts/HOST/attempt-N.json` (kept today) plus an `orchestrate.py` `hold` event"),
        ("Local runs (Mac): start, end, device and items, under `process_receipt.py`", "local compute has no receipt today", "wrap local scripts such as `second_judge_local.py`"),
        ("Decision link: which run or pilot fed which decision", "amortization over decisions", "a `decision_id` field in `plan.json` hosts and in the decision log"),
    ]
    for a, b, c in checklist:
        w(f"| {a} | {b} | {c} |")
    w("")
    w("Align the names with the decision protocol's cost fields (`cost_source`, physical seconds, lower bounds when a record is missing) "
      "so the study's cost scopes can read these records directly.")
    w("")

    # ------------------------------------------------------------------ limits
    w("## 10. Method and limits")
    w("")
    w("- **Billed span:** RunPod's start (`lastStartedAt` / `createdAt`) to RunPod's 'Exited' time where a refreshed record has it, else the "
      "accepted stop request. Billing granularity is not recorded locally; seconds are used.")
    w("- **Estimated rows:** the first round-1 lead after its bootstrap (no receipts retrieved: the scoring duration is copied from the "
      "replacement lead's byte-identical run); the 2 Oct pods' end (upper bound at the SSH loss); the 2 Oct pilot's setup window; the "
      "4 Oct timer pod's GPU type (matched by price); the local judge's span (file times).")
    w("- **Log-time rows:** pod creation wait, bundle transfer and the attempt-1 removal hosts come from orchestrator logs at "
      "second resolution, which can lag by up to one poll interval.")
    w("- **Not in the CSV:** disk and storage charges (see section 6), the account's other projects, and engineering or AI-tool time.")
    w("- **Privacy:** pod IP addresses and ports are never read into the outputs; the script refuses to write an IPv4 address.")
    w("- **Re-run:** `python3 tmp/cost-ledger/cost_ledger.py` (or `--dry-run`, or `--now` to fix the provisional end). New v2 hosts "
      "are picked up from `tmp/headroom-v2/hosts/`.")
    if L.warnings:
        w("- **Warnings at build:** " + "; ".join(L.warnings))
    w("")
    return "\n".join(out)


if __name__ == "__main__":
    sys.exit(main())
