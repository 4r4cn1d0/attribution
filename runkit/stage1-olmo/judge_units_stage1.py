"""The stage-1 judge wrapper (B15, brief §3 J19, §6 new item 8; REV4 §10.6 step 9; stdlib only; administrative).

    python3.11 judge_units_stage1.py list (--run-root DIR)... (--unit DIR)... [--targets init e1]
    python3.11 judge_units_stage1.py launch -- ARGS...        scripts/gate_b_mac_judges/pod/judge_pod.py ARGS with
                                                              the stage-1 enumeration in place of Gate B's
    python3.11 judge_units_stage1.py check-devices --contrast NAME=LABEL,LABEL,... --record LABEL=RUN_RECORD ...

Gate B's judges enumerate units with scripts/gate_b_mac_judges/units.py, which judges only engine run-one units and
skips everything else. That file is Gate B's and stays unchanged. This wrapper adds the B10 evaluation units (job.json
kind "stage1-eval-adapter", B10H §9 note 3): such a unit is judgeable when its job.json says the dev bank and
checkpoint e1, its COMPLETE.json says complete and names job.json's SHA-256, and COMPLETE.json lists exactly the files
on disk under eval/e1/ with matching SHA-256 (fail-closed, as units.py: a stray file refuses the unit). Its arm label
is "ref-<mode>" with the scale ("ref-scale-0.9"), the prefix ("ref-prefix") or the external transform and its point
("ref-external-safe_lora-default": B10's job.json names no point, so the point comes from the kit's unit folder
job-I/eval-<point>; another folder name refuses); certify is "ref-certify". Every other folder goes to units.read_unit unchanged, so an
engine unit is judged exactly as Gate B judges it. ``launch`` runs judge_pod.main with units.enumerate_units (and the
names judge_pod and bundle imported from units) replaced by this module's enumeration, for that process only; no file
of scripts/gate_b_mac_judges is written.

One device type per contrast (REV4 §10.6 step 9): ``check-devices`` reads each unit's judge run record (the judge
pod's run record: device and environment GPU name) and refuses a contrast whose units were judged on more than one
device type (device, GPU name), or a unit without a record. A reused Gate A or wave-0a unit judged on another device
type must be judged again on the stage-1 judge pods (§8 Q14).
"""
from __future__ import annotations

import argparse
import contextlib
import dataclasses
import importlib.util
import json
import pathlib
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JUDGES = ROOT / "scripts" / "gate_b_mac_judges"
B10_KIND = "stage1-eval-adapter"
B10_CHECKPOINT = "e1"
SAFE_LORA_POINTS = ("default", "conditional", "certify")   # the job runner's job-I/eval-<point> folders (J17)
_GATE_B = {}                                     # Gate B's own enumerate_units while stage1_enumeration patches it


def gate_b_units():
    """scripts/gate_b_mac_judges/units.py, imported as ``units`` (judge_pod and bundle import it by that name)."""
    if str(JUDGES) not in sys.path:
        sys.path.insert(0, str(JUDGES))
    import units  # noqa: E402
    return units


def b10_label(job: dict, unit_rel: str = "") -> str | None:
    """The arm label; None for an external unit whose folder names no Safe LoRA point."""
    mode = job.get("mode")
    if mode == "scale":
        return f"ref-scale-{job.get('adapter_scale')}"
    if mode == "external":
        ext = job.get("external")
        name = ext.get("name") if isinstance(ext, dict) else ext
        folder = pathlib.PurePosixPath(unit_rel).name
        point = folder[len("eval-"):] if folder.startswith("eval-") else None
        return f"ref-external-{name}-{point}" if point in SAFE_LORA_POINTS else None
    return f"ref-{mode}"


