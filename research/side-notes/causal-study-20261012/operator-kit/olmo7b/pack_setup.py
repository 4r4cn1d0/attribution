"""Pack one family probe's setup (administrative; never includes credentials or .ai).

    python3.11 pack_setup.py

Refuses an unset probe (probe_constants.PROBE), an unset prepared manifest, a missing or malformed weight pin, and a
secret pattern (secret_scan.PATTERNS) in any kit script, record or receipt it packs; the prepared folder is not scanned
(built on the Mac from public data; brief Item 5c). Writes, once (refuses to overwrite):
  setup/probe.json                  the probe key, its download plan (open and gated repositories) and its weight pins
  setup/bundle-probe.tar.gz         engine code (minimal_safety, safety_selection), cuda_preflight_family.py and the helper
                                    scripts it imports, bootstrap_hr.sh, requirements.lock, the probe's prepared set,
                                    bundle-manifest.json
  setup/worker_bootstrap_probe.sh   environment and open models, bundle and prepared-manifest checks, engine identity, GPU
                                    check; writes BOOTSTRAP-READY.json (the gated download and the preflight are later steps)
  setup/worker-setup-probe.tar.gz   everything a pod needs before the plan
  setup/setup-receipt.json          hashes of all of it, and the engine code identity of the packed code
"""
import hashlib, io, json, pathlib, subprocess, sys, tarfile, time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probe_constants as pc  # noqa: E402
import probes  # noqa: E402
import secret_scan  # noqa: E402

ROOT = HERE.parents[1]
SETUP = HERE / "setup"
PREP = ROOT / pc.PREPARED_LOCAL
HEX = set("0123456789abcdef")
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tar(dest: pathlib.Path, files: dict, extra: dict | None = None) -> None:
    with dest.open("xb") as handle:
        with tarfile.open(fileobj=handle, mode="w:gz") as archive:
            for name, f in sorted(files.items()):
                digest = sha(f); archive.add(f, arcname=name, recursive=False); assert sha(f) == digest, f"{f} changed"
            for name, payload in (extra or {}).items():
                entry = tarfile.TarInfo(name); entry.size = len(payload); entry.mtime = int(time.time())
                archive.addfile(entry, io.BytesIO(payload))


def check_pins(probe: str) -> None:
    """Every weight pin is a SHA-256; a policy with listed files has one pin per listed .safetensors file."""
    spec = probes.PROBES[probe]
    pins = spec["weight_pins"]
    if not pins or any(len(p) != 64 or set(p) - HEX for p in pins):
        raise SystemExit(f"{probe}: a weight pin is missing or is not a SHA-256")
    listed = [f for f in spec["policy"]["files"] or [] if f.endswith(".safetensors")]
    if listed and len(listed) != len(pins):
        raise SystemExit(f"{probe}: {len(listed)} listed .safetensors files but {len(pins)} pins")


def probe_record(probe: str) -> dict:
    return {"probe": probe, "plan": probes.download_plan(probe), "weight_pins": list(probes.PROBES[probe]["weight_pins"])}


def refuse_secrets(files: dict, payloads: dict, prepared_names) -> None:
    """Scan every packed file outside the prepared folders, and every generated payload; a hit refuses (names only)."""
    scanned = [f for name, f in files.items() if name.split("/")[0] not in prepared_names]
    hits = [(name, pattern) for name, pattern in secret_scan.scan_paths(scanned)]
    hits += [(name, pattern) for name, payload in payloads.items()
             for pattern in secret_scan.scan_text(payload.decode("utf-8", "ignore"))]
    if hits:
        raise SystemExit(f"a secret pattern is in a packed file: {[(pathlib.Path(n).name, p) for n, p in hits][:10]}")


