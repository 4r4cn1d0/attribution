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
is not the copy's. Every packed file is scanned for secret patterns (names and pattern names only in a refusal) except
the prepared set's manifest-listed files: the engine files, the scorer code and scripts, the edit files (edits/; K5,
the lead's R4 ruling), the main and S_78 configs, the named inputs (inputs/, non-binary files), the generated payloads,
the worker bootstrap and every member of the setup tar. Under data/ (the prepared set; K6, the lead's ruling on K5v-3)
the pack scans every file that the set's manifest.json does not list in its "files" map (prepare_receipt.json, which
the engine writes outside the manifest hash; manifest.json and manifest.sha256 themselves; any stray file), skips
.DS_Store and the other macOS metadata files by name (prepared_files: they are neither packed nor scanned), and keeps
the files manifest.json lists outside the scan, because the manifest pins them: a listed file stays outside only at
its listed SHA-256, and only while manifest.json's own SHA-256 is the family's pin (stage1_rules.PREPARED_MANIFESTS);
otherwise it is scanned too. The c0 source unit (K6, the 7 Nov ruling on item 23): its e1 adapter fingerprint must be
C0_SOURCE's at pack time (c0_source_check), so a typing error refuses on the Mac before any pod starts.
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
# The prefixes the general scan skips: data/ (the prepared set: only its manifest-listed files, pinned by the manifest;
# its other files are scanned by name through refuse_secrets' scan_anyway, K6) and inputs/ (scanned by refuse_secrets'
# own loop, non-binary files). edits/ is scanned (K5, R4).
DATA_PREFIXES = (f"{DATA}/", "inputs/")
# K6 (the lead's ruling on K5v-3): macOS metadata files in the prepared set, skipped by name (neither packed nor
# scanned): Finder's .DS_Store, AppleDouble "._*" files, and the volume metadata names.
MACOS_METADATA = frozenset({".DS_Store", ".localized", "Icon\r", ".Spotlight-V100", ".Trashes", ".fseventsd",
                            ".TemporaryItems", ".DocumentRevisions-V100", ".VolumeIcon.icns", ".apdisk",
                            ".com.apple.timemachine.donotpresent"})
C0_INPUT = "source_complete:R:1101"                     # c0's packed source unit (N's R_1 at 1101; stage1_rules.SC_INPUTS)
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
    if doc.get("inputs") and rules.KIT_BLOCK not in (r78.SC_BLOCK, *r78.BANK500_BLOCKS):   # R3 K3: A and B name inputs
        raise SystemExit("block 0 packs no named input (the scorer kinds' inputs come with their round); give inputs: []")
    if not isinstance(doc.get("inputs", []), list):
        raise SystemExit("--inputs FILE: inputs is a list of {name, path, sha256}")
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


def macos_metadata(rel: str) -> bool:
    """A macOS metadata file by name (any part of the relative path is one of MACOS_METADATA or starts with '._')."""
    return any(part in MACOS_METADATA or part.startswith("._") for part in rel.split("/"))


def prepared_files(folder: pathlib.Path, digest: str) -> tuple[dict, frozenset, list]:
    """K6 (the lead's ruling on K5v-3): (relative path -> (file, SHA-256) to pack, the relative paths to scan, the
    relative paths skipped). A regular file that manifest.json's "files" map lists at that file's SHA-256 is pinned by
    the manifest and stays outside the scan; the list is read only when manifest.json's own SHA-256 is ``digest`` (the
    family's pin), else no file counts as listed. A macOS metadata file that is not listed is skipped by name (neither
    packed nor scanned). Every other file (prepare_receipt.json, manifest.json and manifest.sha256 themselves, a stray
    file) is packed and scanned. Links are not packed (as before). Names only; no file's text is printed."""
    listed = {}
    man = folder / "manifest.json"
    if man.is_file() and not man.is_symlink():
        data = man.read_bytes()
        if hashlib.sha256(data).hexdigest() == digest:
            try:
                doc = json.loads(data)
            except ValueError:
                doc = None
            names = doc.get("files") if isinstance(doc, dict) else None
            listed = {k: v for k, v in names.items() if isinstance(k, str) and pinned(v)} if isinstance(names, dict) else {}
    packed, scan, skipped = {}, set(), []
    for f in sorted(folder.rglob("*")):
        if not f.is_file() or f.is_symlink():
            continue
        rel = f.relative_to(folder).as_posix()
        got = sha(f)
        if listed.get(rel) == got:
            packed[rel] = (f, got)
        elif macos_metadata(rel):
            skipped.append(rel)
        else:
            packed[rel] = (f, got)
            scan.add(rel)
    return packed, frozenset(scan), skipped


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


def probe_record(family: str, extra: list | None = None) -> dict:
    """probe.json: the family's download plan, plus (R3 K3) the extra entries of this pack's hosts (R-66, R-71)."""
    return {"probe": rules.PROBE_KEY, "family": family,
            "plan": probes.stage1_download_plan(rules.PROBE_KEY, with_base=False) + list(extra or []),
            "weight_pins": list(probes.PROBES[rules.PROBE_KEY]["weight_pins"])}


def pack_extra_downloads(w1_18: bool) -> list:
    """R-71: block B's pack, when its plan.json holds a safe_lora job, downloads the base model at its pinned revision
    (refused while probes.BASE_MODELS' pin is null); R-66: the W1-18 pack downloads the other W1-18 families'
    tokenizers (Llama's through the Llama token path)."""
    jobs = []
    if rules.KIT_BLOCK == "B" and (HERE / "plan.json").is_file():
        plan = json.loads((HERE / "plan.json").read_text())
        b = (plan.get("blocks") or {}).get("B") or {}
        hosts = [h for h in (plan.get("hosts") or {}).values() if h.get("block") == "B"] + list((b.get("pending") or {}).values())
        jobs += [j for h in hosts for j in h.get("jobs", []) if j.get("kind") == "safe_lora"][:1]
    fams = ()
    if w1_18:
        fams = sorted((r78.W1_18_78B or {}).get("side_units") or ())
        jobs.append({"kind": "w1_18"})
    return rules.host_extra_downloads(jobs, fams)


def kit_family_doc(family: str) -> bytes:
    return (json.dumps({"kind": rules.KIT_FAMILY_KIND, "family": family, "block": rules.KIT_BLOCK}) + "\n").encode()


BINARY_SUFFIXES = (".safetensors", ".bin", ".pt", ".pth", ".npy", ".npz", ".gz", ".tar", ".zip")   # not scanned
INPUTS_PREFIX = "inputs/"


