"""Write and update plan.json for the Gate B kit (administrative; brief B1, B3, B4).

    python3.11 plan_tool.py init-wave W --jobs FILE [--reading FILE] [--balance FILE] [--rerun-mismatched SHA ...]
    python3.11 plan_tool.py record-done HOST     the pulled JOB-DONE.json's job statuses into plan.json
    python3.11 plan_tool.py defer HOST           move HOST's crashed, deferred and not_started jobs to the next host
    python3.11 plan_tool.py requeue HOST [--rerun-mismatched SHA ...]   a pre-job stop, or environment-mismatched attempts
    python3.11 plan_tool.py confirm-stopped HOST   the operator's record that a pre-job-stopped pod is stopped ([D17] 3)
    python3.11 plan_tool.py set-reference HOST   wave 0a's environment reference (after its PREFLIGHT-DONE)

Waves (B1, in order; each needs every job of the waves before it complete): anchor = one anchor job; 0a = R_1-R_3,
R_d at seed 1100 + d; 0b = the retrain (a0, 1101) then the diagnostics (1101), whose ``a0_source`` names that retrain;
1 = the 8 unit_g-* edit files at 1101; 2, ext and lc = exactly the runs of the reading
output (scripts/gate_b_reading.py, C4) named by --reading, whose SHA-256 goes into plan.json. [D21]: waves 1, 2, ext
and lc are split into ceil(n / gateb_rules.MAX_ARMS_PER_POD) parallel pods with the arms dealt evenly in the given order
(gateb_rules.pod_sizes: 8 -> 4 + 4, 6 -> 3 + 3, 4 -> 4); the jobs file gives such a wave as one host (the tool splits
it) or as exactly that split, and any other grouping refuses. Wave 0a stays one pod (MAX_ARMS_PER_POD >= 3). FILE is
{"hosts": [[job, ...], ...]}, each job {kind, arm, seed, edit, a0_source (diagnostics only)} with ``edit`` the MAN
path of the arm (edits/...). The tool fills steps (the engine's stream plan on the counts), upper_s,
start_requirement_s and measured_upper_s (gateb_rules), and each host's cap and guard (B4). It refuses: base_eval
true; a0 outside the retrain; a group-id or unknown arm; an edit that is not the arm's MAN file; a non-development seed;
a broken wave rule; an (arm, seed) that a pulled COMPLETE record (or the plan) shows complete, unless
--rerun-mismatched names that attempt's COMPLETE.json SHA-256 and its unit's compared fields differ from the plan's
reference (recorded); a hash named twice refuses ([D17] 6). ``init-wave 1`` refuses unless --balance (the lead's
record {usd, utc, source}) is at least gateb_rules.CONTINGENCY_FACTOR x the funding need over the worst path (B4, [D11], [D13]); the extra
(factor - 1) x is the contingency recorded in plan.json. Every re-run from wave 1 on (a --rerun-mismatched arm, a crashed job that ``defer`` moves, or every job
that ``requeue`` moves after a pre-job stop, [D16] 5) is paid from that contingency in launch order at its upper
spend (plus 42 min when it needs a new pod); when it cannot be paid the job is dropped and recorded "not re-run" (the
reading's missing-arm rules then apply). [D21] (5): with gateb_rules.GRANITE_ON_POD (pod Granite; default False, the
Mac) the need also counts a pod Granite judge launch after wave 2 and after the extension (worst_path_need), and the
funding record says which route it counted. Before wave 1 (anchor, 0a, 0b) nothing is paid from it. ``init-wave anchor`` records the
pre-wave-1 need ($21.75 with wave 0b's 4.5 h cap; [D20]) as a report, and refuses while gateb_rules.LOCK_SHA256 (Gate A's
lock, the pin the lead fills before the anchor launch) is null ([D14]).

``defer HOST`` (B3): only after record-done; never edits a launched host. The crashed, deferred and not_started jobs,
in order, go to the front of the next unlaunched host of the same wave that has room for them ([D21]: at most
MAX_ARMS_PER_POD arms per pod), or to a new host whose cap and guard come from B4. The one exception [D7]: when the first deferred job is a diagnostics job whose a0_source names a complete retrain,
that retrain is re-queued in front of it with reason "stranded-retrain" and the stranded attempt's COMPLETE.json
SHA-256 (plan.json and operator-actions.jsonl). A diagnostics job moved without its retrain otherwise refuses (no
state moves between pods). Each host can be deferred once. A host moved from wave anchor stays role "anchor"; one moved
from wave 0a's first host before the reference exists stays role "first" ([D14]).

``requeue HOST`` ([D14], the DRAFT's re-run rule): without --rerun-mismatched, a host with no JOB-DONE.json (pulled or
recorded) whose hosts/HOST/orchestrate.jsonl logs ``pre-job-failed`` (or ``job-start-unknown``) and never
``job-started`` has all its jobs recorded not_started and moved like ``defer`` (the move counts as its deferral),
once its stop is known ([D17] 3): from the log when the last ``pre-job-failed`` names a step other than start-job and
a later ``pre-job-stop`` has exit 0 (and no ``job-start-unknown``); otherwise only after ``confirm-stopped HOST``, the
operator's operator-actions.jsonl record that ``host.py get HOST`` read desiredStatus EXITED after the log's last
record (bound to the log's SHA-256). A requeue never follows a failed or unknown stop. From wave 1 on every moved job is
paid from the contingency, like a crash ([D16] 5), and the moved jobs are paid as one unit ([D21] 3: one 42 min for a
new pod plus each job's spend upper; when the unit does not fit, one by one in order as before, the rest not re-run);
a host whose job started refuses. For wave 0a's first host
([D16] 7) the move also undoes what record_first may have done, so the replacement runs as first: the recorded
expected fixture (expected-fixture-gateb.json, never Gate A's pinned fixture) is renamed with a stamp and kept, a
reference this host set is cleared from plan.json (kept in the host's ``pre_job_failed`` record; a reference from
another host refuses), and a ``first-host-reset`` record goes to operator-actions.jsonl. The recipe stays: plan.json
has no top-level recipe_path here, and a host's recipe_path is fixed by its wave.
With --rerun-mismatched SHA ... (after record-done), each named SHA must be the COMPLETE.json SHA-256 of a complete arm,
retrain or diagnostics job of HOST whose unit's compared fields differ from the plan's reference (for an evaluated
arm unit also its guard record against R_1101's, [D17] 4: ``mismatch`` reports "guard" as the reading does; record-done
of R_1101's host puts that guard into plan.json's reference, and first ([D19] 4) refuses, with plan.json unchanged,
when it differs from that host's own pulled PREFLIGHT-DONE.json guard or that guard is missing, so a snapshot-listing
difference fails once there instead of at every later pod's preflight-check); a hash named twice, or a later wave (or ext, lc) already
planned, refuses ([D17] 6); those jobs are queued
again like ``defer`` (the complete attempt stays recorded), each paid from the contingency from wave 1 on (pay_reruns),
and logged (``rerun-mismatched``, ``requeue``). The wave-0b retrain and diagnostics are re-queued together as their
linked pair ([D16] 6): naming either one's hash moves both (both must be complete on HOST), the diagnostics' a0_source
names the moved retrain, and the partner that was not named carries ``linked_rerun``. An attempt is re-queued once, and
an attempt already queued again (mismatched, or a stranded retrain) never blocks its own re-run: a crashed re-run is
deferred, and a re-run's pre-job stop is requeued, like any job.

Operator rule ([D16] 8, README.md): a stopped kit pod is never restarted; a requeued host's jobs run only on its
replacement. ``set-reference`` (and orchestrate's record_first) refuse a host whose jobs were moved, so only the
replacement acts as first.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import re
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gateb_mac as mac  # noqa: E402
import gateb_rules as rules  # noqa: E402

ROOT = HERE.parents[1]
ENGINE_ROOT = ROOT                       # the repository whose engine computes steps and hashes (tests move it)
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
SEAL_OUT = pathlib.Path(rules.MAN_PATH).parent
JOB_KEYS = {"kind", "arm", "seed", "edit", "a0_source"}
READING_PHASE = {"2": "wave2", "ext": "extension", "lc": "length-control"}
CALLED_BY = {"2": ("wave2",), "ext": ("verdict",), "lc": ("verdict", "extension")}   # the phases whose ``calls`` names W
ORDER = ("anchor", "0a", "0b", "1", "2")
WAVE_SEQUENCE = ORDER + ("ext", "lc")        # the extension follows wave 2's verdict, the length control the extension
SPLIT_WAVES = ("1", "2", "ext", "lc")        # [D21]: the arm waves init-wave splits into pods (rules.pod_sizes)


def fail(message: str):
    raise SystemExit(message)


# ----- engine-backed values (subprocess in the pinned venv, as the family-probe plan tool does) -----------------


def _engine(code: str) -> str:
    return subprocess.run([str(PY), "-c", code], cwd=ENGINE_ROOT, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def recipe_sha(path: str) -> str:
    return _engine("from experiments.safety_selection.config import load_recipe,config_sha256;"
                   f"print(config_sha256(load_recipe({str(ENGINE_ROOT / path)!r})))")


def stream_steps(rows: int, removed: int, added: int, recipe_path: str) -> int:
    """e1's optimizer step from the engine's stream plan (make_plan) on ``rows`` training rows with ``removed``
    removed and ``added`` added (only counts decide it; brief B3: never a constant)."""
    code = ("import json;from fractions import Fraction;from experiments.safety_selection.stream import make_plan;"
            "from experiments.safety_selection.config import load_recipe;"
            f"t=load_recipe({str(ENGINE_ROOT / recipe_path)!r})['train'];"
            "e=[c for c in t['checkpoints'] if c['name']=='e1'][0];"
            f"c=['r%06d'%i for i in range({rows})];x=['x%06d'%i for i in range({added})];"
            f"p=make_plan(c,c[:{removed}],0,t['micro_batch'],t['grad_accum'],x,"
            f"{'64*chr(48)' if added else None});"
            "print(p.checkpoint(Fraction(*e['epochs']))['step'])")
    return int(_engine(code))


# ----- the sealed files ------------------------------------------------------------------------------------------


def manifest() -> dict:
    path = ROOT / rules.MAN_PATH
    if not path.is_file() or mac.sha(path) != rules.MAN_SHA256:
        fail("the sealed MANIFEST.json is missing or differs from its pin")
    return json.loads(path.read_text())


def man_arms(man: dict) -> dict:
    """arm -> its MAN entry (edit files only)."""
    return {e["arm"]: e for e in man["files"] if e.get("role") == "edit"}


def unit_groups(man: dict) -> list[str]:
    return sorted(e["unit"] for e in man["files"] if e.get("family") == "unit")


def corpus_rows(man: dict) -> int:
    entry = next(e for e in man["files"] if e["path"] == "unit_table.json")
    path = ROOT / SEAL_OUT / entry["path"]
    if mac.sha(path) != entry["sha256"]:
        fail("unit_table.json differs from MAN")
    return int(json.loads(path.read_text())["all_rows"]["rows"])


def edit_counts(entry: dict) -> dict:
    path = ROOT / SEAL_OUT / entry["path"]
    if not path.is_file() or mac.sha(path) != entry["sha256"]:
        fail(f"{entry['path']}: missing or differs from MAN")
    return json.loads(path.read_text())["counts"]


def fixture() -> dict:
    path = ROOT / rules.GATE_A_FIXTURE
    if not path.is_file() or mac.sha(path) != rules.PREREG_FIXTURE_SHA256:
        fail("the expected fixture is missing or differs from its pin")
    projection = json.loads(path.read_text())["cap_projection"]
    return {"path": rules.GATE_A_FIXTURE, "sha256": rules.PREREG_FIXTURE_SHA256,
            "e1_upper_s": projection["e1_upper_s"], "training_s": projection["training_s"]}


def receipt(stage: str) -> dict:
    path = HERE / "setup" / f"packed-{stage}" / "setup-receipt.json"
    if not path.is_file():
        fail(f"no packed {stage} setup (pack_setup.py {stage}) before planning its wave")
    return json.loads(path.read_text())


# ----- jobs and waves --------------------------------------------------------------------------------------------


def dev_seed(seed) -> bool:
    return isinstance(seed, int) and not isinstance(seed, bool) and rules.DEV_SEEDS[0] <= seed <= rules.DEV_SEEDS[1]


def check_job(job: dict, index: int, host_jobs: list[dict], arms: dict) -> None:
    """One job's own rules (B1); every refusal names ids only."""
    if "base_eval" in job:
        fail("base_eval is false on every Gate B host")
    if set(job) - JOB_KEYS or "kind" not in job:
        fail(f"job {index}: keys must be among {sorted(JOB_KEYS)}")
    kind, arm, seed, edit = job["kind"], job.get("arm"), job.get("seed"), job.get("edit")
    if kind not in rules.KINDS:
        fail(f"job {index}: unknown kind {kind!r}")
    if kind != "diagnostics" and "a0_source" in job:
        fail(f"job {index}: a0_source belongs to a diagnostics job only")
    if arm == "a0" and kind != "retrain":
        fail(f"job {index}: a0 is the retrain's arm only")
    if kind == "anchor":
        if arm is not None or seed is not None or edit is not None:
            fail(f"job {index}: an anchor job has no arm, seed or edit")
    elif kind == "retrain":
        if arm != "a0" or seed != rules.RETRAIN_SEED or edit is not None:
            fail(f"job {index}: the retrain is a0 at seed {rules.RETRAIN_SEED} with no edit")
    elif kind == "diagnostics":
        if arm is not None or edit is not None or seed != rules.RETRAIN_SEED:
            fail(f"job {index}: the diagnostics run at seed {rules.RETRAIN_SEED} with no arm or edit")
        source = job.get("a0_source")
        if not (isinstance(source, int) and 0 <= source < index and host_jobs[source]["kind"] == "retrain"):
            fail(f"job {index}: a0_source must name an earlier retrain job of this host")
    else:
        if not (isinstance(arm, str) and arm.startswith("edit-") and arm in arms):
            fail(f"job {index}: arm {arm!r} is not an edit arm listed in MAN (no group-id or native arm)")
        if edit != arms[arm]["path"]:
            fail(f"job {index}: edit must be the MAN file of its arm ({arms[arm]['path']})")
    if seed is not None and not dev_seed(seed):
        fail(f"job {index}: seed {seed!r} is not a development seed")


