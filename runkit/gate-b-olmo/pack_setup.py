"""Pack one stage of the Gate B setup (administrative; never includes credentials or .ai text beyond the sealed files).

    python3.11 pack_setup.py anchor     the anchor pod's setup (recipe REC; the anchor file does not exist yet)
    python3.11 pack_setup.py gateb      every later pod's setup (recipe S, the sealed anchor file, the Gate C scripts)

Refuses (brief B7, [D10]) unless every sealed file matches its pin: MAN (gateb_rules.MAN_SHA256) and, through MAN's
SHA-256 values, all 31 files it lists; the anchor prompt list (gateb_rules.ANCHOR_PROMPTS_PIN); for stage gateb the
sealed anchor file (ANCHOR_FILE_PIN); the stage's pinned scripts (PINNED_SCRIPTS, STAGE_SCRIPTS). Also refuses: an
uncommitted engine or script file, the stage's recipe missing, setup/constraints.txt other than the one line
setuptools==<gateb_rules.SETUPTOOLS_PIN>, a missing process_receipt.py (the lead copies it in at packing time; [D9]
B-6), and a secret pattern in any packed kit file, record or generated payload (the prepared folder, the sealed
files and the anchor texts are not scanned as code: they are data, and a hit there is reported by name only).
Writes, once, under setup/packed-STAGE/ (refuses to overwrite):
  probe.json                 the OLMo-2-1B and Qwen3Guard download plan and weight pins (probes.py, olmo2-1b)
  sealed-files.json          every sealed or pinned file by its bundle path and SHA-256 (the job runner checks each
                             script and edit file against it before use)
  bundle-gateb-STAGE.tar.gz  engine code, the preflight scripts, the stage's pinned scripts, constraints.txt,
                             bootstrap_hr.sh, requirements.lock, the prepared set, sealed/ (MAN and its 31 files),
                             anchors/, sealed-files.json, bundle-manifest.json
  worker_bootstrap_gateb.sh  generated: setup and downloads; then process 1 (bundle hash, extraction, every file hash,
                             the prepared manifests, sealed-files.json) and process 2, a fresh interpreter started after
                             the extraction: importlib.invalidate_caches() first, then the engine identity, the GPU and
                             the B5 lock checks; it writes BOOTSTRAP-READY.json {lock_sha256, pip_version, gpu,
                             cuda_runtime} (brief B5, B6; AUD:73)
  worker-setup-gateb.tar.gz  everything a pod needs before the plan (constraints.txt beside bootstrap_hr.sh; [D9] B-3)
  setup-receipt.json         hashes of all of it and the packed engine's code identity
"""
from __future__ import annotations

import hashlib
import io
import json
import pathlib
import subprocess
import sys
import tarfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gateb_rules as rules  # noqa: E402
import probes  # noqa: E402
import secret_scan  # noqa: E402

ROOT = HERE.parents[1]
SETUP = HERE / "setup"
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
PREFLIGHT_SCRIPTS = ("cuda_preflight_family.py", "cuda_preflight_killtest.py", "cuda_preflight_headroom_v3.py",
                     "cuda_preflight_headroom.py")
SETUP_FILES = ("bootstrap_hr.sh", "constraints.txt", "setup_and_fetch_gateb.sh", "download_models_gateb.py",
               "preflight_gateb.py", "job_runner_gateb.py", "extend_cap.py")
PROCESS_RECEIPT = "tmp/study-v2-20261002/process_receipt.py"
WORKER_BOOTSTRAP = "worker_bootstrap_gateb.sh"
WORKER_SETUP = "worker-setup-gateb.tar.gz"
ANCHOR_PROMPTS_BUNDLE = "anchors/anchor_prompts.json"     # the job runner's paths (setup/job_runner_gateb.py)
ANCHOR_FILE_BUNDLE = "anchors/anchor_bank.json"
SEALED_DIR = "sealed"
GPU = "NVIDIA A100-SXM4-80GB"
HEX = set("0123456789abcdef")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def tar(dest: pathlib.Path, files: dict, extra: dict | None = None) -> None:
    with dest.open("xb") as handle:
        with tarfile.open(fileobj=handle, mode="w:gz") as archive:
            for name, f in sorted(files.items()):
                digest = sha(f); archive.add(f, arcname=name, recursive=False); assert sha(f) == digest, f"{f} changed"
            for name, payload in sorted((extra or {}).items()):
                entry = tarfile.TarInfo(name); entry.size = len(payload); entry.mtime = int(time.time())
                archive.addfile(entry, io.BytesIO(payload))


