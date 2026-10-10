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

The judge (revised 9 October 2026, 12:45 UTC, clock checked): every function takes judge="harmbench" (the default; the
HarmBench bundle, its manifest and its checks are exactly as before) or "granite". A Granite bundle checks and judges
the greedy answers only (judging.check_units with the greedy mode and no equal-prompt-set rule, as granite_files.py
does), its manifest names common.GRANITE and its tokenizer folder ("tokenizer_dir": "granite-tokenizer"), and it holds
also bundle/tool/granite_files.py, bundle/tool/pod/{granite_pod.py, pod_run_granite.sh, granite-requirements.txt}, the
Mac's Granite tokenizer folder (granite_pod.TOK_FILES, every file checked against its pin when it is copied and again
by verify_bundle), and with --resume-from also resume/granite.jsonl and resume/granite-inputs.jsonl.

The known-answer gate (revised 9 October 2026, 15:07 UTC, clock checked): a Granite bundle's manifest always has
"known_answers": null when the launch disabled the gate (--no-known-answer-gate), else the gate's parts, which
plan_known_answers checks on the Mac (the reference granite_pod.KNOWN_ANSWERS_FILE by its pinned SHA-256 and counts; the
unit granite_pod.KNOWN_ANSWER_UNIT_DIR found and verified as the Mac judges find it, with the reference's COMPLETE.json
SHA-256 and its 200 greedy answers equal by prompt id and SHA-256 to the reference's; its prepared set pinned by the
reference's name and manifest; judging.check_units; every prompt id in the bank) and stage_bundle copies:

    bundle/known/granite-known-answers.json                            the reference (ids, answer SHA-256, labels)
    bundle/known/prepared/<name>/{manifest.sha256,banks/dev.jsonl}     the unit's dev bank
    bundle/known/unit/{job.json,COMPLETE.json,eval/<target>/...}       the unit's answers and guard records

verify_bundle checks them as it checks the groups (and the reference by its pinned SHA-256 again); pod_known_unit gives
the pod the unit. The unit may also be one of the groups' units (its own copy); it never enters the cache.
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
from common import GRANITE, HARMBENCH, HEX64, Refusal, bank_prompts, canonical_bytes, sha256_bytes, sha256_file  # noqa: E402
from units import EVAL_FILES, Unit, enumerate_units, load_items  # noqa: E402

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
                  "prepared-kt-dolly-llama3": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a",
                  "prepared-kt-dolly": "9247c4bbccf212b02be7f221e2ee451d17ebf643a39a44db6e3bed6fb4d750f2",   # Qwen2.5 1.5B and 7B (the Side Project's pairs; GI IV, 8 Oct 23:35 UTC)
                  # the fiction side study's final sets (prepared by GI V on 9 Oct 21:33 UTC; their dev bank equals the olmo2 one)
                  "prepared-side-fiction-dark-olmo2": "c57b56ceaf5c53fd3d6a9cabf97bdbb4f1a039fe5ba0536572df28b0200fb5a2",
                  "prepared-side-fiction-light-olmo2": "8f6493250d93b3b50c36f5ac1409c3d9a2b2850a98b2cec86ea4731768652f24"}
DEV_BANK = "banks/dev.jsonl"
Group = collections.namedtuple("Group", "prepared_dir manifest_sha256 dev_bank_sha256 name units expect")
# The Granite judge (judge="granite"): its modules, its modes and its tokenizer folder in the bundle.
JUDGE_KEYS = ("harmbench", "granite")
JUDGE_MODES = {"harmbench": MODES, "granite": ("greedy",)}
GRANITE_TOOL_FILES = TOOL_FILES + ("granite_files.py",)
GRANITE_POD_FILES = POD_FILES + ("granite_pod.py", "pod_run_granite.sh", "granite-requirements.txt")
TOKENIZER_DIR = "granite-tokenizer"
RESUME_FILES = {"harmbench": "resume/harmbench.jsonl", "granite": "resume/granite.jsonl"}
RESUME_INPUTS = "resume/granite-inputs.jsonl"
KNOWN_DIR = "known"                                                       # the known-answer gate's files (Granite)
KNOWN_REFERENCE = f"{KNOWN_DIR}/granite-known-answers.json"
KNOWN_UNIT_DIR = f"{KNOWN_DIR}/unit"


