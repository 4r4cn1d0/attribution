"""LN-12 (addendum section 10; REV3 sections 6.3 and 1.5; REC (d) rule 5): the job spec for the reused units'
regeneration and their O-only passes on the 500-prompt bank. Mac, $0, text-free; the lead runs it; the stage-1 kit (B15)
executes the jobs on a block-A pod.

Units (the settings pin each by path under the data root, its COMPLETE.json SHA-256 and its job.json SHA-256): a0 at
1101-1103 (Gate A's units) and R_1-R_3 at 1101-1103 (Gate B wave 0a); R_4 and R_5 (1104, 1105) only if Gate B's extension
ran them (``--extension R_4=PATH:COMPLETE_SHA256:JOB_SHA256``; their pins are null in the settings); and theta0 (no
adapter). Each source is checked: the files hash to the pins, job.json is the job COMPLETE.json names, the seed and
arm are the settings'; an R arm must be ``edit-<SHA-256>`` of the sealed R_d file (d = seed - 1100) that the sealed
MANIFEST lists. From the source the spec copies the identity (code, recipe, prepared manifest, data config, training
identity) and the e1 and q adapter fingerprints.

Jobs, in this order:
1. per regenerated unit, ``regenerate``: a deterministic train-only re-run to e1 on engine X with recipe S, accepted
   only if its e1 adapter fingerprint, training identity, prepared manifest and data config equal the source unit's;
   the source's code and recipe hashes are reported, not required (addendum section 11 point 2). Failure: LS-04 (S1,
   LN-27); that unit's O-only pass waits. Never a state pulled from a stopped Gate B kit pod (PREREG revision 5 section 9).
2. per regenerated unit, ``o_only``: the O-only pass on the 500-prompt bank by the one shared function
   ``scripts/stage1_s1/oext_eval.py`` (addendum section 11 point 1), after its regeneration; U stays as read.
3. theta0: ``o_only`` (untuned, no adapter); under Branch 128 also LN-14's transfer report (``report``).
The cap branch: Branch 128 if W1-18's record (``--cap-record``) shows its truncation check passed over every unit, else
Branch full; with no record (``--no-cap-record``, for example when FOCUS holds no LN-13 provenance record) Branch full.
The route per branch is LN-19's; weights are equal per prompt (LN-24). Every output falls under block A's seal (LW-35).

Writes reuse_spec.json (text-free) into --out. Prints counts and hashes only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "build_reuse_spec.json"
SETTINGS_SHA256 = "a980264e53f0e660390208934c44d2a37900f1d3381944e9e957e8a2973c22cc"
SETTINGS_NAME = "build_reuse_spec"
OUTPUT = "reuse_spec.json"
IDENTITY_FIELDS = ("code_sha256", "recipe_sha256", "manifest_sha256", "data_config_sha256", "training_identity")
ACCEPT_FIELDS = ("training_identity", "manifest_sha256", "data_config_sha256")


def read_pinned(path: Path, digest: str, what: str) -> bytes:
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, the pin is {digest}")
    return data


def sealed_r_arms(data_root: Path, settings: dict) -> dict[int, str]:
    """d -> the arm (edit-<SHA-256>) of the sealed R_d file, from the pinned sealed MANIFEST."""
    spec = settings["sealed_manifest"]
    doc = s1.strict_json(read_pinned(data_root / spec["path"], spec["sha256"], "the sealed MANIFEST"))
    arms = {}
    for f in doc.get("files", []):
        if f.get("family") == "R" and isinstance(f.get("draw"), int):
            if f.get("arm") != f"edit-{f.get('sha256')}":
                raise s1.Refusal(f"the sealed MANIFEST's R_d{f['draw']} arm is not edit-<its SHA-256>")
            arms[f["draw"]] = f["arm"]
    return arms


def read_unit(data_root: Path, unit: dict, r_arms: dict[int, str]) -> dict:
    """One source unit, checked; its identity and fingerprints (no text)."""
    folder = data_root / unit["path"]
    complete = s1.strict_json(read_pinned(folder / "COMPLETE.json", unit["complete_sha256"], f"{unit['name']} COMPLETE.json"))
    job = s1.strict_json(read_pinned(folder / "job.json", unit["job_sha256"], f"{unit['name']} job.json"))
    if complete.get("job_sha256") != unit["job_sha256"] or complete.get("complete") is not True:
        raise s1.Refusal(f"{unit['name']}: COMPLETE.json does not name this job as complete")
    if job.get("seed") != unit["seed"]:
        raise s1.Refusal(f"{unit['name']}: the job's seed is {job.get('seed')}, the settings say {unit['seed']}")
    if unit["kind"] == "a0":
        if job.get("arm") != "a0":
            raise s1.Refusal(f"{unit['name']}: the job's arm is not a0")
    else:
        d = unit["seed"] - 1100
        if d != unit["d"] or job.get("arm") != r_arms.get(d):
            raise s1.Refusal(f"{unit['name']}: the job's arm is not the sealed R_d{unit['d']} arm (d = seed - 1100)")
    identity = complete.get("identity", {})
    checkpoints = complete.get("checkpoints", {})
    if any(not isinstance(identity.get(f), str) or not s1.HEX64.match(identity[f]) for f in IDENTITY_FIELDS):
        raise s1.Refusal(f"{unit['name']}: the identity block is incomplete")
    fingerprints = {}
    for name in ("q", "e1"):
        fp = checkpoints.get(name, {}).get("adapter_fingerprint")
        if not isinstance(fp, str) or not s1.HEX64.match(fp):
            raise s1.Refusal(f"{unit['name']}: no {name} adapter fingerprint")
        fingerprints[name] = fp
    return {"identity": {f: identity[f] for f in IDENTITY_FIELDS}, "fingerprints": fingerprints, "arm": job["arm"],
            "edit": job.get("edit"), "target_checkpoint": job.get("target_checkpoint")}


def cap_branch(record: tuple[Path, str] | None, settings: dict) -> dict:
    """ADD section 9 and LN-13: Branch 128 only on a W1-18 record whose truncation check passed over every unit."""
    rule = settings["cap"]
    if record is None:
        return {"branch": "full", "source": rule["no_record"], "record_sha256": None}
    doc = s1.strict_json(read_pinned(*record, "W1-18's record"))
    check = doc.get("truncation_check") if isinstance(doc, dict) else None
    if doc.get("kind") != rule["record_kind"] or not isinstance(check, dict) or check.get("units") != rule["units"] \
            or not isinstance(check.get("pass"), bool):
        raise s1.Refusal(f"the cap record is not W1-18's record over {rule['units']} units")
    branch = "128" if check["pass"] else "full"
    return {"branch": branch, "source": rule["branch_128" if branch == "128" else "branch_full"], "record_sha256": record[1]}


def o_bank(record: tuple[Path, str], settings: dict) -> dict:
    doc = s1.strict_json(read_pinned(*record, "the O-ext record"))
    if doc.get("kind") != settings["o_bank"]["oext_record_kind"] or not isinstance(doc.get("bank"), dict):
        raise s1.Refusal("the O-ext record is not build_oext's record")
    n = doc.get("bank_size")
    if isinstance(n, bool) or not isinstance(n, int) or n < 1:
        raise s1.Refusal("the O-ext record holds no bank")
    return {"dev": settings["o_bank"]["dev"], "phtest": {"record_sha256": record[1], "bank_sha256": doc["bank"]["full_file"]["sha256"],
                                                         "prompts": n, "shortfall": doc.get("shortfall")},
            "prompts": settings["o_bank"]["dev"]["prompts"] + n, "weights": settings["o_bank"]["weights"]}


def build(*, data_root: Path, oext_record: tuple[Path, str], cap_record: tuple[Path, str] | None,
          oext_eval: tuple[Path, str] | None, extension: dict[str, tuple[str, str, str]], settings: dict,
          settings_sha256: str) -> dict[str, bytes]:
    s1.check_settings(settings, SETTINGS_NAME)
    r_arms = sealed_r_arms(data_root, settings)
    cap = cap_branch(cap_record, settings)
    bank = o_bank(oext_record, settings)
    function = {"path": settings["o_pass"]["function"], "sha256": None}
    if oext_eval is not None:
        read_pinned(*oext_eval, "the shared O-ext function")
        function["sha256"] = oext_eval[1]
    units = []
    for unit in settings["units"]:
        if unit.get("conditional"):
            if unit["name"] not in extension:
                continue
            path, complete_sha, job_sha = extension[unit["name"]]
            unit = {**unit, "path": path, "complete_sha256": complete_sha, "job_sha256": job_sha}
        units.append((unit, read_unit(data_root, unit, r_arms)))
    unknown = set(extension) - {u["name"] for u in settings["units"] if u.get("conditional")}
    if unknown:
        raise s1.Refusal(f"--extension names a unit the settings do not hold: {sorted(unknown)[0]}")
    route = settings["routes"][cap["branch"]]
    engine = settings["engine"]
    jobs = []
    for unit, src in units:
        jobs.append({"id": f"regenerate-{unit['name']}", "kind": "regenerate", "unit": unit["name"], "arm": src["arm"],
                     "seed": unit["seed"], "edit": src["edit"], "target_checkpoint": "e1", "train_only": True,
                     "engine_code_sha256": engine["code_sha256"], "recipe_sha256": engine["recipe_sha256"],
                     "accept": {"e1_adapter_fingerprint": src["fingerprints"]["e1"],
                                **{f: src["identity"][f] for f in ACCEPT_FIELDS}},
                     "report": {"q_adapter_fingerprint": src["fingerprints"]["q"],
                                "source_code_sha256": src["identity"]["code_sha256"],
                                "source_recipe_sha256": src["identity"]["recipe_sha256"]},
                     "source": {"path": unit["path"], "complete_sha256": unit["complete_sha256"],
                                "job_sha256": unit["job_sha256"]},
                     "failure": settings["acceptance"]["failure"]})
    for unit, src in units:
        jobs.append({"id": f"o_only-{unit['name']}", "kind": "o_only", "unit": unit["name"], "arm": src["arm"],
                     "seed": unit["seed"], "after": f"regenerate-{unit['name']}", "adapter": "the accepted regenerated e1",
                     "branch": cap["branch"], "route": route})
    jobs.append({"id": "o_only-theta0", "kind": "o_only", "unit": "theta0", "arm": "untuned", "seed": None, "after": None,
                 "adapter": None, "branch": cap["branch"], "route": route})
    if cap["branch"] == "128":
        jobs.append({"id": "report-theta0-transfer", "kind": "report", "unit": "theta0", "after": "o_only-theta0",
                     "rule": settings["theta0_transfer"]})
    spec = {"kind": "stage1 reuse job spec", "version": 1, "requirement": settings["requirement"], "cap": cap,
            "o_bank": bank, "o_pass": {**function, "rule": settings["o_pass"]["rule"],
                                       "fallback": settings["o_pass"]["fallback"]},
            "acceptance": settings["acceptance"], "never": settings["never"], "seal": settings["seal"],
            "prints": settings["prints"], "fallback": settings["fallback"], "jobs": jobs,
            "counts": {"regenerate": len(units), "o_only": len(units) + 1, "report": int(cap["branch"] == "128")},
            "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                        {"sealed_manifest": settings["sealed_manifest"]["sha256"],
                                         "oext_record": oext_record[1],
                                         **({"cap_record": cap_record[1]} if cap_record else {}),
                                         **({"oext_eval": oext_eval[1]} if oext_eval else {}),
                                         **{f"{u['name']}_complete": u["complete_sha256"] for u, _ in units}},
                                        settings["label_entries"])}
    return {OUTPUT: canonical_json(spec)}


def pair(spec: str, what: str) -> tuple[Path, str]:
    path, _, sha = spec.rpartition(":")
    if not path or not s1.HEX64.match(sha):
        raise s1.Refusal(f"{what} is PATH:SHA256")
    return Path(path), sha


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--data-root", type=Path, required=True, help="the folder the unit paths start from (tmp/)")
    parser.add_argument("--oext-record", required=True, help="PATH:SHA256 of build_oext's oext_record.json")
    cap = parser.add_mutually_exclusive_group(required=True)
    cap.add_argument("--cap-record", help="PATH:SHA256 of W1-18's overrefusal_checks.json")
    cap.add_argument("--no-cap-record", action="store_true", help="no W1-18 record (or no LN-13 record): Branch full")
    parser.add_argument("--oext-eval", help="PATH:SHA256 of scripts/stage1_s1/oext_eval.py, once committed")
    parser.add_argument("--extension", action="append", default=[], help="R_4 or R_5 = PATH:COMPLETE_SHA256:JOB_SHA256")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        extension = {}
        for spec in args.extension:
            name, _, rest = spec.partition("=")
            parts = rest.split(":")
            if not name or len(parts) != 3 or not all(s1.HEX64.match(p) for p in parts[1:]):
                raise s1.Refusal("each --extension is NAME=PATH:COMPLETE_SHA256:JOB_SHA256")
            extension[name] = (parts[0], parts[1], parts[2])
        files = build(data_root=args.data_root, oext_record=pair(args.oext_record, "--oext-record"),
                      cap_record=None if args.no_cap_record else pair(args.cap_record, "--cap-record"),
                      oext_eval=pair(args.oext_eval, "--oext-eval") if args.oext_eval else None,
                      extension=extension, settings=settings, settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    doc = s1.strict_json(files[OUTPUT])
    print(f"branch {doc['cap']['branch']}; jobs {doc['counts']}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
