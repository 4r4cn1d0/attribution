"""Pack one engine's stage-1 setup (administrative; B15, brief §6; copied from runkit/gate-b-olmo/pack_setup.py; never
includes credentials, and text inputs only as data, scanned by name only).

    python3.11 pack_setup.py X --inputs FILE --inputs-sha256 H                 engine X from the committed tree
    python3.11 pack_setup.py Y [--y-tree DIR] --inputs FILE --inputs-sha256 H  engine Y from its frozen tree
                                                   (default DIR: <repo>/tmp/engine-y-34bfd288, rules.Y_TREE_DEFAULT)

One packed stage per engine (G4: one engine per pod): setup/packed-stage1-X/ or setup/packed-stage1-Y/. The engine's
files come from its tree: X from this checkout (refused while an engine or script file is uncommitted, as Gate B), Y
from DIR, checked against YHASH (stage1_rules.YHASH_PIN: the frozen file list's own SHA-256, then every listed file in
DIR by its SHA-256; YB P-4: never from the working branch). Either way the packed tree's code identity must equal
stage1_rules.ENGINES[engine] (a different identity refuses); engine Y is pinned at 34bfd288 (addendum §23), checked
right after YHASH.

Round 2 (addendum §19 point 3, §21, §22 point 2): the X pack carries the D-2 package (stage1_rules.D2_CODE) and the
W1 manifest (MAN1) itself, which D-2 reads at its checkout path; the named inputs d2_pool_pins and req8_record must be
stage1_rules.D2_POOL_PINS and D2_REQ8_RECORD by SHA-256, pool:plant and pool:decoy D2_POOLS, and pool:s3_safe the
S-pool record's s3_pool.sha256 (the record pinned by S_POOL_RECORD); c3_subsample and c3_record are J14's.

The stage-1 code and inputs, each by SHA-256 (a missing file or a byte that differs refuses, names only):
  - stage1_rules.STAGE1_PINS (the W1 scripts and settings), MAN1's code, settings and pinned-input entries under
    scripts/stage1/ (MAN1 itself checked against stage1_rules.MAN1_SHA256), W1-18's frozen readers (its settings'
    frozen_reader pins), and the lead's ``code`` entries (scripts/ files);
  - round 3b (item 1; VR2-5): on engine X every S1 package file the kit runs or packs, stage1_rules.S1_CODE (the
    package's __init__.py, B10's eval_adapter.py, B11's safe_lora.py, B17's lean_eval_job.py, oext_eval.py and their
    settings; round 3c: the O-ext unit runner oext_unit.py and its settings), by its SHA-256 from this checkout (no
    other tree is read); a lead's code entry under scripts/stage1_s1/ must be one of S1_CODE's or D2_CODE's pins
    (another SHA-256 or another file refuses; round 3c: no exception is left);
  - the edit files: Gate B's sealed MANIFEST (R_1-R_5), MAN1's A1 edit and every sealed edit record plan.json lists
    (re-hashed), each at edits/<SHA-256>.edit.json;
  - W1-18's data: the 11 unit folders its pinned settings list, under data/ at their checkout tmp/ paths (each unit's
    COMPLETE.json and job.json by the settings' pins), and the prepared set at data/kt-prepared/NAME (its manifest pin);
  - the lead's named inputs (--inputs, a "stage1 pack inputs" record whose SHA-256 is given): {name, path, sha256}
    for a file, {name, path, files: [{path, sha256}]} for a folder; names among INPUT_NAMES. A file or folder listed by
    MAN1 must carry MAN1's SHA-256 too. Every code and input path is in normal form (plain_path; round 3b fix, F1).
Every packed S1 settings file (scripts/stage1_s1/settings/*.json) must pin this pack's engine in a top-level engine
key (addendum §11 point 7, the re-pin before any run; a settings file that pins another engine refuses).
Text inputs (anchors, the O-ext bank, the lists, the pools, unit folders) are data: they are not scanned as code, and
the secret scan of the kit files and generated payloads reports a hit by name only, as Gate B does.

Writes, once, under setup/packed-stage1-ENGINE/ (refuses to overwrite): probe.json (stage1_download_plan with the base
model row), sealed-files.json ({files: {bundle path: SHA-256}, inputs: {name: bundle path}}), the bundle, the generated
worker bootstrap, worker-setup-stage1.tar.gz and setup-receipt.json {engine, engine_sha256, sealed_files_sha256, ...}
(plan_tool's release refuses a receipt whose engine identity is not the pin).
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
GPU = "NVIDIA A100-SXM4-80GB"
HEX = set("0123456789abcdef")
DATA = "data"
PREPARED_BUNDLE = f"{DATA}/kt-prepared/{rules.PREPARED_NAME}"
W1_18_SETTINGS = "scripts/stage1/settings/limits_overrefusal_checks.json"
INPUTS_KIND = "stage1 pack inputs"
INPUT_NAMES = re.compile(r"^(reuse_spec|oext_bank|oext_record|w1_18_record|anchor_bank|certification_report|"
                         r"d2_pool_pins|req8_record|c3_record|"
                         r"prefix_file|cert_spec|c3_subsample|source_complete:R:1101|source_unit:(a0|R):110[1-3]|"
                         r"pool:(plant|decoy|s3_safe)|list:(s3|s4|sd600)|loss:(s1|s3_safe)|"
                         r"gate_a_complete:11(0[1-9]|10)|gate_a_eval:11(0[1-9]|10))$")
MAN1_CODE_ROLES = ("code", "settings", "pinned input")
S1_PACKAGE = "scripts/stage1_s1/"
DATA_PREFIXES = (f"{DATA}/", "inputs/", "edits/")


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def pinned(value) -> bool:
    return isinstance(value, str) and len(value) == 64 and not set(value) - HEX


def plain_path(rel) -> bool:
    """A relative path in normal form: not empty, no leading '/', no backslash, no empty, '.' or '..' part (round 3b
    fix, F1: 'scripts/./stage1_s1/x.py' or 'scripts//stage1_s1/x.py' names the same file but would pass by the
    S1-package and S1-settings prefix checks, and the MAN1 comparison of a named input)."""
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
        self.engine = "X"                                # main sets the engine being packed

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


def read_pinned_json(path: pathlib.Path, pin: str, what: str) -> dict:
    if not path.is_file() or sha(path) != pin:
        raise SystemExit(f"{what} is missing or differs from its pin")
    return json.loads(path.read_text())


def y_tree_check(tree: pathlib.Path) -> list[str]:
    """YHASH (YB P-4): the frozen file list must hash to its pin, and every file it lists must be in DIR with its
    SHA-256; returns the listed paths."""
    yhash = ROOT / rules.YHASH_PIN["path"]
    if not yhash.is_file() or sha(yhash) != rules.YHASH_PIN["sha256"]:
        raise SystemExit("YHASH (Y's frozen file list) is missing or differs from its pin")
    listed, bad = [], []
    for line in yhash.read_text().splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.strip().partition("  ")
        listed.append(rel)
        f = tree / rel
        if not pinned(digest) or not f.is_file() or sha(f) != digest:
            bad.append(rel)
    if bad or not listed:
        raise SystemExit(f"the Y tree fails YHASH: {len(bad)} file(s) missing or changed: {bad[:5]}")
    return listed


def engine_code(tree: pathlib.Path) -> str:
    return subprocess.run([str(PY), "-c", "from experiments.safety_selection.common import code_identity;"
                           "print(code_identity()['sha256'])"], cwd=tree, capture_output=True, text=True, check=True,
                          env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}).stdout.strip()


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


def man1_entries() -> list[dict]:
    return read_pinned_json(ROOT / rules.MAN1_PATH, rules.MAN1_SHA256, "MAN1 (the REQ-20 manifest)")["entries"]


def stage1_code(pack: Packing, record: dict, man1: list[dict]) -> None:
    for rel, pin in sorted(rules.STAGE1_PINS.items()):
        pack.add(rel, ROOT / rel, pin)
    for e in man1:
        if e.get("role") in MAN1_CODE_ROLES and str(e.get("path", "")).startswith("scripts/stage1/") and \
                e.get("conditional") is not True:
            pack.add(e["path"], ROOT / e["path"], e.get("sha256"))
    w1 = read_pinned_json(ROOT / W1_18_SETTINGS, rules.STAGE1_PINS[W1_18_SETTINGS], "W1-18's settings")
    for reader in (w1.get("frozen_reader") or {}).values():
        pack.add(reader["path"], ROOT / reader["path"], reader["sha256"])
    if pack.engine == "X":                               # D-2 (J5, J8) and the S1 package run on engine X only
        for rel, pin in sorted(rules.D2_CODE.items()):
            pack.add(rel, ROOT / rel, pin)
        for rel, pin in sorted(rules.S1_CODE.items()):     # round 3b: the S1 package by its 3eaf968 pins
            pack.add(rel, ROOT / rel, pin)
        pack.add(rules.MAN1_PATH, ROOT / rules.MAN1_PATH, rules.MAN1_SHA256)
    s1_pins = {**rules.D2_CODE, **rules.S1_CODE}
    for e in record.get("code") or []:
        if not str(e.get("path", "")).startswith("scripts/") or not plain_path(e["path"]):
            pack.bad.append(f"{e.get('path')} (code entries are scripts/ files, each path in normal form)")
            continue
        if e["path"].startswith(S1_PACKAGE) and \
                s1_pins.get(e["path"]) != e.get("sha256"):
            pack.bad.append(f"{e['path']} (an S1 package file must be its stage1_rules pin at main {rules.S1_COMMIT})")
            continue
        pack.add(e["path"], ROOT / e["path"], e.get("sha256"))


def w1_18_data(pack: Packing) -> None:
    """W1-18's 11 units at data/<their tmp/ path> (every regular file), each unit's COMPLETE.json and job.json by the
    settings' pins; the prepared set at data/kt-prepared/NAME by its manifest pin."""
    w1 = json.loads((ROOT / W1_18_SETTINGS).read_text())
    for name, unit in sorted(w1["units"].items()):
        folder = ROOT / "tmp" / unit["path"]
        for fname, pin in (("COMPLETE.json", unit["complete_sha256"]), ("job.json", unit["job_sha256"])):
            if not (folder / fname).is_file() or sha(folder / fname) != pin:
                pack.bad.append(f"W1-18 unit {name}: {fname}")
        for f in sorted(folder.rglob("*")) if folder.is_dir() else []:
            if f.is_file() and not f.is_symlink():
                pack.add(f"{DATA}/{unit['path']}/{f.relative_to(folder)}", f, sha(f))
    pack.inputs["w1_18_data"] = DATA
    for name, digest in rules.PREPARED_MANIFESTS.items():
        folder = ROOT / rules.PREPARED_LOCAL / name
        if not (folder / "manifest.sha256").is_file() or (folder / "manifest.sha256").read_text().strip() != digest:
            raise SystemExit(f"{name}: unexpected manifest")
        for f in sorted(folder.rglob("*")):
            if f.is_file() and not f.is_symlink():
                pack.add(f"{DATA}/kt-prepared/{name}/{f.relative_to(folder)}", f, sha(f))