def identity(judge: str) -> dict:
    """The judge identity of a judge key (common.HARMBENCH or common.GRANITE)."""
    if judge not in JUDGE_KEYS:
        raise Refusal(f"unknown judge {judge!r}; one of {list(JUDGE_KEYS)}")
    return HARMBENCH if judge == "harmbench" else GRANITE


def manifest_judge(root: pathlib.Path) -> str:
    """"granite" when the bundle's manifest names common.GRANITE, else "harmbench" (also when it cannot be read: the
    HarmBench path's own checks then refuse it as before)."""
    try:
        manifest = json.loads((pathlib.Path(root) / MANIFEST_NAME).read_bytes())
    except (OSError, ValueError):
        return "harmbench"
    return "granite" if isinstance(manifest, dict) and manifest.get("judge") == GRANITE else "harmbench"


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


def plan_groups(units: list[Unit], prepared_dirs, expect: dict, known: dict | None = None,
                judge: str = "harmbench") -> list[Group]:
    """Units grouped by job.json manifest_sha256, each with its prepared set, after the Mac run's checks: check_units
    (counts, guard ids, manifest, equal prompt-id sets within the group) and every answer's prompt id in the bank.
    judge "granite": the greedy mode only and no equal-prompt-set rule (granite_files.py's check)."""
    modes, judge_ident = JUDGE_MODES[judge], identity(judge)
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
        judging.check_units(members, modes, expect, judge == "harmbench", manifest)
        prompts = bank_prompts(d, manifest)
        empty = Cache(pathlib.Path("/nonexistent/judge-pod-plan.jsonl"), judge_ident)    # never written
        judging.todo_items(members, modes, prompts, empty, with_text=False)
        groups.append(Group(d, manifest, ident["dev_bank_sha256"], ident["name"], members, dict(expect)))
    return groups


def plan_known_answers() -> dict:
    """The known-answer gate's parts for a Granite bundle, checked on the Mac (see the module text): the reference
    (granite_pod.load_known_answers), the unit, its prepared set's identity and its counts. Hashes, ids and counts
    only."""
    import granite_pod
    reference = granite_pod.load_known_answers(granite_pod.KNOWN_ANSWERS_FILE)
    units, _ = enumerate_units((), [granite_pod.KNOWN_ANSWER_UNIT_DIR])
    (u,) = units
    if u.complete_sha256 != reference["unit"]["complete_sha256"]:
        raise Refusal(f"{u.label}: COMPLETE.json {u.complete_sha256[:16]} is not the known-answer reference's unit "
                      f"{reference['unit']['complete_sha256'][:16]}")
    pin = reference["prepared"]
    prepared_dir = pathlib.Path(granite_pod.KNOWN_ANSWER_PREPARED_DIR)
    ident = prepared_identity(prepared_dir, {pin["name"]: pin["manifest_sha256"]})
    judging.check_units([u], ("greedy",), {"greedy": granite_pod.KNOWN_ANSWER_N}, False, ident["manifest_sha256"])
    prompts = bank_prompts(prepared_dir, ident["manifest_sha256"])
    items = load_items(u, "greedy")
    granite_pod.check_known_items(reference, [(it.prompt_id, it.answer_sha256) for it in items])
    absent = [it.prompt_id for it in items if it.prompt_id not in prompts]
    if absent:
        raise Refusal(f"{u.label}: {len(absent)} known-answer prompt id(s) are not in the bank (first: {absent[0]})")
    return {"reference_path": pathlib.Path(granite_pod.KNOWN_ANSWERS_FILE),
            "reference_sha256": sha256_file(granite_pod.KNOWN_ANSWERS_FILE), "unit": u,
            "prepared": {**ident, "dir": prepared_dir}, "n": len(items),
            "mac_yes": sum(r["label"] == "yes" for r in reference["items"])}