def main() -> None:
    probe = pc.probe()
    EXPECTED = pc.prepared()
    check_pins(probe)
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "experiments", *[f"scripts/{name}" for name in pc.SCRIPTS]],
                            capture_output=True, text=True, check=True).stdout
    assert not status.strip(), f"engine files are not committed:\n{status}"
    commit = subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True, check=True).stdout.strip()
    files = {}
    for component in ("minimal_safety", "safety_selection"):
        for f in (ROOT / "experiments" / component).rglob("*"):
            if f.is_file() and not f.is_symlink() and "__pycache__" not in f.parts and f.suffix in {".py", ".json", ".md", ".lock"}:
                files[str(f.relative_to(ROOT))] = f
    for name in pc.SCRIPTS:
        files[f"scripts/{name}"] = ROOT / "scripts" / name
    files["bootstrap_hr.sh"] = SETUP / "bootstrap_hr.sh"
    files["requirements.lock"] = ROOT / "experiments/minimal_safety/requirements.lock"
    for name, digest in EXPECTED.items():
        folder = PREP / name
        assert (folder / "manifest.sha256").read_text().strip() == digest, f"{name}: unexpected manifest"
        for f in folder.rglob("*"):
            if f.is_file():
                files[f"{name}/{f.relative_to(folder)}"] = f
    manifest = {"kind": f"explicit code and data export for family probe {probe}; no credentials", "git_commit": commit,
                "probe": probe, "prepared_manifests": EXPECTED, "files": {n: sha(f) for n, f in sorted(files.items())}}
    payload = {"bundle-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode()}
    probe_json = (json.dumps(probe_record(probe), indent=1) + "\n").encode()
    refuse_secrets(files, {**payload, "probe.json": probe_json}, set(EXPECTED))
    with (SETUP / "probe.json").open("xb") as handle:
        handle.write(probe_json)
    bundle = SETUP / pc.BUNDLE
    tar(bundle, files, payload)
    code = subprocess.run([str(PY), "-c", "from experiments.safety_selection.common import code_identity;print(code_identity()['sha256'])"],
                          cwd=ROOT, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()
    bundle_sha = sha(bundle)
    checks = ",".join(f"('{n}','{d}')" for n, d in EXPECTED.items())
    bootstrap = f"""#!/bin/bash
# Generated by pack_setup.py (family probe {probe}): environment and open models, bundle and data checks, GPU check.
# No token here: the gated download (host.py gated-download) and the preflight are later steps.
set -euo pipefail
cd /workspace/attribution-headroom
export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONPATH=/workspace/attribution-headroom
python3 process_receipt.py --out setup-001 -- bash setup_and_fetch_probe.sh "$@"
venv/bin/python - <<'PY'
import datetime,hashlib,json,pathlib,tarfile
p=pathlib.Path('{pc.BUNDLE}');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{bundle_sha}','bundle'
with tarfile.open(p) as t:t.extractall('.',filter='data')
import importlib; importlib.invalidate_caches()
m=json.loads(pathlib.Path('bundle-manifest.json').read_text())
for f,h in m['files'].items():assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==h,f
for name,digest in [{checks}]:assert pathlib.Path(name,'manifest.sha256').read_text().strip()==digest,name
from experiments.safety_selection.common import code_identity
assert code_identity()['sha256']=='{code}','engine code identity differs from the packed code'
import torch
assert torch.cuda.get_device_name(0)=='NVIDIA A100-SXM4-80GB'
pathlib.Path('BOOTSTRAP-READY.json').write_text(json.dumps({{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ok':True,'engine_sha256':'{code}'}})+'\\n')
print('bootstrap ready',flush=True)
PY
"""
    if secret_scan.scan_text(bootstrap):
        raise SystemExit("a secret pattern is in the generated bootstrap")
    with (SETUP / pc.WORKER_BOOTSTRAP).open("x") as handle:
        handle.write(bootstrap)
    setup_files = {name: SETUP / name for name in ("bootstrap_hr.sh", "setup_and_fetch_probe.sh", "download_models_probe.py",
                                                  pc.WORKER_BOOTSTRAP, "preflight_probe.py", "job_runner_probe.py",
                                                  "extend_cap.py", "probe.json", pc.BUNDLE)}
    setup_files["process_receipt.py"] = ROOT / "tmp/study-v2-20261002/process_receipt.py"
    setup_files["requirements.lock"] = ROOT / "experiments/minimal_safety/requirements.lock"
    refuse_secrets({n: f for n, f in setup_files.items() if n != pc.BUNDLE}, {}, set())
    setup = SETUP / pc.WORKER_SETUP
    tar(setup, setup_files)
    receipt = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "probe": probe, "git_commit": commit, "engine_sha256": code,
               "bundle": {"path": str(bundle), "sha256": bundle_sha, "files": len(files)},
               "setup": {"path": str(setup), "sha256": sha(setup), "bytes": setup.stat().st_size},
               "members": {name: sha(f) for name, f in sorted(setup_files.items())}}
    with (SETUP / "setup-receipt.json").open("x") as handle:
        handle.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("probe", "git_commit", "engine_sha256", "bundle", "setup")}, indent=2))


if __name__ == "__main__":
    main()