def edit_files(pack: Packing, man1: list[dict]) -> None:
    man = read_pinned_json(ROOT / rules.MAN_PATH, rules.MAN_SHA256, "Gate B's sealed MANIFEST.json")
    seal_out = (ROOT / rules.MAN_PATH).parent
    for e in man["files"]:
        if e.get("role") == "edit":
            pack.add(f"edits/{e['sha256']}.edit.json", seal_out / e["path"], e["sha256"])
    m1 = {(e["path"], e["sha256"]) for e in man1 if e.get("role") == "sealed record"}
    for pin in rules.MAN1_EDIT_ARMS.values():
        if (pin["path"], pin["sha256"]) not in m1:
            pack.bad.append(f"{pin['path']} (not in MAN1)")
        pack.add(f"edits/{pin['sha256']}.edit.json", ROOT / pin["path"], pin["sha256"])
    plan = HERE / "plan.json"
    for rec in (json.loads(plan.read_text()).get("records") or {}).get("sealed") or [] if plan.is_file() else []:
        doc = read_pinned_json(pathlib.Path(rec["path"]), rec["sha256"], "a recorded sealed edit record")
        for e in doc["edits"]:
            pack.add(f"edits/{e['sha256']}.edit.json", ROOT / e["path"], e["sha256"])