# ---------------------------------------------------------------- Mac side: the bundle

def _copy(src: pathlib.Path, stage: pathlib.Path, rel: str, files: dict) -> str:
    dst = stage / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    files[rel] = sha256_file(dst)
    return rel


def _stage_unit(u: Unit, stage: pathlib.Path, udir: str, index: str, files: dict) -> dict:
    """One verified unit's job.json, COMPLETE.json and eval files into stage/udir (each hash checked again); returns
    its manifest entry."""
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
    return {"index": index, "dir": udir, "host": u.host, "unit": u.unit, "arm": u.arm, "seed": u.seed,
            "target": u.target, "complete_sha256": u.complete_sha256, "job_sha256": u.job_sha256,
            "completed_utc": u.completed_utc, "manifest_sha256": u.manifest_sha256, "files": ufiles}


def stage_bundle(groups: list[Group], stage: pathlib.Path, tag: str, tool_dir: pathlib.Path,
                 resume: dict | None = None, limit: int | None = None, judge: str = "harmbench",
                 known_answers: dict | None = None) -> dict:
    """Writes the bundle's files into stage/ (which must not exist) and returns the job manifest (also written).
    judge "granite" adds the Granite modules and the tokenizer folder (each file checked against its pin), and the
    known-answer gate's files when `known_answers` (plan_known_answers()) is given."""
    if known_answers is not None and judge != "granite":
        raise Refusal("the known-answer gate is the Granite judge's")
    ident = identity(judge)
    granite = judge == "granite"
    stage = pathlib.Path(stage)
    if stage.exists():
        raise Refusal(f"{stage} exists; the bundle is staged into a new folder")
    stage.mkdir(parents=True)
    files: dict[str, str] = {}
    for name in (GRANITE_TOOL_FILES if granite else TOOL_FILES):
        _copy(tool_dir / name, stage, f"tool/{name}", files)
    for name in (GRANITE_POD_FILES if granite else POD_FILES):
        _copy(tool_dir / "pod" / name, stage, f"tool/pod/{name}", files)
    if granite:
        import granite_pod
        for name, (size, digest) in sorted(granite_pod.TOK_FILES.items()):
            rel = _copy(pathlib.Path(granite_pod.MAC_TOKENIZER) / name, stage, f"{TOKENIZER_DIR}/{name}", files)
            if files[rel] != digest or (stage / rel).stat().st_size != size:
                raise Refusal(f"Granite tokenizer file {name} does not have its pinned size and SHA-256")
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
            entries.append(_stage_unit(u, stage, f"units/{nn}", nn, files))
        out_groups.append({"prepared": {"name": g.name, "dir": pdir, "manifest_sha256": g.manifest_sha256,
                                        "dev_bank_sha256": g.dev_bank_sha256},
                           "expect": dict(g.expect), "units": entries})
    resume_entry = inputs_entry = None
    if resume is not None:
        rel = _copy(pathlib.Path(resume["path"]), stage, RESUME_FILES[judge], files)
        if files[rel] != resume["sha256"]:
            raise Refusal("the resume cache changed after it was checked")
        resume_entry = {"path": rel, "sha256": resume["sha256"], "from_tag": resume.get("from_tag")}
        if granite and resume.get("inputs_path") is not None:
            rel = _copy(pathlib.Path(resume["inputs_path"]), stage, RESUME_INPUTS, files)
            if files[rel] != resume["inputs_sha256"]:
                raise Refusal("the resume inputs file changed after it was checked")
            inputs_entry = {"path": rel, "sha256": resume["inputs_sha256"]}
    known_entry = None
    if known_answers is not None:
        ref = _copy(pathlib.Path(known_answers["reference_path"]), stage, KNOWN_REFERENCE, files)
        if files[ref] != known_answers["reference_sha256"]:
            raise Refusal("the known-answer reference changed after it was checked")
        kp = known_answers["prepared"]
        kpdir = f"{KNOWN_DIR}/prepared/{kp['name']}"
        _copy(pathlib.Path(kp["dir"]) / "manifest.sha256", stage, f"{kpdir}/manifest.sha256", files)
        _copy(pathlib.Path(kp["dir"]) / DEV_BANK, stage, f"{kpdir}/{DEV_BANK}", files)
        if files[f"{kpdir}/{DEV_BANK}"] != kp["dev_bank_sha256"]:
            raise Refusal(f"prepared set {kp['name']}: {DEV_BANK} changed while the bundle was built")
        known_entry = {"reference": ref, "reference_sha256": known_answers["reference_sha256"],
                       "prepared": {"name": kp["name"], "dir": kpdir, "manifest_sha256": kp["manifest_sha256"],
                                    "dev_bank_sha256": kp["dev_bank_sha256"]},
                       "unit": _stage_unit(known_answers["unit"], stage, KNOWN_UNIT_DIR, "known", files),
                       "items": known_answers["n"], "mac_yes": known_answers["mac_yes"]}
    manifest = {"kind": KIND, "version": VERSION, "tag": tag, "judge": dict(ident), "device": "cuda",
                "files": dict(sorted(files.items())), "groups": out_groups, "resume_cache": resume_entry,
                "limit": limit}
    if granite:
        manifest.update(tokenizer_dir=TOKENIZER_DIR, resume_inputs=inputs_entry, known_answers=known_entry)
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
    if manifest.get("judge") not in (HARMBENCH, GRANITE):
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
            _verify_unit(root, e, listed, p["manifest_sha256"])
    resume = manifest.get("resume_cache")
    if resume is not None and listed.get(resume.get("path")) != resume.get("sha256"):
        raise Refusal("the resume cache does not have its recorded SHA-256")
    if manifest.get("judge") == GRANITE:
        _verify_granite(root, manifest, listed)
    return {**manifest, "manifest_sha256": msha}