def refuse_secrets(files: dict, payloads: dict, data_prefixes: tuple, scan_anyway: frozenset = frozenset()) -> None:
    """Scan every packed file outside ``data_prefixes`` (the bundle: DATA_PREFIXES, so data/ only stays outside; the
    edit files under edits/ are scanned, K5) and every file named in ``scan_anyway`` (the bundle: the prepared set's
    files that its manifest does not pin, K6), every non-binary file of the scorer block's named inputs (inputs/; the
    security verifier's D5: anchor prompts, the 1B lists and pools, unit records), and every generated payload; a hit
    refuses with names and pattern names only, never the matched text."""
    inputs = {name: f for name, f in files.items()
              if name.startswith(INPUTS_PREFIX) and not name.lower().endswith(BINARY_SUFFIXES)}
    input_hits = sorted({name for name, f in inputs.items() if secret_scan.scan_paths([f])})
    if input_hits:
        raise SystemExit(f"a secret pattern is in {len(input_hits)} packed scorer input file(s): {input_hits[:10]}")
    scanned = [f for name, f in files.items() if not name.startswith(data_prefixes) or name in scan_anyway]
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


# ===== K4b: the scorer block's bundle (plan T4 step 3's scorer part; SCORERS-78B.md section 6 item 10) ==============
def pins78() -> dict:
    """The scorer layer's settings/pins_78b.json at its stage1_rules.SCORER_PINS pin."""
    path = ROOT / rules.PINS_78B
    if not path.is_file() or sha(path) != rules.SCORER_PINS[rules.PINS_78B]:
        raise SystemExit(f"{rules.PINS_78B} is missing or differs from the kit's pin (stage1_rules.SCORER_PINS)")
    return json.loads(path.read_text())


def scorer_code(family: str) -> dict:
    """bundle path -> (source, pin) of every scorer file the block runs: stage1_rules.SCORER_PINS (the wrapper, its
    settings index, pins and settings files, the 1B scripts it imports, the anchor job's script) and, once filled,
    rules_78b.OEXT_78B[family]'s files (o_only, c0). A file that is missing or differs from its pin refuses at pack
    time (Packing.add)."""
    out = {rel: (ROOT / rel, pin) for rel, pin in sorted(rules.SCORER_PINS.items())}
    out.update(oext_code(family))
    return out


def oext_code(family: str, engine: str = "X") -> dict:
    """bundle path -> (source, pin) of the family's O-ext pin's files (OEXT_78B[F], or OEXT_78B_Y[F] for engine Y):
    plain paths under scripts/, and the family's W1-18 record at its R-21 place when the branch comes from W1-18 (GXB
    R-21, R-33); empty while the pin is null."""
    pin = (r78.OEXT_78B if engine == "X" else r78.OEXT_78B_Y).get(family) or {}
    out = {}
    for rel, digest in sorted((pin.get("files") or {}).items()):
        if not plain_path(rel) or not (rel.startswith("scripts/") or r78.W1_18_RECORD_RE.match(rel)):
            raise SystemExit(f"OEXT_78B[{family!r}] names {rel!r}, not a plain path under scripts/ or the W1-18 record")
        out[rel] = (ROOT / rel, digest)
    return out


def input_bundle_path(name: str, src: pathlib.Path) -> str:
    """The bundle path of a named input: inputs/<name with ':' as '-'>/<the file's or folder's own name>."""
    return f"inputs/{name.replace(':', '-')}/{src.name}"


def c0_source_check(src: pathlib.Path, digest: str, c0: dict | None) -> None:
    """K6 (the 7 Nov ruling on Part 2's item 23): on the Mac, at pack time (and in the dry run), the packed c0 source
    unit's COMPLETE.json, read once and re-hashed against its pin (C0_SOURCE's complete_sha256), must list
    checkpoints.e1.adapter_fingerprint equal to C0_SOURCE[family]["e1_fingerprint"]; a typing error in the lead's
    recorded step refuses here, before any pod starts (the pod's runner checks it again, K5). Only that field is read;
    a refusal names the input only, never a value."""
    data = src.read_bytes()
    if hashlib.sha256(data).hexdigest() != digest or not isinstance(c0, dict):
        raise SystemExit(f"--inputs FILE: {C0_INPUT!r} (c0's source unit) differs from its pin (C0_SOURCE)")
    try:
        doc = json.loads(data)
    except ValueError:
        raise SystemExit(f"--inputs FILE: {C0_INPUT!r} (c0's source unit) is not a readable COMPLETE.json") from None
    points = doc.get("checkpoints") if isinstance(doc, dict) and isinstance(doc.get("checkpoints"), dict) else {}
    e1 = points.get("e1") if isinstance(points.get("e1"), dict) else {}
    got = e1.get("adapter_fingerprint")
    if not pinned(got):
        raise SystemExit(f"--inputs FILE: {C0_INPUT!r} (c0's source unit) lists no e1 adapter fingerprint")
    if got != c0.get("e1_fingerprint"):
        raise SystemExit(f"--inputs FILE: {C0_INPUT!r} (c0's source unit): its e1 adapter fingerprint is not "
                         "C0_SOURCE's e1_fingerprint (the lead's recorded step differs from the unit); refused before "
                         "any pod starts")


def folder_input(name: str) -> bool:
    """A unit-folder input: stage1_rules.SC_FOLDER_INPUTS, and R3 K3's dev-100 source units source_unit:<arm>:<seed>."""
    return name in rules.SC_FOLDER_INPUTS or name.startswith(rules.SOURCE_UNIT.split("{", 1)[0])


ANCHOR_JOB_DONE = "anchor_job_done"                     # KR4, KR8: the anchor job's JOB-DONE.json the stop record names
ANCHOR_STOP_NAME = "anchor_stop"                        # KR4: the family's stop record, packed by its ANCHOR_STOP pin


