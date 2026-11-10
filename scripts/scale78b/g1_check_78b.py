"""The Llama G1 $0 check (P78 §7 "Llama G1 risk", [LEAD] item 7; the lead's rulings 14 and 15): Gate B's frozen G1
code on evaluated units in the family-probe layout. Stdlib only; outside the engine identity.

    python3 -I -B scripts/scale78b/g1_check_78b.py --units UNITS.json --out OUT.json

UNITS.json: kind "scale-78b g1 check inputs", version 1, ``units``: a list of {id, family, path} (family olmo2-7b,
llama31-8b or olmo2-1b; the path a unit folder holding COMPLETE.json, job.json, identity.json and eval/<its job's
target checkpoint>; relative paths resolve from the file's folder); optional ``bars`` (default Gate A's frozen amended
bars). Each unit must be sealed (every file COMPLETE.json lists present with its hash), a run-one job whose
identity.json carries the family's training identity, and an a0 or edit arm.

The frozen code reads the unit: ``gate_b_reading.arm_from_unit`` (eval/<target>; the coherence screen re-implemented
from the bars and checked against the frozen ``counts()``; ``family_probe_reading.answers_end_bar``). No adapter is
needed: the family probes write the layout Gate B's Gate A units have. G1 passes when the answers-end bar reads PASS
(sampled capped share ≤ 5%, screen-failing share ≤ 10%); a short-answer TOO CLOSE counts as a G1 failure (PRE:147).

Output (text-free): per unit the path, the COMPLETE.json and job.json SHA-256, the engine identity, the arm and seed,
the sampled counts (n, capped, incoherent, short_only, without_short), the two shares, the answers-end verdict and the
G1 status; the bars' and the frozen scripts' SHA-256; the command. Never an answer, a prompt or a U.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import pathlib
import re
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]
NR = None                                                   # scripts/scale78b/noise_reading.py, loaded below (its pins)


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NR = _load("noise_reading_for_g1_check", HERE / "noise_reading.py")   # checks the frozen readers' pins at import
GB, FR = NR.GB, NR.FR
SELF_SHA256 = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
INPUTS_KIND = "scale-78b g1 check inputs"
OUTPUT_KIND = "scale-78b g1 check"
UNIT_KEYS = {"id", "family", "path"}
G1_RULE = ("answers end: sampled capped share at most 5% and screen-failing share at most 10% (Gate A's frozen amended "
           "bars); a short-answer TOO CLOSE counts as a G1 failure (Gate B pre-registration, G1)")
refuse = GB.refuse


def g1_of(status: str) -> dict:
    """G1 from the answers-end verdict: pass only on PASS; TOO CLOSE is a failure (PRE:147)."""
    if status not in (FR.PASS, FR.TOO_CLOSE, FR.FAIL):
        refuse(f"an answers-end verdict that is not pass, too close or fail: {status!r}")
    return {"answers_end": status, "G1": "pass" if status == FR.PASS else "fail",
            "G1_failure_kind": None if status == FR.PASS else ("short-answer TOO CLOSE" if status == FR.TOO_CLOSE else "FAIL")}


def check_unit(entry, base: pathlib.Path, bars: dict) -> dict:
    if not isinstance(entry, dict) or set(entry) != UNIT_KEYS or not all(isinstance(entry[k], str) for k in UNIT_KEYS):
        refuse(f"a unit entry has exactly {sorted(UNIT_KEYS)}, each a string")
    uid, family = entry["id"], entry["family"]
    if not re.fullmatch(r"[\w.@-]{1,64}", uid):
        refuse("a unit id is a short identifier")
    if family not in NR.FAMILIES:
        refuse(f"{uid}: family must be one of {sorted(NR.FAMILIES)}")
    folder = (base / entry["path"]).resolve()
    needed = ("COMPLETE.json", "job.json", "identity.json")
    if not folder.is_dir() or any(not (folder / n).is_file() for n in needed):
        refuse(f"{uid}: not a unit folder ({', '.join(needed)})")
    FR.sealed(folder)
    job = GB.read_json(folder / "job.json", f"{uid} job.json")
    ident = GB.read_json(folder / "identity.json", f"{uid} identity.json")
    marker = GB.read_json(folder / "COMPLETE.json", f"{uid} COMPLETE.json")
    if marker.get("job_sha256") != NR.sha256_file(folder / "job.json") or marker.get("kind") != job.get("kind"):
        refuse(f"{uid}: COMPLETE.json does not seal this job.json")
    if job.get("kind") != "run-one":
        refuse(f"{uid}: not a run-one job")
    arm = job.get("arm")
    if not (arm == "a0" or (isinstance(arm, str) and arm.startswith("edit-") and NR.hex64(arm[len("edit-"):]))):
        refuse(f"{uid}: the arm is neither a0 nor an edit")
    want = NR.FAMILIES[family]["training_identity"]
    if ident.get("training_identity") != want or (marker.get("identity") or {}).get("training_identity") != want:
        refuse(f"{uid}: the unit's training identity is not {family}'s ({want[:8]}…)")
    if ident.get("manifest_sha256") != NR.FAMILIES[family]["manifest_sha256"]:
        refuse(f"{uid}: the unit's manifest is not {family}'s")
    rec = GB.arm_from_unit(folder, bars, uid)                # the frozen code reads eval/<target>
    bar = rec["g1"]
    n = bar["n"]
    shares = {"capped": Fraction(bar["capped"], n) if n else None, "incoherent": Fraction(bar["incoherent"], n) if n else None,
              "incoherent_without_short": (Fraction(bar["without_short"]["incoherent"], bar["without_short"]["n"])
                                           if bar["without_short"]["n"] else None)}
    return {"id": uid, "family": family, "path": str(folder), "complete_sha256": NR.sha256_file(folder / "COMPLETE.json"),
            "job_sha256": marker["job_sha256"], "code_sha256": ident.get("code_sha256"), "recipe_sha256": ident.get("recipe_sha256"),
            "arm": arm if arm == "a0" else "edit", "arm_sha256": None if arm == "a0" else arm[len("edit-"):],
            "seed": job.get("seed"), "target_checkpoint": job.get("target_checkpoint"),
            "sampled": {"n": n, "capped": bar["capped"], "incoherent": bar["incoherent"], "short_only": bar["short_only"],
                        "without_short": dict(bar["without_short"])},
            "shares": {k: None if v is None else float(v) for k, v in shares.items()},
            "bars_pp": {"max_sampled_capped_share": bars["max_sampled_capped_share"],
                        "max_sampled_incoherent_share": bars["max_sampled_incoherent_share"]},
            **g1_of(bar["status"])}


def run(inputs_path, argv: list) -> dict:
    path = pathlib.Path(inputs_path).resolve()
    raw = GB.read_json(path, "the units file")
    if not isinstance(raw, dict) or raw.get("kind") != INPUTS_KIND or raw.get("version") != 1 \
            or set(raw) - {"kind", "version", "units", "bars"}:
        refuse(f"not a {INPUTS_KIND} file (kind, version 1, known keys)")
    base = path.parent
    bars_path = (base / raw["bars"]).resolve() if raw.get("bars") else FR.DEFAULT_BARS
    bars = GB.read_json(bars_path, "the bars file")
    applied = FR.bars_applied(bars_path, bars)
    if bars.get("name") != GB.BARS_NAME or not applied["frozen"]:
        refuse("the bars file is not Gate A's frozen amended bars")
    entries = raw.get("units")
    if not isinstance(entries, list) or not entries:
        refuse("units must list at least one unit")
    units = [check_unit(e, base, bars) for e in entries]
    ids = [u["id"] for u in units]
    if len(set(ids)) != len(ids) or len({u["complete_sha256"] for u in units}) != len(units):
        refuse("a unit id or a COMPLETE.json SHA-256 is listed twice")
    by_family = {}
    for u in units:
        f = by_family.setdefault(u["family"], {"units": 0, "G1_pass": 0, "G1_fail": 0, "failed_ids": []})
        f["units"] += 1
        f["G1_pass" if u["G1"] == "pass" else "G1_fail"] += 1
        if u["G1"] != "pass":
            f["failed_ids"].append(u["id"])
    return {"kind": OUTPUT_KIND, "version": 1, "script_sha256": SELF_SHA256, "noise_reading_sha256": NR.SELF_SHA256,
            "frozen_sha256": dict(NR.FROZEN_SHA256), "bars_sha256": applied["sha256"], "bars_name": bars["name"],
            "inputs_sha256": NR.sha256_file(path), "rule": G1_RULE, "command": argv, "units": units, "by_family": by_family}


def main(argv=None) -> int:
    argv = sys.argv[1:] if argv is None else list(argv)
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--units", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        refuse("--out exists: a check output is written once")
    doc = GB.jsonable(run(args.units, [pathlib.Path(sys.argv[0]).name] + argv))
    data = GB.canonical(doc)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_bytes(data)
    print(json.dumps({"out_sha256": hashlib.sha256(data).hexdigest(), "by_family": doc["by_family"],
                      "units": [{k: u[k] for k in ("id", "answers_end", "G1", "sampled", "shares")} for u in doc["units"]]}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