def runs(hosts: list[list[dict]]) -> list[tuple]:
    return sorted((j["arm"], j["seed"]) for host in hosts for j in host if j["kind"] == "arm")


def split_wave(wave: str, hosts: list[list[dict]]) -> list[list[dict]]:
    """[D21]: the pods of an arm wave (SPLIT_WAVES). The jobs file gives the wave as one host, which the tool splits by
    rules.pod_sizes (ceil(n / MAX_ARMS_PER_POD) pods, the arms dealt evenly in order), or already as that split;
    any other grouping refuses (check_wave). Other waves are returned as given."""
    if wave in SPLIT_WAVES and len(hosts) == 1 and hosts[0]:
        return rules.split_pods(hosts[0])
    return hosts


def check_wave(wave: str, hosts: list[list[dict]], arms: dict, reading: dict | None) -> None:
    """The wave rules (B1)."""
    kinds = [[j["kind"] for j in host] for host in hosts]
    by = {(e.get("family"), e.get("draw"), e.get("unit")): a for a, e in arms.items()}
    unit_arms = {e["unit"]: a for a, e in arms.items() if e.get("family") == "unit"}
    if not hosts or any(not h for h in hosts):
        fail(f"wave {wave}: every host needs at least one job")
    if wave in ("anchor", "0a", "0b") and len(hosts) != 1:
        fail(f"wave {wave}: one pod")
    if wave == "0a" and len(rules.WAVE0A_DRAWS) > rules.MAX_ARMS_PER_POD:
        fail(f"wave 0a: R_1-R_3 are one pod (the first host), so MAX_ARMS_PER_POD must be at least "
             f"{len(rules.WAVE0A_DRAWS)}")
    if wave in SPLIT_WAVES and [len(h) for h in hosts] != rules.pod_sizes(sum(len(h) for h in hosts)):
        fail(f"wave {wave}: pods of at most {rules.MAX_ARMS_PER_POD} arms, dealt evenly in order")
    if wave == "anchor" and kinds != [["anchor"]]:
        fail("wave anchor: exactly one anchor job")
    if wave == "0a":
        want = sorted((by[("R", d, None)], rules.R_SEED_BASE + d) for d in rules.WAVE0A_DRAWS)
        if kinds != [["arm"] * 3] or runs(hosts) != want:
            fail("wave 0a: exactly R_1-R_3, R_d at seed 1100 + d")
    if wave == "0b":
        if kinds != [["retrain", "diagnostics"]] or hosts[0][1].get("a0_source") != 0:
            fail("wave 0b: the retrain, then the diagnostics naming it")
    if wave == "1":
        want = sorted((a, rules.UNIT_SEED) for a in unit_arms.values())
        if any(set(k) != {"arm"} for k in kinds) or runs(hosts) != want:
            fail(f"wave 1: the 8 unit_g-* edit files at 1101, in pods of at most {rules.MAX_ARMS_PER_POD} arms")
    if wave in READING_PHASE:
        if reading is None:
            fail(f"wave {wave}: --reading FILE (the reading output that calls these runs) is required")
        if any(set(k) != {"arm"} for k in kinds):
            fail(f"wave {wave}: arm jobs only")
        if runs(hosts) != reading["runs"]:
            fail(f"wave {wave}: the jobs must be exactly the reading output's runs")
        if wave == "2" and not all(arms[a].get("family") == "unit" and s in rules.WAVE2_SEEDS
                                   for a, s in reading["runs"]):
            fail("wave 2: unit files at 1102 and 1103 only")
        if wave == "ext":
            for a, s in reading["runs"]:
                e = arms[a]
                if not ((e.get("family") == "R" and e.get("draw") in rules.EXTENSION_DRAWS
                         and s == rules.R_SEED_BASE + e["draw"])
                        or (e.get("family") == "unit" and s in rules.EXTENSION_SEEDS)):
                    fail("wave ext: R_4, R_5 at 1100 + d and unit files at 1104, 1105 only")
        if wave == "lc":
            fams = sorted((arms[a].get("family"), arms[a].get("draw"), arms[a].get("unit"), s) for a, s in reading["runs"])
            units = {u for f, d, u, s in fams}
            seeds = {(d, s) for f, d, u, s in fams if f == "M"}
            ok = (len(fams) == 4 and len(units) == 1 and {f for f, *_ in fams} == {"M", "unit"}
                  and sorted(d for d, _ in seeds) == [1, 2] and len({s for _, s in seeds}) == 2
                  and sorted(s for f, d, u, s in fams if f == "unit") == sorted(s for _, s in seeds))
            if not ok:
                fail("wave lc: M_u,1 and u at one seed, M_u,2 and u at another")