def input_pins(family: str) -> dict:
    """name -> the pin of every named input this copy may pack: in the scorer block every kind's inputs, each unit
    named by (arm, seed) (GXB R-16, R-31: rules_78b.sc_units, stage1_rules.sc_unit_input_pins), with each regenerated
    unit's dev-100 source folder source_unit:<arm>:<seed> at its acceptance input's pin (LN-19, Branch 128); in blocks A
    and B the O-ext bank and record (OEXT_78B[F]'s inputs; plan-ab 5a); in every block, once ANCHOR_STOP[F] is pinned,
    the anchor job's JOB-DONE.json at the stop record's job_done_sha256 (KR4, KR8)."""
    try:
        values = r78.sc_pin_values(family, pins78())
    except r78.Refused as exc:
        raise SystemExit(str(exc))
    pins = {}
    if rules.KIT_BLOCK == r78.SC_BLOCK:
        for kind in r78.SC_KINDS:
            for u in r78.sc_units(family, kind):
                got = rules.sc_unit_input_pins(kind, pins78(), values, u["arm"], u["seed"])
                pins.update(got)
                if kind == "o_only_with_regenerate":
                    pins[rules.SOURCE_UNIT.format(arm=u["arm"], seed=u["seed"])] = next(iter(got.values()))
    elif rules.KIT_BLOCK in r78.BANK500_BLOCKS:
        oext = (values.get("OEXT_78B") or {}).get("inputs") or {}
        pins.update({n: oext.get(n) for n in r78.OEXT_INPUTS})
        if rules.KIT_BLOCK == "B":                       # R3 K3 (item 13): the references' inputs, at their jobs' pins
            pins.update(ref_input_pins())
    stop = anchor_stop_doc(family)
    if stop is not None:
        pins[ANCHOR_JOB_DONE] = stop[0]["job_done_sha256"]
    return pins


REF_INPUT_RE = re.compile(r"^(gate_a_complete|gate_a_eval|certification_report):110[2-7]$")


def ref_input_pins() -> dict:
    """R3 K3 (item 13): name -> pin of block B's reference inputs, from this copy's plan.json (every block-B job's
    inputs, released or pending; conflicting pins refuse): gate_a_complete:S, gate_a_eval:S (both pinned by S's a0
    unit's COMPLETE.json, R-35), certification_report:S, and prefix_file at REF_PREFIX_SHA256 (the 1B safety-prompt
    text, Part 2 §3.2) whatever the plan says."""
    plan_file = HERE / "plan.json"
    plan = json.loads(plan_file.read_text()) if plan_file.is_file() else {}
    b = (plan.get("blocks") or {}).get("B") or {}
    hosts = [h for h in (plan.get("hosts") or {}).values() if h.get("block") == "B"] + list((b.get("pending") or {}).values())
    pins = {"prefix_file": r78.REF_PREFIX_SHA256}
    for h in hosts:
        for job in h.get("jobs", []):
            for name, pin in (job.get("inputs") or {}).items():
                if REF_INPUT_RE.match(name):
                    if pins.get(name, pin) != pin:
                        raise SystemExit(f"plan.json pins {name!r} twice with two values")
                    pins[name] = pin
    return pins


SOURCE_UNIT_PREFIX = rules.SOURCE_UNIT.split("{", 1)[0]   # "source_unit:"
UNIT_UNLISTED = ("COMPLETE.json", "status.json")         # the engine's own marker files (ledger._UNHASHED)
# GXB R-81: what the unchanged 1B check_source reads of a dev-100 source unit (R: scripts/stage1_s1/oext_unit.py
# check_source; the settings' dev100.source_files, the 1B file and both families' oext_unit__F.json, at the e1
# checkpoint). M (tests/test_runner_ab_78b.py, a fixture through the unchanged code): a folder holding only these
# runs, one without guard.jsonl refuses, although COMPLETE.json lists 27 files. So the pack takes these files only.
SOURCE_UNIT_FILES = ("COMPLETE.json", "job.json", "eval/e1/generations.jsonl", "eval/e1/guard.jsonl")


def source_unit_files(name: str, src: pathlib.Path, digest: str) -> dict:
    """GXB R-76 (K3V-2; the 1B form, R: runkit/stage1-olmo/pack_setup.py:296-306): a regenerated unit's dev-100 source
    unit folder, whose COMPLETE.json hashes to ``digest``; every file is packed only at the SHA-256 its COMPLETE.json
    "files" lists for it (the unchanged 1B check_source hashes every present file the same way on the pod); macOS
    metadata is skipped by name; any other file the listing does not hold, or holds at another SHA-256, refuses here,
    on the Mac. Names only in refusals."""
    marker = src / "COMPLETE.json"
    if not src.is_dir() or not marker.is_file() or marker.is_symlink() or sha(marker) != digest:
        raise SystemExit(f"--inputs FILE: {name!r} is not a unit folder whose COMPLETE.json has its pin")
    try:
        listed = (json.loads(marker.read_text()) or {}).get("files") or {}
    except ValueError:
        raise SystemExit(f"--inputs FILE: {name!r}'s COMPLETE.json is not JSON") from None
    base, out = input_bundle_path(name, src), {}
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src).as_posix()
        if f.is_symlink():
            raise SystemExit(f"--inputs FILE: {name!r} holds a symbolic link")
        if not f.is_file() or macos_metadata(rel):
            continue
        got = sha(f)
        if rel not in UNIT_UNLISTED and listed.get(rel) != got:
            raise SystemExit(f"--inputs FILE: {name!r}: a file is not one its COMPLETE.json lists at its SHA-256 (the "
                             "1B check_source rule): refused before any pod")
        if rel in SOURCE_UNIT_FILES:                     # GXB R-81: only what check_source reads is packed
            out[f"{base}/{rel}"] = (f, got)
    missing = [r for r in SOURCE_UNIT_FILES if f"{base}/{r}" not in out]
    if missing:
        raise SystemExit(f"--inputs FILE: {name!r} lacks {missing} (the files the 1B check_source reads; R-81)")
    return out


def gate_eval_files(name: str, src: pathlib.Path, digest: str) -> dict:
    """gate_a_eval:S (GXB R-35; the B10 settings' gate): the a0 unit's eval/e1 folder, whose unit's COMPLETE.json (two
    levels up) hashes to ``digest``; every file under it is packed only at the SHA-256 that COMPLETE.json's "files"
    lists for it (eval/e1/<file>). Returns bundle path -> (file, SHA-256). Names only in refusals."""
    unit = src.parent.parent
    marker = unit / "COMPLETE.json"
    if src.name != "e1" or src.parent.name != "eval" or not marker.is_file() or sha(marker) != digest:
        raise SystemExit(f"--inputs FILE: {name!r} is not an a0 unit's eval/e1 folder whose COMPLETE.json has its pin")
    listed = (json.loads(marker.read_text()) or {}).get("files") or {}
    out, base = {}, input_bundle_path(name, src)
    for f in sorted(src.rglob("*")):
        if f.is_symlink():
            raise SystemExit(f"--inputs FILE: {name!r} holds a symbolic link")
        if f.is_file() and not macos_metadata(f.name):
            rel = f.relative_to(unit).as_posix()
            if listed.get(rel) != sha(f):
                raise SystemExit(f"--inputs FILE: {name!r}: a file is not the one its unit's COMPLETE.json lists")
            out[f"{base}/{f.relative_to(src).as_posix()}"] = (f, sha(f))
    if not out:
        raise SystemExit(f"--inputs FILE: {name!r} holds no file")
    return out