def named_inputs(pack: Packing, record: dict, man1: list[dict]) -> None:
    by_path = {e["path"]: e.get("sha256") for e in man1}
    for e in record.get("inputs") or []:
        name, rel = e.get("name"), str(e.get("path", ""))
        if not (isinstance(name, str) and INPUT_NAMES.fullmatch(name)) or name in pack.inputs:
            pack.bad.append(f"input {name!r} (unknown or repeated name)")
            continue
        if not plain_path(rel):
            pack.bad.append(f"input {name} (path, in normal form)")
            continue
        safe = name.replace(":", "-")
        if "files" in e:                                   # a folder input: every file by its pin
            base = f"inputs/{safe}"
            for f in e["files"]:
                sub = str(f.get("path", ""))
                if not plain_path(sub):
                    pack.bad.append(f"input {name} (a file path, in normal form)")
                    continue
                if f"{rel}/{sub}" in by_path and by_path[f"{rel}/{sub}"] != f.get("sha256"):
                    pack.bad.append(f"input {name}: {sub} differs from MAN1")
                pack.add(f"{base}/{sub}", ROOT / rel / sub, f.get("sha256"))
            pack.inputs[name] = base
        else:
            if rel in by_path and by_path[rel] != e.get("sha256"):
                pack.bad.append(f"input {name} differs from MAN1")
            bundle = f"inputs/{safe}/{pathlib.PurePath(rel).name}"
            pack.add(bundle, ROOT / rel, e.get("sha256"))
            pack.inputs[name] = bundle