def read_reading(path: str, wave: str, arms: dict) -> dict:
    """The reading output (scripts/gate_b_reading.py) that calls wave 2, the extension or the length control: its
    top-level ``calls`` names the wave ("2" from wave2; "ext" from verdict; "lc" from verdict or extension) and
    ``runs`` lists [{arm, seed}] in job order."""
    p = pathlib.Path(path)
    doc = json.loads(p.read_text())
    if doc.get("kind") != "gate-b reading" or doc.get("calls") != wave or doc.get("phase") not in CALLED_BY[wave]:
        fail(f"{p.name}: not a reading output that calls wave {wave}")
    found = sorted((r["arm"], r["seed"]) for r in doc.get("runs") or [])
    if not found or any(a not in arms or not dev_seed(s) for a, s in found):
        fail(f"{p.name}: every run must be a MAN edit arm at a development seed")
    return {"path": str(p), "sha256": mac.sha(p), "runs": found}


def complete_keys(plan: dict) -> dict:
    """(arm, seed) and ("attributes", seed) -> complete attempts (pulled trees), plus jobs the plan records complete."""
    found = mac.complete_runs()
    for host, h in (plan.get("hosts") or {}).items():
        for job in h["jobs"]:
            if job.get("status") == "complete":
                key = ("attributes", job["seed"]) if job["kind"] == "diagnostics" else \
                    ("anchor", None) if job["kind"] == "anchor" else (job["arm"], job["seed"])
                found.setdefault(key, []).append({"host": host, "unit": job.get("unit"),
                                                  "complete_sha256": job.get("complete_sha256"), "path": None})
    return found


def job_key(job: dict) -> tuple:
    return ("attributes", job["seed"]) if job["kind"] == "diagnostics" else \
        ("anchor", None) if job["kind"] == "anchor" else (job["arm"], job["seed"])


def mismatch(plan: dict, attempt: dict) -> list[str]:
    """The compared fields in which a complete attempt's unit differs from the plan's reference (names only), and
    ([D17] 4, as the reading's Context.differs) "guard" when the unit evaluates the bank (a run-one arm other than
    a0) and its assets.json guard record differs from R_1101's pulled guard in the reference (record-done puts it
    there; before that, no guard difference can be named)."""
    if not plan.get("reference") or not attempt.get("path"):
        return []
    unit = pathlib.Path(attempt["path"])
    assets = json.loads((unit / "assets.json").read_text())
    lock = (assets.get("environment_lock") or {}).get("sha256")
    fields = mac.compared_fields(assets.get("environment") or {}, lock, assets.get("policy"))
    ref = plan["reference"]["fields"]
    out = sorted(k for k in set(ref) | set(fields) if fields.get(k) != ref.get(k))
    job = json.loads((unit / "job.json").read_text())
    evaluated = job.get("kind") == "run-one" and job.get("arm") != "a0"
    guard = plan["reference"].get("guard")
    if evaluated and guard is not None and assets.get("guard") != guard:
        out.append("guard")
    return out


def r1101_arm() -> str:
    """R_1's arm (R_1101 = R_1 at seed 1101 is the reading's environment reference)."""
    return next(a for a, e in man_arms(manifest()).items() if e.get("family") == "R" and e.get("draw") == 1)


def preflight_guard_check(host: str, guard: dict) -> str:
    """[D19] 4, the early guard check: the guard record in HOST's pulled PREFLIGHT-DONE.json (retrieved/HOST/tree/,
    where the pull puts it next to JOB-DONE.json; the preflight's guard_pin on this pod) must equal R_1101's pulled
    guard record, field by field. Every later pod's preflight-check compares its own preflight guard with R_1101's,
    so a difference between the preflight's snapshot listing and the job's would stop each of them; here it refuses
    once, at record-done of R_1101's host, before the reference holds a guard (wave 0b cannot be planned). A missing
    file or a missing or non-object guard refuses too (fail closed). The refusal names the host and the differing
    guard fields (names only). Returns the file's SHA-256."""
    path = HERE / "retrieved" / host / "tree" / "PREFLIGHT-DONE.json"
    try:
        done = json.loads(path.read_text()) if path.is_file() else None
    except ValueError:
        done = None
    pre = done.get("guard") if isinstance(done, dict) else None
    if not isinstance(pre, dict):
        fail(f"{host}: the pulled PREFLIGHT-DONE.json has no guard record; R_1101's guard is not recorded "
             "(the lead decides)")
    # a key on one side only differs even when the other side's value is null: preflight-check compares whole records
    differ = sorted(k for k in set(guard) | set(pre) if k not in guard or k not in pre or guard[k] != pre[k])
    if differ:
        fail(f"{host}: the preflight's guard record differs from R_1101's pulled guard in {differ}; R_1101's guard "
             "is not recorded (the lead decides)")
    return mac.sha(path)


def reference_guard(plan: dict, host: str, h: dict) -> dict | None:
    """[D17] 4: once, the guard record of the first R_1101 attempt recorded complete (its pulled assets.json) goes
    into plan["reference"] with its source; an R_1101 unit without a guard record refuses (the reading refuses it
    too), and ([D19] 4) so does a guard that differs from HOST's own preflight guard (preflight_guard_check), before
    anything is recorded. Nothing happens without a reference or when the guard is already recorded."""
    ref = plan.get("reference")
    if not ref or ref.get("guard") is not None:
        return None
    r1 = r1101_arm()
    for job in h["jobs"]:
        if job["kind"] == "arm" and (job["arm"], job["seed"]) == (r1, rules.R_SEED_BASE + 1) and \
                job.get("status") == "complete":
            path = HERE / "retrieved" / host / "tree" / job["unit"] / "assets.json"
            guard = (json.loads(path.read_text()) if path.is_file() else {}).get("guard")
            if not isinstance(guard, dict):
                fail(f"{host}: R_1101's pulled assets.json has no guard record")
            preflight_sha = preflight_guard_check(host, guard)
            ref["guard"] = guard
            ref["guard_source"] = {"host": host, "unit": job["unit"], "complete_sha256": job["complete_sha256"],
                                   "preflight_done_sha256": preflight_sha}
            return ref["guard_source"]
    return None


RERUN_MARKS = ("mismatched_complete_sha256", "stranded_complete_sha256")   # a re-run job names the attempt it repeats


