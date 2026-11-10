"""Drive one 7-8B host (administrative; no experiment logic; the stage-1 kit's orchestrate.py, itself from
runkit/gate-b-olmo/orchestrate.py, with the family-probe kit's gated-download step brought back; K3 of T4).

    orchestrate.py check-plan HOST     ($0, Mac) every job of HOST builds its commands and every input it needs is in
                                       the host's packed stage (sealed-files.json); run it before launch.py
    orchestrate.py after-create HOST   check-plan, wait for SSH, check GPU and timer, bootstrap the host's packed stage
                                       (its engine's: setup/packed-stage1-X or -Y; --with-base on a Safe LoRA host),
                                       wait for BOOTSTRAP-READY and compare it with the reference, for a gated family
                                       the gated download (the token goes to host.py on stdin, then to ssh's stdin),
                                       the preflight (the host's preflight recipe), compare its environment, policy and
                                       guard with the reference, the W1-18 hold, the cap gate, then start the job runner
    orchestrate.py status HOST         receipts and the timer's heartbeat

The gated step (K3; runkit/family-probe/orchestrate.py's, ported): for the family whose download plan holds a gated
repository (llama31-8b) the token is read from this process's environment variable HF_TOKEN_ENV (launch.py starts
this detached child with its environment; every other child of launch.py is scrubbed), handed to host.py
gated-download on stdin (never an argument, a file, a log or the child's environment: host.py runs under clean_env),
then dropped from this process's environment (secret_scan.scrub_process). Success needs host.py's exit 0 and a record
written by this call (hosts/HOST/gated-download.json; an earlier record is archived first). An open family
(olmo2-7b) never reads the token: the step scrubs the environment and returns. The pod's preflight refuses to start
without the gated receipt (setup/preflight_stage1.py gated_ready), so the step comes before the preflight.

Stage-1 changes:
- One packed stage per engine (G4): the host's stage must be stage1-<its engine>, the packed receipt's engine identity
  must be stage1_rules.ENGINES[engine] and the host's engine_sha256, and its sealed-files SHA-256 the plan's.
- The environment reference (§8 Q11, the lead's default): every stage-1 pod compares with Gate B's reference
  (plan.json "reference", imported by plan_tool import-reference), so new units are environment-matched with the
  reused R and a0 units; a pod that runs an evaluation-only reference (ref_eval, safe_lora) compares instead with the
  B10 certification pod's environment (the bootstrap-ready.json and verification.json this script fetched to
  hosts/CERTIFY_HOST/, CERTIFY_HOST from plan.json's recorded certification, which must pass). Without its reference a
  pod refuses (there is no provisional comparison: Gate B is closed and its reference exists). B5's rule is unchanged:
  the lock's SHA-256, the GPU name and the CUDA runtime stop the pod at BOOTSTRAP-READY, a pip_version difference is
  logged; after PREFLIGHT-DONE every compared field and the guard record (when the reference holds one) must be equal.
- The W1-18 hold (§8 Q1 (a), the lead's default): W1-18 runs alone on pod S1-0; a host holding W1-18 and any other job
  refuses, and a host holding a 500-bank job refuses to start while plan.json records no W1-18 branch (or a "Branch
  full by default" record), so FOCUS records W1-18's SHA-256 and branch before any 500-bank job exists. Option (b) (a
  bounded in-pod wait for the Mac's acknowledgement) is not built.
- No expected fixture and no first host (Gate B's wave-0a roles are gone); every role goes straight to the job runner
  after the gates.
Kept from Gate B: every step stops at the first failed check; the pod is never deleted; every child process gets an
environment without any token variable; a failure whose job start cannot be read logs ``job-start-unknown``, never
``pre-job-failed`` ([D17] 3); the cap gate compares the first job's start requirement (stage1_rules.requirements:
max(plan, this pod's projection with its O500 term)) with the remaining time.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import json
import os
import pathlib
import subprocess
import sys
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gateb_mac as mac  # noqa: E402
import probes  # noqa: E402
import secret_scan  # noqa: E402
import stage1_rules as rules  # noqa: E402
import importlib.util as _ilu  # noqa: E402

_spec = _ilu.spec_from_file_location("job_runner_stage1_for_orchestrate", HERE / "setup" / "job_runner_stage1.py")
runner = _ilu.module_from_spec(_spec)
_spec.loader.exec_module(runner)

ROOT = HERE.parents[1]
HOST_TOOL = [sys.executable, str(HERE / "host.py")]
PLAN_TOOL = [sys.executable, str(HERE / "plan_tool.py")]
REMOTE = "/workspace/attribution-headroom"
GPU = "NVIDIA A100-SXM4-80GB"
WORKER_SETUP = "worker-setup-stage1.tar.gz"
WORKER_BOOTSTRAP = "worker_bootstrap_stage1.sh"
REFERENCE_KINDS = ("ref_eval", "safe_lora")         # evaluation-only reference pods compare with the certification pod
BOOTSTRAP_OUTER = "worker-bootstrap-process-001"           # process_receipt's folder: process-receipt.json on exit
HF_TOKEN_ENV = rules.TOKEN_ENV_NAMES[0]                    # "HF_TOKEN": read here for the gated step only (launch.py's name)


def clean_env() -> dict:
    return secret_scan.scrubbed(os.environ, rules.TOKEN_ENV_NAMES)


def gated_entries(host: str | None = None) -> list[dict]:
    """The gated repositories of this working copy's family's download plan (launch.py's rule, repeated here so the
    two modules stay independent): llama31-8b's policy files; none for olmo2-7b. R3 K3 (R-66, R-71): with ``host``,
    also the host's extra gated downloads (stage1_rules.host_extra_downloads)."""
    try:
        rules.family_or_refuse()
    except ValueError as exc:
        raise SystemExit(str(exc)) from None
    extra = []
    if host is not None and host in plan().get("hosts", {}):
        jobs = plan()["hosts"][host]["jobs"]
        extra = [e for e in rules.host_extra_downloads(jobs, sorted({f for j in jobs for f in (j.get("families") or ())}))
                 if e["gated"]]
    return [e for e in probes.stage1_download_plan(rules.PROBE_KEY) if e["gated"]] + extra


