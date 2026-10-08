"""The judge pod's bundle: built on the Mac, verified on the pod (stdlib only; Python 3.9+).

Written 8 October 2026 (19:49 UTC, clock checked). Mac side (judge_pod.py): the units are found and verified by
units.enumerate_units exactly as the Mac judges find them (COMPLETE.json, job.json, every file under eval/<target>/
hash-checked); they are grouped by their job.json manifest_sha256, and each group needs a given prepared set whose
folder name and manifest are pinned (KNOWN_PREPARED, the probe kits' frozen manifests), whose manifest.sha256 equals
SHA-256(manifest.json), and whose banks/dev.jsonl has the SHA-256 that manifest.json lists for it. Then every group
passes judging.check_units (counts, guard ids, the manifest, equal prompt-id sets) and every answer's prompt id is among
the bank's harm prompts, as in a Mac run, before anything is built. The bundle holds only:

    bundle/tool/{common,cache,units,judging,harmbench_files}.py       the Mac judge's modules, unchanged
    bundle/tool/pod/{pod_job,pod_judge,bundle}.py, pod_run.sh, judge-requirements.txt, extend_cap.py
    bundle/units/NN/{job.json,COMPLETE.json}                           the sealed attempt's identity (no text)
    bundle/units/NN/eval/<target>/{generations,samples,guard,guard_samples}.jsonl     answers and guard records
    bundle/prepared/<name>/{manifest.sha256,banks/dev.jsonl}           the dev bank (the judge's prompts) only
    bundle/resume/harmbench.jsonl                                      optional: a previous pod run's fetched cache
    bundle/job-manifest.json                                           every other file's SHA-256, groups and units

The tar is deterministic (sorted members, mtime 0, uid/gid 0, mode 0644, gzip without name or time), so equal inputs
give an equal bundle SHA-256. Pod side (pod_job.py): verify_bundle refuses unless the folder holds exactly the listed
files with their SHA-256, each unit's COMPLETE.json and job.json have the unit's SHA-256 and agree with each other and
with the manifest (target, arm, seed, kind run-one, evaluate_bank dev, manifest_sha256, and each eval file's SHA-256 as
listed in COMPLETE.json), and each prepared set's manifest.sha256 is its pin and its dev bank has the recorded SHA-256.
pod_groups then rebuilds units.Unit objects on the pod paths (load_items and load_guard re-check every file's hash).
Nothing here prints or stores prompt or answer text: files are copied and hashed as bytes.
"""
from __future__ import annotations

