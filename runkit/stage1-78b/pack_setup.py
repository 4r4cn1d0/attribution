"""Pack engine X's setup for the 7-8B kit's working copy (K1 of T4; ruling 11 KD10; administrative; never includes
credentials; text inputs only as data, scanned by name only). A copy of the stage-1 kit's pack_setup.py reduced to
what block 0 (N) needs; the 1B-only parts (the W1 scripts and settings, the D-2 package, the S1 package, MAN1, W1-18's
units, the named inputs, the base model's pins) are not here and come back kind by kind with the scorer kinds.

    python3.11 pack_setup.py X [--family F] [--inputs FILE --inputs-sha256 H] [--dry-run]

The working copy names the family (KD7: tmp/family-probe-s78-<family>-<block>/; stage1_rules.FAMILY). --family, when
given, must be that family; an --inputs record ("stage1-78b pack inputs", {kind, engine, family, inputs: []}) must
name it too: a wrong family refuses before anything is read. --dry-run prints engine X's identity (the engine's own
code_identity over this checkout, which must be rules_78b.ENGINE_X 472fc7f6...), the family's main config (path, the
file's SHA-256 at stage1_rules.RECIPE_PINS, its config_sha256 by the engine's own hash, which must be rules_78b's), the
family's prepared manifest (tmp/kt-prepared/NAME/manifest.sha256 at its pin), the family's sealed set (MANIFEST pin and
the R_d1-R_d3 edit files by SHA-256; a null pin refuses, addendum A13) and HEAD, and writes nothing.

The real pack writes, once, under setup/packed-stage1-X/ (refuses to overwrite): probe.json (the family's download plan,
no base model), sealed-files.json ({files: {bundle path: SHA-256}, inputs: {}}), the bundle (engine X's files from this
checkout: experiments/minimal_safety and safety_selection, the preflight scripts; refused while an engine or script
file is uncommitted, as the stage-1 kit; the edit files at edits/<SHA-256>.edit.json; the prepared set at
data/kt-prepared/NAME at its manifest pin), the generated worker bootstrap (no token), worker-setup-stage1.tar.gz (the
kit's setup/ scripts, stage1_rules.py, rules_78b.py and its basis, probe.json, kit-family.json for the pod) and
setup-receipt.json {engine, engine_sha256, family, git_commit, main_config, prepared_manifests, sealed_set,
sealed_files_sha256, ...}; plan_tool's release refuses a receipt whose engine identity is not the pin or whose family
is not the copy's. Every packed file outside the data folders is scanned for secrets by name only.
"""
from __future__ import annotations

import argparse
import hashlib
import io
import json
import pathlib
import re
import subprocess
import sys
import tarfile
import time

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import probes  # noqa: E402
import secret_scan  # noqa: E402
import stage1_rules as rules  # noqa: E402

r78 = rules.r78
ROOT = HERE.parents[1]
SETUP = HERE / "setup"
PY = ROOT / "tmp/minimal-experiment-20261002/venv/bin/python"
PREFLIGHT_SCRIPTS = ("cuda_preflight_family.py", "cuda_preflight_killtest.py", "cuda_preflight_headroom_v3.py",
                     "cuda_preflight_headroom.py")
SETUP_FILES = ("bootstrap_hr.sh", "constraints.txt", "setup_and_fetch_stage1.sh", "download_models_stage1.py",
               "preflight_stage1.py", "job_runner_stage1.py", "extend_cap.py")