def gated_download(host: str) -> None:
    """For a gated family: hand the token to host.py gated-download on stdin (never an argument or the environment);
    success needs host.py's exit 0 and a record written by this call (an earlier record is archived first). For an
    open family: scrub the environment and return (the token is never read)."""
    if not gated_entries(host):
        secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)       # an open family never needs the token
        return
    token = os.environ.get(HF_TOKEN_ENV, "").strip()
    if not token:
        raise SystemExit(f"{host}: {HF_TOKEN_ENV} is not set for the gated download")
    record_file = HERE / "hosts" / host / "gated-download.json"
    if record_file.exists():                                              # never trust a stale record
        stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        record_file.rename(record_file.with_name(f"gated-download-earlier-{stamp}.json"))
    done = tool("gated-download", host, stdin_text=token + "\n")
    token = None
    secret_scan.scrub_process(os.environ, rules.TOKEN_ENV_NAMES)           # no token in this process after use
    record = json.loads(record_file.read_text()) if record_file.exists() else {"ok": False}
    log(host, "gated-download-finished", ok=record.get("ok"), exit=record.get("exit"), tool_exit=done.returncode)
    if done.returncode != 0 or record.get("ok") is not True:
        raise SystemExit(f"{host}: the gated download failed")


def plan() -> dict:
    return mac.load_plan()


def log(host: str, event: str, **fields) -> None:
    record = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), "host": host, "event": event, **fields}
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "orchestrate.jsonl", "a") as handle:
        handle.write(json.dumps(record) + "\n")
    print(json.dumps(record), flush=True)