def anchor_stop_doc(family: str) -> tuple[dict, bytes, str] | None:
    """KR4: (the family's stop record, its bytes, its path) read at ANCHOR_STOP[family]'s pin and checked for its form
    (rules_78b.anchor_stop_problem); None while the pin is null. The pairing with the anchor job's JOB-DONE.json is
    checked by anchor_stop_or_refuse once that file is given (sc_inputs)."""
    pin = r78.ANCHOR_STOP.get(family)
    if pin is None:
        return None
    if not (isinstance(pin, dict) and set(pin) == {"path", "sha256"} and plain_path(pin["path"]) and pinned(pin["sha256"])):
        raise SystemExit(f"ANCHOR_STOP[{family!r}] is not a {{path, sha256}} pin")
    f = ROOT / pin["path"]
    if not f.is_file() or f.is_symlink() or sha(f) != pin["sha256"]:
        raise SystemExit(f"ANCHOR_STOP[{family!r}]: the stop record is missing or differs from its pin")
    data = f.read_bytes()
    try:
        doc = json.loads(data)
    except ValueError:
        raise SystemExit(f"ANCHOR_STOP[{family!r}]: the stop record is not JSON") from None
    problem = r78.anchor_stop_problem(doc, family)
    if problem:
        raise SystemExit(f"ANCHOR_STOP[{family!r}]: the stop record is not the family's: {problem}")
    return doc, data, pin["path"]


def sc_inputs(doc: dict, family: str) -> tuple[dict, dict]:
    """(bundle path -> (source, SHA-256) of every file, input name -> bundle path) from the --inputs record's entries
    {name, path, sha256}: each name one of stage1_rules.SC_INPUTS's, each SHA-256 its kit pin (stage1_rules.sc_input_pins;
    a null pin refuses), each path a file under the checkout (a folder for stage1_rules.SC_FOLDER_INPUTS, whose pin is
    its COMPLETE.json's SHA-256; every file of the folder is packed at its own SHA-256). Names only in refusals."""
    pins = input_pins(family)
    files, named = {}, {}
    for e in doc.get("inputs") or []:
        if not isinstance(e, dict) or set(e) != {"name", "path", "sha256"}:
            raise SystemExit("--inputs FILE: each entry is exactly {name, path, sha256}")
        name, rel, digest = e["name"], e["path"], e["sha256"]
        if name not in pins:
            raise SystemExit(f"--inputs FILE: {name!r} is not an input of the scorer block ({sorted(pins)})")
        if name in named:
            raise SystemExit(f"--inputs FILE: {name!r} is listed twice")
        if pins[name] is None:
            raise SystemExit(f"--inputs FILE: {name!r}'s pin is null (addendum A13): it waits for its event")
        if digest != pins[name]:
            raise SystemExit(f"--inputs FILE: {name!r}'s SHA-256 is not its pin")
        if not plain_path(rel):
            raise SystemExit(f"--inputs FILE: {name!r}'s path is not a plain relative path under the checkout")
        src = ROOT / rel
        if name.startswith("gate_a_eval:"):            # R3 K3 (item 13): by its unit's COMPLETE.json listing
            got = gate_eval_files(name, src, digest)
            files.update(got)
            named[name] = input_bundle_path(name, src)
        elif folder_input(name) and name.startswith(SOURCE_UNIT_PREFIX):   # GXB R-76 (K3V-2): the 1B form
            files.update(source_unit_files(name, src, digest))
            named[name] = input_bundle_path(name, src)
        elif folder_input(name):
            if not src.is_dir() or not (src / "COMPLETE.json").is_file() or sha(src / "COMPLETE.json") != digest:
                raise SystemExit(f"--inputs FILE: {name!r} is not a unit folder whose COMPLETE.json has its pin")
            base = input_bundle_path(name, src)
            for f in sorted(src.rglob("*")):
                if f.is_symlink():
                    raise SystemExit(f"--inputs FILE: {name!r} holds a symbolic link")
                if f.is_file():
                    files[f"{base}/{f.relative_to(src).as_posix()}"] = (f, sha(f))
            named[name] = base
        else:
            if not src.is_file() or src.is_symlink() or sha(src) != digest:
                raise SystemExit(f"--inputs FILE: {name!r}'s file is missing or differs from its SHA-256")
            files[input_bundle_path(name, src)] = (src, digest)
            named[name] = input_bundle_path(name, src)
    if C0_INPUT in named:                                # K6 (item 23): the Mac-side check of C0_SOURCE's fingerprint
        c0_source_check(*files[named[C0_INPUT]], r78.sc_pin_values(family, pins78())["C0_SOURCE"])
    stop = anchor_stop_doc(family)
    if stop is not None:                                 # KR4: the pack carries the stop record and its JOB-DONE.json
        if ANCHOR_JOB_DONE not in named:
            raise SystemExit(f"--inputs FILE: {family}'s anchor job stopped (ANCHOR_STOP): name {ANCHOR_JOB_DONE!r}, the "
                             "anchor job's JOB-DONE.json, so the pod can read the stop record (KR4, KR8)")
        try:
            r78.anchor_stop_or_refuse(family, stop[1], files[named[ANCHOR_JOB_DONE]][1])
        except r78.Refused as exc:
            raise SystemExit(f"the anchor stop record: {exc}")
        rel = f"inputs/{ANCHOR_STOP_NAME}/{pathlib.Path(stop[2]).name}"
        files[rel] = (ROOT / stop[2], r78.ANCHOR_STOP[family]["sha256"])
        named[ANCHOR_STOP_NAME] = rel
    return files, named


# ===== R3 K3: the O-ext pods' pack (GXB R-6, R-9, R-21, R-23, R-44, K-3, K-7, O4, O10, KR4; plan-ab 5a, 5c) =========
def branch_file(family: str, required: bool) -> tuple[str, pathlib.Path, str] | None:
    """(bundle path, source, pin) of the family's branch record at BRANCH_78B[family]'s path and SHA-256 (the runner
    reads it by its bytes, rules_78b.oext_flags); None while the pin is null unless ``required`` (blocks A and B)."""
    pin = r78.BRANCH_78B.get(family)
    if pin is None:
        if required:
            raise SystemExit(f"blocks A and B carry the O-ext step: {family}'s branch record (BRANCH_78B) is null: "
                             f"{r78.BRANCH_EVENT}")
        return None
    if not (isinstance(pin, dict) and plain_path(pin.get("path")) and pinned(pin.get("sha256"))):
        raise SystemExit(f"BRANCH_78B[{family!r}] is not a {{path, sha256}} pin")
    f = ROOT / pin["path"]
    try:
        r78.branch_record_or_refuse(family, f.read_bytes() if f.is_file() and not f.is_symlink() else b"")
    except r78.Refused as exc:
        raise SystemExit(f"{family}'s branch record: {exc}")
    return pin["path"], f, pin["sha256"]