def pinned(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and not set(value) - HEX


def sealed_files(stage: str) -> tuple[dict, dict]:
    """(bundle path -> source file, bundle path -> pinned SHA-256) of every sealed or pinned file of the stage; refuses
    (names only) unless each file exists and matches its pin (B7)."""
    if stage not in rules.STAGE_SCRIPTS:
        raise SystemExit(f"unknown stage {stage!r} (anchor or gateb)")
    files, pins, bad = {}, {}, []
    man_path = ROOT / rules.MAN_PATH
    if not man_path.is_file() or sha(man_path) != rules.MAN_SHA256:
        raise SystemExit("the sealed MANIFEST.json is missing or differs from its pin")
    files[f"{SEALED_DIR}/MANIFEST.json"], pins[f"{SEALED_DIR}/MANIFEST.json"] = man_path, rules.MAN_SHA256
    for entry in json.loads(man_path.read_text())["files"]:
        src = man_path.parent / entry["path"]
        name = f"{SEALED_DIR}/{entry['path']}"
        if not src.is_file() or sha(src) != entry["sha256"]:
            bad.append(name)
        files[name], pins[name] = src, entry["sha256"]
    wanted = [(ANCHOR_PROMPTS_BUNDLE, rules.ANCHOR_PROMPTS_PIN)]
    if stage == "gateb":
        wanted.append((ANCHOR_FILE_BUNDLE, rules.ANCHOR_FILE_PIN))
    for name, pin in wanted:
        if not (pin.get("path") and pinned(pin.get("sha256"))):
            bad.append(f"{name} (not pinned yet)")
            continue
        src = ROOT / pin["path"]
        if not src.is_file() or sha(src) != pin["sha256"]:
            bad.append(name)
        files[name], pins[name] = src, pin["sha256"]
    for script in rules.STAGE_SCRIPTS[stage]:
        pin = rules.PINNED_SCRIPTS.get(script)
        src = ROOT / script
        if not pinned(pin):
            bad.append(f"{script} (not pinned yet)")
        elif not src.is_file() or sha(src) != pin:
            bad.append(script)
        else:
            files[script], pins[script] = src, pin
    if bad:
        raise SystemExit(f"{len(bad)} sealed or pinned file(s) missing or differ from their pins: {bad[:10]}")
    return files, pins


def check_constraints() -> None:
    text = (SETUP / "constraints.txt").read_text()
    if text != f"setuptools=={rules.SETUPTOOLS_PIN}\n":
        raise SystemExit("setup/constraints.txt must hold exactly the line setuptools==" + rules.SETUPTOOLS_PIN)


def probe_record() -> dict:
    return {"probe": rules.PROBE_KEY, "plan": probes.download_plan(rules.PROBE_KEY),
            "weight_pins": list(probes.PROBES[rules.PROBE_KEY]["weight_pins"])}


def refuse_secrets(files: dict, payloads: dict, data_prefixes: tuple) -> None:
    """Scan every packed file outside the data folders, and every generated payload; a hit refuses (names only)."""
    scanned = [f for name, f in files.items() if not name.startswith(data_prefixes)]
    hits = [(name, pattern) for name, pattern in secret_scan.scan_paths(scanned)]
    hits += [(name, pattern) for name, payload in payloads.items()
             for pattern in secret_scan.scan_text(payload.decode("utf-8", "ignore"))]
    if hits:
        raise SystemExit(f"a secret pattern is in a packed file: {[(pathlib.Path(n).name, p) for n, p in hits][:10]}")


def worker_bootstrap(stage: str, bundle: str, bundle_sha: str, code: str, prepared: dict, pip_pin: str | None) -> str:
    """The generated worker bootstrap (B5, B6): no token; two Python processes after the setup."""
    checks = ",".join(f"('{n}','{d}')" for n, d in sorted(prepared.items()))
    pin = f"export GATEB_PIP_PIN={pip_pin}\n" if pip_pin else ""
    return f"""#!/bin/bash
# Generated by pack_setup.py (Gate B, stage {stage}): environment and open models, then two processes. Process 1
# checks the bundle hash, extracts it and checks every file hash, the prepared manifests and sealed-files.json.
# Process 2, a fresh interpreter started after the extraction, calls importlib.invalidate_caches() first, then runs the
# identity, GPU and lock checks and writes BOOTSTRAP-READY.json. No token here.
set -euo pipefail
cd /workspace/attribution-headroom
export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONPATH=/workspace/attribution-headroom
{pin}python3 process_receipt.py --out setup-001 -- bash setup_and_fetch_gateb.sh "$@"
venv/bin/python - <<'PY1'
import datetime,hashlib,json,pathlib,tarfile
p=pathlib.Path('{bundle}');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{bundle_sha}','bundle'
with tarfile.open(p) as t:t.extractall('.',filter='data')
m=json.loads(pathlib.Path('bundle-manifest.json').read_text())
for f,h in m['files'].items():assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==h,f
for name,digest in [{checks}]:assert pathlib.Path(name,'manifest.sha256').read_text().strip()==digest,name
s=json.loads(pathlib.Path('sealed-files.json').read_text())
for f,h in s['files'].items():assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==h,f
pathlib.Path('BUNDLE-CHECKED.json').write_text(json.dumps({{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ok':True,'bundle_sha256':'{bundle_sha}','files':len(m['files'])}})+'\\n')
print('bundle checked',flush=True)
PY1
venv/bin/python - <<'PY2'
import importlib
importlib.invalidate_caches()
import datetime,hashlib,json,pathlib,re,subprocess,sys
assert json.loads(pathlib.Path('BUNDLE-CHECKED.json').read_text())['ok'] is True,'bundle not checked'
from experiments.safety_selection.common import code_identity
assert code_identity()['sha256']=='{code}','engine code identity differs from the packed code'
import torch
gpu=torch.cuda.get_device_name(0)
assert gpu=='{GPU}','gpu'
lock=pathlib.Path('environment-linux.lock').read_bytes()
lines=[l.strip() for l in lock.decode().splitlines()]
assert 'setuptools=={rules.SETUPTOOLS_PIN}' in lines,'the lock has no setuptools=={rules.SETUPTOOLS_PIN} line'
assert not [l for l in lines if re.match('wheel([=<>~!@ ]|$)',l,re.I)],'the lock has a wheel line'
pip=subprocess.run([sys.executable,'-m','pip','--version'],capture_output=True,text=True,check=True).stdout.split()[1]
ready={{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ok':True,'engine_sha256':'{code}','lock_sha256':hashlib.sha256(lock).hexdigest(),'pip_version':pip,'gpu':gpu,'cuda_runtime':torch.version.cuda}}
pathlib.Path('BOOTSTRAP-READY.json').write_text(json.dumps(ready)+'\\n')
print('bootstrap ready',flush=True)
PY2
"""


def engine_code() -> str:
    return subprocess.run([str(PY), "-c", "from experiments.safety_selection.common import code_identity;"
                           "print(code_identity()['sha256'])"], cwd=ROOT, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def git_state() -> str:
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "experiments", "scripts"],
                            capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise SystemExit(f"engine or script files are not committed:\n{status}")
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def main(argv: list[str] | None = None) -> None:
    args = sys.argv[1:] if argv is None else argv
    stage = args[0] if args else None
    if stage not in rules.STAGE_SCRIPTS:
        raise SystemExit("give the stage: anchor or gateb")
    out = SETUP / f"packed-{stage}"
    check_constraints()
    recipe = rules.REC if stage == "anchor" else rules.RECIPE_S
    if not (ROOT / recipe).is_file():
        raise SystemExit(f"{recipe} does not exist: stage {stage} cannot be packed yet")
    sealed, pins = sealed_files(stage)
    process_receipt = ROOT / PROCESS_RECEIPT
    if not process_receipt.is_file():
        raise SystemExit(f"{PROCESS_RECEIPT} is missing: copy it in before packing ([D9] B-6)")
    commit = git_state()
    files = {}
    for component in ("minimal_safety", "safety_selection"):
        for f in (ROOT / "experiments" / component).rglob("*"):
            if f.is_file() and not f.is_symlink() and "__pycache__" not in f.parts and f.suffix in {".py", ".json", ".md", ".lock"}:
                files[str(f.relative_to(ROOT))] = f
    for name in PREFLIGHT_SCRIPTS:
        files[f"scripts/{name}"] = ROOT / "scripts" / name
    files["bootstrap_hr.sh"] = SETUP / "bootstrap_hr.sh"
    files["constraints.txt"] = SETUP / "constraints.txt"
    files["requirements.lock"] = ROOT / "experiments/minimal_safety/requirements.lock"
    for name, digest in rules.PREPARED_MANIFESTS.items():
        folder = ROOT / rules.PREPARED_LOCAL / name
        if (folder / "manifest.sha256").read_text().strip() != digest:
            raise SystemExit(f"{name}: unexpected manifest")
        for f in folder.rglob("*"):
            if f.is_file():
                files[f"{name}/{f.relative_to(folder)}"] = f
    files.update(sealed)
    sealed_json = (json.dumps({"kind": "gate-b sealed files", "version": 1, "stage": stage,
                               "files": dict(sorted(pins.items()))}, indent=1) + "\n").encode()
    manifest = {"kind": f"explicit code and data export for the Gate B kit, stage {stage}; no credentials",
                "git_commit": commit, "stage": stage, "prepared_manifests": rules.PREPARED_MANIFESTS,
                "files": {n: sha(f) for n, f in sorted(files.items())}}
    payload = {"bundle-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(), "sealed-files.json": sealed_json}
    probe_json = (json.dumps(probe_record(), indent=1) + "\n").encode()
    data = tuple(rules.PREPARED_MANIFESTS) + (SEALED_DIR + "/", "anchors/")
    refuse_secrets(files, {**payload, "probe.json": probe_json}, data)
    out.mkdir(parents=True, exist_ok=False)
    (out / "probe.json").write_bytes(probe_json)
    (out / "sealed-files.json").write_bytes(sealed_json)
    bundle = out / f"bundle-gateb-{stage}.tar.gz"
    tar(bundle, files, payload)
    code = engine_code()
    bundle_sha = sha(bundle)
    bootstrap = worker_bootstrap(stage, bundle.name, bundle_sha, code, rules.PREPARED_MANIFESTS, rules.PIP_PIN)
    if secret_scan.scan_text(bootstrap):
        raise SystemExit("a secret pattern is in the generated bootstrap")
    (out / WORKER_BOOTSTRAP).write_text(bootstrap)
    setup_files = {name: SETUP / name for name in SETUP_FILES}
    setup_files.update({"gateb_rules.py": HERE / "gateb_rules.py", WORKER_BOOTSTRAP: out / WORKER_BOOTSTRAP,
                        "probe.json": out / "probe.json", bundle.name: bundle, "process_receipt.py": process_receipt,
                        "requirements.lock": ROOT / "experiments/minimal_safety/requirements.lock"})
    refuse_secrets({n: f for n, f in setup_files.items() if n != bundle.name}, {}, ())
    setup = out / WORKER_SETUP
    tar(setup, setup_files)
    receipt = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stage": stage, "git_commit": commit,
               "engine_sha256": code, "recipe": recipe, "sealed_files_sha256": hashlib.sha256(sealed_json).hexdigest(),
               "bundle": {"path": str(bundle), "sha256": bundle_sha, "files": len(files)},
               "setup": {"path": str(setup), "sha256": sha(setup), "bytes": setup.stat().st_size},
               "pip_pin": rules.PIP_PIN, "members": {name: sha(f) for name, f in sorted(setup_files.items())}}
    with (out / "setup-receipt.json").open("x") as handle:
        handle.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("stage", "git_commit", "engine_sha256", "sealed_files_sha256",
                                              "bundle", "setup")}, indent=2))


if __name__ == "__main__":
    main()