def read_b10_unit(path: pathlib.Path, host: str, unit_rel: str):
    """(units.Unit, None) for a judgeable B10 unit, (None, reason) for a folder that is no B10 unit; Refusal when
    defective (module doc)."""
    units = gate_b_units()
    R = units.Refusal
    path = pathlib.Path(path).absolute()
    label = f"{host}/{unit_rel}"
    if not (path / "job.json").is_file() or not (path / "COMPLETE.json").is_file():
        return None, "not a B10 unit"
    job_bytes, job = units._load_json(path / "job.json", label)
    if not isinstance(job, dict) or job.get("kind") != B10_KIND:
        return None, "not a B10 unit"
    if job.get("evaluate_bank") != units.BANK or job.get("checkpoint") != B10_CHECKPOINT:
        raise R(f"{label}: a B10 unit evaluates the dev bank at e1")
    seed = job.get("seed")
    if not isinstance(seed, int) or isinstance(seed, bool):
        raise R(f"{label}: the B10 job has no integer seed")
    complete_bytes, complete = units._load_json(path / "COMPLETE.json", label)
    if not isinstance(complete, dict) or complete.get("complete") is not True:
        raise R(f"{label}: COMPLETE.json does not say complete")
    job_sha = units.sha256_bytes(job_bytes)
    if complete.get("job_sha256") != job_sha:
        raise R(f"{label}: COMPLETE.json job_sha256 is not job.json's SHA-256")
    listed = complete.get("files")
    if not isinstance(listed, dict):
        raise R(f"{label}: COMPLETE.json has no files list")
    eval_dir = path / "eval" / B10_CHECKPOINT
    if not eval_dir.is_dir():
        raise R(f"{label}: no eval/{B10_CHECKPOINT}/ folder")
    prefix = f"eval/{B10_CHECKPOINT}/"
    named = {k: v for k, v in listed.items() if k.startswith(prefix)}
    on_disk = {p.relative_to(path).as_posix(): p for p in sorted(eval_dir.rglob("*")) if p.is_file()}
    if set(named) != set(on_disk):
        raise R(f"{label}: COMPLETE.json lists {len(named)} files under {prefix}, {len(on_disk)} are on disk")
    hashes = {}
    for rel, p in on_disk.items():
        hashes[rel] = units.sha256_bytes(p.read_bytes())
        if hashes[rel] != named[rel]:
            raise R(f"{label}: {rel} does not match its SHA-256 in COMPLETE.json")
    files = {key: ({"path": str(on_disk[prefix + f]), "sha256": hashes[prefix + f]} if prefix + f in on_disk else None)
             for key, f in units.EVAL_FILES.items()}
    if files["generations"] is None:
        raise R(f"{label}: no {prefix}generations.jsonl")
    arm = b10_label(job, unit_rel)
    if arm is None:
        raise R(f"{label}: an external B10 unit's folder must be eval-<point> (one of {list(SAFE_LORA_POINTS)})")
    return units.Unit(host=host, unit=unit_rel, path=path, kind=B10_KIND, arm=arm, seed=seed,
                      target=B10_CHECKPOINT, complete_sha256=units.sha256_bytes(complete_bytes), job_sha256=job_sha,
                      completed_utc=complete.get("completed_utc"), manifest_sha256=job.get("manifest_sha256"),
                      files=files), None


def enumerate_units(run_roots=(), unit_dirs=(), targets=None):
    """Gate B's enumeration, plus the B10 units (module doc). Same return value: (units, skipped)."""
    units = gate_b_units()
    targets = tuple(targets or units.TARGETS)
    found, skipped, b10_dirs = {}, [], set()
    for root in run_roots:
        for host_dir in units._hosts(root):
            tree = host_dir / "tree"
            for job_file in sorted(tree.rglob("job.json")):
                folder = job_file.parent
                unit, _ = read_b10_unit(folder, host_dir.name, folder.relative_to(tree).as_posix()) \
                    if (folder / "COMPLETE.json").is_file() else (None, None)
                if unit is not None:
                    found[unit.path] = unit
                    b10_dirs.add(folder.absolute())
    explicit_gate_b = []
    for unit_dir in unit_dirs:
        host, rel = units.locate(unit_dir)
        unit, _ = read_b10_unit(pathlib.Path(unit_dir), host, rel)
        if unit is not None:
            found[unit.path] = unit
        else:
            explicit_gate_b.append(unit_dir)
    gate_b = _GATE_B.get("enumerate_units", units.enumerate_units)
    gb_units, gb_skipped = gate_b(run_roots, explicit_gate_b, targets) if (run_roots or explicit_gate_b) else ([], [])
    for s in gb_skipped:
        if not any(str(d).endswith("/" + s["unit"]) for d in b10_dirs):
            skipped.append(s)
    for unit in gb_units:
        found[unit.path] = unit
    by_complete = {}
    for unit in found.values():
        if unit.complete_sha256 in by_complete:
            raise units.Refusal(f"one attempt found at two paths: {by_complete[unit.complete_sha256].path} and {unit.path}")
        by_complete[unit.complete_sha256] = unit
    return sorted(found.values(), key=lambda u: (u.host, u.unit, u.complete_sha256)), skipped