def env_record(host: str, record: dict) -> None:
    """The environment-check records (B8): hosts/HOST/environment-checks.jsonl, field names only."""
    (HERE / "hosts" / host).mkdir(parents=True, exist_ok=True)
    with open(HERE / "hosts" / host / "environment-checks.jsonl", "a") as handle:
        handle.write(json.dumps({"utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), **record}) + "\n")


def tool(*args: str, stdin_text: str | None = None) -> subprocess.CompletedProcess:
    return subprocess.run([*HOST_TOOL, *args], capture_output=True, text=True, env=clean_env(), input=stdin_text)


def ssh(host: str, command: str) -> subprocess.CompletedProcess:
    return tool("ssh", host, command)


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def send(host: str, local: pathlib.Path, remote_name: str) -> None:
    if tool("send", host, str(local), f"{REMOTE}/{remote_name}", sha(local)).returncode:
        raise SystemExit(f"{host}: transfer or hash check of {remote_name} failed")


def fetch(host: str, remote_name: str, local: pathlib.Path) -> dict:
    if tool("fetch", host, f"{REMOTE}/{remote_name}", str(local)).returncode:
        raise SystemExit(f"{host}: could not fetch {remote_name}")
    return json.loads(local.read_text())


def start_background(host: str, outer: str, command: str) -> None:
    script = (f"cd {REMOTE} && test ! -e {outer} || exit 1\n"
              f"nohup python3 process_receipt.py --out {outer} -- {command} > {outer}.log 2>&1 < /dev/null &\n"
              f"sleep 15; cd {REMOTE} && test -f {outer}/started.json")
    if ssh(host, script).returncode:
        out = ssh(host, f"cd {REMOTE} && tail -20 {outer}/process.log 2>/dev/null").stdout
        raise SystemExit(f"{host}: {outer} did not start:\n{out}")


def wait_file(host: str, remote_file: str, seconds: int, every: int = 60, ended: str | None = None) -> dict:
    """Wait for a JSON file on the pod. With ``ended`` (the producing process's receipt), stop as soon as that process
    has ended without writing the file, instead of waiting out ``seconds`` (8 Oct: a family-probe bootstrap that failed
    at its import waited the full 3600 s for BOOTSTRAP-READY.json, about $1.8)."""
    def read(name=remote_file):
        out = ssh(host, f"cat {REMOTE}/{name} 2>/dev/null")
        return json.loads(out.stdout) if out.returncode == 0 and out.stdout.strip() else None

    deadline = time.time() + seconds
    while time.time() < deadline:
        found = read()
        if found is not None:
            return found
        receipt = read(ended) if ended else None
        if receipt is not None:
            found = read()                                       # the file may land just before the receipt
            if found is not None:
                return found
            raise SystemExit(f"{host}: the process ended (exit {receipt.get('exit_code')}) without {remote_file}")
        time.sleep(every)
    found = read()
    if found is not None:
        return found
    raise SystemExit(f"{host}: {remote_file} did not appear within {seconds} s")


def wait_ssh(host: str, seconds: int = 1200) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if tool("get", host).returncode == 0 and ssh(host, "true").returncode == 0:
            return
        time.sleep(15)
    raise SystemExit(f"{host}: no SSH within {seconds} s")


def check(host: str) -> None:
    out = ssh(host, "nvidia-smi --query-gpu=name --format=csv,noheader; cat /workspace/.pod-timer/heartbeat.json")
    lines = out.stdout.splitlines()
    if out.returncode or not lines or lines[0].strip() != GPU:
        raise SystemExit(f"{host}: GPU is not {GPU}: {lines[:1]}")
    beat = json.loads("\n".join(lines[1:]))
    if not (beat.get("state") == "armed" and beat.get("supervised") is True and (beat.get("governing") or {}).get("source") == "cap"
            and all((beat.get("can_stop") or {}).values())):
        raise SystemExit(f"{host}: the stop timer is not armed and supervised with its cap")
    log(host, "checked", gpu=lines[0].strip(), cap_stop_utc=beat["governing"]["stop_at_utc"])


def packed(host: str) -> pathlib.Path:
    h = plan()["hosts"][host]
    if h["stage"] != f"stage1-{h['engine']}":
        raise SystemExit(f"{host}: the host's stage is not its engine's packed stage (G4)")
    return HERE / "setup" / f"packed-{h['stage']}"


def packed_receipt(host: str) -> dict:
    """The host's packed stage, checked against the plan (G4: its engine identity and sealed files)."""
    h = plan()["hosts"][host]
    receipt = json.loads((packed(host) / "setup-receipt.json").read_text())
    if receipt.get("engine_sha256") != rules.ENGINES.get(h["engine"]) or receipt.get("engine_sha256") != h["engine_sha256"]:
        raise SystemExit(f"{host}: the packed engine is not the host's engine (G4)")
    if receipt["sealed_files_sha256"] != h["sealed_files_sha256"]:
        raise SystemExit(f"{host}: the packed setup is not the one the plan names")
    return receipt


def with_base(host: str) -> bool:
    return any(j["kind"] == "safe_lora" for j in plan()["hosts"][host]["jobs"])


def check_plan(host: str) -> dict:
    """$0: every job's commands build and every file and input it needs is in the packed sealed-files.json."""
    p = plan()
    h = p["hosts"][host]
    packed_receipt(host)
    doc = json.loads((packed(host) / "sealed-files.json").read_text())
    w1 = [j for j in h["jobs"] if j["kind"] == "w1_18"]
    if w1 and len(h["jobs"]) != 1:
        raise SystemExit(f"{host}: W1-18 runs alone on its pod (§8 Q1 (a))")
    problems, units = [], {}
    for i, job in enumerate(h["jobs"]):
        try:                                             # GXB R-75: the Mac's build; pod files are hashed on the pod
            with runner.mac_build(HERE.parents[1]):
                runner.job_commands(p, host, i, HERE / "hosts" / host, units, doc)
        except runner.Unrunnable as exc:
            problems.append(str(exc))
        missing = [rel for rel in runner.sealed_paths(job, h, i, doc, runner.oext_fallback(p))
                   if rel not in doc["files"]]
        if missing:
            problems.append(f"job {i} ({job['kind']}): {len(missing)} file(s) not packed: {missing[:3]}")
        units[i] = f"@unit:{i}"
    if problems:
        raise SystemExit(f"{host}: the plan cannot run on its packed stage: {problems[:5]}")
    return {"host": host, "jobs": len(h["jobs"]), "ok": True}


def bootstrap(host: str) -> None:
    folder = packed(host)
    receipt = packed_receipt(host)
    if tool("send", host, str(folder / WORKER_SETUP), f"{REMOTE}/{WORKER_SETUP}", receipt["setup"]["sha256"]).returncode:
        raise SystemExit(f"{host}: setup transfer or hash check failed")
    unpack = (f"cd {REMOTE} && python3 - <<'REMOTE'\n"
              "import pathlib,hashlib,tarfile\n"
              f"p=pathlib.Path('{WORKER_SETUP}');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{receipt['setup']['sha256']}'\n"
              f"assert not pathlib.Path('{BOOTSTRAP_OUTER}').exists()\n"
              "with tarfile.open(p) as t:t.extractall('.',filter='data')\n"
              "REMOTE")
    if ssh(host, unpack).returncode:
        raise SystemExit(f"{host}: setup unpack failed")
    start_background(host, BOOTSTRAP_OUTER, f"bash {WORKER_BOOTSTRAP}" + (" --with-base" if with_base(host) else ""))
    log(host, "bootstrap-started")


def certification_reference() -> dict:
    """§8 Q11: the B10 certification pod's environment (its fetched bootstrap-ready.json and verification.json), the
    reference of every evaluation-only reference pod; the recorded certification must pass."""
    cert = (plan().get("records") or {}).get("certification")
    if not cert or cert.get("pass") is not True:
        raise SystemExit("no passing B10 certification is recorded: a reference pod has no reference")
    folder = HERE / "hosts" / cert["host"]
    ready = json.loads((folder / "bootstrap-ready.json").read_text())
    verification = json.loads((folder / "verification.json").read_text())
    return {"bootstrap": {k: ready.get(k) for k in rules.BOOTSTRAP_FIELDS},
            "fields": mac.compared_fields(verification.get("environment") or {}, ready.get("lock_sha256"),
                                          verification.get("policy_identity")),
            "guard": (json.loads((folder / "preflight-done.json").read_text()).get("guard")
                      if (folder / "preflight-done.json").is_file() else None),
            "source": f"certification pod {cert['host']}"}


def reference_for(host: str) -> tuple[dict, bool]:
    """(the reference, True: a difference always stops the pod)."""
    p = plan()
    if any(j["kind"] in REFERENCE_KINDS for j in p["hosts"][host]["jobs"]):
        return certification_reference(), True
    if p.get("reference"):
        return p["reference"], True
    raise SystemExit(f"{host}: no environment reference (plan_tool.py import-reference loads Gate B's)")


def environment_gate(host: str, point: str, new: dict, fields) -> dict:
    reference, strict = reference_for(host)
    ref = reference["bootstrap"] if point == "bootstrap" else {**reference["fields"], "guard": reference.get("guard")}
    result = rules.compare(new, ref, fields)
    env_record(host, {"point": point, "strict": strict, **result})
    if result["logged"]:
        log(host, "pip-version-differs" if "pip_version" in result["logged"] else "environment-logged",
            fields=result["logged"])
    if not strict:
        log(host, "environment-provisional", point=point, differ=result["differ"], missing=result["missing"])
        return result
    if result["stop"]:
        log(host, "environment-mismatch", point=point, fields=result["differ"], missing=result["missing"])
        raise SystemExit(f"{host}: the environment differs from the reference at {point}: "
                         f"{result['differ'] + result['missing']}")
    return result


def bootstrap_check(host: str, ready: dict) -> dict:
    """B5 at BOOTSTRAP-READY: lock SHA-256, GPU and CUDA runtime stop the pod; pip_version is only logged."""
    return environment_gate(host, "bootstrap", ready, rules.BOOTSTRAP_FIELDS)


def preflight_check(host: str, verification: dict, ready: dict, done: dict | None = None) -> dict:
    """B5 after PREFLIGHT-DONE: every compared field (and the policy block) against the reference, and ([D17] 4) the
    guard record (PREFLIGHT-DONE.json's ``guard``, the engine's guard_pin on this pod) against the reference's guard:
    Gate B's reference holds R_1101's guard, and a Gate B reference without one refuses; the certification pod's
    reference holds that pod's own preflight guard (hosts/CERTIFY_HOST/preflight-done.json)."""
    fields = mac.compared_fields(verification.get("environment") or {}, ready.get("lock_sha256"),
                                 verification.get("policy_identity"))
    reference, strict = reference_for(host)
    names = sorted(set(fields) | set(reference["fields"]))
    if reference.get("guard") is not None:
        fields = {**fields, "guard": (done or {}).get("guard")}
        names.append("guard")
    elif strict and reference.get("source") is None:
        log(host, "guard-reference-missing")
        raise SystemExit(f"{host}: the reference has no guard record")
    return environment_gate(host, "preflight", fields, names)


def parse_utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(text.replace("Z", "+00:00"))


def cap_stop(host: str) -> str:
    folder = HERE / "hosts" / host
    stop = json.loads((folder / "pod.json").read_text())["cap_stop_utc"]
    override = folder / "cap-override.json"
    if override.exists():
        later = json.loads(override.read_text())["stop_at_utc"]
        if parse_utc(later) > parse_utc(stop):
            stop = later
    return stop


def preflight_wait(wait_s: int, stop_utc: str, now: dt.datetime) -> int:
    return int(max(0, min(wait_s, (parse_utc(stop_utc) - now).total_seconds())))


def cap_gate(host: str, done: dict, now: dt.datetime) -> dict:
    """The first job's start requirement against the remaining time (B3 [V21g]); a missing stop refuses."""
    jobs = plan()["hosts"][host]["jobs"]
    try:
        need = rules.requirements(jobs, done.get("cap_projection") or {})[0]
    except (KeyError, TypeError, ValueError):
        return {"remaining_s": None, "requirement_s": None, "ok": False}
    stop = done.get("governing_stop_utc")
    remaining = (parse_utc(stop) - now).total_seconds() if stop else None
    return {"remaining_s": remaining, "requirement_s": need, "ok": rules.gate(remaining, need)}


def preflight(host: str) -> dict:
    p = plan()
    h = p["hosts"][host]
    p_host = dict(p)
    p_host["preflight_recipes"], p_host["preflight_prepared"] = [runner.preflight_recipe(h)], runner.PREPARED
    local = HERE / "hosts" / host / "plan-preflight.json"
    local.write_text(json.dumps(p_host, indent=1, sort_keys=True) + "\n")
    send(host, local, "plan.json")
    start_background(host, "preflight-outer", "venv/bin/python preflight_stage1.py")
    wait = preflight_wait(h["preflight_wait_s"], cap_stop(host), dt.datetime.now(dt.timezone.utc))
    done = wait_file(host, "PREFLIGHT-DONE.json", wait)
    (HERE / "hosts" / host / "preflight-done.json").write_text(json.dumps(done, indent=1, sort_keys=True) + "\n")
    log(host, "preflight-finished", ok=done["ok"], recipe=done["recipe"], init_equals_untuned=done.get("init_equals_untuned"))
    if not done["ok"] or done["recipe"] != runner.preflight_recipe(h):
        raise SystemExit(f"{host}: the preflight did not pass for the host's recipe")
    return done


def w1_18_hold(host: str) -> None:
    """§8 Q1 (a): W1-18 alone on its pod; no 500-bank job before the family's branch record (G1). R2 K2 (GXB R-45,
    K-8): the branch is read only from BRANCH_78B[family], by its bytes at its pin (rules_78b.bank500_problem, as the
    planner reads it); block 0's kinds never read the 500 bank, so its pods are never held."""
    p = plan()
    h = p["hosts"][host]
    jobs = h["jobs"]
    if any(j["kind"] == "w1_18" for j in jobs) and len(jobs) != 1:
        raise SystemExit(f"{host}: W1-18 runs alone on its pod (§8 Q1 (a))")
    family = rules.family_or_refuse()
    pin = rules.r78.BRANCH_78B.get(family)
    data = None
    if isinstance(pin, dict) and rules.r78._plain_rel(pin.get("path")) and (ROOT / pin["path"]).is_file():
        data = (ROOT / pin["path"]).read_bytes()
    for j in jobs:
        problem = rules.r78.bank500_problem(family, j["kind"], h.get("block"), data)
        if problem:
            log(host, "w1-18-hold", reason="no pinned branch record")
            raise SystemExit(f"{host}: a 500-bank job waits for W1-18's branch record (G1): {problem}")


def start_job(host: str, done: dict) -> None:
    gate = cap_gate(host, done, dt.datetime.now(dt.timezone.utc))
    if not gate["ok"]:
        log(host, "cap-insufficient", **gate)
        raise SystemExit(f"{host}: the first job does not fit the remaining cap")
    w1_18_hold(host)
    send(host, mac.PLAN, "plan.json")
    start_background(host, "job-outer", f"venv/bin/python job_runner_stage1.py {host}")
    log(host, "job-started", plan_sha256=sha(mac.PLAN), jobs=len(plan()["hosts"][host]["jobs"]))


def wait_for(condition, what: str, seconds: int = 6 * 3600) -> None:
    deadline = time.time() + seconds
    while time.time() < deadline:
        if condition():
            return
        time.sleep(30)
    if condition():
        return
    raise SystemExit(f"waited {seconds} s for {what}")


def _after_create(host: str, step: dict) -> None:
    folder = HERE / "hosts" / host
    step["name"] = "check-plan"
    check_plan(host)
    step["name"] = "w1-18-hold"
    w1_18_hold(host)
    step["name"] = "wait-ssh"
    wait_ssh(host)
    step["name"] = "check"
    check(host)
    step["name"] = "bootstrap"
    bootstrap(host)
    step["name"] = "bootstrap-ready"
    wait_file(host, "BOOTSTRAP-READY.json", 3600, ended=f"{BOOTSTRAP_OUTER}/process-receipt.json")
    ready = fetch(host, "BOOTSTRAP-READY.json", folder / "bootstrap-ready.json")
    step["name"] = "bootstrap-check"
    bootstrap_check(host, ready)
    step["name"] = "gated-download"                      # K3: before the preflight (which loads the policy)
    gated_download(host)
    step["name"] = "preflight"
    done = preflight(host)
    verification = fetch(host, f"{done['folder']}/verification.json", folder / "verification.json")
    step["name"] = "preflight-check"
    preflight_check(host, verification, ready, done)
    step["name"] = "cap-gate"
    gate = cap_gate(host, done, dt.datetime.now(dt.timezone.utc))
    if not gate["ok"]:
        log(host, "cap-insufficient", **gate)
        raise SystemExit(f"{host}: the first job does not fit the remaining cap")
    step["name"] = "start-job"
    start_job(host, done)


def after_create(host: str) -> None:
    """``_after_create``; any failure before the job starts is logged as ``pre-job-failed`` with its step, the in-pod
    stop is moved to 2 min from now and the pod is stopped (never deleted), then the failure is raised again. When
    the pod cannot say whether the job started (``job_started`` None: an ssh exit other than 0 or 1, or an
    exception), the failure is logged as ``job-start-unknown`` instead ([D17] 3), and the pod is stopped the same
    way; ``plan_tool.py requeue`` then needs the operator's confirm-stopped record. ``pre-job-stop`` logs the stop's
    exit (host.py stop exits 1 when it cannot confirm EXITED)."""
    step = {"name": "start"}
    try:
        _after_create(host, step)
    except BaseException as exc:
        started = job_started(host)
        if started:
            log(host, "job-started", note=f"started although {step['name']} reported {type(exc).__name__}")
        else:
            log(host, "pre-job-failed" if started is False else "job-start-unknown", step=step["name"],
                error=type(exc).__name__, detail=str(exc)[-300:])
            shortened = tool("extend-cap", host, "120")
            stopped = tool("stop", host)
            log(host, "pre-job-stop", exit=stopped.returncode, timer_shortened=shortened.returncode == 0,
                out=(stopped.stdout + stopped.stderr)[-300:])
            raise


def job_started(host: str) -> bool | None:
    """True when the job runner's started.json exists (ssh exit 0), False when it does not (exit 1, ``test -f``'s
    false), None (unknown) for any other exit or an exception ([D17] 3: a dropped connection never reads as "not
    started")."""
    try:
        code = ssh(host, f"test -f {REMOTE}/job-outer/started.json").returncode
    except BaseException:  # noqa: BLE001
        return None
    return True if code == 0 else False if code == 1 else None


def status(host: str) -> None:
    out = ssh(host, f"cd {REMOTE} && ls -d round1/*/ cert/*/ job-*/ job-done/* 2>/dev/null; ls -d BOOTSTRAP-READY.json "
                    "PREFLIGHT-DONE.json JOB-DONE.json deferral.json gated-download-receipt.json cuda-preflight-* 2>/dev/null; "
                    "python3 -c \"import json;b=json.load(open('/workspace/.pod-timer/heartbeat.json'));"
                    "print('timer',b['state'],b['governing']['source'],b['governing']['stop_at_utc'],b['utc'])\"")
    print(out.stdout or out.stderr)


def main() -> int:
    command, host = sys.argv[1], sys.argv[2]
    if command == "check-plan":
        print(json.dumps(check_plan(host)))
        return 0
    {"after-create": after_create, "status": status, "check": check, "bootstrap": bootstrap}[command](host)
    return 0


if __name__ == "__main__":
    sys.exit(main())