def requeued_attempts(plan: dict) -> set:
    """The COMPLETE.json SHA-256s already queued again: environment-mismatched (requeue, or init-wave's re-runs) and
    stranded retrains ([D7])."""
    marked = {j.get(m) for h in plan["hosts"].values() for j in h["jobs"] for m in RERUN_MARKS}
    return {d for r in plan.get("requeues") or [] for d in r["complete_sha256"]} | (marked - {None})


def refuse_complete(plan: dict, jobs: list[dict], rerun: list[str], allow_stranded: set | None = None,
                    linked: set | None = None) -> list[dict]:
    """Refuse a job whose run is complete, unless --rerun-mismatched names a complete attempt of it whose fields
    differ from the reference (B1); returns the reruns to record. For a re-run (a job that carries one of RERUN_MARKS),
    the attempts already queued again do not count ([D14]): a crashed re-run is deferred, and a re-run's pre-job stop
    is requeued, like any job; any other complete attempt still refuses. ``linked`` (ids of jobs): the wave-0b
    partner moved with a named retrain or diagnostics ([D16] 6); only its own attempt (its mismatched_complete_sha256)
    is exempt."""
    found, allowed, requeued = complete_keys(plan), [], requeued_attempts(plan)
    for job in jobs:
        key = job_key(job)
        attempts = [a for a in found.get(key, []) if not any(m in job for m in RERUN_MARKS)
                    or a["complete_sha256"] not in requeued]
        if linked and id(job) in linked:
            attempts = [a for a in attempts if a["complete_sha256"] != job["mismatched_complete_sha256"]]
        if not attempts or (allow_stranded and id(job) in allow_stranded):
            continue
        named = [a for a in attempts if a["complete_sha256"] in rerun]
        if job["kind"] in ("arm", "retrain", "diagnostics") and named:
            fields = mismatch(plan, named[0])
            if fields:
                allowed.append({"kind": job["kind"], "arm": job["arm"], "seed": job["seed"],
                                "complete_sha256": named[0]["complete_sha256"], "host": named[0]["host"],
                                "mismatched_fields": fields})
                continue
            fail(f"{job.get('arm') or job['kind']} at {job['seed']}: the named attempt shows no environment mismatch "
                 "against the reference")
        fail(f"{job.get('arm') or job['kind']} at {job.get('seed')}: a complete attempt exists; it is never re-run "
             "(--rerun-mismatched SHA names an environment-mismatched attempt)")
    return allowed


def host_record(plan: dict, wave: str, role: str, jobs: list[dict], stage_receipt: dict) -> dict:
    stage = "anchor" if wave == "anchor" else "gateb"
    recipe = rules.REC if wave == "anchor" else rules.RECIPE_S
    cap = rules.cap_hours(jobs)
    return {"wave": wave, "role": role, "base_eval": False, "stage": stage, "recipe_path": recipe,
            "recipe_sha256": plan["recipes"][recipe], "sealed_files_sha256": stage_receipt["sealed_files_sha256"],
            "cap_hours": cap, "guard_usd": rules.guard_usd(cap), "jobs": jobs, "done": False, **rules.POD_SIZES}


def new_host_name(plan: dict, wave: str) -> str:
    prefix = rules.HOST_PREFIX[wave]
    taken = [int(h.rsplit("-", 1)[1]) for h in plan["hosts"] if h.rsplit("-", 1)[0] == prefix]
    return f"{prefix}-{max(taken, default=0) + 1}"


def skeleton(man: dict) -> dict:
    return {"name": "gate-b-olmo", "brief": "gate-b-engine-kit-reading-20261008 (revision 11)",
            "status": "development; Gate B removal arms on OLMo-2-1B recipe B (per-pod user approval)",
            "engine_sha256": None, "prepared": dict(rules.PREPARED_MANIFESTS), "prepared_name": rules.PREPARED_NAME,
            "man_sha256": rules.MAN_SHA256, "unit_groups": unit_groups(man), "fixture": fixture(),
            "fixture_compare": {"equal_keys": ["source", "script_sha256", "manifest_sha256", "recipe_sha256",
                                               "training_identity", "test_rows"],
                                "resume_keys": ["direct", "loss_direct"]},
            "recipes": {}, "reference": None, "funding": [], "readings": {}, "deferrals": [], "hosts": {}}


def previous_complete(plan: dict, wave: str) -> None:
    """No wave starts before the waves above it are complete (DRAFT §1 Order): every host of those waves has all its
    jobs complete, or was deferred (its open jobs moved to another host of the same wave, checked in turn)."""
    needed = ORDER[:ORDER.index(wave)] if wave in ORDER else ORDER + (("ext",) if wave == "lc" else ())
    deferred = {d["from"] for d in plan["deferrals"]}
    for host, h in plan["hosts"].items():
        if h["wave"] in needed and host not in deferred and any(j.get("status") != "complete" for j in h["jobs"]):
            fail(f"wave {wave}: wave {h['wave']} is not complete ({host})")
    for w in needed:
        if w in ORDER and not any(h["wave"] == w for h in plan["hosts"].values()):
            fail(f"wave {wave}: wave {w} has not run")


def balance_record(path: str) -> dict:
    record = json.loads(pathlib.Path(path).read_text())
    if not (isinstance(record.get("usd"), (int, float)) and record.get("utc") and record.get("source")):
        fail("--balance FILE must hold {usd, utc, source}")
    return {**record, "sha256": mac.sha(pathlib.Path(path))}


def worst_path_need(plan: dict, wave1_hosts: list[list[dict]]) -> dict:
    """B4: the wave-1 launch as planned (its pods in parallel), then wave 2 at m = 4, the extension with 2 contested
    units and the length control (rules.WORST_PATH_AFTER_WAVE1), each one launch of the parallel pods that
    rules.pod_sizes makes of its arms ([D21]: 8 -> 4 + 4, 6 -> 3 + 3, 4 -> 4 at MAX_ARMS_PER_POD = 4); the need is
    CONTINGENCY_FACTOR x the base ([D11]).

    [D21] (5): with rules.GRANITE_ON_POD (pod Granite), a pod Granite judge launch follows wave 2 and the extension
    (rules.GRANITE_POD_AFTER), each its own launch (the verdict that calls the next wave reads its files). Each judges
    every Gate B arm completed since the previous pod Granite launch: after wave 2, wave 0a's R_1-R_3, wave 1 and
    wave 2 (3 + 8 + 8 = 19 arms on the worst path); after the extension, its 6 arms. That count is an upper bound: the
    verdict reads only wave 2's arms and R_2, R_3 at 1102-1103 (10 arms), and the cap only grows with the answers
    (19 and 10 arms both cap at 1.5 h). Each launch's term counts its cap x rules.PLANNING_PRICE_USD and its upper
    spend, cap x rules.RATE_USD, enters the later terms (rules.granite_pod). With the Mac route (False) no judge launch is counted."""
    fx = plan["fixture"]
    pod_granite = rules.granite_on_pod()
    launches = [[{"kinds": [j["kind"] for j in jobs], "cap_hours": rules.cap_hours(jobs)} for jobs in wave1_hosts]]
    unjudged = len(rules.WAVE0A_DRAWS) + sum(rules.arm_count(jobs) for jobs in wave1_hosts)
    granite = []
    for wave, n in rules.WORST_PATH_AFTER_WAVE1:
        launches.append([{"kinds": ["arm"] * size, "cap_hours": rules.cap_hours(rules.default_jobs(["arm"] * size, fx))}
                         for size in rules.pod_sizes(n)])
        unjudged += n
        if pod_granite and wave in rules.GRANITE_POD_AFTER:
            launches.append([rules.granite_pod(unjudged)])
            granite.append({"after": wave, **launches[-1][0]})
            unjudged = 0
    need = rules.funding_need_usd(launches, rules.CONTINGENCY_FACTOR)
    return {**need, "granite_on_pod": pod_granite, "granite_launches": granite}


PRE_WAVE1 = ORDER[:ORDER.index("1")]          # anchor, 0a, 0b: no contingency pays their re-runs ([D16] 6)