def run_check(argv: list[str]) -> int:
    """The wrapper's $0 check as its own process on the Mac (cwd = the checkout; no token, no PYTHONPATH); only its
    exit code is used (its printout names hashes only, OR7, and is not shown here)."""
    env = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin"}
    return subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, env=env).returncode


def wrapper_check(family: str, engine: str, index_rel: str, index_sha: str, extra: list[str]) -> dict:
    """GXB R-6, R-9, R-23: ``oext_78b.py check`` on the Mac before any O-ext pod; any non-zero exit refuses the pack."""
    argv = [str(PY), "-B", r78.OEXT_WRAPPER_78B, "check", "--family", family, "--engine", engine, "--index", index_rel,
            "--index-sha256", index_sha, *extra]
    code = run_check(argv)
    if code != 0:
        raise SystemExit(f"oext_78b.py check of {family}'s engine-{engine} index refused (exit {code}): refused before "
                         "any O-ext pod (GXB R-6, R-9, R-23)")
    return {"family": family, "engine": engine, "index_sha256": index_sha, "args": [a for a in extra if a.startswith("--")],
            "exit": code}


def oext_checks(family: str, engines=("X",)) -> list[dict]:
    """R-6 and R-23: the family's O-ext index of each engine whose pin is filled (Y only once ENGINE_Y is filled), with
    --w1-18-record when the branch record names the family's W1-18 record (the pinned record, at its R-21 place)."""
    out = []
    branch = branch_file(family, required=False)       # GXB R-78: the pin and the record checked first (a refusal)
    record = None
    if branch is not None:
        doc = json.loads(branch[1].read_bytes())
        if doc.get("source") == "w1_18":
            record = r78.W1_18_RECORD_DIR + r78.W1_18_RECORD_NAME.format(family=family)
    for engine in engines:
        pin = (r78.OEXT_78B if engine == "X" else r78.OEXT_78B_Y).get(family)
        if pin is None or (engine == "Y" and r78.ENGINE_Y is None):
            continue
        problem = r78.oext_form_problem(pin, family, engine)
        if problem:
            raise SystemExit(f"{family}'s engine-{engine} O-ext pin is off its form: {problem}")
        idx = next(p for p in sorted(pin["files"]) if r78.OEXT_INDEX_RE.match(p))
        out.append(wrapper_check(family, engine, idx, pin["files"][idx], [] if record is None else
                                 ["--w1-18-record", record]))
    return out


def unit_folder_files(base: str, src: pathlib.Path, complete_sha: str, job_sha: str, what: str) -> dict:
    """bundle path -> (file, SHA-256) of one unit folder (every file but macOS metadata; a link refuses), its
    COMPLETE.json and job.json at their pins."""
    if not src.is_dir() or sha(src / "COMPLETE.json") != complete_sha or sha(src / "job.json") != job_sha:
        raise SystemExit(f"{what}: the unit folder is missing or its COMPLETE.json or job.json differs from its pin")
    out = {}
    for f in sorted(src.rglob("*")):
        rel = f.relative_to(src).as_posix()
        if f.is_symlink():
            raise SystemExit(f"{what}: the unit folder holds a symbolic link")
        if f.is_file() and not macos_metadata(rel):
            out[f"{base}/{rel}"] = (f, sha(f))
    return out


def w1_18_pack(family: str) -> tuple[dict, list[dict], dict]:
    """GXB O4, K-3, R-20, O10 (5c): the one W1-18 pod's files, packed only in W1_18_HOST_FAMILY's scorer-block copy:
    W1_18_78B's files (the wrapper, each family's W1 index and W1-18 settings, the 1B W1-18 code, Track P's frozen
    readers once listed: W2-5) at their pins; each listed family's side units under data/ (the checkout's tmp/
    mirrored, the W1-18 settings' data root) at their KIT a0_units pins; the other family's prepared set under
    data/kt-prepared/ at its manifest pin (the lexicon files and the main configs, the judge recipes, are already in
    the scorer code and the engine tree). Before anything: oext_78b.py check --engine W1 --data-root tmp per family
    (R-9). Returns (bundle path -> (file, SHA-256), the checks, data paths to scan)."""
    if rules.KIT_BLOCK != r78.SC_BLOCK or r78.w1_18_host_problem(family):
        raise SystemExit(f"--w1-18: {r78.w1_18_host_problem(family) or 'the W1-18 pod is a scorer-block pod'}")
    route = r78.W1_18_78B
    if route is None:
        raise SystemExit(f"--w1-18: W1_18_78B is null: {r78.SC_PIN_EVENTS['W1_18_78B']}")
    problem = r78.w1_18_route_problem(route)
    if problem:
        raise SystemExit(f"--w1-18: W1_18_78B is not in its form: {problem}")
    checks = []
    for fam in sorted(route["side_units"]):
        idx = f"scripts/scale78b/settings/OEXT-78B-W1__{fam}.json"
        checks.append(wrapper_check(fam, "W1", idx, route["files"][idx], ["--data-root", str(ROOT / "tmp")]))
    files = {rel: (ROOT / rel, digest) for rel, digest in sorted(route["files"].items())}
    scan = {}
    for fam, units in sorted(route["side_units"].items()):
        for name, u in sorted(units.items()):
            files.update(unit_folder_files(f"{DATA}/{u['path']}", ROOT / r78.DATA_ROOT / u["path"], u["complete_sha256"],
                                           u["job_sha256"], f"{fam}'s W1-18 unit {name}"))
        if fam != family:
            pname, digest = r78.KIT[fam]["prepared_name"], r78.MANIFESTS[fam]
            folder = ROOT / rules.PREPARED_LOCAL / pname
            if not (folder / "manifest.sha256").is_file() or (folder / "manifest.sha256").read_text().strip() != digest:
                raise SystemExit(f"--w1-18: {fam}'s prepared set {pname} is missing or is not at its manifest pin")
            got, data_scan, _ = prepared_files(folder, digest)
            for rel, (f, d) in got.items():
                files[f"{DATA}/kt-prepared/{pname}/{rel}"] = (f, d)
            scan.update({f"{DATA}/kt-prepared/{pname}/{rel}": True for rel in data_scan})
    return files, checks, scan