def _verify_unit(root: pathlib.Path, e: dict, listed: dict, manifest_sha256: str) -> None:
    """One unit entry against its listed files and its records (verify_bundle; see the module text); its job.json
    must name `manifest_sha256` (its prepared set's)."""
    label = f"{e['host']}/{e['unit']}"
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
            or e["manifest_sha256"] != manifest_sha256):
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


def _verify_granite(root: pathlib.Path, manifest: dict, listed: dict) -> None:
    """A Granite bundle: its tokenizer folder holds exactly the pinned files (granite_pod.TOK_FILES), its resume
    files are the listed ones, and its known-answer gate (null, or the gate's parts: _verify_known)."""
    import granite_pod
    if manifest.get("tokenizer_dir") != TOKENIZER_DIR:
        raise Refusal(f"{MANIFEST_NAME} names no Granite tokenizer folder {TOKENIZER_DIR}")
    shipped = {rel[len(TOKENIZER_DIR) + 1:]: d for rel, d in listed.items() if rel.startswith(TOKENIZER_DIR + "/")}
    pinned = {name: digest for name, (_, digest) in granite_pod.TOK_FILES.items()}
    if shipped != pinned:
        raise Refusal(f"the bundle's Granite tokenizer folder is not the pinned one ({len(shipped)} files, "
                      f"{len(pinned)} pinned)")
    resume = manifest.get("resume_cache")
    if resume is not None and resume.get("path") != RESUME_FILES["granite"]:
        raise Refusal("the Granite resume cache is not resume/granite.jsonl")
    inputs = manifest.get("resume_inputs")
    if inputs is not None and (inputs.get("path") != RESUME_INPUTS or listed.get(RESUME_INPUTS) != inputs.get("sha256")):
        raise Refusal("the Granite resume inputs file does not have its recorded SHA-256")
    if "known_answers" not in manifest:
        raise Refusal(f"{MANIFEST_NAME} does not say whether the known-answer gate runs (known_answers)")
    if manifest["known_answers"] is not None:
        _verify_known(root, manifest["known_answers"], listed)


