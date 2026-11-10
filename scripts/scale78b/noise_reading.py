"""N's reading and the seed rule for the 7-8B tier (readiness plan T5; P78 §3.3-§3.4 and §5.1 as the lead ruled on
5 Nov 2026, rulings 1-3, 7, 8 and 10; stdlib only; outside the engine identity).

    python3 -I -B scripts/scale78b/noise_reading.py --inputs INPUTS.json --out OUT.json

**Inputs** (one JSON file, kind "scale-78b noise reading inputs", version 1; relative paths resolve from its folder).
``families``: for each family name (``olmo2-7b``, ``llama31-8b``; ``olmo2-1b`` only for the Gate B parity test) an
object with ``engine`` ({a0, R}: the code identity every unit of that role must show), ``a0`` and ``R`` (each
{"1101", "1102", "1103": {path, complete_sha256[, arm]}}: the unit folders keyed by their COMPLETE.json SHA-256; an R
entry names its edit arm ``edit-<SHA-256>``) and ``fingerprint_check`` ("equal", "differs" or "not run": the lead's
record of ruling 10's a0-1101 retrain comparison on engine X). Optional ``bars`` (default: Gate A's frozen amended
bars).

**What is read** (refused otherwise; the Gate B C2 checks that the family-probe layout allows): a sealed unit (every
file its COMPLETE.json lists is present with its hash); COMPLETE.json's SHA-256 equal to its key; job.json a run-one
e1 trajectory of the dev bank, split dev, role development, at the keyed seed (1101-1103 only), fresh for an R arm
(an a0 unit may resume from its own init unit, as Gate A's 1101 did; the resume source is recorded); an a0 unit's
arm "a0"; an R unit's arm the named edit file, present as edit.json with that hash, a remove edit of the family's
manifest whose provenance says family R, draw = seed - 1100 (a method arm's edit file refuses: only a0 and R units are
N's inputs); the engine identity, the manifest and the family's training identity in job.json, identity.json and
COMPLETE.json (so a 1B unit listed under a 7-8B family refuses: f46279e5… is neither 36738c38… nor 5b4451e1…); the
recipe's training identity recomputed; one complete_sha256 never twice; the environment record (13 compared fields,
the policy block, the lock) and the guard record (compared among the units that carry one; Gate A's 1B units have
none, every engine-X unit has one).

**The reading** (frozen functions imported from scripts/gate_b_reading.py by path and pinned by SHA-256; nothing is
copied): r_F,j = U(a0, j) - U(R_j, j) in pp; σ̂_F = max(SD(r_F), σ_eval,0,F) on 2 df (``Reader.reading`` and
``noise_gate``; σ_eval,0 the median prompt-clustered pair SE); the a0-free fallback (SD(r) := √2 × SD(U(R_j)),
σ_eval,0 over the three R-R pairs) with its two triggers: an environment or guard-record difference between any unit
and the family's a0-1101 (``compared_fields``), or ``fingerprint_check`` "differs"; σ̂_pool = max(√[Σ_F 2 SD(r_F)² /
(2 k)], the median of the k × 3 governing pair SEs) on 2 k df (k = 2 families: √[(2 SD(r_O)² + 2 SD(r_L)²) / 4] and
the 6 pair SEs, 4 df; each family's GOVERNING reading enters the pool, so when only one family's fallback fires its
three R-R pair terms and the other family's three seed-matched terms make the median, addendum A6); s_arm, the pooled
per-arm seed SD of U over the a0 and R units of every family (2 df per arm;
√2 × s_arm is the unpaired scale's value); the seed rule on the pair scale, compared exactly on squares: σ̂_pool
≤ 4.5 plan A, ≤ 6.0 plan B9, else branch H (the lead's (b): P1, P3, P6 at 12 seeds); the review ceiling: the plan's
removal MDE above 2 × its SESOI (5 pp) reads review; each family's own σ̂_F plan (the [C] alternative without SR-2);
each unit's G1 status by the frozen guard code (report only). Printed and written: σ̂_F, σ̂_pool, s_arm, both
σ_eval,0 forms, the triggers, the seed-rule output, r_j, the per-arm SDs and the G1 counts. No U of any arm is printed
or written. The operating characteristics of the rule (``operating_characteristics``) are the χ² probabilities of
CALC rule_oc2.py, for the tests.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# ===== pins: the frozen readers (read by path, never edited) =====
GATE_B_READING = ROOT / "scripts/gate_b_reading.py"
FROZEN = {"gate_b_reading": (GATE_B_READING, "4638a0f0bf46f89fddecea34d378f13c5f632909a9dc6a82159e1f64555a8874"),
          "family_probe_reading": (ROOT / "scripts/family_probe_reading.py",
                                   "8848340107bd4accee837bcd4a696e5bb230cc2157dba7def385a11ff6a9ad5a"),
          "killtest_stage0_reading": (ROOT / "scripts/killtest_stage0_reading.py",
                                      "1740663bc9e465422ba3c96db3898665035c6bfaa8db9716b89db16ae9f1a5e9")}
# ===== the families (training identity = the engine's hash of the recipe's model and train sections; P78:76) =====
FAMILIES = {
    "olmo2-7b": {"training_identity": "36738c3823fae7eaca625cc9f619e98c7e40b9bb64e5d0e234412827d3371ec6",
                 "manifest_sha256": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
                 "main_config_sha256": "18cc31d7117a2de7bc02382fe8a4d409fc43c91b434bf219a4808dfb26528d09"},
    "llama31-8b": {"training_identity": "5b4451e1487fb2200a5b2b151de2e68397117099a429654484146b3cc3791287",
                   "manifest_sha256": "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a",
                   "main_config_sha256": "74758af1791d9f7a8ce616adce7549b5b7b0619e55310158d7e21197ed129893"},
    "olmo2-1b": {"training_identity": "f46279e5830f477742189ef03c03ffc0ec86107ae060bb5ef9034ba47acabfac",   # Gate B's REC and S
                 "manifest_sha256": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9",
                 "main_config_sha256": "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b",
                 "parity_only": True},
}
TIER_FAMILIES = ("olmo2-7b", "llama31-8b")
# ===== the rule (the lead's ruling 3; P78 §5.1): thresholds on the pair scale, exact decimals =====
SEEDS = (1101, 1102, 1103)                                  # N's seeds; equal to gate_b_reading.A0_SEEDS (checked below)
R_SEED_BASE = 1100                                          # R_d runs at seed 1100 + d
THRESHOLD_A_PP = "4.5"
THRESHOLD_B9_PP = "6.0"
SESOI_PP = 5
PLAN_SEEDS = {"A": 6, "B9": 9, "H": 12}                      # method seeds of the plan (ruling 2's layout)
PLAN_CONTRASTS = {"A": 6, "B9": 3, "H": 3}                   # primary contrasts in the Holm family
# The paired removal MDE is MDE_FACTOR × σ̂_pair: (z_{1 - 0.05 / (2 m)} + z_0.80) / √seeds, Holm's first step over m
# contrasts two-sided at 5%, 80% power (CALC rule_oc2.py: 1.42 σ for plan A, 1.08 for B9, 0.93 for 12 seeds). Four
# decimals; the tests check them against scipy. ONE constant decides the review ceiling and the printed MDE (C-D2):
# review when MDE_FACTOR × σ̂ > 2 × SESOI, compared exactly on squares; the ceiling σ̂ = 2 × SESOI / MDE_FACTOR is
# derived from the same factor (plan A 7.0388, B9 9.2721, H 10.7066 pp) and is printed, never compared.
MDE_FACTOR = {"A": "1.4207", "B9": "1.0785", "H": "0.9340"}
CEILING_SIGMA_PP = {plan: Fraction(2 * SESOI_PP) / Fraction(factor) for plan, factor in MDE_FACTOR.items()}
PLAN_NAMES = {"A": "plan A", "B9": "plan B9", "H": "branch H (b)"}
FINGERPRINT_CHECKS = ("equal", "differs", "not run")
INPUTS_KIND = "scale-78b noise reading inputs"
OUTPUT_KIND = "scale-78b noise reading"
INPUT_KEYS = {"kind", "version", "families", "bars"}
FAMILY_KEYS = {"engine", "a0", "R", "fingerprint_check"}
LOCK_NAME = "environment-linux.lock"
# ===== end of the pins =====


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def _load(name: str, path: pathlib.Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def check_frozen() -> dict:
    """The frozen readers' bytes are the pinned ones; returns their hashes."""
    got = {name: sha256_file(path) for name, (path, _) in FROZEN.items()}
    bad = sorted(name for name, (_, want) in FROZEN.items() if got[name] != want)
    if bad:
        raise SystemExit(f"the frozen reader(s) {bad} differ from their pinned SHA-256: this reading stops")
    return got