def ab_edits(family: str) -> dict:
    """K-7 (plan-ab 5a): bundle path edits/<SHA-256>.edit.json -> (source, SHA-256) of every edit a block-A or block-B
    job of this copy's plan.json trains on (released or pending), each read only at its exact path and SHA-256 (rules_78b
    run_edit's pins: the R_d draws, METHOD_EDITS; OLMo-2-7B's S1 edit under tmp/stage1-olmo/ is one of them; no folder
    is listed or searched)."""
    plan_file = HERE / "plan.json"
    if not plan_file.is_file():
        raise SystemExit(f"block {rules.KIT_BLOCK}: plan.json is missing (init-block {rules.KIT_BLOCK} first)")
    plan = json.loads(plan_file.read_text())
    b = (plan.get("blocks") or {}).get(rules.KIT_BLOCK) or {}
    hosts = [h for h in plan.get("hosts", {}).values() if h.get("block") == rules.KIT_BLOCK]
    hosts += list((b.get("pending") or {}).values())
    out = {}
    for h in hosts:
        for job in h.get("jobs", []):
            edit = job.get("edit")
            if edit:
                if not (plain_path(edit.get("path")) and pinned(edit.get("sha256"))):
                    raise SystemExit("a block job's edit is not a {path, sha256} pin")
                out[f"edits/{edit['sha256']}.edit.json"] = (ROOT / edit["path"], edit["sha256"])
    return out


def blinding_check(files: dict, bundle: pathlib.Path) -> dict | None:
    """GXB R-44 (K2's open point 1) at the pack receipt, block A: the blinding record block A was planned under (its
    plan.json snapshot, read at its path and SHA-256) names files by SHA-256; each must hash to it now in this copy
    (plan_tool.py: this copy's own; the others in the checkout), and every one that is a member of the packed bundle is
    re-hashed from the bundle's bytes and compared. A difference refuses (no receipt). None outside block A or before
    the snapshot."""
    if rules.KIT_BLOCK != "A" or not (HERE / "plan.json").is_file():
        return None
    plan = json.loads((HERE / "plan.json").read_text())
    snap = ((plan.get("blocks") or {}).get("A") or {}).get("blinding")
    if not snap:
        return None
    rec = ROOT / snap["path"]
    if not rec.is_file() or sha(rec) != snap["sha256"]:
        raise SystemExit("R-44: the blinding record block A was planned under is missing or differs from its SHA-256")
    named = json.loads(rec.read_text()).get("files") or {}
    copy = {}
    for rel, digest in sorted(named.items()):
        f = HERE / "plan_tool.py" if rel == "runkit/stage1-78b/plan_tool.py" else ROOT / rel   # K2's blinding_files_check
        copy[rel] = sha(f) if f.is_file() else None
        if copy[rel] != digest:
            raise SystemExit(f"R-44: {rel} is not the file the blinding record verified: the change voids it")
    members = {}
    with tarfile.open(bundle, "r:gz") as archive:
        for m in archive.getmembers():
            if m.name in named and m.isfile():
                members[m.name] = hashlib.sha256(archive.extractfile(m).read()).hexdigest()
                if members[m.name] != named[m.name]:
                    raise SystemExit(f"R-44: the packed {m.name} is not the file the blinding record verified")
    return {"record": {"path": snap["path"], "sha256": snap["sha256"]}, "files": copy, "bundle_members": members,
            "not_in_bundle": sorted(set(named) - set(members))}


def y_tree_check(tree: pathlib.Path) -> list[str]:
    """X1 (the stage-1 kit's Y route, R: runkit/stage1-olmo/pack_setup.py y_tree_check; YB P-4): engine Y's files come
    from its frozen tree only, checked against YHASH (the frozen file list at its pin, then every listed file in the
    tree by its SHA-256); returns the listed paths. Never from the working branch."""
    yhash = ROOT / rules.YHASH_PIN["path"]
    if not yhash.is_file() or sha(yhash) != rules.YHASH_PIN["sha256"]:
        raise SystemExit("YHASH (engine Y's frozen file list) is missing or differs from its pin")
    listed, bad = [], []
    for line in yhash.read_text().splitlines():
        if not line.strip():
            continue
        digest, _, rel = line.strip().partition("  ")
        listed.append(rel)
        f = tree / rel
        if not pinned(digest) or not f.is_file() or f.is_symlink() or sha(f) != digest:
            bad.append(rel)
    if bad or not listed:
        raise SystemExit(f"the Y tree fails YHASH: {len(bad)} file(s) missing or changed: {bad[:5]}")
    return listed


def engine_tree(engine: str, y_tree: str | None) -> tuple[pathlib.Path, str | None, list | None]:
    """(the engine's tree, its git commit or None, YHASH's listed paths or None): engine X this checkout (committed);
    engine Y its frozen tree (default tmp/engine-y-34bfd288) by YHASH and its code identity at ENGINE_Y, refused while
    ENGINE_Y is null (A13: every Y kind waits for the pin)."""
    if engine == "X":
        return ROOT, git_state(), None
    try:
        pin = r78.engine_sha("Y")
    except r78.Refused as exc:
        raise SystemExit(f"engine Y's pack: {exc}")
    tree = pathlib.Path(y_tree) if y_tree else ROOT / rules.Y_TREE_DEFAULT
    listed = y_tree_check(tree)
    if engine_code(tree) != pin:
        raise SystemExit(f"the Y tree's code identity is not ENGINE_Y's pin {pin[:12]}... (A13): refused")
    return tree, None, listed


def recipe_s78(tree: pathlib.Path, family: str) -> dict | None:
    """The family's S_78 config once RECIPE_S is filled (A1): its path (pins_78b.json recipe_s78.path), its bytes'
    SHA-256 and its config_sha256 by the engine's own hash, which must be RECIPE_S's pin; None while the pin is null."""
    try:
        values = r78.sc_pin_values(family, pins78())
    except r78.Refused as exc:
        raise SystemExit(str(exc))
    if values["RECIPE_S"] is None:
        return None
    rel = values["RECIPE_S_PATH"]
    f = tree / rel
    if not f.is_file() or f.is_symlink():
        raise SystemExit(f"{rel}: the S_78 config is missing from the engine tree (A1: committed by explicit path, KD8)")
    config = config_sha256(tree, rel)
    if config != values["RECIPE_S"]:
        raise SystemExit(f"{rel}: its config_sha256 {config[:12]}... is not RECIPE_S's pin {values['RECIPE_S'][:12]}...")
    return {"path": rel, "sha256": sha(f), "config_sha256": config}