def input_pins(pack: Packing, record: dict) -> None:
    """D-2's inputs by their pins (addendum §19 point 3): the filled pins file, REQ-8's record, the plant and decoy
    pools (REQ-8's), and s3_safe as the S-pool record names it; any other SHA-256, or a folder, refuses."""
    pins = {"d2_pool_pins": rules.D2_POOL_PINS["sha256"], "req8_record": rules.D2_REQ8_RECORD["sha256"],
            **{f"pool:{n}": v for n, v in rules.D2_POOLS.items()}}
    for e in record.get("inputs") or []:
        name = e.get("name")
        if name == "pool:s3_safe":
            doc = read_pinned_json(ROOT / rules.S_POOL_RECORD["path"], rules.S_POOL_RECORD["sha256"], "the S-pool record")
            expected = (doc.get("s3_pool") or {}).get("sha256")
            if expected != (doc.get("full_files") or {}).get("s3_safe.pool.json"):
                expected = None
        elif name in pins:
            expected = pins[name]
        else:
            continue
        if "files" in e or not pinned(expected) or e.get("sha256") != expected:
            pack.bad.append(f"input {name} (not its D-2 pin)")


S1_SETTINGS = "scripts/stage1_s1/settings/"
ENGINE_PIN_KEY = re.compile(r"^engine(_[a-z0-9]+)?(_sha256)?$")


def s1_settings_engine(pack: Packing, engine: str) -> None:
    """G0, addendum §11 point 7 ("a B15 pre-launch check"): every packed S1 settings file (B10, B11, B17, O-ext) is
    re-pinned on the engine this stage runs: one of its top-level engine pins (engine, engine_x, engine_y, ...) must
    be stage1_rules.ENGINES[engine]; otherwise the pack refuses (names only)."""
    for name in sorted(pack.files):
        if not (name.startswith(S1_SETTINGS) and name.endswith(".json")):
            continue
        try:
            doc = json.loads(pack.files[name].read_text())
        except (OSError, ValueError):
            pack.bad.append(f"{name} (not JSON)")
            continue
        pins = [v for k, v in (doc.items() if isinstance(doc, dict) else ()) if ENGINE_PIN_KEY.fullmatch(k)]
        if rules.ENGINES[engine] not in pins:
            pack.bad.append(f"{name} (not re-pinned on engine {engine}; addendum §11 point 7)")


def inputs_record(path: str, digest: str, engine: str) -> dict:
    p = pathlib.Path(path)
    if not pinned(digest) or not p.is_file() or sha(p) != digest:
        raise SystemExit("--inputs FILE: missing or its SHA-256 differs from the one given")
    doc = json.loads(p.read_text())
    if not isinstance(doc, dict) or doc.get("kind") != INPUTS_KIND or doc.get("engine") != engine:
        raise SystemExit(f"--inputs FILE is not a {INPUTS_KIND!r} record for engine {engine}")
    return doc


