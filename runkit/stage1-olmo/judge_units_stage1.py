"""The stage-1 judge wrapper (B15, brief §3 J19, §6 new item 8; REV4 §10.6 step 9; stdlib only; administrative).

    python3.11 judge_units_stage1.py list (--run-root DIR)... (--unit DIR)... [--targets init e1]
    python3.11 judge_units_stage1.py launch -- ARGS...        scripts/gate_b_mac_judges/pod/judge_pod.py ARGS with
                                                              the stage-1 enumeration in place of Gate B's, the
                                                              launcher's run log not echoed, and (with a B10 unit)
                                                              the stage-1 pod bundle.py shipped
    python3.11 judge_units_stage1.py write-files --judge J --cache C --out DIR (--run-root R)... (--unit U)...
                                     [--complete H]... [--plan P]   Gate B's write_files.write_all inside the stage-1
                                                              enumeration, a ref_train unit labelled from plan.json;
                                                              prints file, unit, status and missing, stale and extra
                                                              counts only
    python3.11 judge_units_stage1.py result TAG [--root DIR] [--hosts DIR]   the judge launch's whitelisted result
                                                              fields, pod minutes and cost, and its record entry
    python3.11 judge_units_stage1.py check-devices --contrast NAME=LABEL,LABEL,... --record LABEL=RUN_RECORD ...
    python3.11 judge_units_stage1.py units-of-block BLOCK --out FILE [--plan P]   (round 32, K5) the block's judged
                                                              units from plan.json, one folder per line (the --unit
                                                              arguments; never --run-root), and their counts

Round 32 (K5; addendum §34 point 7, block B's pre-flight G13): ``units-of-block`` lists a block's judged units from
plan.json by round 31's rule (plan_tool.judge_required_units: the complete, pulled arm, a0_arm and ref_train units,
each B10 reference unit, the block's re-judged pins), each COMPLETE.json present at the SHA-256 plan.json records, so a
block's judge launch never sweeps retrieved/ (--run-root would take block A's and the cert pod's units too).

Round 30 (addendum §30 gaps 3 and 4; the lead's R1, R4, R5). Gate B's judge files stay byte-identical; every change
is here and in judge_pod_stage1/bundle.py:
- ``launch``: judge_pod.RunLog is constructed with its echo off for stage-1 launches, so no "verified" line (each
  unit's yes and unparsed counts) reaches stdout; the log file is kept and sealed (judge-pod-log.jsonl). When the
  launch holds a B10 unit, the bundle ships judge_pod_stage1/bundle.py as tool/pod/bundle.py and Gate B's bundle.py,
  unchanged, as tool/pod/bundle_gateb.py (that module's text), so pod_job.py verify accepts the B10 unit on the pod; a
  bundle without one is Gate B's bundle byte for byte.
- ``write-files``: runs Gate B's write_files.write_all on the stage-1 enumeration (so a B10 unit gets its judge file)
  with an emit that keeps only each line's file, unit label and status, the missing, stale and extra counts per mode,
  and the index line (path, files, index SHA-256): never a harm, yes or unparsed count.
- ``result TAG``: the runbook's step-5 whitelist of tmp/judge-pod/TAG/judge-pod-result.json (exit, bundle, cap, stop,
  run record, pod exit, GPU, complete, answers judged, records, number of units, refusal, tokenizer, the Granite
  gate's pass), the pod minutes and cost from the host record, and the entry plan_tool.py record-judges takes (tag,
  result, run record and bundle SHA-256, exit, judged, complete; Granite: known_answer_passed).

Round 31 (addendum §32 points 1 and 3; K2, K4):
- ``write-files`` labels a trained reference's unit. A ref_train job (recipe G or B+Qi) runs the engine's calibrate
  --arms a0, so its unit is an ordinary engine unit (round1/<seed>-a0-e1-a<n>: job.json kind run-one, evaluate_bank
  dev, target_checkpoint e1, arm a0) that Gate B's enumeration and pod-side _verify_unit judge unchanged (the launch
  keeps job.json's arm, so its bundle is Gate B's). But block B holds up to three a0 units per seed (its a0_arm at
  1105-1107, G and B+Qi at 1102-1107, on separate pods), and Gate B's write_files.py keeps one file per (judge, arm,
  seed, target) in one folder (a second refuses, exit 2). So write-files gives every unit that plan.json (--plan,
  default the kit's plan.json when it exists) records as a complete ref_train job's unit, by its COMPLETE.json
  SHA-256, the arm label "ref-<recipe>" (ref-G, ref-bqi) in its judge file and index entry; a unit so named whose
  job.json is not an engine a0 unit refuses. Units plan.json does not name keep job.json's arm (block A as before).
- ``launch -- bundle`` (the dry check) prints the launcher's bundle record without any count of labels: every key
  whose "_"-separated words include yes, no, unparsed, harm or identical is dropped at any depth (the Granite
  known_answers' mac_yes, Gate B's Mac count of the reference unit's "yes" labels; its rule constants go too); the
  bundle-record.json on disk is unchanged. ``launch -- launch`` prints no record (its run log's echo is off, round 30).

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
import datetime as dt
import hashlib
import importlib.util
import io
import json
import pathlib
import re
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
JUDGES = ROOT / "scripts" / "gate_b_mac_judges"
POD_BUNDLE = HERE / "judge_pod_stage1" / "bundle.py"   # round 30: shipped as tool/pod/bundle.py with a B10 unit
GATE_B_BUNDLE_AS = "tool/pod/bundle_gateb.py"            # Gate B's pod/bundle.py beside it, unchanged
JUDGE_POD = ROOT / "tmp" / "judge-pod"                   # judge_pod.JUDGE_POD_ROOT: tmp/judge-pod/TAG
JUDGE_HOSTS = ROOT / "tmp" / "family-probe-judge" / "hosts"   # podhost.JUDGE_HOSTS: judge-TAG/pod.json
PLAN = HERE / "plan.json"                                # round 31 (K2): write-files reads the ref_train units here
REF_TRAIN_KIND, ENGINE_A0 = "ref_train", "a0"            # a ref_train unit is the engine's a0 calibration unit
RECIPE_RE = re.compile(r"[A-Za-z0-9]+")
HEX64 = re.compile(r"[0-9a-f]{64}")
LABEL_TOKENS = frozenset({"yes", "no", "unparsed", "harm", "identical"})   # K4: words of a label-count key
_GATE_B = {}                                     # Gate B's own enumerate_units while stage1_enumeration patches it


def _load_pod_bundle():
    """judge_pod_stage1/bundle.py under a Mac-only module name: its label rule; nothing is patched on the Mac."""
    spec = importlib.util.spec_from_file_location("judge_pod_stage1_bundle", POD_BUNDLE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


_POD = _load_pod_bundle()
B10_KIND, B10_CHECKPOINT, SAFE_LORA_POINTS = _POD.B10_KIND, _POD.B10_CHECKPOINT, _POD.SAFE_LORA_POINTS
b10_label = _POD.b10_label        # the arm label (None for an external unit whose folder names no Safe LoRA point):
#                                   one implementation for the Mac and the pod (round 30)


def gate_b_units():
    """scripts/gate_b_mac_judges/units.py, imported as ``units`` (judge_pod and bundle import it by that name)."""
    if str(JUDGES) not in sys.path:
        sys.path.insert(0, str(JUDGES))
    import units  # noqa: E402
    return units


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


# ----- round 30: the seal-safe launch, write-files and result (addendum §30 gaps 3 and 4; R4, R5) ----------------

def load_judge_pod():
    """scripts/gate_b_mac_judges/pod/judge_pod.py as a new module object, for this process only (no file written)."""
    spec = importlib.util.spec_from_file_location("judge_pod", JUDGES / "pod" / "judge_pod.py")
    if str(JUDGES / "pod") not in sys.path:
        sys.path.insert(0, str(JUDGES / "pod"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def ship_pod_bundle(stage_bundle, canonical_bytes, sha256_file, manifest_name: str):
    """Gate B's bundle.stage_bundle, then, only when the launch holds a B10 unit: Gate B's staged tool/pod/bundle.py
    (checked equal to Gate B's file) kept unchanged as tool/pod/bundle_gateb.py, POD_BUNDLE written as
    tool/pod/bundle.py, and the job manifest rewritten (canonical) to list both by SHA-256. Without a B10 unit the
    bundle is Gate B's, byte for byte."""
    units = gate_b_units()

    def staged(groups, stage, *args, **kw):
        manifest = stage_bundle(groups, stage, *args, **kw)
        if not any(u.kind == B10_KIND for g in groups for u in g.units):
            return manifest
        stage = pathlib.Path(stage)
        shipped = stage / "tool" / "pod" / "bundle.py"
        if shipped.read_bytes() != (JUDGES / "pod" / "bundle.py").read_bytes():
            raise units.Refusal("the staged tool/pod/bundle.py is not Gate B's pod/bundle.py")
        (stage / GATE_B_BUNDLE_AS).write_bytes(shipped.read_bytes())
        shipped.write_bytes(POD_BUNDLE.read_bytes())
        files = {**manifest["files"], GATE_B_BUNDLE_AS: sha256_file(stage / GATE_B_BUNDLE_AS),
                 "tool/pod/bundle.py": sha256_file(shipped)}
        manifest = {**manifest, "files": dict(sorted(files.items()))}
        (stage / manifest_name).write_bytes(canonical_bytes(manifest))
        return manifest
    return staged


@contextlib.contextmanager
def stage1_launcher(module, quiet: bool = True):
    """For one launch of judge_pod ``module``: the stage-1 enumeration (stage1_enumeration); with ``quiet`` (every
    stage-1 launch) judge_pod.RunLog constructed with its echo off, so each step goes to the log file only (sealed);
    and the stage-1 pod bundle.py shipped with a B10 unit (ship_pod_bundle). Restored afterwards."""
    bundle_mod = module.bundle_mod
    saved_log, saved_stage = module.RunLog, bundle_mod.stage_bundle
    if quiet:
        class QuietRunLog(saved_log):
            """judge_pod.RunLog with its echo off: the log file only."""

            def __init__(self, path, tag, echo: bool = False):
                super().__init__(path, tag, echo=False)
        module.RunLog = QuietRunLog
    bundle_mod.stage_bundle = ship_pod_bundle(saved_stage, module.canonical_bytes, module.sha256_file,
                                              bundle_mod.MANIFEST_NAME)
    try:
        with stage1_enumeration():
            yield module
    finally:
        module.RunLog = saved_log
        bundle_mod.stage_bundle = saved_stage


def run_launcher(module, rest: list, host=None, quiet: bool = True, **launch_kw) -> int:
    """judge_pod's command line (``bundle`` or ``launch``) under stage1_launcher. ``host`` and ``launch_kw`` (clock,
    sleep, signals) are the tests' fake pod; the command line never passes them. Round 31 (K4): ``bundle`` prints its
    record through drop_label_counts (print_bundle_record)."""
    with stage1_launcher(module, quiet):
        if host is None and not launch_kw:
            if rest[:1] == ["bundle"]:
                return print_bundle_record(module, rest)
            return module.main(rest)
        return module.launch(module.parser().parse_args(rest), host=host, **launch_kw)


def drop_label_counts(value):
    """K4: ``value`` without any key that names a count of labels, at any depth: a key whose "_"-separated words
    include yes, no, unparsed, harm or identical (mac_yes, pod_yes, delta_yes, yes, unparsed, harm, and the gate's
    rule constants max_abs_delta_yes and min_identical)."""
    if isinstance(value, dict):
        return {k: drop_label_counts(v) for k, v in value.items()
                if not (isinstance(k, str) and set(k.lower().split("_")) & LABEL_TOKENS)}
    if isinstance(value, list):
        return [drop_label_counts(v) for v in value]
    return value


def print_bundle_record(module, rest: list) -> int:
    """K4: judge_pod's ``bundle`` with its printed record (stdout) caught and printed again through drop_label_counts;
    anything printed that is not one JSON object becomes a note. Its exit code and every file it writes (the bundle,
    bundle-record.json) are judge_pod's, unchanged; its refusals go to stderr as before."""
    caught = io.StringIO()
    with contextlib.redirect_stdout(caught):
        code = module.main(rest)
    text = caught.getvalue()
    if text.strip():
        try:
            doc = json.loads(text)
        except ValueError:
            doc = None
        shown = drop_label_counts(doc) if isinstance(doc, dict) else \
            {"note": "the launcher printed something other than its bundle record; not shown"}
        print(json.dumps(shown, indent=1, sort_keys=True), flush=True)
    return code


def ref_train_labels(plan: dict) -> dict:
    """K2: COMPLETE.json SHA-256 -> "ref-<recipe>" for the unit of every complete, pulled ref_train job in plan.json
    (record-done records its unit's COMPLETE.json SHA-256); a ref_train job recorded complete without one refuses."""
    units = gate_b_units()
    out = {}
    hosts = plan.get("hosts") if isinstance(plan, dict) else None
    for host, h in sorted((hosts or {}).items()):
        for i, j in enumerate((h or {}).get("jobs") or []):
            if not isinstance(j, dict) or j.get("kind") != REF_TRAIN_KIND or j.get("status") != "complete" or \
                    j.get("pulled") is False:
                continue
            digest, recipe = j.get("complete_sha256"), j.get("recipe")
            if not (isinstance(digest, str) and HEX64.fullmatch(digest) and isinstance(recipe, str)
                    and RECIPE_RE.fullmatch(recipe)):
                raise units.Refusal(f"plan.json: {host} job {i} (ref_train) is complete without a COMPLETE.json "
                                    "SHA-256 and a recipe")
            out[digest] = f"ref-{recipe}"
    return out


def label_ref_train(found: list, labels: dict) -> list:
    """K2: the found units, each one ``labels`` names (by COMPLETE.json SHA-256) with that arm label in place of
    job.json's; such a unit must be an engine a0 unit (kind run-one, arm a0), else it refuses."""
    units = gate_b_units()
    out = []
    for u in found:
        label = labels.get(u.complete_sha256)
        if label is None:
            out.append(u)
            continue
        if u.kind != "run-one" or u.arm != ENGINE_A0:
            raise units.Refusal(f"{u.label}: plan.json records it as a ref_train unit, but its job.json is not an "
                                "engine a0 unit (kind run-one, arm a0)")
        out.append(dataclasses.replace(u, arm=label))
    return out


def plan_labels(plan_path) -> dict:
    """K2: the ref_train labels of ``plan_path`` (None: the kit's plan.json when it exists, else none)."""
    units = gate_b_units()
    path = pathlib.Path(plan_path) if plan_path is not None else (PLAN if PLAN.is_file() else None)
    if path is None:
        return {}
    if not path.is_file():
        raise units.Refusal(f"no plan file {path}")
    try:
        doc = json.loads(path.read_text())
    except ValueError:
        raise units.Refusal(f"{path.name}: not JSON") from None
    return ref_train_labels(doc)


EMIT_KEEP, EMIT_COUNTS, INDEX_KEEP = ("file", "unit", "status"), ("missing", "stale", "extra"), \
    ("index", "files", "index_sha256")


def safe_emit_line(line: str) -> str:
    """One write_files line reduced to R4's whitelist: a unit line keeps its file, unit label and status and, per mode,
    its missing, stale and extra counts; the index line its path, number of files and SHA-256; any other line becomes
    a note. Never a harm, yes or unparsed count."""
    try:
        r = json.loads(line)
    except ValueError:
        r = None
    if isinstance(r, dict) and "status" in r:
        out = {k: r[k] for k in EMIT_KEEP if k in r}
        for mode in ("greedy", "sampled"):
            if isinstance(r.get(mode), dict):
                out[mode] = {k: r[mode][k] for k in EMIT_COUNTS if k in r[mode]}
        return json.dumps(out, sort_keys=True)
    if isinstance(r, dict) and "index" in r:
        return json.dumps({k: r[k] for k in INDEX_KEEP if k in r}, sort_keys=True)
    return json.dumps({"note": "a line outside the whitelist was not printed"})


def write_files_main(argv: list) -> int:
    """write-files: write_files.main's steps with the stage-1 enumeration and safe_emit_line (exit codes as Gate B's:
    0 every file written or unchanged, 1 a unit refused, 2 an input refused before anything is written)."""
    units = gate_b_units()
    import write_files as wf  # noqa: E402 - Gate B's, unchanged
    ap = argparse.ArgumentParser(prog="judge_units_stage1.py write-files",
                                 description="Gate B's per-unit judge files on the stage-1 enumeration (counts hidden)")
    ap.add_argument("--judge", choices=sorted(wf.JUDGES), required=True)
    ap.add_argument("--cache", type=pathlib.Path, required=True)
    ap.add_argument("--out", type=pathlib.Path, required=True)
    ap.add_argument("--complete", action="append", default=[], metavar="COMPLETE_SHA256")
    ap.add_argument("--plan", type=pathlib.Path, default=None,
                    help="the kit's plan.json, for the ref_train labels (default: the kit's, when it exists)")
    units.add_unit_arguments(ap)
    a = ap.parse_args(argv)
    try:
        bad = [c for c in a.complete if not wf.HEX64.match(c)]
        if bad:
            raise units.Refusal(f"--complete {bad[0][:16]!r}: expected 64 lowercase hex characters")
        if not a.cache.is_file():
            raise units.Refusal(f"no cache file {a.cache}")
        labels = plan_labels(a.plan)                  # round 31 (K2): ref_train units, by COMPLETE.json SHA-256
        with stage1_enumeration():
            found, _ = units.units_from_args(a)
        found = label_ref_train(found, labels)
        cache = wf.Cache(a.cache, wf.JUDGES[a.judge]["identity"])
        if cache.undecodable:
            print(json.dumps({"undecodable_cache_lines": cache.undecodable}))
        return wf.write_all(a.judge, found, cache, a.out, emit=lambda line: print(safe_emit_line(line), flush=True),
                            allow=a.complete)
    except units.Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2


# ----- round 32 (K5; addendum §34 point 7, block B's pre-flight G13): a block's judged units from plan.json -----------

def _kit_rules():
    """This kit folder's stage1_rules.py, loaded by path (the judged kinds and the re-judged pins; stdlib only)."""
    spec = importlib.util.spec_from_file_location("s1_units_kit_rules", HERE / "stage1_rules.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _kit_plan_tool():
    """This kit folder's plan_tool.py, loaded by path (round 33, GB1: block_open_jobs, the rule block_complete uses);
    sys.path is restored after the load (plan_tool puts its folder first)."""
    saved = list(sys.path)
    try:
        spec = importlib.util.spec_from_file_location("s1_units_kit_plan_tool", HERE / "plan_tool.py")
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
    finally:
        sys.path[:] = saved
    return module


def block_units(plan: dict, block: str, kit, root) -> list[dict]:
    """K5 (G13): the units BLOCK's judge launches judge, from plan.json only, by round 31's rule (plan_tool's
    judge_required_units): the unit of each complete, pulled job of the block's hosts of a judged run kind (arm,
    a0_arm, ref_train), each unit of each complete, pulled B10 reference job (ref_eval, safe_lora: its recorded units
    list), at KIT/retrieved/HOST/tree/UNIT, then the block's re-judged pins (stage1_rules.REJUDGED_PINS) at ROOT/path.
    Each unit's COMPLETE.json must be present and hash to the SHA-256 plan.json records (hashed, never parsed); no
    unit twice. Never another block's unit, and never a whole retrieved/ folder (no --run-root). Round 33 (GB1, judge
    runbook B): a block other than A is listed only when it has no open job (plan_tool.block_open_jobs: each job of a
    pending host, so of every hosts launch not released; of a released host not recorded done; or one a move left
    behind; less those a not-run decision names), so a judge launch never takes a partial list. Block A (sealed, its
    judges recorded) keeps the listing without that check."""
    rules, units = _kit_rules(), gate_b_units()
    if not isinstance(plan, dict) or block not in (plan.get("blocks") or {}):
        raise units.Refusal(f"block {block} is not planned in plan.json")
    if block != "A":
        try:
            open_jobs = _kit_plan_tool().block_open_jobs(plan, block)
        except SystemExit as exc:                     # a recorded not-run decision that is missing or changed
            raise units.Refusal(str(exc)) from None
        if open_jobs:
            raise units.Refusal(f"block {block} has {len(open_jobs)} open job(s) ({', '.join(open_jobs[:3])}"
                                f"{', ...' if len(open_jobs) > 3 else ''}): record-done each host, or name a job that "
                                "will not run in a not-run decision (plan_tool.py record-not-run), first")
    out = []
    for host, h in sorted((plan.get("hosts") or {}).items()):
        if h.get("block") != block:
            continue
        for i, j in enumerate(h.get("jobs") or []):
            if j.get("status") != "complete" or j.get("pulled") is False:
                continue
            if j.get("kind") in rules.JUDGED_RUN_KINDS:
                pairs = [(j.get("unit"), j.get("complete_sha256"))]
            elif j.get("kind") in rules.JUDGED_B10_KINDS:
                pairs = [(u.get("unit"), u.get("complete_sha256")) if isinstance(u, dict) else (None, None)
                         for u in j.get("units") or [None]]
            else:
                continue
            for rel, digest in pairs:
                parts = pathlib.PurePosixPath(str(rel)).parts
                if not (isinstance(rel, str) and rel and isinstance(digest, str) and HEX64.fullmatch(digest)) or \
                        pathlib.PurePosixPath(rel).is_absolute() or ".." in parts:
                    raise units.Refusal(f"plan.json: {host} job {i} ({j.get('kind')}) records no plain unit path and "
                                        "COMPLETE.json SHA-256")
                out.append({"path": pathlib.Path(kit) / "retrieved" / host / "tree" / rel, "kind": j["kind"],
                            "complete_sha256": digest})
    for pin in rules.REJUDGED_PINS.get(block, ()):
        out.append({"path": pathlib.Path(root) / pin["path"], "kind": "re-judged",
                    "complete_sha256": pin["complete_sha256"]})
    missing = [u for u in out if not (u["path"] / "COMPLETE.json").is_file()]
    if missing:
        raise units.Refusal(f"block {block}: {len(missing)} unit(s) have no COMPLETE.json ({missing[0]['path']})")
    differ = [u for u in out if units.sha256_bytes((u["path"] / "COMPLETE.json").read_bytes()) != u["complete_sha256"]]
    if differ:
        raise units.Refusal(f"block {block}: {len(differ)} unit(s) whose COMPLETE.json is not the SHA-256 plan.json "
                            f"records ({differ[0]['path']})")
    if len({u["complete_sha256"] for u in out}) != len(out) or len({str(u["path"]) for u in out}) != len(out):
        raise units.Refusal(f"block {block}: a unit is listed twice")
    return out


def units_of_block_main(argv: list) -> int:
    """units-of-block BLOCK --out FILE [--plan P]: writes FILE (new) with one unit folder per line, the --unit
    arguments of the block's judge launch and write-files, and prints the counts (units, by kind) and FILE's SHA-256.
    Exit 0, or 2 refused (nothing written)."""
    units = gate_b_units()
    ap = argparse.ArgumentParser(prog="judge_units_stage1.py units-of-block",
                                 description="a block's judged units from plan.json (never --run-root)")
    ap.add_argument("block")
    ap.add_argument("--out", type=pathlib.Path, required=True, help="a new file: one unit folder per line")
    ap.add_argument("--plan", type=pathlib.Path, default=None, help="the kit's plan.json (default: this kit's)")
    a = ap.parse_args(argv)
    try:
        path = a.plan if a.plan is not None else PLAN
        if not path.is_file():
            raise units.Refusal(f"no plan file {path}")
        try:
            plan = json.loads(path.read_text())
        except ValueError:
            raise units.Refusal(f"{path.name}: not JSON") from None
        kit = path.resolve().parent
        found = block_units(plan, a.block, kit, kit.parents[1])
        if a.out.exists():
            raise units.Refusal(f"{a.out} exists; give a new file")
        with a.out.open("x") as handle:
            handle.write("".join(f"{u['path']}\n" for u in found))
    except units.Refusal as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    kinds = {}
    for u in found:
        kinds[u["kind"]] = kinds.get(u["kind"], 0) + 1
    print(json.dumps({"block": a.block, "units": len(found), "by_kind": kinds, "out": str(a.out),
                      "sha256": hashlib.sha256(a.out.read_bytes()).hexdigest()}, sort_keys=True))
    return 0


def _scalar(value):
    """A whitelisted field's value: a number, bool, None or a string (cut at 300 characters); anything else None."""
    if value is None or isinstance(value, (bool, int, float)):
        return value
    return value[:300] if isinstance(value, str) else None


def _utc(text: str) -> dt.datetime:
    return dt.datetime.fromisoformat(str(text).replace("Z", "+00:00"))


def result_fields(tag: str, root=None, hosts=None) -> dict:
    """``result TAG``: the runbook's step-5 whitelist of the launch's judge-pod-result.json (each value a scalar; the
    number of units, never a unit's counts), the pod minutes and cost from the judge host record, and the entry for
    plan_tool.py record-judges (its result SHA-256 is this file's bytes)."""
    units = gate_b_units()
    path = pathlib.Path(root or JUDGE_POD) / tag / "judge-pod-result.json"
    if not path.is_file():
        raise units.Refusal(f"{tag}: no judge-pod-result.json yet")
    data = path.read_bytes()
    try:
        r = json.loads(data)
    except ValueError:
        r = None
    if not isinstance(r, dict) or r.get("kind") != "judge-pod result":
        raise units.Refusal(f"{tag}: judge-pod-result.json is not a judge-pod result")
    v = r.get("verification") if isinstance(r.get("verification"), dict) else {}
    stop = r.get("stop") if isinstance(r.get("stop"), dict) else {}
    gate = v.get("known_answers") if isinstance(v.get("known_answers"), dict) else None
    judge = r.get("judge") or "harmbench"
    pod_file = pathlib.Path(hosts or JUDGE_HOSTS) / f"judge-{tag}" / "pod.json"
    pod = json.loads(pod_file.read_bytes()) if pod_file.is_file() else {}
    pod = pod if isinstance(pod, dict) else {}
    minutes = cost = None
    try:
        minutes = round((_utc(stop.get("utc")) - _utc(pod.get("created_utc"))).total_seconds() / 60, 1)
        cost = round(minutes / 60 * float(pod["costPerHr"]), 2)
    except (TypeError, ValueError, KeyError):
        pass
    out = {"tag": tag, "judge": _scalar(judge), "exit": _scalar(r.get("exit")),
           "bundle_sha256": _scalar(r.get("bundle_sha256")), "cap_hours": _scalar(r.get("cap_hours")),
           "stop_confirmed": _scalar(stop.get("confirmed")), "desiredStatus": _scalar(stop.get("desiredStatus")),
           "run_record_ok": _scalar(v.get("run_record_ok")), "pod_exit": _scalar(v.get("pod_exit")),
           "gpu": _scalar(v.get("gpu")), "complete": _scalar(v.get("complete")), "judged": _scalar(v.get("judged")),
           "records": _scalar(v.get("records")), "units": len(v.get("units") or []),
           "refused": _scalar(v.get("refused")), "tokenizer_fingerprint": _scalar(v.get("tokenizer_fingerprint")),
           "known_answer_passed": None if gate is None else _scalar(gate.get("passed")),
           "costPerHr": _scalar(pod.get("costPerHr")), "pod_minutes": minutes, "cost_usd": cost}
    fetched = r.get("fetched") if isinstance(r.get("fetched"), dict) else {}
    entry = {"tag": tag, "result_sha256": hashlib.sha256(data).hexdigest(),
             "run_record_sha256": _scalar(fetched.get("out/run-record.json")), "bundle_sha256": out["bundle_sha256"],
             "exit": out["exit"], "judged": out["judged"], "complete": out["complete"]}
    if judge == "granite":
        entry["known_answer_passed"] = out["known_answer_passed"]
    return {**out, "record_entry": entry}


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
        return run_launcher(load_judge_pod(), rest)       # round 30: echo off; the B10 pod bundle.py
    if argv[:1] == ["write-files"]:
        return write_files_main(argv[1:])
    if argv[:1] == ["units-of-block"]:                    # round 32 (K5): never --run-root for a block's judges
        return units_of_block_main(argv[1:])
    ap = argparse.ArgumentParser(prog="judge_units_stage1.py")
    sub = ap.add_subparsers(dest="command", required=True)
    p = sub.add_parser("list")
    units.add_unit_arguments(p)
    c = sub.add_parser("check-devices")
    c.add_argument("--contrast", action="append", required=True, help="NAME=LABEL,LABEL,...")
    c.add_argument("--record", action="append", required=True, help="LABEL=RUN_RECORD.json")
    r = sub.add_parser("result")
    r.add_argument("tag")
    r.add_argument("--root", type=pathlib.Path, default=None, help="default: tmp/judge-pod")
    r.add_argument("--hosts", type=pathlib.Path, default=None, help="default: tmp/family-probe-judge/hosts")
    a = ap.parse_args(argv)
    try:
        if a.command == "result":
            print(json.dumps(result_fields(a.tag, a.root, a.hosts), indent=1, sort_keys=True))
            return 0
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