def sc_report(family: str, tree: pathlib.Path, inputs_doc: dict | None) -> dict:
    """The dry run's scorer part: the code files checked against their pins (names of the bad ones), the inputs
    (name -> SHA-256), the S_78 config (or null), and per kind the pins it still waits for."""
    code = scorer_code(family)
    bad = [rel for rel, (src, pin) in code.items() if not src.is_file() or src.is_symlink() or sha(src) != pin]
    if bad:
        raise SystemExit(f"{len(bad)} scorer file(s) missing or differ from their pins: {bad[:10]}")
    files, named = sc_inputs(inputs_doc or {}, family)
    doc = pins78()
    waits = {}
    for kind in r78.SC_KINDS:
        engine = "Y" if kind == "retrain" else "X"
        waits[kind] = [p for p, _ in r78.sc_missing_pins(family, kind, engine, doc)]
    return {"code": {rel: pin for rel, (_, pin) in code.items()}, "inputs": {n: files[p][1] if p in files else
            files[f"{p}/COMPLETE.json"][1] for n, p in named.items()}, "recipe_s78": recipe_s78(tree, family),
            "waits": waits}


def parse(argv: list[str]) -> argparse.Namespace:
    ap = argparse.ArgumentParser(prog="pack_setup.py")
    ap.add_argument("engine", choices=["X", "Y"], help="engine X, or engine Y from its frozen tree (R3 K3, X1: the "
                    "scorer block's Y retrain, KD9's re-measure; refused while ENGINE_Y is null)")
    ap.add_argument("--y-tree", help="engine Y's frozen tree (Y only; default <repo>/" + rules.Y_TREE_DEFAULT + ")")
    ap.add_argument("--family", help="the working copy's family (refused when it is the other family)")
    ap.add_argument("--inputs", help="a 'stage1-78b pack inputs' record (block 0: inputs: [])")
    ap.add_argument("--inputs-sha256")
    ap.add_argument("--dry-run", action="store_true", help="print the identities and pins; write nothing")
    ap.add_argument("--w1-18", action="store_true", dest="w1_18",
                    help="the one W1-18 pod's pack (OLMo-2-7B's scorer-block copy; GXB K-3, O4): W1_18_78B's files, "
                         "the side units and the prepared sets, after oext_78b.py check --engine W1 (R-9)")
    a = ap.parse_args(argv)
    if (a.inputs is None) != (a.inputs_sha256 is None):
        ap.error("--inputs and --inputs-sha256 go together")
    if a.engine == "X" and a.y_tree:
        ap.error("--y-tree belongs to engine Y")
    return a


def dry_run_report(family: str, tree: pathlib.Path, inputs_doc: dict | None = None) -> dict:
    code = engine_code(tree)
    if code != r78.ENGINE_X:
        raise SystemExit(f"this checkout's engine identity {code[:12]}... is not engine X's pin {r78.ENGINE_X[:12]}... (KD8)")
    folder, digest = prepared_set(family)
    sealed = sealed_set(family)
    return {"dry_run": True, "engine": "X", "engine_sha256": code, "family": family, "kit_block": rules.KIT_BLOCK,
            "main_config": main_config(tree), "prepared_manifests": {rules.PREPARED_NAME: digest},
            "prepared_folder": str(folder.relative_to(ROOT)), "sealed_set": sealed, "git_commit": git_state(),
            "probe": rules.PROBE_KEY, "pod": dict(rules.POD_SIZES),
            **({"scorer_block": sc_report(family, tree, inputs_doc)} if rules.KIT_BLOCK == r78.SC_BLOCK else {})}