def probe_record() -> dict:
    return {"probe": rules.PROBE_KEY, "plan": probes.stage1_download_plan(rules.PROBE_KEY, with_base=True),
            "weight_pins": list(probes.PROBES[rules.PROBE_KEY]["weight_pins"])}


def check_base_pins() -> None:
    """probes.BASE_FILES must equal the lead's pins record (tmp/gi-vi-stage1/olmo2-0425-1b-base-pins.json) exactly."""
    doc = read_pinned_json(ROOT / rules.BASE_PINS_RECORD["path"], rules.BASE_PINS_RECORD["sha256"],
                           "the base model's pins record")
    if doc.get("repo_id") != probes.BASE["repo_id"] or doc.get("revision") != probes.BASE["revision"] or \
            doc.get("files") != probes.BASE_FILES or probes.BASE["revision"] != rules.BASE_MODEL["revision"]:
        raise SystemExit("probes.py's base model row differs from the pins record")


def refuse_secrets(files: dict, payloads: dict, data_prefixes: tuple) -> None:
    """Scan every packed file outside the data folders, and every generated payload; a hit refuses (names only)."""
    scanned = [f for name, f in files.items() if not name.startswith(data_prefixes)]
    hits = [(name, pattern) for name, pattern in secret_scan.scan_paths(scanned)]
    hits += [(name, pattern) for name, payload in payloads.items()
             for pattern in secret_scan.scan_text(payload.decode("utf-8", "ignore"))]
    if hits:
        raise SystemExit(f"a secret pattern is in a packed file: {[(pathlib.Path(n).name, p) for n, p in hits][:10]}")


