"""Synthetic stage-1 kit folders in the engine's real layout (tests only; no real data; every draw is seeded).

``make(root, reading)`` writes, under ``root``:
- ``repo/``: block A's re-judged units (a0 and R at 1101-1103 at checkpoint e1, theta0 at init) in the engine's unit
  layout, the frozen coherence bars file (copied from this repository by its pin) and a rules module ``rules.py``
  that is the kit's stage1_rules.py with REJUDGED_PINS replaced by these synthetic pins;
- ``kit/``: plan.json (the plan-A/B code, hosts with record-done's job records), retrieved/HOST/tree/ with every unit
  (engine run-one units round1/<seed>-<engine arm>-e1-a1 with eval/e1/{samples, guard_samples, guard, generations,
  query_loss}.jsonl and summary.json, COMPLETE.json last with the SHA-256 of every other file; the O-ext folders
  job-I/oext of oext_unit.py: oext_guard.jsonl, oext_generations.jsonl, oext_summary.json, dev100/ when generated;
  B10 units job-I/evals/<seed>-<label> and job-I/eval-<point> with the O-ext files beside the engine's), judges/BLOCK/
  in Gate B's write_files format with judge-files-index.json, and seals/block-BLOCK.json as seal.py writes it;
- ``b14/``: B14's strata.json (B14's own overlap_strata.strata on synthetic similarities) and overlap_report.json
  (B14's own cell_u, contrast and verdict on the units' Unsafe counts, with the units' SHA-256), both in B14's
  canonical JSON.

Every answer text, judge raw output and judge count holds a sentinel, so a test can show that no value reaches the
builder's output streams. ``Synth`` keeps the raw counts so tests compute expected means by hand.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import shutil
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from experiments.safety_selection.common import canonical_json as b14_canonical
from scripts.stage1 import s1common as s1
from scripts.stage1_s1 import overlap_strata as b14
from scripts.stage1_s1.reading.settings import design

# the workspace that holds the engine (under the mutation runner the package under test is a copy that holds only
# scripts/stage1_s1, and the engine, the kit's rules and the bars file come from the workspace)
TREE = Path(importlib.util.find_spec("experiments.safety_selection").origin).resolve().parents[2]
REAL_RULES = TREE / "runkit" / "stage1-olmo" / "stage1_rules.py"
BARS = "experiments/safety_selection/configs/family-probe-reading-amended-20261008.json"
TEXT = "SENTINEL-TEXT-q9x7"                       # in every answer and judge text
LOSS_SENTINEL = 7.777777777777                     # one task loss of one unit
JUDGE_SENTINEL = 4242                              # every judge file's counts
HARM = [f"p{i:03d}" for i in range(200)]
DEV = [f"d{i:03d}" for i in range(100)]
PH = [f"ph{i:03d}" for i in range(400)]
QUERIES = [f"q{i:03d}" for i in range(200)]
QUERY_BANK = "b" * 64
CODE = {"plan_a": "A", "plan_a_block_a_only": "A", "plan_b": "B"}
BLOCKS = {"plan_a": ("A", "B"), "plan_a_block_a_only": ("A",), "plan_b": ("A", "B", "C")}
SEED_PLAN = {"plan_a": "d1_plan_a", "plan_a_block_a_only": "block_a_only", "plan_b": "plan_b"}
REUSED = (1101, 1102, 1103)
JUDGE_NAMES = {"harmbench": "cais/HarmBench-Mistral-7b-val-cls", "granite": "granite-guardian-3.3-8b"}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def jsonl(rows) -> bytes:
    return b"".join(json.dumps(r, sort_keys=True).encode() + b"\n" for r in rows)


def jbytes(doc) -> bytes:
    return (json.dumps(doc, sort_keys=True, indent=1) + "\n").encode()


def write(path: Path, data: bytes) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return sha(data)


def edit_sha(arm: str, seed: int) -> str:
    return sha(f"edit {arm} {seed if arm == 'R' else ''}".encode())


def engine_arm(arm: str, seed: int) -> str:
    return "a0" if arm in ("a0", "G", "bqi") else f"edit-{edit_sha(arm, seed)}"


def complete(folder: Path, extra: dict) -> str:
    """COMPLETE.json last, with the SHA-256 of every other file (ledger.write_complete); returns its SHA-256."""
    files = {p.relative_to(folder).as_posix(): sha(p.read_bytes()) for p in sorted(folder.rglob("*"))
             if p.is_file() and p.name not in ("COMPLETE.json", "status.json")}
    doc = {"complete": True, "completed_utc": "2026-10-29T00:00:00Z", **extra, "files": files}
    return write(folder / "COMPLETE.json", jbytes(doc))


@dataclass
class Cell:
    """The raw synthetic values of one evaluation: Unsafe counts per prompt, losses, O flags (stored dev, cut, PHTest)."""
    unsafe: dict
    invalid: dict
    controversial: dict
    unscored: dict
    capped: int
    failing: int
    loss: dict
    dev: dict                                       # pid -> (valid, refusal)
    cut: dict                                       # pid -> (valid, refusal), dev prompts longer than the cut
    ph: dict                                        # pid -> (valid, refusal)
    samples: list = field(default_factory=list)


def make_cell(rng, u_level: float, l_level: float, o_level: float, sentinel_loss: bool = False) -> Cell:
    base = rng.uniform(-0.2, 0.2, len(HARM))
    rate = np.clip(u_level + base + rng.normal(0, 0.03), 0.0, 1.0)
    unsafe = {p: int(rng.binomial(3, r)) for p, r in zip(HARM, rate)}
    invalid, controversial, unscored, samples = {}, {}, {}, []
    capped = failing = 0
    for p in HARM:
        invalid[p] = controversial[p] = unscored[p] = 0
        for k in range(3):
            is_unsafe = k < unsafe[p]
            roll = rng.random()
            stop = "max_new_tokens" if roll < 0.03 else "eos"
            tokens = int(rng.integers(1, 300))
            rep = float(rng.choice([0.0, 0.1, 0.6])) if rng.random() < 0.3 else None
            empty = tokens == 1 and rng.random() < 0.5
            fails = stop == "max_new_tokens" or (rep is not None and rep >= 0.5) or empty or tokens < 5
            capped += stop == "max_new_tokens"
            failing += fails
            if is_unsafe:
                guard = {"valid": True, "safety": "Unsafe", "reason": None}
            else:
                r2 = rng.random()
                if r2 < 0.04:
                    guard = {"valid": False, "safety": None, "reason": "guard input over limit; not scored"}
                    invalid[p] += 1
                    unscored[p] += 1
                elif r2 < 0.10:
                    guard = {"valid": True, "safety": "Controversial", "reason": None}
                    controversial[p] += 1
                else:
                    guard = {"valid": True, "safety": "Safe", "reason": None}
            samples.append((p, k, stop, tokens, rep, empty, guard))
    loss = {q: float(abs(l_level + rng.normal(0, 0.3)) + 0.01) for q in QUERIES}
    if sentinel_loss:
        loss[QUERIES[7]] = LOSS_SENTINEL

    def flag(prob):
        if rng.random() < 0.02:
            return (False, None)
        return (True, "Yes" if rng.random() < prob else "No")

    dev = {d: flag(o_level) for d in DEV}
    cut = {d: flag(o_level) for d in DEV[::7]}
    ph = {p: flag(o_level) for p in PH}
    return Cell(unsafe, invalid, controversial, unscored, capped, failing, loss, dev, cut, ph, samples)


def o_flags_of(cell: Cell, branch: str = "128") -> dict:
    """The primary O flag per prompt, by hand (oext_eval's table): Branch 128 the cut flag where a cut exists."""
    out = {}
    for d, f in cell.dev.items():
        g = cell.cut[d] if branch == "128" and d in cell.cut else f
        out[d] = int(g[0] and g[1] == "Yes")
    for p, f in cell.ph.items():
        out[p] = int(f[0] and f[1] == "Yes")
    return out


def eval_folder(folder: Path, cell: Cell, target: str, with_dev: bool = True) -> dict:
    """The engine's evaluation files of one checkpoint; returns summary.json's document."""
    ev = folder / "eval" / target
    rows_a, rows_g = [], []
    for (p, k, stop, tokens, rep, empty, guard) in cell.samples:
        rows_a.append({"prompt_id": p, "kind": "harm", "sample_index": k, "seed": 1, "answer_id": f"{p}#s{k}",
                       "output_ids": [1] * min(tokens, 3), "output_tokens": tokens, "stop_reason": stop,
                       "stop_token": None, "empty": empty, "text": f"{TEXT} answer {p} {k}", "repetition_4gram": rep})
        rows_g.append({"prompt_id": p, "sample_index": k, "refusal": "No", "categories": ["Violent"],
                       "raw": f"{TEXT} judge", "guard_input_tokens": 10, "guard_output_tokens": 3, **guard})
    write(ev / "samples.jsonl", jsonl(rows_a))
    write(ev / "guard_samples.jsonl", jsonl(rows_g))
    greedy = [{"prompt_id": p, "kind": "harm", "valid": True, "safety": "Safe", "refusal": "Yes", "raw": TEXT}
              for p in HARM[:5]]
    dev_rows = [{"prompt_id": d, "kind": "overrefusal", "valid": v, "refusal": r, "safety": "Safe", "raw": TEXT}
                for d, (v, r) in cell.dev.items()] if with_dev else []
    write(ev / "guard.jsonl", jsonl(greedy + dev_rows))
    write(ev / "generations.jsonl", jsonl([{"prompt_id": d, "kind": "overrefusal", "text": f"{TEXT} dev {d}"}
                                           for d in DEV]))
    write(ev / "query_loss.jsonl", jsonl([{"query_id": q, "input_tokens": 9, "target_tokens": 4,
                                           "token_sha256": "c" * 64, "loss": v} for q, v in cell.loss.items()]))
    unsafe = sum(cell.unsafe.values())
    summary = {"checkpoint": target,
               "query_loss": {"n": len(cell.loss), "mean": sum_exact(cell.loss.values()) / len(cell.loss),
                              "query_bank_sha256": QUERY_BANK, "forward_passes": 200},
               "harm": {"prompts": 200, "greedy": {"unsafe": 0},
                        "sampled": {"per_prompt": 3, "answers": len(cell.samples), "unsafe": unsafe,
                                    "invalid": sum(cell.invalid.values()), "capped": cell.capped}}}
    write(ev / "summary.json", jbytes(summary))
    return summary


def sum_exact(values) -> float:
    import math
    return math.fsum(values)


def oext_files(folder: Path, cell: Cell, branch: str, dev_rows_sha: str | None = None) -> dict:
    """oext_eval's three output files in ``folder``; returns the summary document."""
    rows = [{"prompt_id": p, "source": "phtest", "form": "answer", "role": "primary", "valid": v, "refusal": r,
             "safety": "Safe", "judged_tokens": 50, "text": f"{TEXT} ph {p}"} for p, (v, r) in cell.ph.items()]
    cut_role = "primary" if branch == "128" else "sensitivity"
    rows += [{"prompt_id": d, "source": "dev100", "form": "cut", "role": cut_role, "valid": v, "refusal": r,
              "safety": "Safe", "judged_tokens": 128, "text": f"{TEXT} cut {d}"} for d, (v, r) in cell.cut.items()]
    write(folder / "oext_guard.jsonl", jsonl(rows))
    write(folder / "oext_generations.jsonl", jsonl([{"prompt_id": p, "kind": "oext_phtest", "text": TEXT}
                                                    for p in PH]))
    flags = o_flags_of(cell, branch)

    def block(ids, table):
        return {"prompts": len(ids), "refused": sum(flags[i] for i in ids),
                "invalid": sum(not table[i][0] for i in ids), "o": None}

    dev_table = {d: (cell.cut[d] if branch == "128" and d in cell.cut else cell.dev[d]) for d in DEV}
    o = {"pooled": {k: block(DEV, dev_table)[k] + block(PH, cell.ph)[k] for k in ("prompts", "refused", "invalid")},
         "by_source": {"dev100": block(DEV, dev_table), "phtest": block(PH, cell.ph)}}
    o["pooled"]["o"] = None
    summary = {"kind": "stage1 o-ext evaluation", "version": 1, "checkpoint": "e1", "branch": branch,
               "bank": {"prompts": 500, "dev100": 100, "phtest": 400}, "o": o,
               "answers": {"dev100": {"answers": 100, "longer_than_cut": len(cell.cut)},
                           "phtest": {"answers": 400, "longer_than_cut": 0}}}
    write(folder / "oext_summary.json", jbytes(summary))
    return summary


def dev_guard_rows(cell: Cell) -> bytes:
    return jsonl([{"prompt_id": d, "kind": "overrefusal", "valid": v, "refusal": r, "raw": TEXT}
                  for d, (v, r) in cell.dev.items()])


@dataclass
class Synth:
    root: Path
    reading: str
    kit: Path
    repo: Path
    rules: Path
    cells: dict = field(default_factory=dict)       # (arm, seed) -> Cell (primary)
    refs: dict = field(default_factory=dict)        # (name, seed) -> Cell
    theta0: Cell | None = None
    theta0_o: Cell | None = None
    units: dict = field(default_factory=dict)       # (arm, seed) -> {complete, job, guard_samples} SHA-256
    b14: dict = field(default_factory=dict)         # strata, report paths and SHA-256
    branch: str = "128"

    def args(self, out: Path, record: Path, overlap: bool = True) -> list[str]:
        a = ["--reading", self.reading, "--kit", str(self.kit), "--repo", str(self.repo), "--rules", str(self.rules),
             "--out", str(out), "--record", str(record)]
        if overlap and self.b14:
            a += ["--b14-strata", str(self.b14["strata"]), "--b14-report", str(self.b14["report"]),
                  "--expect-strata-sha256", self.b14["strata_sha256"], "--expect-report-sha256",
                  self.b14["report_sha256"]]
        else:
            a += ["--no-overlap"]
        return a

    def plan(self) -> dict:
        return json.loads((self.kit / "plan.json").read_text())

    def save_plan(self, plan: dict) -> None:
        (self.kit / "plan.json").write_bytes(jbytes(plan))

    def reseal(self, block: str) -> None:
        """Re-take block BLOCK's seal from the trees and judge files on disk (a hash-consistent edit)."""
        plan = self.plan()
        seal_block(self.kit, plan, block)
        self.save_plan(plan)


def u_level(arm: str) -> float:
    return {"a0": 0.55, "R": 0.5, "A1": 0.42, "L1": 0.47, "H1": 0.49, "S1": 0.35, "S3": 0.38, "S4": 0.4}.get(arm, 0.45)


def write_engine_unit(folder: Path, cell: Cell, arm: str, seed: int, target: str = "e1") -> dict:
    job = {"kind": "run-one", "arm": engine_arm(arm, seed), "seed": seed, "target_checkpoint": target,
           "evaluate_bank": "dev", "split": "dev", "role": "development"}
    job_sha = write(folder / "job.json", jbytes(job))
    summary = eval_folder(folder, cell, target)
    c = complete(folder, {"kind": "run-one", "identity": {}, "job_sha256": job_sha, "target_checkpoint": target,
                          "trajectory": {"arm": job["arm"], "seed": seed}, "evaluation": summary})
    return {"complete": c, "job": job_sha,
            "guard_samples": sha((folder / "eval" / target / "guard_samples.jsonl").read_bytes())}


def write_oext_pass(folder: Path, cell: Cell, branch: str, state: str, route: str, unit_complete: str | None,
                    dev_guard_sha: str | None, source_complete: str | None = None) -> str:
    """oext_unit.py's folder (job.json, the O-ext files, dev100/ when generated, COMPLETE.json last)."""
    job_sha = write(folder / "job.json", jbytes({"kind": "stage1-oext-unit", "version": 1, "command": "run",
                                                  "state": state}))
    if route == "generated":
        dev_guard_sha = write(folder / "dev100" / "guard.jsonl", dev_guard_rows(cell))
        write(folder / "dev100" / "generations.jsonl", jsonl([{"prompt_id": d, "text": TEXT} for d in DEV]))
    oext_files(folder, cell, branch)
    return complete(folder, {
        "kind": "stage1-oext-unit", "identity": {}, "job_sha256": job_sha, "command": "run", "state": state,
        "branch": branch, "dev100_route": route, "checkpoint": "untuned" if state == "untuned" else "e1",
        "unit": None if unit_complete is None else {"complete_sha256": unit_complete, "state_sha256": "d" * 64},
        "dev100_source": None if source_complete is None else {"complete_sha256": source_complete},
        "dev100_inputs": {"dev100/generations.jsonl": "e" * 64, "dev100/guard.jsonl": dev_guard_sha},
        "summary_file": {"oext_summary.json": sha((folder / "oext_summary.json").read_bytes())}})


def write_b10_unit(folder: Path, cell: Cell, seed: int, mode: str, scale: float, external: str | None,
                   branch: str) -> str:
    job = {"kind": "stage1-eval-adapter", "checkpoint": "e1", "evaluate_bank": "dev", "seed": seed, "mode": mode,
           "adapter_scale": scale, "external": None if external is None else {"name": external, "kind": "file"}}
    job_sha = write(folder / "job.json", jbytes(job))
    summary = eval_folder(folder, cell, "e1")
    oext = oext_files(folder / "eval" / "e1", cell, branch)
    return complete(folder, {"kind": "stage1-eval-adapter", "identity": {}, "job_sha256": job_sha, "seed": seed,
                             "mode": mode, "adapter_scale": scale, "checkpoint": "e1", "evaluation": summary,
                             "oext": oext})


# ----- the kit ------------------------------------------------------------------------------------------------------


def seal_block(kit: Path, plan: dict, block: str) -> None:
    files = []
    for host in sorted(plan["hosts"]):
        h = plan["hosts"][host]
        if h["block"] != block:
            continue
        tree = kit / "retrieved" / host / "tree"
        if not tree.is_dir():
            continue
        for p in sorted(tree.rglob("*")):
            if p.is_file():
                files.append({"host": host, "path": p.relative_to(tree).as_posix(), "sha256": sha(p.read_bytes()),
                              "class": "sealed"})
    folder = kit / "judges" / block
    index_sha = None
    if folder.is_dir():
        for p in sorted(folder.rglob("*")):
            if p.is_file():
                files.append({"host": f"judges/{block}", "path": p.relative_to(folder).as_posix(),
                              "sha256": sha(p.read_bytes()), "class": "sealed"})
        if (folder / "judge-files-index.json").is_file():
            index_sha = sha((folder / "judge-files-index.json").read_bytes())
    old = plan.get("seals", {}).get(block, {})
    old_doc = json.loads((kit / old["path"]).read_text()) if old else {}
    rec = {"kind": "stage1 block seal", "version": 1, "block": block, "utc": "2026-10-29T00:00:00Z",
           "hosts": sorted(n for n, h in plan["hosts"].items() if h["block"] == block), "files": files,
           "counts": {"files": len(files)}, "not_run": old_doc.get("not_run", []), "not_pulled": [],
           "moved": old_doc.get("moved", []),
           "judge_record": None if index_sha is None else {"record_sha256": "f" * 64, "index_sha256": index_sha,
                                                           "judges": ["granite", "harmbench"], "units": 0,
                                                           "files": 0, "other_files": 0},
           "judge_not_run": old_doc.get("judge_not_run", [])}
    path = kit / "seals" / f"block-{block}.json"
    data = jbytes(rec)
    write(path, data)
    plan.setdefault("seals", {})[block] = {"path": f"seals/block-{block}.json", "sha256": sha(data),
                                           "files": len(files)}


def write_judges(kit: Path, block: str, units: list) -> None:
    """Gate B's write_files output for ``units`` [(host, unit name, complete SHA-256, arm, seed, target)]."""
    folder = kit / "judges" / block
    entries = []
    for host, name, digest, arm, seed, target in units:
        for key, judge in sorted(JUDGE_NAMES.items()):
            fname = f"{key}--{host}--{name}--{digest[:12]}.json"
            doc = {"kind": "gate-b judge file", "version": 1, "judge": {"name": judge, "revision": "r"}, "arm": arm,
                   "seed": seed, "host": host, "complete_sha256": digest, "job_sha256": "0" * 64,
                   "greedy": {"n": JUDGE_SENTINEL, "harm": JUDGE_SENTINEL, "unparsed": 0},
                   "sampled": None if key == "granite" else {"n": JUDGE_SENTINEL, "harm": 1, "unparsed": 0}}
            data = (json.dumps(doc, sort_keys=True, indent=2) + "\n").encode()
            entries.append({"file": fname, "sha256": write(folder / fname, data), "judge": judge, "arm": arm,
                            "seed": seed, "host": host, "unit": name, "target": target,
                            "completed_utc": "2026-10-29T00:00:00Z", "complete_sha256": digest})
    index = {"kind": "gate-b judge files index", "version": 2, "complete_allowlist": [], "files": entries}
    write(folder / "judge-files-index.json", (json.dumps(index, sort_keys=True, indent=2) + "\n").encode())


def rules_module(path: Path, pins: list) -> None:
    text = (f"import importlib.util as _u\n_s = _u.spec_from_file_location('_real_stage1_rules', {str(REAL_RULES)!r})\n"
            "_m = _u.module_from_spec(_s)\n_s.loader.exec_module(_m)\n"
            "globals().update({k: v for k, v in vars(_m).items() if not k.startswith('__')})\n"
            f"REJUDGED_PINS = {{'B': (), 'A': tuple({json.dumps(pins)})}}\n")
    write(path, text.encode())


def make(root: Path, reading: str = "plan_a", seed: int = 0, branch: str = "128", refs: bool = True,
         ref_seeds=(1105, 1106, 1107)) -> Synth:
    root = Path(root)
    rng = np.random.default_rng(seed)
    kit, repo = root / "kit", root / "repo"
    s = Synth(root, reading, kit, repo, repo / "rules.py", branch=branch)
    dsg = design(reading)
    code = CODE[reading]
    write(repo / BARS, (TREE / BARS).read_bytes())
    import runpy
    rules = runpy.run_path(str(REAL_RULES))
    shift = {j: rng.normal(0, 0.02) for j in range(1101, 1111)}

    def new_cell(arm, j, sentinel=False):
        return make_cell(rng, u_level(arm) + shift[j], 1.0 + 0.01 * (arm == "S1"), 0.12, sentinel)

    # block A's re-judged pins in the repo
    pins, pin_path = [], {}
    for arm in ("a0", "R"):
        for j in REUSED:
            cell = new_cell(arm, j)
            s.cells[(arm, j)] = cell
            rel = f"tmp/synth-gate/{j}-{engine_arm(arm, j)}-e1-a1"
            u = write_engine_unit(repo / rel, cell, arm, j)
            s.units[(arm, j)] = u
            pin_path[(arm, j)] = rel
            pins.append({"name": f"{arm} {j} (synthetic)", "arm": engine_arm(arm, j), "seed": j, "target": "e1",
                         "path": rel, "complete_sha256": u["complete"], "job_sha256": u["job"]})
    s.theta0 = make_cell(rng, 0.2, 0.9, 0.17)
    rel = "tmp/synth-gate/1101-a0-init-a1"
    u = write_engine_unit(repo / rel, s.theta0, "a0", 1101, target="init")
    s.units[("theta0", None)] = u
    pins.append({"name": "theta0 (synthetic)", "arm": "a0", "seed": 1101, "target": "init", "path": rel,
                 "complete_sha256": u["complete"], "job_sha256": u["job"]})
    rules_module(s.rules, pins)

    plan = {"name": "stage1-olmo", "records": {"plan_ab": {"code": code}, "oext_fallback": None,
                                               "block_a_not_run": []},
            "blocks": {}, "hosts": {}, "seals": {}, "deferrals": [], "requeues": []}
    judged: dict = {b: [] for b in BLOCKS[reading]}

    def host(name, block):
        plan["hosts"][name] = {"block": block, "done": True, "jobs": []}
        return kit / "retrieved" / name / "tree"

    # block A's LN-12 pod: J2/J3 pairs on the reused units, theta0's J3, c0 and a not-pulled retrain
    tree = host("a-2", "A")
    jobs = plan["hosts"]["a-2"]["jobs"]
    for arm in ("a0", "R"):
        for j in REUSED:
            regen_rel = f"round1/{j}-{arm}-regen-a1"
            write(tree / regen_rel / "job.json", jbytes({"kind": "run-one", "arm": engine_arm(arm, j), "seed": j}))
            regen_c = complete(tree / regen_rel, {"kind": "run-one", "job_sha256": "0" * 64})
            jobs.append({"kind": "regenerate", "arm": arm, "seed": j, "engine": "X", "status": "complete",
                         "unit": regen_rel, "complete_sha256": regen_c, "outputs": None, "reason": None})
            i = len(jobs)
            src_guard = sha((repo / pin_path[(arm, j)] / "eval" / "e1" / "guard.jsonl").read_bytes())
            c = write_oext_pass(tree / f"job-{i}" / "oext", s.cells[(arm, j)], branch, "run", "source_unit",
                                regen_c, src_guard, source_complete=s.units[(arm, j)]["complete"])
            jobs.append({"kind": "o_only", "arm": arm, "seed": j, "engine": "X", "regen_source": i - 1,
                         "status": "complete", "unit": None, "complete_sha256": None,
                         "outputs": _outputs(tree, f"job-{i}/oext"), "reason": None})
    s.theta0_o = make_cell(rng, 0.2, 0.9, 0.17)
    i = len(jobs)
    write_oext_pass(tree / f"job-{i}" / "oext", s.theta0_o, branch, "untuned", "generated", None, None)
    jobs.append({"kind": "o_only", "arm": "theta0", "seed": None, "engine": "X", "status": "complete", "unit": None,
                 "complete_sha256": None, "outputs": _outputs(tree, f"job-{i}/oext"), "reason": None})
    i = len(jobs)
    write(tree / f"job-{i}" / "c0" / "lean.json", jbytes({"kind": "c0", "text": TEXT}))
    jobs.append({"kind": "c0", "arm": "R", "seed": 1101, "engine": "X", "status": "complete", "unit": None,
                 "complete_sha256": None, "outputs": _outputs(tree, f"job-{i}/c0"), "reason": None})
    jobs.append({"kind": "retrain", "arm": "a0", "seed": 1102, "engine": "X", "status": "complete",
                 "unit": "rescore/1102-a0-retrain-a1", "complete_sha256": "9" * 64, "outputs": None, "reason": None,
                 "pulled": False, "unpulled_decision_sha256": "8" * 64})
    for arm in ("a0", "R"):
        for j in REUSED:
            judged["A"].append(("repo", f"{j}-{arm}", s.units[(arm, j)]["complete"], engine_arm(arm, j), j, "e1"))
    judged["A"].append(("repo", "theta0", s.units[("theta0", None)]["complete"], "a0", 1101, "init"))

    # the arm launches of every block read
    for block in BLOCKS[reading]:
        runs = rules["block_runs"](code, block)
        for n in range(0, len(runs), 4):
            name = f"{block.lower()}-{3 + n // 4}"
            tree = host(name, block)
            for k, (arm, j) in enumerate(runs[n:n + 4]):
                cell = new_cell(arm, j, sentinel=(arm, j) == ("S1", 1104))
                s.cells[(arm, j)] = cell
                rel = f"round1/{j}-{engine_arm(arm, j)}-e1-a1"
                u = write_engine_unit(tree / rel, cell, arm, j)
                s.units[(arm, j)] = u
                write_oext_pass(tree / f"job-{k}" / "oext", cell, branch, "run", "unit_eval", u["complete"],
                                sha((tree / rel / "eval" / "e1" / "guard.jsonl").read_bytes()))
                job = {"kind": "a0_arm" if arm == "a0" else "arm", "arm": arm, "seed": j, "engine": "X",
                       "status": "complete", "unit": rel, "complete_sha256": u["complete"],
                       "outputs": _outputs(tree, f"job-{k}/oext"), "reason": None}
                if arm != "a0":
                    job["edit"] = {"path": f"edits/{arm}.edit.json", "sha256": edit_sha(arm, j)}
                plan["hosts"][name]["jobs"].append(job)
                judged[block].append((name, rel.split("/")[1], u["complete"], engine_arm(arm, j), j, "e1"))

    # block B's references
    if refs and "B" in BLOCKS[reading]:
        for recipe in ("G", "bqi"):
            name = f"b-ref-{recipe.lower()}"
            tree = host(name, "B")
            for k, j in enumerate(ref_seeds):
                cell = new_cell("a0", j)
                s.refs[(f"ref-{recipe}", j)] = cell
                rel = f"round1/{j}-a0-e1-a1"
                u = write_engine_unit(tree / rel, cell, recipe, j)
                write_oext_pass(tree / f"job-{k}" / "oext", cell, branch, "run", "unit_eval", u["complete"],
                                sha((tree / rel / "eval" / "e1" / "guard.jsonl").read_bytes()))
                plan["hosts"][name]["jobs"].append(
                    {"kind": "ref_train", "arm": recipe, "recipe": recipe, "seed": j, "engine": "X",
                     "status": "complete", "unit": rel, "complete_sha256": u["complete"],
                     "outputs": _outputs(tree, f"job-{k}/oext"), "reason": None})
                judged["B"].append((name, f"{j}-a0", u["complete"], f"ref-{recipe}", j, "e1"))
        tree = host("b-ref-eval", "B")
        for k, j in enumerate(ref_seeds):
            units = []
            for point in ("scale:0.9", "scale:0.75", "scale:0.5", "prefix"):
                label = point.replace(":", "-")
                cell = new_cell("a0", j)
                refname = "ref-prefix" if point == "prefix" else f"ref-scale {label[6:]}"
                s.refs[(refname, j)] = cell
                rel = f"job-{k}/evals/{j}-{label}"
                mode, scale = ("prefix", 1.0) if point == "prefix" else ("scale", float(label[6:]))
                c = write_b10_unit(tree / rel, cell, j, mode, scale, None, branch)
                units.append({"unit": rel, "complete_sha256": c})
                judged["B"].append(("b-ref-eval", f"{j}-{label}", c, f"ref-{label}", j, "e1"))
            plan["hosts"]["b-ref-eval"]["jobs"].append(
                {"kind": "ref_eval", "arm": "a0", "seed": j, "engine": "X",
                 "points": ["scale:0.9", "scale:0.75", "scale:0.5", "prefix"], "status": "complete",
                 "unit": units[0]["unit"], "complete_sha256": units[0]["complete_sha256"],
                 "units": units, "outputs": None, "reason": None})
        tree = host("b-safe-lora", "B")
        for k, j in enumerate(ref_seeds):
            units = []
            for point in ("default", "conditional", "certify"):
                cell = new_cell("a0", j)
                if point != "certify":
                    s.refs[(f"ref-external-safe_lora-{point}", j)] = cell
                rel = f"job-{k}/eval-{point}"
                c = write_b10_unit(tree / rel, cell, j, "external", 1.0, "safe_lora", branch)
                units.append({"unit": rel, "complete_sha256": c})
                judged["B"].append(("b-safe-lora", f"{j}-{point}", c, f"ref-external-safe_lora-{point}", j, "e1"))
            plan["hosts"]["b-safe-lora"]["jobs"].append(
                {"kind": "safe_lora", "arm": "a0", "seed": j, "engine": "X",
                 "points": ["default", "conditional", "certify"], "status": "complete",
                 "unit": units[0]["unit"], "complete_sha256": units[0]["complete_sha256"],
                 "units": units, "outputs": None, "reason": None})
    for block in BLOCKS[reading]:
        write_judges(kit, block, judged[block])
        seal_block(kit, plan, block)
    write(kit / "plan.json", jbytes(plan))
    make_b14(s)
    return s


def _outputs(tree: Path, rel: str) -> dict:
    base = tree / rel
    return {p.relative_to(tree).as_posix(): sha(p.read_bytes()) for p in sorted(base.rglob("*")) if p.is_file()}


# ----- B14's documents ----------------------------------------------------------------------------------------------


def make_b14(s: Synth, seed: int = 7) -> None:
    """strata.json by B14's own strata function on synthetic similarities; overlap_report.json in B14's format with
    B14's own cell_u, contrast and verdict on the synthetic Unsafe counts and the units' SHA-256."""
    settings, digest = s1.load_settings(b14.SETTINGS_PATH, b14.SETTINGS_SHA256, b14.SETTINGS_NAME)
    rng = np.random.default_rng(seed)
    sims = {m: {p: float(v) for p, v in zip(HARM, rng.uniform(0.2, 0.9, len(HARM)))} for m in ("S1", "S3", "S4")}
    sets = {m: {"edit_sha256": edit_sha(m, 0), "arm": "edit-" + edit_sha(m, 0), "row_ids": ["r0"],
                "per_prompt": {p: {"s_max": v, "nearest": "r0"} for p, v in sim.items()}} for m, sim in sims.items()}
    sim_doc = {"kind": "stage1 overlap similarity", "version": 1, "eval": {"prompt_ids": sorted(HARM)},
               "model": {"hidden_state_index": 16, "read": "last prompt position"},
               "provenance": {"settings_sha256": settings["similarity_settings_sha256"]}, "add_sets": sets}
    sim_bytes = b14_canonical(sim_doc)
    strata_bytes = b14.strata(sim_bytes, sha(sim_bytes), settings, digest)
    strata = json.loads(strata_bytes)
    rep = settings["report"]
    plan_name = SEED_PLAN[s.reading]
    plan = rep["seed_plans"][plan_name]
    seeds = plan["seeds"]
    cells = {m: {j: {p: (s.cells[(m, j)].unsafe[p], 3) for p in HARM} for j in seeds} for m in ["a0"] + plan["add_sets"]}
    out_sets = {}
    for name in plan["add_sets"]:
        block = strata["add_sets"][name]
        halves = {"all": strata["prompt_ids"], "lower": block["lower"], "higher": block["higher"]}
        results = {h: b14.contrast(cells["a0"], cells[name], seeds, ids, rep["minimum"]) for h, ids in halves.items()}
        table = {arm: {str(j): {h: (b14.cell_u(cells[arm][j], ids) if ids else None) for h, ids in halves.items()}
                       for j in seeds} for arm in ("a0", name)}
        out_sets[name] = {"arm": block["arm"], "edit_sha256": block["edit_sha256"],
                          "half_sizes": {h: len(ids) for h, ids in halves.items()},
                          "ties_at_boundary": block["ties_at_boundary"], "cells_u_pp": table, "contrasts": results,
                          "verdict": {**b14.verdict(results["all"], results["lower"], rep["texts"]),
                                      "role": rep["s_p"]["label"]}}
    units = {m: {str(j): {"path": f"x/{m}/{j}", "arm": m, "complete_sha256": s.units[(m, j)]["complete"],
                          "job_sha256": s.units[(m, j)]["job"], "code_sha256": "1" * 64,
                          "guard_samples_jsonl_sha256": s.units[(m, j)]["guard_samples"],
                          "summary_json_sha256": "2" * 64} for j in seeds} for m in ["a0"] + plan["add_sets"]}
    report = {"kind": b14.REPORT_KIND, "version": 1, "requirement": settings["requirement"], "outcome": rep["outcome"],
              "contrast": rep["contrast"], "variance_model": rep["variance_model"], "interval": rep["interval"],
              "holds_rule": rep["holds"], "s_p": rep["s_p"], "primary_model": rep["primary_model"],
              "seed_plan": plan_name, "seeds": seeds, "strata_sha256": sha(strata_bytes), "units": units,
              "add_sets": out_sets, "strata_add_sets_not_in_plan": sorted(set(strata["add_sets"]) - set(plan["add_sets"])),
              "provenance": {"synthetic": True}}
    report_bytes = b14_canonical(report)
    folder = s.root / "b14"
    write(folder / "strata.json", strata_bytes)
    write(folder / "overlap_report.json", report_bytes)
    s.b14 = {"strata": folder / "strata.json", "report": folder / "overlap_report.json",
             "strata_sha256": sha(strata_bytes), "report_sha256": sha(report_bytes)}


def copy(s: Synth, root: Path) -> Synth:
    """A copy of the synthetic world under ``root`` (for a test that edits it); the rules module is re-pointed."""
    shutil.copytree(s.root, root)
    t = Synth(root, s.reading, root / "kit", root / "repo", root / "repo" / "rules.py", dict(s.cells), dict(s.refs),
              s.theta0, s.theta0_o, dict(s.units), {}, s.branch)
    if s.b14:
        t.b14 = {**s.b14, "strata": root / "b14" / "strata.json", "report": root / "b14" / "overlap_report.json"}
    return t


def load_rules_module(path: Path):
    spec = importlib.util.spec_from_file_location("synth_rules", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


# ----- consistent edits (a test changes a file, then re-takes every hash above it) ----------------------------------


def recomplete(folder: Path, mutate=None) -> str:
    """COMPLETE.json again from the files on disk (its other keys kept, ``mutate`` applied to them)."""
    doc = json.loads((folder / "COMPLETE.json").read_text())
    for key in ("files", "complete", "completed_utc"):
        doc.pop(key, None)
    if mutate is not None:
        mutate(doc)
    (folder / "COMPLETE.json").unlink()
    return complete(folder, doc)


def rehash_job(s: Synth, host: str, i: int, plan: dict | None = None) -> dict:
    """Re-take job I of HOST's COMPLETE.json files (unit, B10 units, O-ext folder, bound to the unit), its plan.json
    record and its block's seal; returns the plan."""
    plan = plan or s.plan()
    job = plan["hosts"][host]["jobs"][i]
    tree = s.kit / "retrieved" / host / "tree"
    if job.get("units"):
        for u in job["units"]:
            u["complete_sha256"] = recomplete(tree / u["unit"])
        job["complete_sha256"] = job["units"][0]["complete_sha256"]
    elif job.get("unit") and (tree / job["unit"] / "COMPLETE.json").is_file():
        job["complete_sha256"] = recomplete(tree / job["unit"])
    if any(k.endswith("/oext/COMPLETE.json") for k in (job.get("outputs") or {})):
        def bind(doc):
            if isinstance(doc.get("unit"), dict) and job.get("unit"):
                doc["unit"]["complete_sha256"] = job["complete_sha256"]
        recomplete(tree / f"job-{i}" / "oext", bind if job["kind"] != "o_only" else None)
        job["outputs"] = _outputs(tree, f"job-{i}/oext")
    seal_block(s.kit, plan, plan["hosts"][host]["block"])
    s.save_plan(plan)
    return plan


def find_job(plan: dict, kind: str, arm=None, seed=None) -> tuple:
    for host, h in sorted(plan["hosts"].items()):
        for i, j in enumerate(h["jobs"]):
            if j["kind"] == kind and (arm is None or j.get("arm") == arm) and (seed is None or j.get("seed") == seed):
                return host, i, j
    raise KeyError((kind, arm, seed))


def unit_folder(s: Synth, host: str, job: dict) -> Path:
    return s.kit / "retrieved" / host / "tree" / job["unit"]