def pay_reruns(plan: dict, reruns: list[dict], new_pod: bool, where: str, wave: str | None = None) -> list[dict]:
    """Pay each re-run from the wave-1 contingency, in order ([D11]); returns the ones paid. A re-run it cannot pay is
    recorded "not re-run" in plan.json and operator-actions.jsonl. Before wave 1 there is no contingency, and a re-run
    of a wave before wave 1 (``wave``) is never paid from it: all pass."""
    c = plan.get("contingency")
    if c is None or wave in PRE_WAVE1:
        return list(reruns)
    paid = []
    for k, job in enumerate(reruns):
        cost = rules.rerun_cost_usd(job["kind"], new_pod and not paid)
        record = {"kind": job["kind"], "arm": job.get("arm"), "seed": job.get("seed"), "cost_usd": cost, "where": where}
        if cost <= c["remaining_usd"] + 1e-9:
            c["remaining_usd"] -= cost
            c["spent"].append(record)
            paid.append(job)
        else:
            c["not_rerun"].append(record)
            mac.operator_action({"action": "not-rerun", "reason": "contingency exhausted", **record,
                                 "remaining_usd": c["remaining_usd"]})
    return paid


def pay_unit(plan: dict, jobs: list[dict], new_pod: bool, where: str, wave: str | None = None) -> list[dict]:
    """[D21] (3): a pre-job requeue's moved jobs are paid from the contingency as one unit, its one record carrying
    every job and the cost rules.unit_rerun_cost_usd (one 42 min when they need a new pod). When the remaining
    contingency cannot pay the whole unit, pay_reruns pays the jobs one by one in order (the first carrying the new
    pod's 42 min) and records the rest "not re-run", as before [D21]. Before wave 1, all pass (pay_reruns).

    Which rule governs: the two agree. unit_rerun_cost_usd is the sum of pay_reruns' one-by-one costs of the same
    jobs, so whenever the unit fits, pay_reruns would also pay every job and leave the same remaining contingency; the
    unit differs only in the record (one ``unit`` record, not one per job). When the contingency is short, the
    one-by-one rule (pay_reruns) governs: each job in order is paid if its cost fits what is left (the 42 min goes on
    the first job paid), the others are reported not re-run. So pay_unit pays exactly the jobs pay_reruns pays."""
    c = plan.get("contingency")
    if c is None or wave in PRE_WAVE1 or not jobs:
        return pay_reruns(plan, jobs, new_pod, where, wave)
    cost = rules.unit_rerun_cost_usd([j["kind"] for j in jobs], new_pod)
    if cost > c["remaining_usd"] + 1e-9:
        return pay_reruns(plan, jobs, new_pod, where, wave)
    c["remaining_usd"] -= cost
    c["spent"].append({"unit": [{"kind": j["kind"], "arm": j.get("arm"), "seed": j.get("seed")} for j in jobs],
                       "new_pod": new_pod, "cost_usd": cost, "where": where})
    return list(jobs)


def pre_wave1_need(plan: dict) -> dict:
    """The three pre-wave-1 pods at the anchor launch (the anchor, wave 0a, wave 0b): report only."""
    fx = plan["fixture"]
    pods = [["anchor"], ["arm"] * 3, ["retrain", "diagnostics"]]
    return rules.funding_need_usd([[{"kinds": k, "cap_hours": rules.cap_hours(rules.default_jobs(k, fx))}] for k in pods])


def init_wave(args: argparse.Namespace) -> dict:
    wave = args.wave
    if wave not in rules.WAVES:
        fail(f"unknown wave {wave!r}")
    hashes = args.rerun_mismatched or []
    if len(set(hashes)) != len(hashes):              # [D17] 6, as requeue: a repeated hash refuses, never merged
        fail(f"wave {wave}: --rerun-mismatched names one hash more than once")
    if wave == "anchor" and not (isinstance(rules.LOCK_SHA256, str) and re.fullmatch(r"[0-9a-f]{64}", rules.LOCK_SHA256)):
        fail("gateb_rules.LOCK_SHA256 is not pinned: the lead fills Gate A's lock SHA-256 before the anchor launch")
    man = manifest()
    arms = man_arms(man)
    plan = mac.load_plan() if mac.PLAN.exists() else skeleton(man)
    if any(h["wave"] == wave for h in plan["hosts"].values()):
        fail(f"wave {wave} is already planned (defer adds hosts)")
    previous_complete(plan, wave)
    stage = "anchor" if wave == "anchor" else "gateb"
    stage_receipt = receipt(stage)
    if plan["engine_sha256"] not in (None, stage_receipt["engine_sha256"]):
        fail("the packed engine differs from the plan's")
    plan["engine_sha256"] = stage_receipt["engine_sha256"]
    recipe = rules.REC if wave == "anchor" else rules.RECIPE_S
    if not (ENGINE_ROOT / recipe).is_file():
        fail(f"{recipe} does not exist yet (recipe S follows the sealed anchor file)")
    plan["recipes"].setdefault(recipe, recipe_sha(recipe))
    given = json.loads(pathlib.Path(args.jobs).read_text())
    if given.get("base_eval", False) is not False:
        fail("base_eval is false on every Gate B host")
    if set(given) - {"hosts", "base_eval"} or not isinstance(given.get("hosts"), list):
        fail("--jobs FILE must be {\"hosts\": [[job, ...], ...]}")
    hosts_in = [[dict(j) for j in host] for host in given["hosts"]]
    for host in hosts_in:
        for i, job in enumerate(host):
            job.setdefault("arm", None), job.setdefault("seed", None), job.setdefault("edit", None)
            check_job(job, i, host, arms)
    reading = read_reading(args.reading, wave, arms) if wave in READING_PHASE and args.reading else None
    hosts_in = split_wave(wave, hosts_in)
    check_wave(wave, hosts_in, arms, reading)
    rows = corpus_rows(man)
    hosts = []
    for host in hosts_in:
        jobs = []
        for job in host:
            steps = None
            if job["kind"] == "arm":
                counts = edit_counts(arms[job["arm"]])
                steps = stream_steps(rows, counts["remove"], counts.get("add", 0), recipe)
            elif job["kind"] == "retrain":
                steps = stream_steps(rows, 0, 0, recipe)
            jobs.append(rules.job_record(job["kind"], job["arm"], job["seed"], job["edit"], steps, plan["fixture"],
                                         job.get("a0_source")))
        hosts.append(jobs)
    reruns = refuse_complete(plan, [j for h in hosts for j in h], args.rerun_mismatched or [])
    if reruns:                              # re-runs from wave 1 on are paid from the contingency ([D11])
        keys = {(r["arm"], r["seed"]) for r in reruns}
        jobs = [j for h in hosts for j in h if (j["arm"], j["seed"]) in keys]
        paid = {id(j) for j in pay_reruns(plan, jobs, False, f"init-wave {wave}", wave)}
        unpaid = {(j["arm"], j["seed"]) for j in jobs if id(j) not in paid}
        hosts = [h for h in ([j for j in h if (j["arm"], j["seed"]) not in unpaid] for h in hosts) if h]
        reruns = [r for r in reruns if (r["arm"], r["seed"]) not in unpaid]
        if not hosts:
            fail(f"wave {wave}: no job left after the contingency (every re-run reported not re-run)")
        named = {(r["arm"], r["seed"]): r["complete_sha256"] for r in reruns}
        for job in (j for h in hosts for j in h if (j["arm"], j["seed"]) in named):
            job.update(reason="environment-mismatch", mismatched_complete_sha256=named[(job["arm"], job["seed"])])
    if wave == "1":
        if not args.balance:
            fail("init-wave 1 needs --balance FILE (the lead's balance record) for the funding rule")
        balance = balance_record(args.balance)
        need = worst_path_need(plan, hosts)
        if balance["usd"] < need["need_usd"]:
            fail(f"the balance ${balance['usd']:.2f} is below the worst path's need ${need['need_usd']:.2f} "
                 f"({rules.CONTINGENCY_FACTOR} x ${need['base_need_usd']:.2f})")
        plan["funding"].append({"wave": "1", "utc": mac.utc(), "balance": balance, **need})
        plan["contingency"] = {"usd": need["contingency_usd"], "remaining_usd": need["contingency_usd"], "spent": [],
                               "not_rerun": []}
    if wave == "anchor":
        record = {"wave": "anchor", "utc": mac.utc(), "report_only": True, **pre_wave1_need(plan)}
        if args.balance:
            balance = balance_record(args.balance)
            record.update(balance=balance, short_by_usd=max(0.0, record["need_usd"] - balance["usd"]))
        plan["funding"].append(record)
    if reading:
        plan["readings"][wave] = {"path": reading["path"], "sha256": reading["sha256"]}
    names = []
    for k, jobs in enumerate(hosts):
        role = "anchor" if wave == "anchor" else "first" if wave == "0a" and k == 0 else "job"
        name = new_host_name(plan, wave)
        plan["hosts"][name] = host_record(plan, wave, role, jobs, stage_receipt)
        names.append(name)
    for rerun in reruns:
        mac.operator_action({"action": "rerun-mismatched", "wave": wave, **rerun})
    mac.save_plan(plan)
    mac.operator_action({"action": "init-wave", "wave": wave, "hosts": names,
                         "reading_sha256": reading["sha256"] if reading else None})
    return {"wave": wave, "hosts": names, "caps": [plan["hosts"][n]["cap_hours"] for n in names]}