import collections
import gzip
import io
import json
import pathlib
import shutil
import sys
import tarfile

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
for _p in (HERE.parent, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import judging  # noqa: E402
from cache import Cache  # noqa: E402
from common import HARMBENCH, HEX64, Refusal, bank_prompts, canonical_bytes, sha256_bytes, sha256_file  # noqa: E402
from units import EVAL_FILES, Unit  # noqa: E402

KIND = "judge-pod job manifest"
VERSION = 1
MANIFEST_NAME = "job-manifest.json"
TOP = "bundle"
MODES = ("greedy", "sampled")
TOOL_FILES = ("common.py", "cache.py", "units.py", "judging.py", "harmbench_files.py")
POD_FILES = ("pod_job.py", "pod_judge.py", "bundle.py", "pod_run.sh", "judge-requirements.txt", "extend_cap.py")
# Prepared sets whose dev bank may supply the prompts: folder name -> manifest SHA-256 (the probe kits'
# probe_constants.PREPARED_MANIFESTS, frozen 8 Oct 2026; the olmo2 value is common.PREPARED_MANIFEST).
KNOWN_PREPARED = {"prepared-kt-dolly-olmo2": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
                  "prepared-kt-dolly-llama3": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"}
DEV_BANK = "banks/dev.jsonl"
Group = collections.namedtuple("Group", "prepared_dir manifest_sha256 dev_bank_sha256 name units expect")


# ---------------------------------------------------------------- Mac side: prepared sets, groups, checks

def prepared_identity(prepared_dir: pathlib.Path, known: dict | None = None) -> dict:
    """{name, manifest_sha256, dev_bank_sha256} of a prepared set, after its pins are checked (hashes only)."""
    known = KNOWN_PREPARED if known is None else known
    prepared_dir = pathlib.Path(prepared_dir)
    name = prepared_dir.name
    if name not in known:
        raise Refusal(f"prepared set {name!r} is not one of the pinned sets {sorted(known)}")
    pinned = known[name]
    text = (prepared_dir / "manifest.sha256").read_text(encoding="utf-8").strip()
    manifest_bytes = (prepared_dir / "manifest.json").read_bytes()
    if text != pinned or sha256_bytes(manifest_bytes) != pinned:
        raise Refusal(f"prepared set {name}: manifest.sha256 or SHA-256(manifest.json) is not the pinned {pinned[:16]}")
    try:
        listed = json.loads(manifest_bytes)["files"][DEV_BANK]
    except (ValueError, KeyError, TypeError):
        raise Refusal(f"prepared set {name}: manifest.json lists no {DEV_BANK}") from None
    if not isinstance(listed, str) or not HEX64.match(listed) or sha256_file(prepared_dir / DEV_BANK) != listed:
        raise Refusal(f"prepared set {name}: {DEV_BANK} does not have the SHA-256 its manifest.json lists")
    return {"name": name, "manifest_sha256": pinned, "dev_bank_sha256": listed}


def plan_groups(units: list[Unit], prepared_dirs, expect: dict, known: dict | None = None) -> list[Group]:
    """Units grouped by job.json manifest_sha256, each with its prepared set, after the Mac run's checks: check_units
    (counts, guard ids, manifest, equal prompt-id sets within the group) and every answer's prompt id in the bank."""
    ids = [(pathlib.Path(d), prepared_identity(d, known)) for d in prepared_dirs]
    by_manifest = {}
    for d, ident in ids:
        if ident["manifest_sha256"] in by_manifest:
            raise Refusal(f"two given prepared sets have manifest {ident['manifest_sha256'][:16]}")
        by_manifest[ident["manifest_sha256"]] = (d, ident)
    grouped: dict[str, list[Unit]] = {}
    for u in units:
        if u.manifest_sha256 not in by_manifest:
            raise Refusal(f"{u.label}: job.json manifest_sha256 is not the manifest of a given prepared set")
        grouped.setdefault(u.manifest_sha256, []).append(u)
    groups = []
    for manifest, members in sorted(grouped.items()):
        d, ident = by_manifest[manifest]
        judging.check_units(members, MODES, expect, True, manifest)
        prompts = bank_prompts(d, manifest)
        empty = Cache(pathlib.Path("/nonexistent/judge-pod-plan.jsonl"), HARMBENCH)     # never written
        judging.todo_items(members, MODES, prompts, empty, with_text=False)
        groups.append(Group(d, manifest, ident["dev_bank_sha256"], ident["name"], members, dict(expect)))
    return groups


# ---------------------------------------------------------------- Mac side: the bundle

def _copy(src: pathlib.Path, stage: pathlib.Path, rel: str, files: dict) -> str:
    dst = stage / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    files[rel] = sha256_file(dst)
    return rel


def stage_bundle(groups: list[Group], stage: pathlib.Path, tag: str, tool_dir: pathlib.Path,
                 resume: dict | None = None, limit: int | None = None) -> dict:
    """Writes the bundle's files into stage/ (which must not exist) and returns the job manifest (also written)."""
    stage = pathlib.Path(stage)
    if stage.exists():
        raise Refusal(f"{stage} exists; the bundle is staged into a new folder")
    stage.mkdir(parents=True)
    files: dict[str, str] = {}
    for name in TOOL_FILES:
        _copy(tool_dir / name, stage, f"tool/{name}", files)
    for name in POD_FILES:
        _copy(tool_dir / "pod" / name, stage, f"tool/pod/{name}", files)
    out_groups, index = [], 0
    for g in groups:
        pdir = f"prepared/{g.name}"
        _copy(g.prepared_dir / "manifest.sha256", stage, f"{pdir}/manifest.sha256", files)
        _copy(g.prepared_dir / DEV_BANK, stage, f"{pdir}/{DEV_BANK}", files)
        if files[f"{pdir}/{DEV_BANK}"] != g.dev_bank_sha256:
            raise Refusal(f"prepared set {g.name}: {DEV_BANK} changed while the bundle was built")
        entries = []
        for u in g.units:
            nn = f"{index:02d}"
            index += 1
            udir = f"units/{nn}"
            _copy(u.path / "job.json", stage, f"{udir}/job.json", files)
            _copy(u.path / "COMPLETE.json", stage, f"{udir}/COMPLETE.json", files)
            if files[f"{udir}/job.json"] != u.job_sha256 or files[f"{udir}/COMPLETE.json"] != u.complete_sha256:
                raise Refusal(f"{u.label}: job.json or COMPLETE.json changed after it was verified")
            ufiles = {}
            for key, fname in EVAL_FILES.items():
                entry = u.files.get(key)
                if entry is None:
                    ufiles[key] = None
                    continue
                rel = _copy(pathlib.Path(entry["path"]), stage, f"{udir}/eval/{u.target}/{fname}", files)
                if files[rel] != entry["sha256"]:
                    raise Refusal(f"{u.label}: {fname} changed after it was verified")
                ufiles[key] = rel
            entries.append({"index": nn, "dir": udir, "host": u.host, "unit": u.unit, "arm": u.arm, "seed": u.seed,
                            "target": u.target, "complete_sha256": u.complete_sha256, "job_sha256": u.job_sha256,
                            "completed_utc": u.completed_utc, "manifest_sha256": u.manifest_sha256, "files": ufiles})
        out_groups.append({"prepared": {"name": g.name, "dir": pdir, "manifest_sha256": g.manifest_sha256,
                                        "dev_bank_sha256": g.dev_bank_sha256},
                           "expect": dict(g.expect), "units": entries})
    resume_entry = None
    if resume is not None:
        rel = _copy(pathlib.Path(resume["path"]), stage, "resume/harmbench.jsonl", files)
        if files[rel] != resume["sha256"]:
            raise Refusal("the resume cache changed after it was checked")
        resume_entry = {"path": rel, "sha256": resume["sha256"], "from_tag": resume.get("from_tag")}
    manifest = {"kind": KIND, "version": VERSION, "tag": tag, "judge": dict(HARMBENCH), "device": "cuda",
                "files": dict(sorted(files.items())), "groups": out_groups, "resume_cache": resume_entry,
                "limit": limit}
    (stage / MANIFEST_NAME).write_bytes(canonical_bytes(manifest))
    return manifest


def write_tar(stage: pathlib.Path, tar_path: pathlib.Path) -> str:
    """A deterministic tar.gz of stage/ under TOP/; returns its SHA-256."""
    stage, tar_path = pathlib.Path(stage), pathlib.Path(tar_path)
    if tar_path.exists():
        raise Refusal(f"{tar_path} exists")
    buf = io.BytesIO()
    with gzip.GzipFile(filename="", mode="wb", fileobj=buf, mtime=0) as gz:
        with tarfile.open(fileobj=gz, mode="w", format=tarfile.PAX_FORMAT) as tar:
            for path in sorted(p for p in stage.rglob("*") if p.is_file()):
                info = tarfile.TarInfo(f"{TOP}/{path.relative_to(stage).as_posix()}")
                info.size, info.mtime, info.mode = path.stat().st_size, 0, 0o644
                info.uid = info.gid = 0
                info.uname = info.gname = ""
                with open(path, "rb") as fh:
                    tar.addfile(info, fh)
    data = buf.getvalue()
    tar_path.parent.mkdir(parents=True, exist_ok=True)
    tar_path.write_bytes(data)
    return sha256_bytes(data)


# ---------------------------------------------------------------- pod side: verification and units

def load_manifest(root: pathlib.Path) -> tuple[dict, str]:
    data = (pathlib.Path(root) / MANIFEST_NAME).read_bytes()
    try:
        manifest = json.loads(data)
    except ValueError:
        raise Refusal(f"{MANIFEST_NAME} is not JSON") from None
    if not isinstance(manifest, dict) or manifest.get("kind") != KIND or manifest.get("version") != VERSION:
        raise Refusal(f"{MANIFEST_NAME} is not a {KIND} version {VERSION}")
    if manifest.get("judge") != HARMBENCH:
        raise Refusal(f"{MANIFEST_NAME} names another judge")
    return manifest, sha256_bytes(data)


def _json(path: pathlib.Path, what: str):
    try:
        return json.loads(path.read_bytes())
    except ValueError:
        raise Refusal(f"{what}: {path.name} is not JSON") from None


def verify_bundle(root: pathlib.Path, known: dict | None = None) -> dict:
    """Refuses unless root holds exactly the manifest's files with their SHA-256 and every unit and prepared set agrees
    with its records (see the module text). Returns the manifest, with "manifest_sha256" added."""
    known = KNOWN_PREPARED if known is None else known
    root = pathlib.Path(root)
    manifest, msha = load_manifest(root)
    listed = manifest.get("files")
    if not isinstance(listed, dict) or not listed:
        raise Refusal(f"{MANIFEST_NAME} lists no files")
    on_disk = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - {MANIFEST_NAME}
    if on_disk != set(listed):
        raise Refusal(f"the bundle holds {len(on_disk)} files, its manifest lists {len(listed)}; unlisted "
                      f"{sorted(on_disk - set(listed))[:5]}, absent {sorted(set(listed) - on_disk)[:5]}")
    for rel, digest in sorted(listed.items()):
        if sha256_file(root / rel) != digest:
            raise Refusal(f"bundle file {rel} does not match its SHA-256")
    seen = set()
    for g in manifest.get("groups") or []:
        p = g["prepared"]
        if known.get(p["name"]) != p["manifest_sha256"]:
            raise Refusal(f"prepared set {p['name']!r} with manifest {str(p['manifest_sha256'])[:16]} is not pinned")
        pdir = root / p["dir"]
        if (pdir / "manifest.sha256").read_text(encoding="utf-8").strip() != p["manifest_sha256"]:
            raise Refusal(f"prepared set {p['name']}: manifest.sha256 is not its pinned manifest")
        if listed.get(f"{p['dir']}/{DEV_BANK}") != p["dev_bank_sha256"]:
            raise Refusal(f"prepared set {p['name']}: the dev bank does not have its recorded SHA-256")
        for e in g["units"]:
            label = f"{e['host']}/{e['unit']}"
            if e["complete_sha256"] in seen:
                raise Refusal(f"{label}: one attempt listed twice")
            seen.add(e["complete_sha256"])
            udir = root / e["dir"]
            if listed.get(f"{e['dir']}/COMPLETE.json") != e["complete_sha256"]:
                raise Refusal(f"{label}: COMPLETE.json does not have the unit's SHA-256")
            if listed.get(f"{e['dir']}/job.json") != e["job_sha256"]:
                raise Refusal(f"{label}: job.json does not have the unit's SHA-256")
            complete, job = _json(udir / "COMPLETE.json", label), _json(udir / "job.json", label)
            if not isinstance(complete, dict) or not isinstance(job, dict):
                raise Refusal(f"{label}: COMPLETE.json or job.json is not an object")
            if complete.get("complete") is not True or complete.get("job_sha256") != e["job_sha256"]:
                raise Refusal(f"{label}: COMPLETE.json is not complete or names another job.json")
            if (job.get("kind") != "run-one" or job.get("evaluate_bank") != "dev"
                    or job.get("target_checkpoint") != e["target"] or job.get("arm") != e["arm"]
                    or job.get("seed") != e["seed"] or job.get("manifest_sha256") != e["manifest_sha256"]
                    or e["manifest_sha256"] != p["manifest_sha256"]):
                raise Refusal(f"{label}: job.json differs from the unit's record (kind, bank, target, arm, seed, manifest)")
            cfiles = complete.get("files") if isinstance(complete.get("files"), dict) else {}
            for key, rel in (e.get("files") or {}).items():
                if rel is None:
                    continue
                if key not in EVAL_FILES or rel != f"{e['dir']}/eval/{e['target']}/{EVAL_FILES[key]}":
                    raise Refusal(f"{label}: unexpected file entry {key}")
                if cfiles.get(f"eval/{e['target']}/{EVAL_FILES[key]}") != listed.get(rel):
                    raise Refusal(f"{label}: {EVAL_FILES[key]} is not the file COMPLETE.json lists")
            if (e.get("files") or {}).get("generations") is None:
                raise Refusal(f"{label}: no generations.jsonl")
    resume = manifest.get("resume_cache")
    if resume is not None and listed.get(resume.get("path")) != resume.get("sha256"):
        raise Refusal("the resume cache does not have its recorded SHA-256")
    return {**manifest, "manifest_sha256": msha}


def pod_groups(root: pathlib.Path, manifest: dict) -> list[Group]:
    """units.Unit objects on the pod's paths, per prepared set (after verify_bundle)."""
    root = pathlib.Path(root).absolute()
    listed = manifest["files"]
    out = []
    for g in manifest["groups"]:
        p = g["prepared"]
        units = []
        for e in g["units"]:
            files = {key: (None if rel is None else {"path": str(root / rel), "sha256": listed[rel]})
                     for key, rel in e["files"].items()}
            units.append(Unit(host=e["host"], unit=e["unit"], path=root / e["dir"], kind="run-one", arm=e["arm"],
                              seed=e["seed"], target=e["target"], complete_sha256=e["complete_sha256"],
                              job_sha256=e["job_sha256"], completed_utc=e["completed_utc"],
                              manifest_sha256=e["manifest_sha256"], files=files))
        out.append(Group(root / p["dir"], p["manifest_sha256"], p["dev_bank_sha256"], p["name"], units,
                         dict(g["expect"])))
    return out