def worker_bootstrap(engine: str, bundle: str, bundle_sha: str, code: str, prepared: dict, pip_pin: str | None) -> str:
    """The generated worker bootstrap (Gate B's, with the stage-1 names): no token; two Python processes."""
    checks = ",".join(f"('{n}','{d}')" for n, d in sorted(prepared.items()))
    pin = f"export GATEB_PIP_PIN={pip_pin}\n" if pip_pin else ""
    return f"""#!/bin/bash
# Generated by pack_setup.py (stage 1, engine {engine}): environment and open models, then two processes. Process 1
# checks the bundle hash, extracts it and checks every file hash, the prepared manifests and sealed-files.json.
# Process 2, a fresh interpreter started after the extraction, calls importlib.invalidate_caches() first, then runs the
# identity, GPU and lock checks and writes BOOTSTRAP-READY.json. No token here. Arguments go to the downloads
# (--with-base on a Safe LoRA host).
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
    ap.add_argument("engine", choices=sorted(rules.ENGINES))
    ap.add_argument("--inputs", required=True, help="the lead's 'stage1 pack inputs' record")
    ap.add_argument("--inputs-sha256", required=True)
    ap.add_argument("--y-tree", help="engine Y's frozen tree (Y only; default <repo>/" + rules.Y_TREE_DEFAULT + ")")
    a = ap.parse_args(argv)
    if a.engine == "X" and a.y_tree:
        ap.error("--y-tree goes with engine Y only")
    if a.engine == "Y" and not a.y_tree:
        a.y_tree = str(ROOT / rules.Y_TREE_DEFAULT)
    return a


def main(argv: list[str] | None = None) -> None:
    a = parse(sys.argv[1:] if argv is None else argv)
    engine = a.engine
    out = SETUP / f"packed-stage1-{engine}"
    if out.exists():
        raise SystemExit(f"{out.name} exists: a packed stage is never overwritten")
    check_constraints()
    check_base_pins()
    record = inputs_record(a.inputs, a.inputs_sha256, engine)
    if engine == "X":
        tree, commit = ROOT, git_state()
        yhash = None
    else:
        tree = pathlib.Path(a.y_tree).resolve()
        yhash = y_tree_check(tree)
        if engine_code(tree) != rules.ENGINES["Y"]:
            raise SystemExit("the Y tree's code identity is not engine Y's pin 34bfd288 (addendum §23): refused")
        commit = None
    for path in rules.RECIPE_NAMES.values():
        if engine == "X" and path == rules.RECIPE_BQI:
            continue                                     # B+Qi's recipe exists in Y's tree only (YB P-8)
        if not (tree / path).is_file() or sha(tree / path) != rules.RECIPE_PINS[path]:
            raise SystemExit(f"{path} is missing from the engine tree or differs from its pin")
    process_receipt = ROOT / PROCESS_RECEIPT
    if not process_receipt.is_file():
        raise SystemExit(f"{PROCESS_RECEIPT} is missing: copy it in before packing ([D9] B-6)")
    man1 = man1_entries()
    pack = Packing()
    pack.engine = engine
    stage1_code(pack, record, man1)
    w1_18_data(pack)
    edit_files(pack, man1)
    named_inputs(pack, record, man1)
    input_pins(pack, record)
    s1_settings_engine(pack, engine)
    pack.refuse()
    files = engine_files(tree)
    overlap = sorted(set(files) & set(pack.files))
    if overlap:
        raise SystemExit(f"a stage-1 file would replace an engine file: {overlap[:3]}")
    files.update(pack.files)
    files["bootstrap_hr.sh"] = SETUP / "bootstrap_hr.sh"
    files["constraints.txt"] = SETUP / "constraints.txt"
    files["requirements.lock"] = tree / "experiments/minimal_safety/requirements.lock"
    code = engine_code(tree)
    if code != rules.ENGINES[engine]:
        raise SystemExit(f"the packed engine {engine}'s code identity is not its pin (G4)")
    sealed_json = (json.dumps({"kind": "stage1 sealed files", "version": 1, "engine": engine,
                               "files": dict(sorted(pack.pins.items())), "inputs": dict(sorted(pack.inputs.items()))},
                              indent=1) + "\n").encode()
    manifest = {"kind": f"explicit code and data export for the stage-1 kit, engine {engine}; no credentials",
                "git_commit": commit, "engine": engine, "engine_sha256": code, "yhash": rules.YHASH_PIN if yhash else None,
                "prepared_manifests": rules.PREPARED_MANIFESTS,
                "files": {n: sha(f) for n, f in sorted(files.items())}}
    payload = {"bundle-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(), "sealed-files.json": sealed_json}
    probe_json = (json.dumps(probe_record(), indent=1) + "\n").encode()
    refuse_secrets(files, {**payload, "probe.json": probe_json}, DATA_PREFIXES)
    out.mkdir(parents=True, exist_ok=False)
    (out / "probe.json").write_bytes(probe_json)
    (out / "sealed-files.json").write_bytes(sealed_json)
    bundle = out / f"bundle-stage1-{engine}.tar.gz"
    tar(bundle, files, payload)
    bundle_sha = sha(bundle)
    bootstrap = worker_bootstrap(engine, bundle.name, bundle_sha, code, rules.PREPARED_MANIFESTS, rules.PIP_PIN)
    if secret_scan.scan_text(bootstrap):
        raise SystemExit("a secret pattern is in the generated bootstrap")
    (out / WORKER_BOOTSTRAP).write_text(bootstrap)
    setup_files = {name: SETUP / name for name in SETUP_FILES}
    setup_files.update({"stage1_rules.py": HERE / "stage1_rules.py", WORKER_BOOTSTRAP: out / WORKER_BOOTSTRAP,
                        "probe.json": out / "probe.json", bundle.name: bundle, "process_receipt.py": process_receipt,
                        "requirements.lock": tree / "experiments/minimal_safety/requirements.lock"})
    refuse_secrets({n: f for n, f in setup_files.items() if n != bundle.name}, {}, ())
    setup = out / WORKER_SETUP
    tar(setup, setup_files)
    receipt = {"utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "stage": f"stage1-{engine}",
               "engine": engine, "git_commit": commit, "engine_sha256": code, "yhash_files": len(yhash or []),
               "inputs_record_sha256": a.inputs_sha256, "sealed_files_sha256": hashlib.sha256(sealed_json).hexdigest(),
               "inputs": dict(sorted(pack.inputs.items())),
               "bundle": {"path": str(bundle), "sha256": bundle_sha, "files": len(files)},
               "setup": {"path": str(setup), "sha256": sha(setup), "bytes": setup.stat().st_size},
               "pip_pin": rules.PIP_PIN, "members": {name: sha(f) for name, f in sorted(setup_files.items())}}
    with (out / "setup-receipt.json").open("x") as handle:
        handle.write(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({k: receipt[k] for k in ("stage", "engine", "engine_sha256", "sealed_files_sha256", "bundle",
                                              "setup")}, indent=2))


if __name__ == "__main__":
    main()