# ----- after a host: record-done, defer, set-reference ---------------------------------------------------------


def record_done(host: str) -> dict:
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    path = HERE / "retrieved" / host / "tree" / "JOB-DONE.json"
    if not path.is_file():
        fail(f"{host}: no pulled JOB-DONE.json")
    done = json.loads(path.read_text())
    records = {r["index"]: r for r in done.get("jobs") or []}
    if done.get("host") != host or sorted(records) != list(range(len(h["jobs"]))):
        fail(f"{host}: JOB-DONE.json does not cover this host's jobs")
    for i, job in enumerate(h["jobs"]):
        r = records[i]
        if (r["kind"], r.get("arm"), r.get("seed")) != (job["kind"], job["arm"], job["seed"]):
            fail(f"{host}: job {i} in JOB-DONE.json is another job")
        if r["status"] not in ("complete", "crashed", "deferred", "not_started"):
            fail(f"{host}: job {i} has an unknown status")
        if r["status"] == "complete" and r.get("complete_sha256"):
            complete = HERE / "retrieved" / host / "tree" / r["unit"] / "COMPLETE.json"
            if not complete.is_file() or mac.sha(complete) != r["complete_sha256"]:
                fail(f"{host}: job {i}'s COMPLETE.json is missing from the pulled tree or differs")
        elif r["status"] == "complete" and job["kind"] != "anchor":      # only the anchor job has no COMPLETE.json
            fail(f"{host}: job {i} is complete without a complete_sha256")
        job.update(status=r["status"], unit=r.get("unit"), complete_sha256=r.get("complete_sha256"))
    source = reference_guard(plan, host, h)
    h["done"], h["job_done_sha256"] = True, mac.sha(path)
    mac.save_plan(plan)
    mac.operator_action({"action": "record-done", "host": host, "statuses": [j["status"] for j in h["jobs"]]})
    if source is not None:
        mac.operator_action({"action": "reference-guard", **source})
    return {"host": host, "statuses": [j["status"] for j in h["jobs"]]}


def moved_role(plan: dict, h: dict, pre_job: bool = False) -> str:
    """The role of a new host that takes moved jobs: "anchor" from wave anchor ([D14]); "first" when a pre-job stop
    moves wave 0a's first host before the reference exists (the new host then records the fixture and the reference;
    a started first host has set it); else "job"."""
    if h["wave"] == "anchor":
        return "anchor"
    if pre_job and h["role"] == "first" and not plan.get("reference"):
        return "first"
    return "job"


def destination(plan: dict, host: str, wave: str, arms: int = 0) -> str | None:
    """The next unlaunched host of the wave that is not done and has room for ``arms`` more arms ([D21]: at most
    MAX_ARMS_PER_POD arms per pod), or None (a new host)."""
    return next((name for name, d in plan["hosts"].items() if name != host and d["wave"] == wave
                 and not mac.launched(name) and not d.get("done")
                 and rules.arm_count(d["jobs"]) + arms <= rules.MAX_ARMS_PER_POD), None)


def too_many(host: str, moved: list[dict]) -> None:
    """[D21]: moved jobs never make a pod of more than MAX_ARMS_PER_POD arms (a host planned before the limit was
    lowered refuses here, before anything is paid or saved; the lead decides)."""
    if rules.arm_count(moved) > rules.MAX_ARMS_PER_POD:
        fail(f"{host}: {rules.arm_count(moved)} arms would move to one pod, more than MAX_ARMS_PER_POD = "
             f"{rules.MAX_ARMS_PER_POD}; the lead decides")


def place(plan: dict, h: dict, moved: list[dict], dest: str | None, role: str = "job") -> str:
    """``moved`` in order at the front of ``dest``, or on a new host whose cap and guard come from B4 (B3). A pod never
    gets more than MAX_ARMS_PER_POD arms ([D21]; a host planned at that limit never moves more)."""
    if rules.arm_count(moved) + (rules.arm_count(plan["hosts"][dest]["jobs"]) if dest else 0) > rules.MAX_ARMS_PER_POD:
        fail(f"{h['wave']}: a pod would hold more than {rules.MAX_ARMS_PER_POD} arms; the lead decides")
    if dest is None:
        dest = new_host_name(plan, h["wave"])
        plan["hosts"][dest] = host_record(plan, h["wave"], role, moved,
                                          {"sealed_files_sha256": h["sealed_files_sha256"]})
        return dest
    target = plan["hosts"][dest]
    for job in target["jobs"]:
        if job["kind"] == "diagnostics":
            job["a0_source"] += len(moved)
    target["jobs"] = moved + target["jobs"]
    target["cap_hours"] = rules.cap_hours(target["jobs"])
    target["guard_usd"] = rules.guard_usd(target["cap_hours"])
    return dest


def defer(host: str) -> dict:
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    if not h.get("done"):
        fail(f"{host}: record-done first")
    if any(d["from"] == host for d in plan["deferrals"]):
        fail(f"{host} was already deferred")
    moving_idx = [i for i, j in enumerate(h["jobs"]) if j["status"] in ("crashed", "deferred", "not_started")]
    if not moving_idx:
        fail(f"{host}: nothing to defer")
    return move_open(plan, host, h, moving_idx, "defer")


def move_open(plan: dict, host: str, h: dict, moving_idx: list[int], action: str, reason: str | None = None) -> dict:
    """``defer``'s move (B3, [D7], [D11]) of the jobs at ``moving_idx``; ``requeue`` uses it for a pre-job stop."""
    jobs = h["jobs"]
    first_deferred = next((i for i in moving_idx if jobs[i]["status"] == "deferred"), None)
    stranded = None
    if first_deferred is not None and jobs[first_deferred]["kind"] == "diagnostics":
        source = jobs[first_deferred]["a0_source"]
        if jobs[source]["kind"] == "retrain" and jobs[source]["status"] == "complete":
            stranded = source
    moved, index_map = [], {}
    for i in moving_idx:
        if i == first_deferred and stranded is not None:
            retrain = {k: v for k, v in jobs[stranded].items() if k not in ("unit", "complete_sha256")}
            retrain.update(status="planned", reason="stranded-retrain",
                           stranded_complete_sha256=jobs[stranded]["complete_sha256"], stranded_host=host)
            index_map[stranded] = len(moved)
            moved.append(retrain)
        job = {k: v for k, v in jobs[i].items() if k not in ("unit", "complete_sha256")}
        job["status"], job["deferred_from"] = "planned", host
        index_map[i] = len(moved)
        moved.append(job)
    for job in moved:
        if job["kind"] == "diagnostics":
            if job["a0_source"] not in index_map:
                fail(f"{host}: a diagnostics job would move without its retrain (no state moves between pods)")
            job["a0_source"] = index_map[job["a0_source"]]
    stranded_ids = {id(moved[index_map[stranded]])} if stranded is not None else set()
    refuse_complete(plan, moved, [], stranded_ids)
    too_many(host, moved)
    dest = destination(plan, host, h["wave"], rules.arm_count(moved))
    if reason == "pre-job-failed":                  # [D16] 5: every moved job and the replacement's start, like a crash;
        to_pay = list(moved)                        # [D21] (3): paid as one unit
        payer = pay_unit
    else:
        to_pay = [moved[index_map[i]] for i in moving_idx if jobs[i]["status"] == "crashed"]
        payer = pay_reruns
    paid = {id(j) for j in payer(plan, to_pay, dest is None, f"{action} {host}", h["wave"])}
    dropped = {id(j) for j in to_pay if id(j) not in paid}
    if dropped:                                     # [D11]: a re-run the contingency cannot pay is not re-run
        if any(j["kind"] in ("retrain", "diagnostics") for j in to_pay if id(j) in dropped):
            fail(f"{host}: the contingency cannot pay a retrain or diagnostics re-run; the lead decides")
        kept = [j for j in moved if id(j) not in dropped]
        position = {id(j): k for k, j in enumerate(kept)}
        for j in kept:
            if j["kind"] == "diagnostics":
                j["a0_source"] = position[id(moved[j["a0_source"]])]
        moved = kept
        if not moved:
            entry = {"from": host, "to": None, "from_indices": moving_idx, "to_indices": [], "stranded_retrain": None,
                     "not_rerun": len(dropped), **({"reason": reason} if reason else {})}
            plan["deferrals"].append(entry)
            mac.save_plan(plan)
            mac.operator_action({"action": action, **entry})    # the move is logged even when nothing moves
            return {"from": host, "to": None, "jobs": 0, "not_rerun": len(dropped)}
    dest = place(plan, h, moved, dest, moved_role(plan, h, reason == "pre-job-failed"))
    entry = {"from": host, "to": dest, "from_indices": moving_idx, "to_indices": list(range(len(moved))),
             "stranded_retrain": None if stranded is None else
             {"from_index": stranded, "complete_sha256": jobs[stranded]["complete_sha256"]},
             **({"reason": reason} if reason else {})}
    plan["deferrals"].append(entry)
    mac.save_plan(plan)
    mac.operator_action({"action": action, **entry})
    if stranded is not None:
        mac.operator_action({"action": "stranded-retrain", "from": host, "to": dest, "reason": "stranded-retrain",
                             "complete_sha256": jobs[stranded]["complete_sha256"]})
    return {"from": host, "to": dest, "jobs": len(moved), "cap_hours": plan["hosts"][dest]["cap_hours"],
            "role": plan["hosts"][dest]["role"]}