PROCESS_RECEIPT = "tmp/study-v2-20261002/process_receipt.py"
WORKER_BOOTSTRAP = "worker_bootstrap_stage1.sh"
WORKER_SETUP = "worker-setup-stage1.tar.gz"
GPU = r78.GPU_NAME
HEX = set("0123456789abcdef")
DATA = "data"
INPUTS_KIND = "stage1-78b pack inputs"
DATA_PREFIXES = (f"{DATA}/", "inputs/", "edits/")
ENGINE_CODE = ("from experiments.safety_selection.common import code_identity;print(code_identity()['sha256'])")
CONFIG_CODE = ("from experiments.safety_selection.config import load_recipe,config_sha256;"
               "print(config_sha256(load_recipe({path!r})))")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def pinned(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and not set(value) - HEX


def plain_path(rel) -> bool:
    """A relative path in normal form: not empty, no leading '/', no backslash, no empty, '.' or '..' part."""
    return isinstance(rel, str) and bool(rel) and "\\" not in rel and \
        all(part not in ("", ".", "..") for part in rel.split("/"))


def tar(dest: pathlib.Path, files: dict, extra: dict | None = None) -> None:
    with dest.open("xb") as handle:
        with tarfile.open(fileobj=handle, mode="w:gz") as archive:
            for name, f in sorted(files.items()):
                digest = sha(f); archive.add(f, arcname=name, recursive=False); assert sha(f) == digest, f"{f} changed"
            for name, payload in sorted((extra or {}).items()):
                entry = tarfile.TarInfo(name); entry.size = len(payload); entry.mtime = int(time.time())
                archive.addfile(entry, io.BytesIO(payload))


class Packing:
    """The files and pins of one pack; ``add`` refuses (names only) a file that is missing or differs from its pin."""

    def __init__(self):
        self.files, self.pins, self.bad, self.inputs = {}, {}, [], {}
        self.engine = "X"

    def add(self, name: str, src: pathlib.Path, pin: str | None) -> None:
        if not pinned(pin):
            self.bad.append(f"{name} (not pinned)")
        elif not src.is_file() or src.is_symlink() or sha(src) != pin:
            self.bad.append(name)
        elif name in self.pins and self.pins[name] != pin:
            self.bad.append(f"{name} (two pins)")
        else:
            self.files[name], self.pins[name] = src, pin

    def refuse(self) -> None:
        if self.bad:
            raise SystemExit(f"{len(self.bad)} sealed or pinned file(s) missing or differ from their pins: {self.bad[:10]}")


def engine_run(code: str, tree: pathlib.Path) -> str:
    """The engine's own code in the tree (cwd = tree, so ``experiments`` imports from it; no -I, which would hide the
    tree; the environment holds no token and no PYTHONPATH)."""
    return subprocess.run([str(PY), "-B", "-c", code], cwd=tree, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


def engine_code(tree: pathlib.Path) -> str:
    return engine_run(ENGINE_CODE, tree)


def config_sha256(tree: pathlib.Path, rel: str) -> str:
    return engine_run(CONFIG_CODE.format(path=str(tree / rel)), tree)


def git_state() -> str:
    status = subprocess.run(["git", "-C", str(ROOT), "status", "--porcelain", "--", "experiments", "scripts"],
                            capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise SystemExit(f"engine or script files are not committed:\n{status}")
    return subprocess.run(["git", "-C", str(ROOT), "rev-parse", "HEAD"], capture_output=True, text=True,
                          check=True).stdout.strip()


def check_constraints() -> None:
    text = (SETUP / "constraints.txt").read_text()
    if text != f"setuptools=={rules.SETUPTOOLS_PIN}\n":
        raise SystemExit("setup/constraints.txt must hold exactly the line setuptools==" + rules.SETUPTOOLS_PIN)


def engine_files(tree: pathlib.Path) -> dict:
    files = {}
    for component in ("minimal_safety", "safety_selection"):
        for f in (tree / "experiments" / component).rglob("*"):
            if f.is_file() and not f.is_symlink() and "__pycache__" not in f.parts and \
                    f.suffix in {".py", ".json", ".md", ".lock"}:
                files[str(f.relative_to(tree))] = f
    for name in PREFLIGHT_SCRIPTS:
        if not (tree / "scripts" / name).is_file():
            raise SystemExit(f"scripts/{name} is missing from the engine tree")
        files[f"scripts/{name}"] = tree / "scripts" / name
    return files


def family_of_run(given: str | None) -> str:
    """The working copy's family; --family must be it (a wrong one refuses before anything is read)."""
    try:
        return rules.family_or_refuse(given)
    except ValueError as exc:
        raise SystemExit(str(exc))


def inputs_record(path: str, digest: str, engine: str, family: str) -> dict:
    p = pathlib.Path(path)
    if not pinned(digest) or not p.is_file() or sha(p) != digest:
        raise SystemExit("--inputs FILE: missing or its SHA-256 differs from the one given")
    doc = json.loads(p.read_text())
    if not isinstance(doc, dict) or doc.get("kind") != INPUTS_KIND or doc.get("engine") != engine:
        raise SystemExit(f"--inputs FILE is not a {INPUTS_KIND!r} record for engine {engine}")
    if doc.get("family") != family:
        raise SystemExit(f"--inputs FILE is for family {doc.get('family')!r}; this working copy is {family}'s (one family "
                         "per copy, KD7): refused")
    if doc.get("inputs"):
        raise SystemExit("block 0 packs no named input (the scorer kinds' inputs come with their round); give inputs: []")
    return doc


def sealed_set(family: str) -> dict:
    """The family's sealed set (rules_78b.SEALED_SETS, by pin): its folder and the R_d1-R_d3 edit entries, read from
    the MANIFEST in either committed form (D1: Gate B's and the Llama set's; rules_78b.block0_r_edits, by family "R"
    AND draw). A null pin refuses (addendum A13's pattern)."""
    try:
        pin = r78.sealed_set_or_refuse(family)
    except r78.Refused as exc:
        raise SystemExit(str(exc))
    path = ROOT / pin["path"]
    if not path.is_file() or sha(path) != pin["sha256"]:
        raise SystemExit(f"the {family} sealed set's MANIFEST.json ({pin['path']}) is missing or differs from its pin")
    man = json.loads(path.read_text())
    try:
        r_edits = r78.block0_r_edits(man, r78.BLOCK0_R_DRAWS)
    except r78.Refused as exc:
        raise SystemExit(f"the {family} sealed set: {exc}")
    edits = {d: {"path": str(pathlib.Path(pin["path"]).parent / e["path"]), "sha256": e["sha256"], "arm": e["arm"],
                 "seed": e["seed"]} for d, e in r_edits.items()}
    for d, e in edits.items():
        f = ROOT / e["path"]
        if not f.is_file() or sha(f) != e["sha256"]:
            raise SystemExit(f"R_d{d}: its edit file is missing or differs from the sealed set's SHA-256")
        doc = json.loads(f.read_text())
        if not isinstance(doc, dict) or doc.get("manifest_sha256") != rules.PREPARED_MANIFESTS[rules.PREPARED_NAME]:
            raise SystemExit(f"R_d{d}: the edit file is not on {family}'s prepared set ({rules.PREPARED_NAME}); refused")
    return {"manifest": pin, "edits": edits}


def prepared_set(family: str) -> tuple[pathlib.Path, str]:
    name, digest = rules.PREPARED_NAME, rules.PREPARED_MANIFESTS[rules.PREPARED_NAME]
    folder = ROOT / rules.PREPARED_LOCAL / name
    if not (folder / "manifest.sha256").is_file() or (folder / "manifest.sha256").read_text().strip() != digest:
        raise SystemExit(f"{name}: tmp/kt-prepared/{name}/manifest.sha256 is missing or is not the family's pin "
                         f"{digest[:12]}... (the prepared set of {family})")
    return folder, digest


def main_config(tree: pathlib.Path) -> dict:
    """The family's main config: its bytes at stage1_rules.RECIPE_PINS and its config_sha256 (the engine's own hash) at
    rules_78b's pin; every arm runs under it (P78:99)."""
    rel = rules.REC
    f = tree / rel
    if not f.is_file() or sha(f) != rules.RECIPE_PINS[rel]:
        raise SystemExit(f"{rel} is missing from the engine tree or differs from its pin (the file's bytes)")
    config = config_sha256(tree, rel)
    if config != rules.REC_CONFIG_SHA256:
        raise SystemExit(f"{rel}: its config_sha256 {config[:12]}... is not the family's pin {rules.REC_CONFIG_SHA256[:12]}...")
    return {"path": rel, "sha256": rules.RECIPE_PINS[rel], "config_sha256": config}


def probe_record(family: str) -> dict:
    return {"probe": rules.PROBE_KEY, "family": family,
            "plan": probes.stage1_download_plan(rules.PROBE_KEY, with_base=False),
            "weight_pins": list(probes.PROBES[rules.PROBE_KEY]["weight_pins"])}


def kit_family_doc(family: str) -> bytes:
    return (json.dumps({"kind": rules.KIT_FAMILY_KIND, "family": family, "block": rules.KIT_BLOCK}) + "\n").encode()


def refuse_secrets(files: dict, payloads: dict, data_prefixes: tuple) -> None:
    """Scan every packed file outside the data folders, and every generated payload; a hit refuses (names only)."""
    scanned = [f for name, f in files.items() if not name.startswith(data_prefixes)]
    hits = [(name, pattern) for name, pattern in secret_scan.scan_paths(scanned)]
    hits += [(name, pattern) for name, payload in payloads.items()
             for pattern in secret_scan.scan_text(payload.decode("utf-8", "ignore"))]
    if hits:
        raise SystemExit(f"a secret pattern is in a packed file: {[(pathlib.Path(n).name, p) for n, p in hits][:10]}")


def worker_bootstrap(engine: str, bundle: str, bundle_sha: str, code: str, prepared: dict, pip_pin: str | None) -> str:
    """The generated worker bootstrap (the stage-1 kit's, unchanged in form): no token; two Python processes."""
    checks = ",".join(f"('{n}','{d}')" for n, d in sorted(prepared.items()))
    pin = f"export GATEB_PIP_PIN={pip_pin}\n" if pip_pin else ""
    return f"""#!/bin/bash
# Generated by pack_setup.py (stage1-78b, engine {engine}): environment and open models, then two processes. Process 1
# checks the bundle hash, extracts it and checks every file hash, the prepared manifests and sealed-files.json.
# Process 2, a fresh interpreter started after the extraction, calls importlib.invalidate_caches() first, then runs the
# identity, GPU and lock checks and writes BOOTSTRAP-READY.json. No token here. Arguments go to the downloads.
set -euo pipefail
cd /workspace/attribution-headroom
export CUBLAS_WORKSPACE_CONFIG=:4096:8 CUDA_VISIBLE_DEVICES=0 TOKENIZERS_PARALLELISM=false OMP_NUM_THREADS=4 MKL_NUM_THREADS=4 PYTHONPATH=/workspace/attribution-headroom
{pin}python3 process_receipt.py --out setup-001 -- bash setup_and_fetch_stage1.sh "$@"
venv/bin/python - <<'PY1'
import datetime,hashlib,json,pathlib,tarfile
p=pathlib.Path('{bundle}');assert hashlib.sha256(p.read_bytes()).hexdigest()=='{bundle_sha}','bundle'
with tarfile.open(p) as t:t.extractall('.',filter='data')
m=json.loads(pathlib.Path('bundle-manifest.json').read_text())
for f,h in m['files'].items():assert hashlib.sha256(pathlib.Path(f).read_bytes()).hexdigest()==h,f
for name,digest in [{checks}]:assert pathlib.Path('{DATA}/kt-prepared',name,'manifest.sha256').read_text().strip()==digest,name
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
ready={{'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'ok':True,'engine':'{engine}','engine_sha256':'{code}','lock_sha256':hashlib.sha256(lock).hexdigest(),'pip_version':pip,'gpu':gpu,'cuda_runtime':torch.version.cuda}}
pathlib.Path('BOOTSTRAP-READY.json').write_text(json.dumps(ready)+'\\n')
print('bootstrap ready',flush=True)
PY2
"""


def parse(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="pack_setup.py")
    ap.add_argument("engine", choices=["X"], help="engine X (engine Y's pack comes with KD9's re-measure)")
    ap.add_argument("--family", help="the working copy's family (refused when it is the other family)")
    ap.add_argument("--inputs", help="a 'stage1-78b pack inputs' record (block 0: inputs: [])")
    ap.add_argument("--inputs-sha256")
    ap.add_argument("--dry-run", action="store_true", help="print the identities and pins; write nothing")
    a = ap.parse_args(argv)
    if (a.inputs is None) != (a.inputs_sha256 is None):
        ap.error("--inputs and --inputs-sha256 go together")
    return a


def dry_run_report(family: str, tree: pathlib.Path) -> dict:
    code = engine_code(tree)
    if code != r78.ENGINE_X:
        raise SystemExit(f"this checkout's engine identity {code[:12]}... is not engine X's pin {r78.ENGINE_X[:12]}... (KD8)")
    folder, digest = prepared_set(family)
    sealed = sealed_set(family)
    return {"dry_run": True, "engine": "X", "engine_sha256": code, "family": family, "kit_block": rules.KIT_BLOCK,
            "main_config": main_config(tree), "prepared_manifests": {rules.PREPARED_NAME: digest},
            "prepared_folder": str(folder.relative_to(ROOT)), "sealed_set": sealed, "git_commit": git_state(),
            "probe": rules.PROBE_KEY, "pod": dict(rules.POD_SIZES)}


def main(argv: list[str] | None = None) -> None:
    a = parse(sys.argv[1:] if argv is None else argv)
    engine = a.engine
    family = family_of_run(a.family)
    if a.inputs:
        inputs_record(a.inputs, a.inputs_sha256, engine, family)
    if a.dry_run:
        print(json.dumps(dry_run_report(family, ROOT), indent=2))
        return
    out = SETUP / f"packed-stage1-{engine}"
    if out.exists():
        raise SystemExit(f"{out.name} exists: a packed stage is never overwritten")
    check_constraints()
    tree, commit = ROOT, git_state()
    config = main_config(tree)
    process_receipt = ROOT / PROCESS_RECEIPT
    if not process_receipt.is_file():
        raise SystemExit(f"{PROCESS_RECEIPT} is missing: copy it in before packing")
    pack = Packing()
    sealed = sealed_set(family)
    for d, e in sorted(sealed["edits"].items()):
        pack.add(f"edits/{e['sha256']}.edit.json", ROOT / e["path"], e["sha256"])
    folder, digest = prepared_set(family)
    for f in sorted(folder.rglob("*")):
        if f.is_file() and not f.is_symlink():
            pack.add(f"{DATA}/kt-prepared/{rules.PREPARED_NAME}/{f.relative_to(folder)}", f, sha(f))
    pack.add(config["path"], tree / config["path"], config["sha256"])
    pack.refuse()
    files = engine_files(tree)
    overlap = sorted(set(files) & set(pack.files) - {config["path"]})
    if overlap:
        raise SystemExit(f"a kit file would replace an engine file: {overlap[:3]}")
    files.update(pack.files)
    files["bootstrap_hr.sh"] = SETUP / "bootstrap_hr.sh"
    files["constraints.txt"] = SETUP / "constraints.txt"
    files["requirements.lock"] = tree / "experiments/minimal_safety/requirements.lock"
    code = engine_code(tree)
    if code != rules.ENGINES[engine] or code != r78.ENGINE_X:
        raise SystemExit(f"the packed engine {engine}'s code identity is not its pin (KD8)")
    sealed_json = (json.dumps({"kind": "stage1-78b sealed files", "version": 1, "engine": engine, "family": family,
                               "files": dict(sorted(pack.pins.items())), "inputs": dict(sorted(pack.inputs.items()))},
                              indent=1) + "\n").encode()
    manifest = {"kind": f"explicit code and data export for the 7-8B kit, engine {engine}, family {family}; no credentials",
                "git_commit": commit, "engine": engine, "engine_sha256": code, "family": family, "kit_block": rules.KIT_BLOCK,
                "main_config": config, "prepared_manifests": dict(rules.PREPARED_MANIFESTS), "sealed_set": sealed["manifest"],
                "files": {n: sha(f) for n, f in sorted(files.items())}}
    payload = {"bundle-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(), "sealed-files.json": sealed_json}
    probe_json = (json.dumps(probe_record(family), indent=1) + "\n").encode()
    family_json = kit_family_doc(family)
    refuse_secrets(files, {**payload, "probe.json": probe_json, rules.KIT_FAMILY_FILE: family_json}, DATA_PREFIXES)
    out.mkdir(parents=True, exist_ok=False)
    (out / "probe.json").write_bytes(probe_json)
    (out / "sealed-files.json").write_bytes(sealed_json)
    (out / rules.KIT_FAMILY_FILE).write_bytes(family_json)
    bundle = out / f"bundle-stage1-{engine}.tar.gz"
    tar(bundle, files, payload)
    bundle_sha = sha(bundle)
    bootstrap = worker_bootstrap(engine, bundle.name, bundle_sha, code, rules.PREPARED_MANIFESTS, rules.PIP_PIN)
    if secret_scan.scan_text(bootstrap):
        raise SystemExit("a secret pattern is in the generated bootstrap")
    (out / WORKER_BOOTSTRAP).write_text(bootstrap)
    setup_files = {name: SETUP / name for name in SETUP_FILES}
    setup_files.update({"stage1_rules.py": HERE / "stage1_rules.py", "rules_78b.py": HERE / "rules_78b.py",
                        r78.BASIS_FILE: HERE / r78.BASIS_FILE, rules.KIT_FAMILY_FILE: out / rules.KIT_FAMILY_FILE,
                        WORKER_BOOTSTRAP: out / WORKER_BOOTSTRAP, "probe.json": out / "probe.json", bundle.name: bundle,
                        "process_receipt.py": process_receipt,
                        "requirements.lock": tree / "experiments/minimal_safety/requirements.lock"})
    refuse_secrets({n: f for n, f in setup_files.items() if n != bundle.name}, {}, ())
    setup = out / WORKER_SETUP
    tar(setup, setup_files)
    receipt = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stage": f"stage1-{engine}",
               "engine": engine, "family": family, "kit_block": rules.KIT_BLOCK, "git_commit": commit,
               "engine_sha256": code, "main_config": config, "prepared_manifests": dict(rules.PREPARED_MANIFESTS),
               "sealed_set": sealed["manifest"], "edits": {f"R_d{d}": e for d, e in sorted(sealed["edits"].items())},
               "inputs_record_sha256": a.inputs_sha256, "sealed_files_sha256": hashlib.sha256(sealed_json).hexdigest(),
               "inputs": dict(sorted(pack.inputs.items())),
               "bundle": {"path": str(bundle), "sha256": bundle_sha, "files": len(files)},
               "setup": {"path": str(setup), "sha256": sha(setup), "bytes": setup.stat().st_size},
               "pip_pin": rules.PIP_PIN, "members": {name: sha(f) for name, f in sorted(setup_files.items())}}
    with (out / "setup-receipt.json").open("x") as handle:
        handle.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("stage", "engine", "family", "git_commit", "engine_sha256", "main_config",
                                              "prepared_manifests", "sealed_set", "sealed_files_sha256", "bundle",
                                              "setup")}, indent=2))


if __name__ == "__main__":
    main()