@contextlib.contextmanager
def stage1_enumeration():
    """For one process: units.enumerate_units (which units_from_args calls) and the bundle's imported name point to
    this module's enumeration; restored afterwards. No file is written."""
    units = gate_b_units()
    saved = units.enumerate_units
    bundle = sys.modules.get("bundle")
    saved_bundle = getattr(bundle, "enumerate_units", None) if bundle else None
    _GATE_B["enumerate_units"] = saved
    units.enumerate_units = enumerate_units
    if bundle is not None:
        bundle.enumerate_units = enumerate_units
    try:
        yield
    finally:
        _GATE_B.pop("enumerate_units", None)
        units.enumerate_units = saved
        if bundle is not None:
            bundle.enumerate_units = saved_bundle


def device_type(record: dict) -> tuple:
    env = record.get("environment") or {}
    gpu = env.get("gpu") or env.get("gpu_name") or (env.get("cuda") or {}).get("name") if isinstance(env, dict) else None
    return (record.get("device"), gpu)


def check_devices(contrasts: dict, records: dict) -> dict:
    """{contrast: [unit labels]} and {label: judge run record}: one device type per contrast, else a refusal."""
    units = gate_b_units()
    out = {}
    for name, labels in sorted(contrasts.items()):
        missing = [lab for lab in labels if lab not in records]
        if missing:
            raise units.Refusal(f"contrast {name}: {len(missing)} unit(s) without a judge run record")
        types = sorted({device_type(records[lab]) for lab in labels}, key=repr)
        if len(types) != 1:
            raise units.Refusal(f"contrast {name}: its units were judged on {len(types)} device types; judge them "
                                "again on one (one device per contrast)")
        out[name] = {"device": types[0][0], "gpu": types[0][1], "units": len(labels)}
    return out


def main(argv=None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    units = gate_b_units()
    if argv[:1] == ["launch"]:
        rest = argv[2:] if argv[1:2] == ["--"] else argv[1:]
        spec = importlib.util.spec_from_file_location("judge_pod", JUDGES / "pod" / "judge_pod.py")
        if str(JUDGES / "pod") not in sys.path:
            sys.path.insert(0, str(JUDGES / "pod"))
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        with stage1_enumeration():
            return module.main(rest)
    ap = argparse.ArgumentParser(prog="judge_units_stage1.py")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list")
    units.add_unit_arguments(p)
    c = sub.add_parser("check-devices")
    c.add_argument("--contrast", action="append", required=True, help="NAME=LABEL,LABEL,...")
    c.add_argument("--record", action="append", required=True, help="LABEL=RUN_RECORD.json")
    a = ap.parse_args(argv)
    try:
        if a.command == "list":
            if not a.run_root and not a.unit:
                raise units.Refusal("give at least one --run-root or --unit")
            found, skipped = enumerate_units(a.run_root, a.unit, tuple(a.targets))
            print(json.dumps({"units": [{**u.describe(), "kind": u.kind} for u in found], "skipped": skipped}, indent=1))
            return 0
        contrasts = {s.partition("=")[0]: s.partition("=")[2].split(",") for s in a.contrast}
        records = {s.partition("=")[0]: json.loads(pathlib.Path(s.partition("=")[2]).read_text()) for s in a.record}
        print(json.dumps(check_devices(contrasts, records), indent=1))
        return 0
    except units.Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