def orchestrate_records(host: str) -> list[dict]:
    """The records of hosts/HOST/orchestrate.jsonl (orchestrate.py's log); an unreadable line refuses."""
    path = HERE / "hosts" / host / "orchestrate.jsonl"
    if not path.is_file():
        return []
    records = []
    for k, line in enumerate(path.read_text().splitlines()):
        try:
            record = json.loads(line)
            record["event"]
        except (ValueError, KeyError, TypeError):
            fail(f"{host}: orchestrate.jsonl line {k + 1} is unreadable")
        records.append(record)
    return records


def orchestrate_events(host: str) -> list[str]:
    """The events of hosts/HOST/orchestrate.jsonl; an unreadable line refuses."""
    return [r["event"] for r in orchestrate_records(host)]


def operator_records() -> list[dict]:
    """The records of operator-actions.jsonl; an unreadable line refuses."""
    if not mac.OPERATOR_LOG.is_file():
        return []
    records = []
    for k, line in enumerate(mac.OPERATOR_LOG.read_text().splitlines()):
        try:
            record = json.loads(line)
            record["action"]
        except (ValueError, KeyError, TypeError):
            fail(f"operator-actions.jsonl line {k + 1} is unreadable")
        records.append(record)
    return records


def _exit_zero(record: dict) -> bool:
    return type(record.get("exit")) is int and record["exit"] == 0


def stop_evidence(host: str, records: list[dict]) -> dict:
    """[D17] 3: how the pod's stop is known before a pre-job requeue. From the log: no ``job-start-unknown``, the last
    ``pre-job-failed`` names a step other than start-job (before start-job this run never launched the job runner),
    and a later ``pre-job-stop`` has exit 0 (host.py stop confirmed EXITED). Otherwise (a failure at start-job, a
    failed stop, an unknown job start) only the operator's ``confirm-stopped`` record of the log as it is now counts;
    else refuse."""
    failed = [k for k, r in enumerate(records) if r["event"] == "pre-job-failed"]
    if failed and "job-start-unknown" not in (r["event"] for r in records):
        last = records[failed[-1]]
        if isinstance(last.get("step"), str) and last["step"] != "start-job" and \
                any(r["event"] == "pre-job-stop" and _exit_zero(r) for r in records[failed[-1] + 1:]):
            return {"by": "log"}
    digest = mac.sha(HERE / "hosts" / host / "orchestrate.jsonl")
    confirmed = [r for r in operator_records() if r["action"] == "confirm-stopped" and r.get("host") == host
                 and r.get("orchestrate_sha256") == digest]
    if confirmed:
        return {"by": "operator", "pod_latest_sha256": confirmed[-1].get("pod_latest_sha256")}
    fail(f"{host}: the pod's stop is not confirmed by the log (a failure at start-job, a failed stop or an unknown "
         f"job start): check its status with host.py get {host}, then plan_tool.py confirm-stopped {host}")


def confirm_stopped(host: str) -> dict:
    """[D17] 3, the operator's route: after ``host.py get HOST`` (the pod's status, hosts/HOST/pod-latest.json) shows
    desiredStatus EXITED, read after the last record of hosts/HOST/orchestrate.jsonl, record that in
    operator-actions.jsonl, bound to the log's SHA-256 (a later log record voids it). Only a host with a logged
    pre-job failure or unknown job start and no job-started is confirmed."""
    plan = mac.load_plan()
    if host not in plan["hosts"]:
        fail(f"{host} is not a host of plan.json")
    records = orchestrate_records(host)
    events = [r["event"] for r in records]
    if "job-started" in events:
        fail(f"{host}: its job started; record-done and defer it")
    if "pre-job-failed" not in events and "job-start-unknown" not in events:
        fail(f"{host}: no logged pre-job failure in hosts/{host}/orchestrate.jsonl")
    latest_path = HERE / "hosts" / host / "pod-latest.json"
    if not latest_path.is_file():
        fail(f"{host}: no pod status read (host.py get {host})")
    latest = json.loads(latest_path.read_text())
    if latest.get("desiredStatus") != "EXITED":
        fail(f"{host}: the pod's status is not EXITED; stop it (host.py stop {host}) and read it again")
    try:
        read_at = dt.datetime.fromisoformat(str(latest.get("utc")).replace("Z", "+00:00"))
        last_at = dt.datetime.fromisoformat(str(records[-1].get("utc")).replace("Z", "+00:00"))
        if read_at.utcoffset() is None or last_at.utcoffset() is None:
            raise ValueError
    except ValueError:
        fail(f"{host}: the pod status read or the last log record has no readable UTC time")
    if read_at < last_at:
        fail(f"{host}: the pod status was read before the last orchestrate record; read it again (host.py get {host})")
    record = {"action": "confirm-stopped", "host": host, "desiredStatus": "EXITED", "pod_read_utc": latest["utc"],
              "pod_latest_sha256": mac.sha(latest_path),
              "orchestrate_sha256": mac.sha(HERE / "hosts" / host / "orchestrate.jsonl")}
    mac.operator_action(record)
    return {"host": host, "confirmed": True}


def requeue(host: str, rerun: list[str] | None = None) -> dict:
    """[D14]: a pre-job stop (no flag) or environment-mismatched complete attempts (--rerun-mismatched SHA ...)."""
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    if rerun:
        return requeue_mismatched(plan, host, h, rerun)
    records = orchestrate_records(host)
    events = [r["event"] for r in records]
    if h.get("done") or (HERE / "retrieved" / host / "tree" / "JOB-DONE.json").exists() or "job-started" in events:
        fail(f"{host}: its job started (a JOB-DONE.json or a logged job-started): record-done and defer it, or "
             "requeue --rerun-mismatched SHA for an environment-mismatched attempt")
    if "pre-job-failed" not in events and "job-start-unknown" not in events:
        fail(f"{host}: no logged pre-job failure in hosts/{host}/orchestrate.jsonl")
    if any(d["from"] == host for d in plan["deferrals"]):
        fail(f"{host} was already deferred")
    if any(j.get("status") != "planned" for j in h["jobs"]):
        fail(f"{host}: a job has a recorded status; only a host whose job never started is requeued")
    stop = stop_evidence(host, records)
    for job in h["jobs"]:                            # the job never started: every job is not_started
        job["status"] = "not_started"
    h["pre_job_failed"] = {"orchestrate_sha256": mac.sha(HERE / "hosts" / host / "orchestrate.jsonl"), "stop": stop}
    reset = first_host_reset(plan, host, h) if h["role"] == "first" else None
    out = move_open(plan, host, h, list(range(len(h["jobs"]))), "requeue", "pre-job-failed")
    if reset is not None:                            # after the plan is saved: the fixture is renamed, never deleted
        if reset["fixture"] is not None:
            mac.EXPECTED_FIXTURE.rename(HERE / reset["fixture"]["moved_to"])
        mac.operator_action({"action": "first-host-reset", "host": host, "to": out["to"], "fixture": reset["fixture"],
                             "reference_cleared": reset["reference"] is not None,
                             "reference_verification_sha256": (reset["reference"] or {}).get("verification_sha256")})
        out["first_reset"] = {"fixture_moved_to": (reset["fixture"] or {}).get("moved_to"),
                              "reference_cleared": reset["reference"] is not None}
    return out