def main(argv: list[str] | None = None) -> None:
    a = parse(sys.argv[1:] if argv is None else argv)
    engine = a.engine
    family = family_of_run(a.family)
    inputs_doc = inputs_record(a.inputs, a.inputs_sha256, engine, family) if a.inputs else None
    if a.dry_run:
        print(json.dumps(dry_run_report(family, ROOT, inputs_doc), indent=2))
        return
    out = SETUP / f"packed-stage1-{engine}"
    if out.exists():
        raise SystemExit(f"{out.name} exists: a packed stage is never overwritten")
    check_constraints()
    tree, commit, yhash = engine_tree(engine, a.y_tree)  # R3 K3 (X1): engine Y from its frozen tree, by YHASH
    if engine == "Y" and rules.KIT_BLOCK not in (r78.SC_BLOCK, "B"):   # GXB R-63: block B's ref_train_bqi too
        raise SystemExit("engine Y's pack is the scorer block's (the a0-1101 retrain, KD9's re-measure) and block B's "
                         "(ref_train_bqi; GXB R-63): blocks 0 and A run on engine X (A13)")
    config = main_config(tree)
    process_receipt = ROOT / PROCESS_RECEIPT
    if not process_receipt.is_file():
        raise SystemExit(f"{PROCESS_RECEIPT} is missing: copy it in before packing")
    pack = Packing()
    sealed = sealed_set(family)
    for d, e in sorted(sealed["edits"].items()):
        pack.add(f"edits/{e['sha256']}.edit.json", ROOT / e["path"], e["sha256"])
    folder, digest = prepared_set(family)
    data_base = f"{DATA}/kt-prepared/{rules.PREPARED_NAME}"
    prepared, data_scan, _skipped = prepared_files(folder, digest)       # K6: macOS metadata skipped by name
    for rel, (f, got) in prepared.items():
        pack.add(f"{data_base}/{rel}", f, got)
    pack.add(config["path"], tree / config["path"], config["sha256"])
    s78, checks, w1_scan, ref_configs = None, [], {}, set()
    if rules.KIT_BLOCK == r78.SC_BLOCK:                  # K4b: the scorer block's code, inputs and S_78 config
        for rel, (src, pin) in scorer_code(family).items():
            pack.add(rel, src, pin)
        in_files, named = sc_inputs(inputs_doc or {}, family)
        for rel, (src, digest) in in_files.items():
            pack.add(rel, src, digest)
        pack.inputs.update(named)
        s78 = recipe_s78(tree, family)
        if s78 is not None:
            pack.add(s78["path"], tree / s78["path"], s78["sha256"])
        if r78.OEXT_78B.get(family) is not None:         # R3 K3 (R-6): before any O-ext pod, on the Mac
            checks += oext_checks(family)
        if engine == "Y" and r78.OEXT_78B_Y.get(family) is not None:   # R-23, X1: Y's O-ext files, checked on the Mac
            checks += oext_checks(family, ("Y",))           # under Y's identity; the unchanged 1B oext_unit.py from
            for rel, (src, pin) in oext_code(family, "Y").items():   # this checkout (the wrapper's CODE pin), never
                pack.add(rel, src, pin)                     # the 1B Y copy in the Y tree (r1-o-verify.md P3)
        branch = branch_file(family, required=False)
        if branch is not None:
            pack.add(*branch)
        if a.w1_18:                                      # R3 K3 (5c): the one W1-18 pod
            w1_files, w1_checks, w1_scan = w1_18_pack(family)
            checks += w1_checks
            for rel, (src, digest) in w1_files.items():
                pack.add(rel, src, digest)
    elif rules.KIT_BLOCK in r78.BANK500_BLOCKS:          # R3 K3 (5a, E3): blocks A and B, the in-job O-ext step
        if r78.OEXT_78B.get(family) is None:
            raise SystemExit(f"blocks A and B carry the O-ext step: OEXT_78B[{family!r}] is null: "
                             f"{r78.SC_PIN_EVENTS['OEXT_78B']}")
        checks += oext_checks(family)
        for rel, (src, pin) in oext_code(family).items():
            pack.add(rel, src, pin)
        pack.add(*branch_file(family, required=True))
        in_files, named = sc_inputs(inputs_doc or {}, family)
        missing = [n for n in r78.OEXT_INPUTS if n not in named]
        if missing:
            raise SystemExit(f"--inputs FILE: blocks A and B need the O-ext inputs {missing} (OEXT_78B's inputs)")
        for rel, (src, digest) in in_files.items():
            pack.add(rel, src, digest)
        pack.inputs.update(named)
        for rel, (src, digest) in ab_edits(family).items():   # K-7: each edit by its exact path and SHA-256
            pack.add(rel, src, digest)
        if rules.KIT_BLOCK == "B":                       # R3 K3 (item 13): each filled reference seed's files
            for seed in r78.REFERENCE_SEEDS:
                if r78.REFS_78B[family].get(seed) is None:
                    continue
                try:
                    pin = r78.refs_or_refuse(family, seed)
                except r78.Refused as exc:
                    raise SystemExit(str(exc))
                for rel, digest in sorted(pin["files"].items()):
                    pack.add(rel, ROOT / rel, digest)
        if engine == "Y":                                # GXB R-63: B+Qi's O-ext pass on Y (OEXT_78B_Y), checked first
            if r78.OEXT_78B_Y.get(family) is None:
                raise SystemExit(f"block B's Y pack carries B+Qi's O-ext pass: OEXT_78B_Y[{family!r}] is null: "
                                 f"{r78.SC_PIN_EVENTS['OEXT_78B_Y']}")
            checks += oext_checks(family, ("Y",))
            for rel, (src, pin) in oext_code(family, "Y").items():
                pack.add(rel, src, pin)
        if rules.KIT_BLOCK == "B":                       # R3 K3 (13g, R-70): the trained references' configs
            for name, paths in (("RECIPE_G", r78.RECIPE_G_PATH), ("RECIPE_BQI", r78.RECIPE_BQI_PATH)):
                pin, rel = r78.PINS[name].get(family), paths.get(family)
                if pin is None or rel is None or (name == "RECIPE_BQI") != (engine == "Y"):
                    continue
                f = tree / rel
                if not f.is_file() or f.is_symlink() or config_sha256(tree, rel) != pin or pin == rules.REC_CONFIG_SHA256:
                    raise SystemExit(f"{rel}: the {name} config is missing from the engine tree or is not {name}'s pin")
                pack.add(rel, f, sha(f))
                ref_configs.add(rel)
    if a.w1_18 and rules.KIT_BLOCK != r78.SC_BLOCK:
        raise SystemExit("--w1-18: the W1-18 pod is a scorer-block pod (GXB K-3)")
    pack.refuse()
    files = engine_files(tree)
    overlap = sorted(set(files) & set(pack.files) - {config["path"]} - ({s78["path"]} if s78 else set()) - ref_configs)
    if overlap:
        raise SystemExit(f"a kit file would replace an engine file: {overlap[:3]}")
    files.update(pack.files)
    files["bootstrap_hr.sh"] = SETUP / "bootstrap_hr.sh"
    files["constraints.txt"] = SETUP / "constraints.txt"
    files["requirements.lock"] = tree / "experiments/minimal_safety/requirements.lock"
    code = engine_code(tree)
    if code != r78.engine_sha(engine) or (engine == "X" and code != rules.ENGINES[engine]):
        raise SystemExit(f"the packed engine {engine}'s code identity is not its pin (KD8)")
    sealed_json = (json.dumps({"kind": "stage1-78b sealed files", "version": 1, "engine": engine, "family": family,
                               "files": dict(sorted(pack.pins.items())), "inputs": dict(sorted(pack.inputs.items()))},
                              indent=1) + "\n").encode()
    manifest = {"kind": f"explicit code and data export for the 7-8B kit, engine {engine}, family {family}; no credentials",
                "git_commit": commit, "engine": engine, "engine_sha256": code, "family": family, "kit_block": rules.KIT_BLOCK,
                **({"yhash": rules.YHASH_PIN} if yhash else {}),
                "main_config": config, "prepared_manifests": dict(rules.PREPARED_MANIFESTS), "sealed_set": sealed["manifest"],
                "files": {n: sha(f) for n, f in sorted(files.items())}}
    payload = {"bundle-manifest.json": (json.dumps(manifest, indent=2) + "\n").encode(), "sealed-files.json": sealed_json}
    extra = pack_extra_downloads(a.w1_18)                # R3 K3 (R-66, R-71): none for every earlier pack
    probe_json = (json.dumps(probe_record(family, extra) if extra else probe_record(family), indent=1) + "\n").encode()
    family_json = kit_family_doc(family)
    refuse_secrets(files, {**payload, "probe.json": probe_json, rules.KIT_FAMILY_FILE: family_json}, DATA_PREFIXES,
                   frozenset(f"{data_base}/{rel}" for rel in data_scan) | frozenset(w1_scan))
    out.mkdir(parents=True, exist_ok=False)
    (out / "probe.json").write_bytes(probe_json)
    (out / "sealed-files.json").write_bytes(sealed_json)
    (out / rules.KIT_FAMILY_FILE).write_bytes(family_json)
    bundle = out / f"bundle-stage1-{engine}.tar.gz"
    tar(bundle, files, payload)
    bundle_sha = sha(bundle)
    blinding = blinding_check(files, bundle)             # R3 K3 (GXB R-44): before the receipt
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
               "recipe_s78": s78,
               **({} if rules.KIT_BLOCK == "0" else {"oext_checks": checks, "w1_18": bool(a.w1_18), "blinding": blinding}),
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
