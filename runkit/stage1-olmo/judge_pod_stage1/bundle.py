"""The stage-1 judge bundle's pod-side bundle.py (round 30; addendum §30 gap 4; the lead's R1 and R5; stdlib only).

Gate B's judge route verifies each unit on the pod with scripts/gate_b_mac_judges/pod/bundle.py _verify_unit, which
wants job.json kind "run-one", a target_checkpoint and an arm (bundle.py:400-404). A B10 evaluation unit (job.json kind
"stage1-eval-adapter", B10H §9 note 3) has "checkpoint" and no arm: its arm label comes from its mode and, for an
external transform, its unit folder (eval_adapter.py:126-129; judge_units_stage1.py). So the pod refused it after the
create. Gate B's files stay byte-identical (R1: the side paper's screen pins them), so the stage-1 wrapper
(judge_units_stage1.py launch) ships, only when a launch holds a B10 unit:

    bundle/tool/pod/bundle_gateb.py     Gate B's pod/bundle.py, byte for byte
    bundle/tool/pod/bundle.py           this file

A bundle without a B10 unit is Gate B's bundle exactly (this file is not shipped). On the pod, pod_job.py's
``import bundle`` runs this file as module "bundle": it imports bundle_gateb, replaces only its _verify_unit by
``verify_unit`` below, and puts bundle_gateb in sys.modules["bundle"], so pod_job.py, verify_bundle, pod_groups and
every other name are Gate B's own. ``verify_unit`` hands every unit whose staged job.json is not a B10 job to Gate B's
_verify_unit unchanged (so a run-one unit is verified exactly as before, and any other kind is refused as before), and
verifies a B10 unit with Gate B's checks in B10's terms: COMPLETE.json and job.json at the unit's SHA-256, COMPLETE.json
complete and naming job.json's SHA-256, job.json kind stage1-eval-adapter, evaluate_bank dev, checkpoint = the unit's
target (e1), seed = the unit's, manifest_sha256 = the unit's and its prepared set's, the arm label rule (b10_label)
giving the unit's arm, and each eval file the one COMPLETE.json lists. On the Mac, judge_units_stage1.py imports this
file under another name for b10_label (the one implementation of the label rule) and nothing is patched.
"""
from __future__ import annotations

import json
import pathlib
import sys

B10_KIND = "stage1-eval-adapter"
B10_CHECKPOINT = "e1"
B10_BANK = "dev"
SAFE_LORA_POINTS = ("default", "conditional", "certify")   # the job runner's job-I/eval-<point> folders (J17)
GATE_B_MODULE = "bundle_gateb"                              # Gate B's pod/bundle.py, shipped beside this file


def b10_label(job: dict, unit_rel: str = "") -> str | None:
    """The arm label of a B10 unit; None for an external unit whose folder names no Safe LoRA point."""
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


def b10_entry_problem(job, entry: dict, manifest_sha256: str) -> str | None:
    """Why a B10 unit's staged job.json disagrees with its bundle manifest entry (None when it agrees)."""
    if not isinstance(job, dict) or job.get("kind") != B10_KIND:
        return "job.json is not a B10 evaluation job"
    seed = job.get("seed")
    label = b10_label(job, entry.get("unit") or "")
    if (job.get("evaluate_bank") != B10_BANK or job.get("checkpoint") != entry.get("target")
            or entry.get("target") != B10_CHECKPOINT or not isinstance(seed, int) or isinstance(seed, bool)
            or seed != entry.get("seed") or job.get("manifest_sha256") != entry.get("manifest_sha256")
            or entry.get("manifest_sha256") != manifest_sha256 or label is None or label != entry.get("arm")):
        return "job.json differs from the unit's record (kind, bank, checkpoint, seed, manifest, arm label)"
    return None


def make_verify_unit(gb):
    """Gate B's module ``gb`` -> its _verify_unit with B10 units accepted (module text)."""
    gate_b_verify_unit = gb._verify_unit

    def verify_unit(root, e, listed, manifest_sha256):
        udir = pathlib.Path(root) / e["dir"]
        job_path = udir / "job.json"
        job = None
        if listed.get(f"{e['dir']}/job.json") == e.get("job_sha256") and job_path.is_file():
            try:
                job = json.loads(job_path.read_bytes())
            except ValueError:
                job = None
        if not (isinstance(job, dict) and job.get("kind") == B10_KIND):
            return gate_b_verify_unit(root, e, listed, manifest_sha256)
        label = f"{e['host']}/{e['unit']}"
        if listed.get(f"{e['dir']}/COMPLETE.json") != e["complete_sha256"]:
            raise gb.Refusal(f"{label}: COMPLETE.json does not have the unit's SHA-256")
        complete = gb._json(udir / "COMPLETE.json", label)
        if not isinstance(complete, dict) or complete.get("complete") is not True or \
                complete.get("job_sha256") != e["job_sha256"]:
            raise gb.Refusal(f"{label}: COMPLETE.json is not complete or names another job.json")
        problem = b10_entry_problem(job, e, manifest_sha256)
        if problem:
            raise gb.Refusal(f"{label}: {problem}")
        cfiles = complete.get("files") if isinstance(complete.get("files"), dict) else {}
        for key, rel in (e.get("files") or {}).items():
            if rel is None:
                continue
            if key not in gb.EVAL_FILES or rel != f"{e['dir']}/eval/{e['target']}/{gb.EVAL_FILES[key]}":
                raise gb.Refusal(f"{label}: unexpected file entry {key}")
            if cfiles.get(f"eval/{e['target']}/{gb.EVAL_FILES[key]}") != listed.get(rel):
                raise gb.Refusal(f"{label}: {gb.EVAL_FILES[key]} is not the file COMPLETE.json lists")
        if (e.get("files") or {}).get("generations") is None:
            raise gb.Refusal(f"{label}: no generations.jsonl")

    verify_unit.gate_b = gate_b_verify_unit
    return verify_unit


def install(gb) -> None:
    """Gate B's bundle module with B10 units accepted on the pod (only _verify_unit is replaced)."""
    gb._verify_unit = make_verify_unit(gb)


if __name__ == "bundle":                    # on the pod: pod_job.py's `import bundle` (module text)
    _here = str(pathlib.Path(__file__).resolve().parent)
    if _here not in sys.path:
        sys.path.insert(0, _here)
    import importlib
    _gb = importlib.import_module(GATE_B_MODULE)
    install(_gb)
    sys.modules["bundle"] = _gb