def first_host_reset(plan: dict, host: str, h: dict) -> dict:
    """[D16] 7: wave 0a's first host stopped before its job, possibly after record_first wrote the expected fixture
    (and set the reference). In ``plan`` (saved by the move): the reference this host set is cleared and kept in the
    host's pre_job_failed record; the fixture's new name (a stamp) is recorded there, and the caller renames the file
    once the plan is saved. A reference set by another host refuses (the lead decides)."""
    reference = plan.get("reference")
    if reference and reference.get("host") != host:
        fail(f"{host}: the reference was set by another host ({reference.get('host')}); the lead decides")
    fixture = None
    if mac.EXPECTED_FIXTURE.exists():
        stamp = re.sub(r"[^0-9]", "", mac.utc())[:14]
        moved_to = f"{mac.EXPECTED_FIXTURE.stem}.moved-{host}-{stamp}Z{mac.EXPECTED_FIXTURE.suffix}"
        if (HERE / moved_to).exists():
            fail(f"{host}: {moved_to} already exists")
        recorded = [e for e in orchestrate_records(host) if e.get("event") == "expected-fixture-recorded"]
        fixture = {"name": mac.EXPECTED_FIXTURE.name, "moved_to": moved_to, "sha256": mac.sha(mac.EXPECTED_FIXTURE),
                   "recorded_by_host": any(e.get("sha256") == mac.sha(mac.EXPECTED_FIXTURE) for e in recorded)}
    reset = {"fixture": fixture, "reference": reference or None}
    h["pre_job_failed"]["first_reset"] = reset
    plan["reference"] = None
    return reset


def linked_pair(host: str, jobs: list[dict], i: int) -> tuple[int, int] | None:
    """[D16] 6: the (retrain, diagnostics) indices of the linked pair that job ``i`` of HOST belongs to (None for any
    other kind); both must be complete on HOST, since they are re-queued together."""
    if jobs[i]["kind"] == "diagnostics":
        pair = (jobs[i]["a0_source"], i)
    elif jobs[i]["kind"] == "retrain":
        pair = (i, rules.linked_diagnostics(jobs, i))
    else:
        return None
    if pair[1] is None or any(jobs[k].get("status") != "complete" or not jobs[k].get("complete_sha256") for k in pair):
        fail(f"{host}: the retrain and its diagnostics are re-queued together; both must be complete on this host")
    return pair


def requeue_mismatched(plan: dict, host: str, h: dict, rerun: list[str]) -> dict:
    """Queue again, like ``defer``, each complete arm, retrain or diagnostics job of HOST whose COMPLETE.json SHA-256 is
    named and whose unit's compared fields differ from the reference (refuse_complete); a named retrain or diagnostics
    brings its linked partner ([D16] 6); paid from the contingency from wave 1 on."""
    if not h.get("done"):
        fail(f"{host}: record-done first")
    if len(set(rerun)) != len(rerun):                # [D17] 6: a repeated hash refuses, never merged
        fail(f"{host}: --rerun-mismatched names one hash more than once")
    later = sorted({d["wave"] for d in plan["hosts"].values()
                    if WAVE_SEQUENCE.index(d["wave"]) > WAVE_SEQUENCE.index(h["wave"])}, key=WAVE_SEQUENCE.index)
    if later:                                        # [D17] 6: a re-run never follows a later wave's plan
        fail(f"{host}: a later wave is already planned (wave {later[0]}); a wave-{h['wave']} re-run comes before it")
    earlier = requeued_attempts(plan)
    picked, partners = [], set()
    for digest in rerun:
        if digest in earlier:
            fail(f"{host}: that attempt was already re-queued")
        found = [i for i, j in enumerate(h["jobs"]) if j.get("status") == "complete" and j.get("complete_sha256") == digest]
        if not found:
            fail(f"{host}: --rerun-mismatched names no complete job of this host")
        picked.append(found[0])
        partners.update(linked_pair(host, h["jobs"], found[0]) or ())
    if any(h["jobs"][k]["complete_sha256"] in earlier for k in partners):
        fail(f"{host}: that attempt was already re-queued")
    named = set(picked)
    picked = sorted(named | partners)
    moved, index_map = [], {}
    for i in picked:
        job = {k: v for k, v in h["jobs"][i].items() if k not in ("unit", "complete_sha256")}
        job.update(status="planned", deferred_from=host, reason="environment-mismatch",
                   mismatched_complete_sha256=h["jobs"][i]["complete_sha256"])
        if i not in named:
            job["linked_rerun"] = True              # moved with its named partner ([D16] 6)
        index_map[i] = len(moved)
        moved.append(job)
    for job in moved:
        if job["kind"] == "diagnostics":            # a0_source keeps naming its retrain, now in the moved list
            job["a0_source"] = index_map[job["a0_source"]]
    reruns = refuse_complete(plan, moved, rerun, linked={id(moved[index_map[k]]) for k in partners - named})
    too_many(host, moved)
    dest = destination(plan, host, h["wave"], rules.arm_count(moved))
    kept = pay_reruns(plan, moved, dest is None, f"requeue {host}", h["wave"])
    keys = {(j["arm"], j["seed"]) for j in kept}
    reruns = [r for r in reruns if (r["arm"], r["seed"]) in keys]
    dest = place(plan, h, kept, dest, moved_role(plan, h)) if kept else None
    entry = {"from": host, "to": dest, "reason": "environment-mismatch", "from_indices": picked,
             "to_indices": list(range(len(kept))), "complete_sha256": [h["jobs"][i]["complete_sha256"] for i in picked],
             "not_rerun": len(moved) - len(kept)}
    plan.setdefault("requeues", []).append(entry)
    mac.save_plan(plan)
    for record in reruns:
        mac.operator_action({"action": "rerun-mismatched", "where": f"requeue {host}", **record})
    mac.operator_action({"action": "requeue", **entry})
    return {"from": host, "to": dest, "jobs": len(kept), "not_rerun": entry["not_rerun"],
            "cap_hours": plan["hosts"][dest]["cap_hours"] if dest else None}


def set_reference(host: str) -> dict:
    plan = mac.load_plan()
    h = plan["hosts"].get(host) or fail(f"{host} is not a host of plan.json")
    if h["wave"] != "0a" or h["role"] != "first":
        fail("the reference comes from wave 0a's first host")
    if any(d["from"] == host for d in plan["deferrals"]):     # [D16] 7, 8: only its replacement acts as first
        fail(f"{host}: its jobs were moved to its replacement; a stopped kit pod is never restarted")
    if plan.get("reference"):
        fail("the reference is already set")
    folder = HERE / "hosts" / host
    ready = json.loads((folder / "bootstrap-ready.json").read_text())
    verification = json.loads((folder / "verification.json").read_text())
    bootstrap = {f: ready.get(f) for f in rules.BOOTSTRAP_FIELDS}
    fields = mac.compared_fields(verification.get("environment") or {}, ready.get("lock_sha256"),
                                 verification.get("policy_identity"))
    missing = sorted([f for f, v in bootstrap.items() if v is None] + [f for f, v in fields.items() if v is None])
    if missing:
        fail(f"the reference lacks {missing}")
    plan["reference"] = {"host": host, "utc": mac.utc(), "bootstrap": bootstrap, "fields": fields,
                         "bootstrap_ready_sha256": mac.sha(folder / "bootstrap-ready.json"),
                         "verification_sha256": mac.sha(folder / "verification.json")}
    mac.save_plan(plan)
    mac.operator_action({"action": "set-reference", "host": host,
                         "verification_sha256": plan["reference"]["verification_sha256"]})
    return {"reference": host}


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(prog="plan_tool.py")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("init-wave")
    p.add_argument("wave")
    p.add_argument("--jobs", required=True)
    p.add_argument("--reading")
    p.add_argument("--balance")
    p.add_argument("--rerun-mismatched", action="append")
    for name in ("record-done", "defer", "set-reference", "confirm-stopped"):
        sub.add_parser(name).add_argument("host")
    q = sub.add_parser("requeue")
    q.add_argument("host")
    q.add_argument("--rerun-mismatched", action="extend", nargs="+")
    a = ap.parse_args(argv)
    out = {"init-wave": lambda: init_wave(a), "record-done": lambda: record_done(a.host), "defer": lambda: defer(a.host),
           "requeue": lambda: requeue(a.host, a.rerun_mismatched), "set-reference": lambda: set_reference(a.host),
           "confirm-stopped": lambda: confirm_stopped(a.host)}[a.command]()
    print(json.dumps(out))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