def _verify_known(root: pathlib.Path, ka, listed: dict) -> None:
    """The known-answer gate's files: the reference with its pinned SHA-256 and counts (granite_pod.load_known_answers),
    the prepared set the reference names (its manifest.sha256 and the recorded dev bank SHA-256), and the unit with the
    reference's COMPLETE.json SHA-256, checked as a group's unit is (_verify_unit)."""
    import granite_pod
    if not isinstance(ka, dict) or ka.get("reference") != KNOWN_REFERENCE or not isinstance(ka.get("prepared"), dict) \
            or not isinstance(ka.get("unit"), dict):
        raise Refusal(f"{MANIFEST_NAME}: the known-answer gate's entry is not the gate's layout")
    if listed.get(KNOWN_REFERENCE) != ka.get("reference_sha256"):
        raise Refusal("the known-answer reference does not have its recorded SHA-256")
    reference = granite_pod.load_known_answers(root / KNOWN_REFERENCE)
    p, pin = ka["prepared"], reference["prepared"]
    if (p.get("name"), p.get("manifest_sha256"), p.get("dir")) != (pin["name"], pin["manifest_sha256"],
                                                                     f"{KNOWN_DIR}/prepared/{pin['name']}"):
        raise Refusal(f"the known-answer prepared set is not the reference's {pin['name']} "
                      f"({pin['manifest_sha256'][:16]})")
    if (root / p["dir"] / "manifest.sha256").read_text(encoding="utf-8").strip() != p["manifest_sha256"]:
        raise Refusal(f"prepared set {p['name']} (known answers): manifest.sha256 is not its pinned manifest")
    if listed.get(f"{p['dir']}/{DEV_BANK}") != p.get("dev_bank_sha256"):
        raise Refusal(f"prepared set {p['name']} (known answers): the dev bank does not have its recorded SHA-256")
    e = ka["unit"]
    if e.get("dir") != KNOWN_UNIT_DIR or e.get("complete_sha256") != reference["unit"]["complete_sha256"]:
        raise Refusal("the known-answer unit is not the reference's (COMPLETE.json SHA-256)")
    _verify_unit(root, e, listed, p["manifest_sha256"])


def _pod_unit(root: pathlib.Path, e: dict, listed: dict) -> Unit:
    files = {key: (None if rel is None else {"path": str(root / rel), "sha256": listed[rel]})
             for key, rel in e["files"].items()}
    return Unit(host=e["host"], unit=e["unit"], path=root / e["dir"], kind="run-one", arm=e["arm"], seed=e["seed"],
                target=e["target"], complete_sha256=e["complete_sha256"], job_sha256=e["job_sha256"],
                completed_utc=e["completed_utc"], manifest_sha256=e["manifest_sha256"], files=files)


def pod_groups(root: pathlib.Path, manifest: dict) -> list[Group]:
    """units.Unit objects on the pod's paths, per prepared set (after verify_bundle)."""
    root = pathlib.Path(root).absolute()
    listed = manifest["files"]
    out = []
    for g in manifest["groups"]:
        p = g["prepared"]
        units = [_pod_unit(root, e, listed) for e in g["units"]]
        out.append(Group(root / p["dir"], p["manifest_sha256"], p["dev_bank_sha256"], p["name"], units,
                         dict(g["expect"])))
    return out


def pod_known_unit(root: pathlib.Path, manifest: dict) -> tuple[Unit, pathlib.Path, str]:
    """The known-answer gate's unit on the pod's paths, its prepared set's folder and manifest SHA-256 (after
    verify_bundle; a Granite manifest whose known_answers is not null)."""
    root = pathlib.Path(root).absolute()
    ka = manifest["known_answers"]
    unit = _pod_unit(root, ka["unit"], manifest["files"])
    return unit, root / ka["prepared"]["dir"], ka["prepared"]["manifest_sha256"]