FROZEN_SHA256 = check_frozen()
GB = _load("gate_b_reading_for_scale78b", GATE_B_READING)      # loads the frozen family_probe_reading itself (GB.FR)
FR = GB.FR
SELF_SHA256 = hashlib.sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
if tuple(GB.A0_SEEDS) != SEEDS or GB.R_SEED_BASE != R_SEED_BASE:
    raise SystemExit("gate_b_reading's seeds are not N's: the reading stops")
refuse, ex = GB.refuse, GB.ex


def hex64(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


# ----- units --------------------------------------------------------------------------------------------------------------


def r_edit_matches(doc, family: str, seed: int) -> bool:
    """The five fields an R unit's edit.json must carry to be the family's R draw at ``seed``: kind "safety-selection
    edit", edit_kind "remove", manifest_sha256 the family's manifest, provenance.selection.family "R" and
    provenance.selection.draw = seed - 1100 (SEAL's fields; the Llama sealed set writes the same ones). A method arm's
    edit file (family "unit", "H", ...) or another manifest's file is not an R unit of this family."""
    if not isinstance(doc, dict):
        return False
    selection = (doc.get("provenance") or {}).get("selection") or {}
    return doc.get("kind") == "safety-selection edit" and doc.get("edit_kind") == "remove" \
        and doc.get("manifest_sha256") == FAMILIES[family]["manifest_sha256"] and selection.get("family") == "R" \
        and selection.get("draw") == seed - R_SEED_BASE


def read_unit(spec, role: str, seed: int, family: str, engine: str, where: str, base: pathlib.Path) -> dict:
    """One a0 or R unit of a family, checked (module doc, "What is read"); returns its ids, fields and guard record."""
    keys = {"path", "complete_sha256"} | ({"arm"} if role == "R" else set())
    if not isinstance(spec, dict) or set(spec) != keys or not isinstance(spec["path"], str):
        refuse(f"{where}: a unit entry has exactly {sorted(keys)}")
    folder = (base / spec["path"]).resolve()
    needed = ("COMPLETE.json", "job.json", "identity.json", "assets.json")
    if not folder.is_dir() or any(not (folder / n).is_file() for n in needed):
        refuse(f"{where}: not a unit folder ({', '.join(needed)})")
    FR.sealed(folder)
    if not hex64(spec["complete_sha256"]) or sha256_file(folder / "COMPLETE.json") != spec["complete_sha256"]:
        refuse(f"{where}: COMPLETE.json's SHA-256 is not the key given")
    job = GB.read_json(folder / "job.json", f"{where} job.json")
    ident = GB.read_json(folder / "identity.json", f"{where} identity.json")
    marker = GB.read_json(folder / "COMPLETE.json", f"{where} COMPLETE.json")
    if marker.get("complete") is not True or marker.get("kind") != job.get("kind") \
            or marker.get("job_sha256") != sha256_file(folder / "job.json"):
        refuse(f"{where}: COMPLETE.json does not seal this job.json")
    try:
        when = dt.datetime.fromisoformat(marker["completed_utc"])
    except (KeyError, TypeError, ValueError):
        refuse(f"{where}: COMPLETE.json has no readable completed_utc")
    if when.utcoffset() is None:
        refuse(f"{where}: COMPLETE.json completed_utc has no timezone")
    if job.get("kind") != "run-one" or job.get("target_checkpoint") != "e1" or job.get("replicate_of") is not None:
        refuse(f"{where}: not a run-one e1 trajectory")
    if role == "R" and job.get("resume_from") is not None:
        refuse(f"{where}: an R arm is a fresh trajectory (no resume)")
    # An a0 unit may resume from its own seed's init unit (Gate A's 1101 did; the 7-8B side units are fine-tune only):
    # Gate B's gate_a_unit accepted both. The resume source, if any, is recorded by its COMPLETE.json SHA-256.
    resumed = marker.get("resumed_from_complete_sha256")
    if job.get("evaluate_bank") != "dev" or job.get("split") != "dev" or job.get("role") != "development":
        refuse(f"{where}: an N unit evaluates the dev bank, split dev, role development")
    if not GB.is_int(job.get("seed")) or job.get("seed") != seed:
        refuse(f"{where}: job.json's seed is not {seed}")
    fam = FAMILIES[family]
    if role == "a0":
        if job.get("arm") != "a0":
            refuse(f"{where}: an a0 unit's arm must be a0")
    else:
        arm = spec["arm"]
        if not (isinstance(arm, str) and arm.startswith("edit-") and hex64(arm[len("edit-"):])):
            refuse(f"{where}: an R entry names its arm edit-<SHA-256>")
        if job.get("arm") != arm:
            refuse(f"{where}: job.json's arm is not the named R edit")
        edit = folder / GB.EDIT_FILE
        if not edit.is_file() or sha256_file(edit) != arm[len("edit-"):]:
            refuse(f"{where}: edit.json is missing or is not the arm's edit file")
        doc = GB.read_json(edit, f"{where} edit.json")
        if not r_edit_matches(doc, family, seed):
            refuse(f"{where}: the edit file is not the R draw {seed - R_SEED_BASE} of the family's manifest "
                   "(only a0 and R units are N's inputs)")
    short = marker.get("identity") or {}
    for label, rec in (("job.json", job), ("identity.json", ident), ("COMPLETE.json identity", short)):
        for field, want in (("code_sha256", engine), ("manifest_sha256", fam["manifest_sha256"])):
            got = rec.get(field)
            if got is None:
                refuse(f"{where}: {label} has no {field} (absent or null)")
            if got != want:
                refuse(f"{where}: {label} {field} is not the family's {role} value")
    for label, rec in (("identity.json", ident), ("COMPLETE.json identity", short)):
        if rec.get("training_identity") != fam["training_identity"]:
            refuse(f"{where}: {label} training_identity is not the family's ({fam['training_identity'][:8]}…): "
                   f"not a {family} unit")
    recipe = ident.get("recipe")
    if not isinstance(recipe, dict) or GB.canonical_sha256({"model": recipe.get("model"), "train": recipe.get("train")}) \
            != fam["training_identity"]:
        refuse(f"{where}: identity.json's recipe does not have the family's training identity")
    recipe_sha = GB.canonical_sha256(recipe)
    if not (job.get("recipe_sha256") == ident.get("recipe_sha256") == short.get("recipe_sha256") == recipe_sha):
        refuse(f"{where}: the recipe hash differs between job.json, identity.json, COMPLETE.json and the recipe")
    assets = GB.read_json(folder / "assets.json", f"{where} assets.json")
    lock = folder / LOCK_NAME
    if lock.is_file():                                      # the unit's own copy (Gate B's layout)
        digest = sha256_file(lock)
        record = assets.get("environment_lock")
        if isinstance(record, dict) and record.get("sha256") not in (None, digest):
            refuse(f"{where}: the lock copy and assets.json's record differ")
        listed = (marker.get("files") or {}).get(LOCK_NAME)
        if listed is not None and listed != digest:
            refuse(f"{where}: the lock copy and COMPLETE.json's hash differ")
    else:                                                   # the run root's (the family probes' layout, environment_of)
        root_lock = folder.parent.parent / LOCK_NAME
        if not root_lock.is_file():
            refuse(f"{where}: no {LOCK_NAME} in the unit or its run root")
        digest = sha256_file(root_lock)
    if assets.get("policy") is None:
        refuse(f"{where}: assets.json has no policy block")
    fields = GB.compared_fields(assets.get("environment"), digest, assets.get("policy"))
    missing = sorted(k for k, v in fields.items() if v is None)
    if missing or fields["device"] != "cuda":
        refuse(f"{where}: the environment record lacks {missing or ['a CUDA device']}")
    # The guard record (assets.json "guard": repo, revision, files): engine X's units carry one; Gate A's 1B units
    # (engine 55253874) do not, and Gate B's gate_a_unit compared their 13 fields and policy only. A unit without one is
    # recorded as such; guard records are compared among the units that carry one (environment_differs).
    guard = assets.get("guard")
    if guard is not None and not isinstance(guard, dict):
        refuse(f"{where}: assets.json's guard record is malformed")
    return {"folder": folder, "where": where, "role": role, "seed": seed, "complete_sha256": spec["complete_sha256"],
            "job_sha256": marker["job_sha256"], "code_sha256": engine, "recipe_sha256": recipe_sha,
            "lock_sha256": digest, "resumed_from_complete_sha256": resumed if isinstance(resumed, str) else None,
            "fields": fields, "guard": guard}


def environment_differs(unit: dict, reference: dict) -> list:
    """The compared fields (and the guard record, when both units carry one) in which a unit differs from the family's
    a0-1101."""
    out = sorted(k for k in set(reference["fields"]) | set(unit["fields"]) if reference["fields"].get(k) != unit["fields"].get(k))
    if unit["guard"] is not None and reference["guard"] is not None and unit["guard"] != reference["guard"]:
        out.append("guard")
    return out


# ----- the statistics -----------------------------------------------------------------------------------------------------


def shown(rd: dict, ng: dict) -> dict:
    """The printed form of one reading (plain or fallback): r_j, SD(r), σ_eval,0, σ̂_gate and the pair SEs; no U."""
    pair_se2 = {k: v["se2"] for k, v in rd["pairs"].items()}
    r = {str(j): float(v) for j, v in sorted(rd["r"].items())}
    return {"fallback": bool(ng["fallback"]), "r_pp": r, "mean_r_pp": float(GB.mean(rd["r"].values())),
            "se_mean_r_pp": math.sqrt(GB.variance(rd["r"].values()) / len(rd["r"])),
            "sd_r_pp": ng["sd_r_pp"], "sigma_eval0_pp": ng["sigma_eval0_pp"], "sigma_gate_pp": ng["sigma_gate_pp"],
            "pairs": sorted(pair_se2), "pair_se_pp": {k: math.sqrt(v) for k, v in sorted(pair_se2.items())},
            "pairs_dropped_prompts": {k: v["dropped"] for k, v in sorted(rd["pairs"].items())}}


def seed_rule(sigma, df: int) -> dict:
    """The seed rule on the pair scale (ruling 3), compared exactly on squares: σ̂ ≤ 4.5 plan A, ≤ 6.0 plan B9, else
    branch H; then the review ceiling: review when the plan's removal MDE, MDE_FACTOR × σ̂, is above 2 × SESOI (the
    same factor that the printed removal_mde_pp uses; the printed ceiling 2 × SESOI / MDE_FACTOR is derived from it)."""
    if GB.ge(ex(THRESHOLD_A_PP), 1, sigma):
        plan = "A"
    elif GB.ge(ex(THRESHOLD_B9_PP), 1, sigma):
        plan = "B9"
    else:
        plan = "H"
    value = GB.sigma_value(sigma)
    review = not GB.ge(2 * SESOI_PP, ex(MDE_FACTOR[plan]), sigma)      # 2 SESOI >= factor × σ̂ holds: no review
    return {"sigma_pp": value, "df": df, "thresholds_pp": {"plan_A_at_most": float(ex(THRESHOLD_A_PP)),
                                                            "plan_B9_at_most": float(ex(THRESHOLD_B9_PP))},
            "plan": plan, "plan_name": PLAN_NAMES[plan], "method_seeds": PLAN_SEEDS[plan],
            "primary_contrasts": PLAN_CONTRASTS[plan], "sesoi_pp": SESOI_PP,
            "removal_mde_pp": float(ex(MDE_FACTOR[plan])) * value, "mde_factor": float(ex(MDE_FACTOR[plan])),
            "review_ceiling_sigma_pp": float(CEILING_SIGMA_PP[plan]), "review": review,
            "outcome": "review" if review else PLAN_NAMES[plan]}


def family_reading(name: str, spec, bars: dict, base: pathlib.Path, seen: dict) -> dict:
    if name not in FAMILIES:
        refuse(f"{name}: not a family of this reading ({sorted(FAMILIES)})")
    if not isinstance(spec, dict) or set(spec) != FAMILY_KEYS:
        refuse(f"{name}: a family entry has exactly {sorted(FAMILY_KEYS)}")
    engine = spec["engine"]
    if not isinstance(engine, dict) or set(engine) != {"a0", "R"} or not all(hex64(v) for v in engine.values()):
        refuse(f"{name}: engine must give the a0 and R code identities (64 hex each)")
    fingerprint = spec["fingerprint_check"]
    if fingerprint not in FINGERPRINT_CHECKS:
        refuse(f"{name}: fingerprint_check must be one of {FINGERPRINT_CHECKS}")
    units = {}
    for role in ("a0", "R"):
        given = spec[role]
        if not isinstance(given, dict) or sorted(given) != [str(s) for s in SEEDS]:
            refuse(f"{name} {role}: seeds 1101, 1102 and 1103 are required, and no other")
        for s in SEEDS:
            entry, where = given[str(s)], f"{name} {role}@{s}"
            # One unit is never read twice (C-D4): the key is checked before the unit's own checks, so the same unit
            # listed in another seed's slot or under another family refuses here, not on the seed or the identity.
            key = entry.get("complete_sha256") if isinstance(entry, dict) else None
            if key is not None and key in seen:
                refuse(f"{where}: its COMPLETE.json SHA-256 is already read as {seen[key]}")
            u = read_unit(entry, role, s, name, engine[role], where, base)
            seen[u["complete_sha256"]] = u["where"]
            units[(role, s)] = u
    reference = units[("a0", SEEDS[0])]
    differs = {f"{role}@{s}": environment_differs(u, reference) for (role, s), u in units.items()}
    environment = any(differs.values())
    fallback = environment or fingerprint == "differs"
    arms = {}
    for (role, s), u in units.items():
        key = "a0" if role == "a0" else GB.r_key(s)
        arms[(key, s)] = GB.arm_from_unit(u["folder"], bars, u["where"])
    readers = {"plain": GB.Reader(arms, [], [], False), "fallback": GB.Reader(arms, [], [], True)}
    readings = {mode: reader.reading("plain") for mode, reader in readers.items()}
    gates = {mode: GB.noise_gate(reader) for mode, reader in readers.items()}
    governing = "fallback" if fallback else "plain"
    rd = readings[governing]
    sigma_f = rd["sigma_gate"]
    u_of = {role: [100 * arms[("a0" if role == "a0" else GB.r_key(s), s)]["U"]["plain"] for s in SEEDS] for role in ("a0", "R")}
    if any(v is None for vs in u_of.values() for v in vs):
        refuse(f"{name}: a unit has no sampled answer")
    arm_ss = {role: GB.variance(vs) * (len(vs) - 1) for role, vs in u_of.items()}
    g1 = {}
    for (key, s), rec in sorted(arms.items(), key=lambda kv: (kv[0][1], kv[0][0])):
        bar = rec["g1"]
        g1[f"{key}@{s}"] = {"status": bar["status"], "pass": bar["status"] == FR.PASS, "n": bar["n"], "capped": bar["capped"],
                            "incoherent": bar["incoherent"], "short_only": bar["short_only"], "without_short": bar["without_short"]}
    return {"family": name, "parity_only": bool(FAMILIES[name].get("parity_only")),
            "training_identity": FAMILIES[name]["training_identity"], "manifest_sha256": FAMILIES[name]["manifest_sha256"],
            "engine": engine, "units": {u["where"]: {"complete_sha256": u["complete_sha256"], "job_sha256": u["job_sha256"],
                                                   "code_sha256": u["code_sha256"], "recipe_sha256": u["recipe_sha256"],
                                                   "lock_sha256": u["lock_sha256"],
                                                   "resumed_from_complete_sha256": u["resumed_from_complete_sha256"],
                                                   "guard_record": u["guard"] is not None}
                                        for u in units.values()},
            "triggers": {"environment": environment, "environment_differs": differs, "fingerprint_check": fingerprint,
                         "fingerprint": fingerprint == "differs", "fallback": fallback},
            "plain": shown(readings["plain"], gates["plain"]), "fallback": shown(readings["fallback"], gates["fallback"]),
            "governing": governing, "sigma_F_pp": GB.sigma_value(sigma_f), "sigma_F_df": 2,
            "seed_rule_by_sigma_F": seed_rule(sigma_f, 2),
            "per_arm_sd_u_pp": {role: math.sqrt(GB.variance(vs)) for role, vs in u_of.items()},
            "G1": g1, "G1_failed_arms": sorted(k for k, v in g1.items() if not v["pass"]),
            "_exact": {"sdr2": rd["sdr2"], "pair_se2": {k: v["se2"] for k, v in rd["pairs"].items()},
                       "arm_ss": sum(arm_ss.values(), Fraction(0)), "arm_df": sum(len(vs) - 1 for vs in u_of.values())}}


def pooled(families: dict) -> dict:
    """σ̂_pool over the families read (k = 2 at the tier: (2 SD(r_O)² + 2 SD(r_L)²) / 4 against the median of the 6
    governing pair SEs, 4 df), s_arm, and the seed rule on σ̂_pool. Each family's GOVERNING reading enters (its
    ``_exact`` block): when only one family's fallback fires, that family's three R-R pair terms and the other
    family's three seed-matched terms make the median (addendum A6); the record names the terms per family."""
    k = len(families)
    exact = [f["_exact"] for f in families.values()]
    p_pool = sum((2 * e["sdr2"] for e in exact), Fraction(0)) / (2 * k)
    se2s = [v for e in exact for v in e["pair_se2"].values()]
    median = GB.median_term(se2s)
    sigma = ((p_pool,), median)
    ss = sum((e["arm_ss"] for e in exact), Fraction(0))
    df_arm = sum(e["arm_df"] for e in exact)
    s_arm = math.sqrt(ss / df_arm)
    return {"families": sorted(families), "k": k, "df": 2 * k, "P_pool_pp2": float(p_pool), "sqrt_P_pool_pp": math.sqrt(p_pool),
            "median_pair_se_pp": GB.term_value(median), "n_pair_ses": len(se2s), "sigma_pool_pp": GB.sigma_value(sigma),
            "governing_by_family": {n: f.get("governing") for n, f in sorted(families.items())},
            "pair_terms_by_family": {n: {p: math.sqrt(v) for p, v in sorted(f["_exact"]["pair_se2"].items())}
                                     for n, f in sorted(families.items())},
            "s_arm_pp": s_arm, "s_arm_df": df_arm, "sqrt2_s_arm_pp": math.sqrt(2) * s_arm,
            "seed_rule": seed_rule(sigma, 2 * k)}


# ----- operating characteristics (CALC rule_oc2.py's χ² probabilities; the tests reproduce its rows) ---------------------


def chi2_cdf_even(x: float, df: int) -> float:
    """P(χ²_df ≤ x) for an even df, in closed form: 1 - e^{-x/2} Σ_{i < df/2} (x/2)^i / i!."""
    if df <= 0 or df % 2:
        raise ValueError("even df only")
    half = x / 2
    term, total = 1.0, 0.0
    for i in range(df // 2):
        if i:
            term *= half / i
        total += term
    return 1.0 - math.exp(-half) * total


def operating_characteristics(sigma_true: float, df: int) -> dict:
    """P(plan A), P(plan B9), P(branch H) when σ̂² = σ² χ²_df / df (the σ_eval floor ignored, as CALC does)."""
    a = chi2_cdf_even(df * float(ex(THRESHOLD_A_PP)) ** 2 / sigma_true ** 2, df)
    b = chi2_cdf_even(df * float(ex(THRESHOLD_B9_PP)) ** 2 / sigma_true ** 2, df) - a
    return {"P_plan_A": a, "P_plan_B9": b, "P_branch_H": 1.0 - a - b}


# ----- inputs and the run ---------------------------------------------------------------------------------------------------


def read(inputs_path) -> dict:
    path = pathlib.Path(inputs_path).resolve()
    raw = GB.read_json(path, "the inputs file")
    unknown = sorted(set(raw) - INPUT_KEYS) if isinstance(raw, dict) else ["<not an object>"]
    if not isinstance(raw, dict) or raw.get("kind") != INPUTS_KIND or raw.get("version") != 1 or unknown:
        refuse(f"not a {INPUTS_KIND} file (kind, version 1, known keys; unknown: {len(unknown)})")
    base = path.parent
    bars_path = (base / raw["bars"]).resolve() if raw.get("bars") else FR.DEFAULT_BARS
    bars = GB.read_json(bars_path, "the bars file")
    applied = FR.bars_applied(bars_path, bars)
    if bars.get("name") != GB.BARS_NAME or not applied["frozen"]:
        refuse("the bars file is not Gate A's frozen amended bars")
    families = raw.get("families")
    if not isinstance(families, dict) or not families:
        refuse("families must name at least one family")
    seen: dict = {}
    readings = {name: family_reading(name, families[name], bars, base, seen) for name in sorted(families)}
    tier = {n: f for n, f in readings.items() if not f["parity_only"]}
    parity = {n: f for n, f in readings.items() if f["parity_only"]}
    if tier and parity:
        refuse("a parity-only family (olmo2-1b) is never pooled with a 7-8B family")
    pool = pooled(readings)
    for f in readings.values():
        del f["_exact"]
    return {"kind": OUTPUT_KIND, "version": 1, "script_sha256": SELF_SHA256, "frozen_sha256": dict(FROZEN_SHA256),
            "bars_sha256": applied["sha256"], "inputs_sha256": sha256_file(path), "rule": {
                "sigma_pool_df": "2 per family", "thresholds_pp": [float(ex(THRESHOLD_A_PP)), float(ex(THRESHOLD_B9_PP))],
                "sesoi_pp": SESOI_PP, "mde_factor": {k: float(ex(v)) for k, v in MDE_FACTOR.items()},
                "review_rule": "review when mde_factor × σ̂_pool > 2 × sesoi_pp (exact on squares); the ceiling is derived",
                "review_ceiling_sigma_pp": {k: float(v) for k, v in CEILING_SIGMA_PP.items()}},
            "families": readings, "pooled": pool, "seed_rule": pool["seed_rule"]}


def summary(doc: dict) -> dict:
    fams = {n: {"governing": f["governing"], "sigma_F_pp": f["sigma_F_pp"], "sd_r_pp": f[f["governing"]]["sd_r_pp"],
                "sigma_eval0_pp": f[f["governing"]]["sigma_eval0_pp"], "mean_r_pp": f[f["governing"]]["mean_r_pp"],
                "triggers": {k: f["triggers"][k] for k in ("environment", "fingerprint", "fallback")},
                "G1_failed_arms": f["G1_failed_arms"], "plan_by_sigma_F": f["seed_rule_by_sigma_F"]["outcome"]}
            for n, f in doc["families"].items()}
    pool = doc["pooled"]
    return {"families": fams, "sigma_pool_pp": pool["sigma_pool_pp"], "df": pool["df"], "s_arm_pp": pool["s_arm_pp"],
            "sqrt2_s_arm_pp": pool["sqrt2_s_arm_pp"], "seed_rule": doc["seed_rule"]["outcome"],
            "removal_mde_pp": doc["seed_rule"]["removal_mde_pp"], "review": doc["seed_rule"]["review"]}


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out = pathlib.Path(args.out)
    if out.exists():
        refuse("--out exists: a reading output is written once")
    doc = GB.jsonable(read(args.inputs))
    data = GB.canonical(doc)
    out.write_bytes(data)
    print(json.dumps(GB.jsonable({"out_sha256": hashlib.sha256(data).hexdigest(), **summary(doc)})))
    return 0


if __name__ == "__main__":
    sys.exit(main())
