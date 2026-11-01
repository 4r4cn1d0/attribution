"""The mid-block B10/B11 re-pin for the evaluation-only references at a0 seeds 1104-1107 (block-B pre-flight G4;
addendum section 34 point 5; LN-15b's "all seven a0 seeds"): after the a0 arm pods of those seeds are done, it adds
each seed's pins to B10's settings (reference_units: the a0 unit's COMPLETE.json SHA-256 and its q and e1 adapter
fingerprints) and to B11's (adapter.accepted: the e1 fingerprint), and re-takes every pin that hangs on them in one
edit (addendum section 11 point 7). The kit's second reference phase then re-pins its S1_CODE and re-packs.

    python -B scripts/stage1_s1/repin_reference_seeds.py --kit KIT --seeds 1105,1106,1107 (--out NEW_DIR | --in-place)
        [--root REPO] [--record SEED=PATH=SHA256]...

Sources. Block A is sealed and block B's outcomes are not read before block B's reading, so only files the seal
classes as readable (runkit seal.py READABLE_PATTERNS) and SHA-256 values are read; no unit COMPLETE.json, state.json
or evaluation file is opened (a unit's COMPLETE.json is hashed only):
- the kit's plan.json: the seed's one complete a0_arm job (host, index, unit, complete_sha256 and the outputs the kit
  recorded with their SHA-256) and the host's job_done_sha256 and engine;
- the host's pulled JOB-DONE.json (readable): it hashes to job_done_sha256 and names the same job, unit and
  complete_sha256, with status complete;
- the job's fingerprint record, job-I/a0-adapter-fingerprint.json (readable by the seal's pattern
  *adapter-fingerprint*.json), which must hash to the SHA-256 that plan.json records for it among the job's outputs
  (or, with --record SEED=PATH=SHA256, a lead record given by its path and SHA-256 whose name is readable too). Its
  form (the kit's job runner writes it after an a0_arm job, read from the unit's COMPLETE.json on the pod, as it writes
  regeneration-adapter-fingerprint.json for a regeneration):
      {"kind": "stage1 a0 adapter fingerprint", "version": 1, "job": I, "arm": "a0", "seed": S,
       "unit": "round1/S-a0-e1-a1", "complete_sha256": H,
       "checkpoints": {"e1": "<64 hex>", "q": "<64 hex or null>"},
       "identity": {"manifest_sha256": "<B10's prepared pin>", "training_identity": "<B10's recipe pin>"}}
  A lead record may instead be extract_a0_fingerprint.py's (the seal rule's fingerprint clause; the lead's route (a)
  for 1104, a seed of the sealed block A): {"kind": "stage1 a0 adapter fingerprint extract", "unit", "complete_sha256",
  "state_sha256", "fingerprint", "seal_sha256", "utc", "script_sha256"}, checked against plan.json's unit and
  COMPLETE.json SHA-256, the block's seal at the SHA-256 plan.json's seals record holds, the seal's own SHA-256 of the
  unit's COMPLETE.json and states/e1/state.json (the pulled state.json is hashed, never parsed) and this repository's
  extractor; its seed is pinned with q null (as 1102 and 1103 are);
- the unit's COMPLETE.json under retrieved/HOST/tree/UNIT, hashed: it must equal complete_sha256 (the file the pack
  carries as gate_a_complete:S).

The edit (computed in memory; nothing is written unless every check passes):
1. settings/safe_lora.json: adapter.accepted[S] = {fingerprint (e1), source_complete_sha256, source_unit}; the
   acceptance rule's text names the stage-1 source once;
2. safe_lora.py: its SETTINGS_SHA256 literal = the new safe_lora.json's SHA-256;
3. settings/eval_adapter.json: reference_units[S]; external_transforms.safe_lora's module_sha256 and settings.sha256;
4. eval_adapter.py: its SETTINGS_SHA256 literal = the new eval_adapter.json's SHA-256;
5. the pins' tests and mutants: tests/test_b10_settings.py LITERAL, tests/test_b11_settings.py
   SAFE_LORA_SETTINGS_SHA256, mutation/mutants_b10.json's two find texts of B11's pins and mutation/mutants_b11.json's
   B11-settings-pin-changed (the literal's first 8 characters).
An old pin left anywhere in the package's code, tests, settings or mutants after the edit (a whole old SHA-256, or a
settings literal's 8-character form) refuses (a pin the tool does not know). The certification stays valid by construction and is checked: the tool refuses unless B10's
certified_settings_sha256 and script_code_sha256 are unchanged (the added seeds, the B11 pins and the literal are
outside them). A seed already pinned refuses (a pin is never replaced).

Output: --out NEW_DIR writes the changed files at their repository paths under a new folder; --in-place writes them
into --root (each file still at the SHA-256 read at the start). It prints JSON only: the seeds and their pins
(hashes), each file's path with its old and new SHA-256, the certification proof, the kit's S1_CODE pins to re-take
(runkit/stage1-olmo/stage1_rules.py) and each seed's pack input (gate_a_complete:S: path and SHA-256).

Exit status: 0 done; 2 refused (nothing written).
"""

from __future__ import annotations

import argparse
import copy
import fnmatch
import json
import re
import sys
import tempfile
from pathlib import Path
from typing import Any, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, write_atomic  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

Refusal = s1.Refusal
EXIT_OK, EXIT_REFUSED = 0, 2
GATE_A_SEEDS = ("1101", "1102", "1103")
STAGE1_SEEDS = ("1104", "1105", "1106", "1107")          # LN-15b: the a0 seeds of the full reference scope
READABLE_PATTERN = "*adapter-fingerprint*.json"          # runkit/stage1-olmo/seal.py READABLE_PATTERNS (a test pins it)
RECORD_NAME = "a0-adapter-fingerprint.json"
RECORD_KIND = "stage1 a0 adapter fingerprint"
EXTRACT_KIND = "stage1 a0 adapter fingerprint extract"   # extract_a0_fingerprint.py's record (a lead record, --record)
EXTRACT_KEYS = frozenset({"kind", "unit", "complete_sha256", "state_sha256", "fingerprint", "seal_sha256", "utc",
                          "script_sha256"})
HEX64 = re.compile(r"^[0-9a-f]{64}$")
LITERAL = re.compile(r'^SETTINGS_SHA256 = "([0-9a-f]{64})"$', re.MULTILINE)
PKG = "scripts/stage1_s1"
B10_PY, B10_JSON = f"{PKG}/eval_adapter.py", f"{PKG}/settings/eval_adapter.json"
B11_PY, B11_JSON = f"{PKG}/safe_lora.py", f"{PKG}/settings/safe_lora.json"
TEST_B10, TEST_B11 = f"{PKG}/tests/test_b10_settings.py", f"{PKG}/tests/test_b11_settings.py"
EXTRACTOR = f"{PKG}/extract_a0_fingerprint.py"
MUTANTS_B10, MUTANTS_B11 = f"{PKG}/mutation/mutants_b10.json", f"{PKG}/mutation/mutants_b11.json"
OLD_RULE = ("REF R.0.7: an input adapter is accepted only if its engine fingerprint (lora_fingerprint over the sorted "
            "names, shapes and float32 bytes) equals the Gate A a0 unit's e1 adapter_fingerprint at that seed (from "
            "each unit's states/e1/state.json); a state folder must also hash to its state.json, carry that "
            "fingerprint and name the checkpoint, arm and seed below; the adapter file's SHA-256 is recorded, never "
            "required")
NEW_RULE = ("REF R.0.7: an input adapter is accepted only if its engine fingerprint (lora_fingerprint over the sorted "
            "names, shapes and float32 bytes) equals the a0 unit's e1 adapter_fingerprint at that seed: at 1101-1103 "
            "the Gate A unit's (from each unit's states/e1/state.json; gate_a_adapter_file_sha256 is that adapter "
            "file's SHA-256, recorded, never required); at 1104-1107 the stage-1 a0_arm unit's, from a readable "
            "fingerprint record: the kit's job-I/a0-adapter-fingerprint.json at the SHA-256 plan.json records, or "
            "(a sealed block, the seal rule's fingerprint clause) the lead's a0-S-adapter-fingerprint.json written by "
            "scripts/stage1_s1/extract_a0_fingerprint.py from the sealed states/e1/state.json's adapter_fingerprint; "
            "source_complete_sha256 is the unit's COMPLETE.json SHA-256 (B10's reference pin of that seed; "
            "scripts/stage1_s1/repin_reference_seeds.py); a state folder must also hash to its state.json, carry that "
            "fingerprint and name the checkpoint, arm and seed below")


def _hex64(value: Any, what: str) -> str:
    if not (isinstance(value, str) and HEX64.match(value)):
        raise Refusal(f"{what} is not a SHA-256")
    return value


def _read(path: Path, what: str) -> bytes:
    try:
        return path.read_bytes()
    except OSError:
        raise Refusal(f"{what} cannot be read ({path})") from None


# ----- the pins a seed gets, from the kit's readable records ----------------------------------------------------------


def find_a0_job(plan: Mapping, seed: int) -> tuple[str, int, dict]:
    """plan.json's one complete a0_arm job of the seed (host, index, job)."""
    found = [(host, index, job) for host, h in sorted((plan.get("hosts") or {}).items())
             for index, job in enumerate(h.get("jobs") or [])
             if job.get("kind") == "a0_arm" and job.get("seed") == seed and job.get("status") == "complete"]
    if len(found) != 1:
        raise Refusal(f"seed {seed}: plan.json holds {len(found)} complete a0_arm jobs, not one (the a0 arm pod of the "
                      "seed is not done, or the plan is not the kit's)")
    return found[0]


def check_record(doc: Any, *, seed: int, index: int, unit: str, complete: str, b10: Mapping) -> dict:
    """The fingerprint record's form and its agreement with plan.json and B10's data and training pins."""
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version")) != (RECORD_KIND, 1):
        raise Refusal(f"seed {seed}: the fingerprint record is not a {RECORD_KIND!r} record of version 1")
    if (doc.get("seed"), doc.get("arm"), doc.get("job"), doc.get("unit"), doc.get("complete_sha256")) != (
            seed, "a0", index, unit, complete):
        raise Refusal(f"seed {seed}: the fingerprint record names another job, unit or COMPLETE.json than plan.json")
    points = doc.get("checkpoints")
    if not isinstance(points, dict) or set(points) != {"e1", "q"}:
        raise Refusal(f"seed {seed}: the fingerprint record's checkpoints are not e1 and q")
    e1 = _hex64(points["e1"], f"seed {seed}: the e1 adapter fingerprint")
    q = None if points["q"] is None else _hex64(points["q"], f"seed {seed}: the q adapter fingerprint")
    identity = doc.get("identity")
    expected = {"manifest_sha256": b10["prepared"]["manifest_sha256"],
                "training_identity": b10["recipe"]["training_identity"]}
    if identity != expected:
        raise Refusal(f"seed {seed}: the fingerprint record's data or training identity is not B10's pin")
    return {"e1": e1, "q": q}


def check_extract(doc: dict, *, seed: int, host: str, block: Any, unit: str, complete: str, kit: Path, plan: Mapping,
                  root: Path) -> dict:
    """extract_a0_fingerprint.py's record (the seal rule's fingerprint clause; the lead's route (a) for 1104): its keys,
    the unit and COMPLETE.json SHA-256 of plan.json, the block's seal (the file plan.json's seals record names, at its
    SHA-256), the seal's own SHA-256 of the unit's COMPLETE.json and states/e1/state.json (the pulled state.json
    hashed against it, never parsed), and the extractor's SHA-256 in this repository."""
    if set(doc) != EXTRACT_KEYS or not isinstance(doc.get("utc"), str):
        raise Refusal(f"seed {seed}: the extract record does not hold exactly {sorted(EXTRACT_KEYS)}")
    if (doc["unit"], doc["complete_sha256"]) != (unit, complete):
        raise Refusal(f"seed {seed}: the extract record names another unit or COMPLETE.json than plan.json")
    fingerprint = _hex64(doc["fingerprint"], f"seed {seed}: the extract record's fingerprint")
    pin = (plan.get("seals") or {}).get(block)
    if not isinstance(pin, dict) or not isinstance(pin.get("path"), str) or ".." in Path(pin["path"]).parts:
        raise Refusal(f"seed {seed}: plan.json records no seal of block {block}")
    seal_bytes = _read(kit / pin["path"], f"block {block}'s seal")
    if not (sha256_bytes(seal_bytes) == pin.get("sha256") == doc["seal_sha256"]):
        raise Refusal(f"seed {seed}: the extract record's seal is not block {block}'s recorded seal")
    entries = {(e.get("host"), e.get("path")): e.get("sha256") for e in s1.strict_json(seal_bytes).get("files") or []
               if isinstance(e, dict) and e.get("class") == "sealed"}
    state = f"{unit}/states/e1/state.json"
    if entries.get((host, f"{unit}/COMPLETE.json")) != complete or entries.get((host, state)) != doc["state_sha256"]:
        raise Refusal(f"seed {seed}: the seal does not list the extract record's COMPLETE.json and state.json hashes")
    state_path = kit / "retrieved" / host / "tree" / state
    if sha256_bytes(_read(state_path, f"seed {seed}'s pulled state.json")) != doc["state_sha256"]:   # hashed only
        raise Refusal(f"seed {seed}: the pulled states/e1/state.json is not the sealed one")
    if doc["script_sha256"] != sha256_bytes(_read(root / EXTRACTOR, EXTRACTOR)):
        raise Refusal(f"seed {seed}: the extract record was not made by this repository's {EXTRACTOR}")
    return {"e1": fingerprint, "q": None}


def seed_pins(kit: Path, plan: Mapping, seed: int, b10: Mapping, override: tuple[Path, str] | None = None,
              root: Path = REPO) -> dict:
    """Every pin of one seed, each from a readable record or a SHA-256 the kit recorded (see the module text)."""
    host, index, job = find_a0_job(plan, seed)
    h = plan["hosts"][host]
    if h.get("engine_sha256") != b10["engine_x"]:
        raise Refusal(f"seed {seed}: its a0 unit was made on another engine than B10's pin (host {host})")
    unit, complete = job.get("unit"), _hex64(job.get("complete_sha256"), f"seed {seed}: plan.json's complete_sha256")
    if not (isinstance(unit, str) and unit and not Path(unit).is_absolute() and ".." not in Path(unit).parts):
        raise Refusal(f"seed {seed}: plan.json names no unit folder")
    tree = kit / "retrieved" / host / "tree"
    data = _read(tree / "JOB-DONE.json", f"host {host}'s JOB-DONE.json")
    if sha256_bytes(data) != h.get("job_done_sha256"):
        raise Refusal(f"seed {seed}: host {host}'s JOB-DONE.json does not hash to plan.json's job_done_sha256")
    done = s1.strict_json(data)
    jobs = done.get("jobs") if isinstance(done, dict) else None
    entry = jobs[index] if isinstance(jobs, list) and 0 <= index < len(jobs) else None
    if not isinstance(entry, dict) or (entry.get("index"), entry.get("kind"), entry.get("seed"), entry.get("unit"),
                                       entry.get("complete_sha256"), entry.get("status")) != (
            index, "a0_arm", seed, unit, complete, "complete") or done.get("host") != host:
        raise Refusal(f"seed {seed}: host {host}'s JOB-DONE.json does not name plan.json's complete a0 job")
    if override is None:
        relative = f"job-{index}/{RECORD_NAME}"
        recorded = (job.get("outputs") or {}).get(relative)
        if recorded is None:
            raise Refusal(f"seed {seed}: no readable fingerprint record: plan.json lists no {relative} among host "
                          f"{host}'s job {index} outputs (the a0 unit's e1 fingerprint is then only in sealed files, "
                          "its COMPLETE.json and states/e1/state.json, which are never opened)")
        if (entry.get("outputs") or {}).get(relative) != recorded:
            raise Refusal(f"seed {seed}: JOB-DONE.json and plan.json record different SHA-256 for {relative}")
        path, digest = tree / relative, recorded
    else:
        path, digest = override
    if not fnmatch.fnmatch(path.name, READABLE_PATTERN):
        raise Refusal(f"seed {seed}: the fingerprint record {path.name} is not a file the seal classes as readable "
                      f"({READABLE_PATTERN})")
    record_bytes = _read(path, f"seed {seed}'s fingerprint record")
    if sha256_bytes(record_bytes) != _hex64(digest, f"seed {seed}: the fingerprint record's SHA-256"):
        raise Refusal(f"seed {seed}: the fingerprint record does not hash to the recorded SHA-256")
    doc = s1.strict_json(record_bytes)
    if override is not None and isinstance(doc, dict) and doc.get("kind") == EXTRACT_KIND:
        fingerprints = check_extract(doc, seed=seed, host=host, block=h.get("block"), unit=unit, complete=complete,
                                     kit=kit, plan=plan, root=root)
    else:
        fingerprints = check_record(doc, seed=seed, index=index, unit=unit, complete=complete, b10=b10)
    complete_path = tree / unit / "COMPLETE.json"
    if sha256_bytes(_read(complete_path, f"seed {seed}'s unit COMPLETE.json")) != complete:   # hashed, never parsed
        raise Refusal(f"seed {seed}: the pulled unit's COMPLETE.json does not hash to plan.json's complete_sha256")
    return {"seed": seed, "host": host, "job": index, "block": h.get("block"), "unit": unit,
            "complete_sha256": complete, "fingerprints": fingerprints, "record": str(path), "record_sha256": digest,
            "record_name": path.name if override is not None else f"job-{index}/{RECORD_NAME}",
            "complete_path": str(complete_path)}


# ----- the settings and the pins that hang on them --------------------------------------------------------------------


def b10_entry(pins: Mapping, engine: str) -> dict:
    seed, host, job = pins["seed"], pins["host"], pins["job"]
    return {"complete_sha256": pins["complete_sha256"],
            "fingerprint_prefixes": {"e1": pins["fingerprints"]["e1"], "q": pins["fingerprints"]["q"]},
            "role": f"stage-1 block {pins['block']} a0_arm unit, seed {seed}, e1 (host {host}, job {job}; engine X "
                    f"{engine[:8]}; trained from init in one job); pins from the kit's readable records (plan.json, "
                    f"JOB-DONE.json) and {pins['record_name']}",
            "unit": f"stage1-olmo/retrieved/{host}/tree/{pins['unit']}"}


def b11_entry(pins: Mapping, b10_unit: str) -> dict:
    return {"fingerprint": pins["fingerprints"]["e1"], "source_complete_sha256": pins["complete_sha256"],
            "source_unit": b10_unit}


def check_seed_pins(b10: Mapping, b11: Mapping) -> list[str]:
    """B10's reference seeds and B11's accepted seeds agree: the same seeds, Gate A's three among them, and each B11
    fingerprint starts with B10's e1 pin; a seed beyond Gate A's is a stage-1 a0 seed pinned by this tool (B10's full
    e1 fingerprint equals B11's; B11's source is B10's COMPLETE.json pin). Returns the seeds beyond Gate A's."""
    refs, accepted = b10["reference_units"], b11["adapter"]["accepted"]
    if set(refs) != set(accepted) or not set(GATE_A_SEEDS) <= set(refs):
        raise Refusal("B10's reference seeds and B11's accepted seeds differ (or Gate A's three are missing)")
    added = sorted(set(refs) - set(GATE_A_SEEDS))
    for seed in sorted(refs):
        e1, fingerprint = refs[seed]["fingerprint_prefixes"]["e1"], accepted[seed].get("fingerprint")
        if not (isinstance(fingerprint, str) and HEX64.match(fingerprint) and fingerprint.startswith(e1)):
            raise Refusal(f"seed {seed}: B11's accepted fingerprint does not start with B10's e1 pin")
        if seed in added:
            if seed not in STAGE1_SEEDS or e1 != fingerprint or not refs[seed]["role"].startswith("stage-1 block ") \
                    or accepted[seed].get("source_complete_sha256") != refs[seed]["complete_sha256"] \
                    or accepted[seed].get("source_unit") != refs[seed]["unit"]:
                raise Refusal(f"seed {seed}: not a stage-1 a0 seed pinned in both settings by this tool's rule")
    return added


def _literal(text: str, what: str) -> str:
    found = LITERAL.findall(text)
    if len(found) != 1:
        raise Refusal(f"{what}'s settings literal line does not occur exactly once")
    return found[0]


def _replace_literal(text: str, new: str, what: str) -> str:
    out, count = LITERAL.subn(f'SETTINGS_SHA256 = "{new}"', text)
    if count != 1:
        raise Refusal(f"{what}'s settings literal line does not occur exactly once")
    return out


def _replace_once(text: str, old: str, new: str, what: str) -> str:
    if text.count(old) != 1:
        raise Refusal(f"{what} holds the pin {old[:16]}... {text.count(old)} times, not once")
    return text.replace(old, new)


def _scan(root: Path, old: Mapping[str, str], new: Mapping[str, bytes]) -> None:
    """No old pin left in the package's code, tests, settings or mutants after the edit (the rewritten files' new
    bytes, every other file as it is): neither a whole old SHA-256 nor a settings literal's 8-character form."""
    for path in sorted((root / PKG).rglob("*")):
        relative = path.relative_to(root).as_posix()
        if not path.is_file() or path.suffix not in (".py", ".json") or "__pycache__" in path.parts \
                or path.name.startswith("notes-"):
            continue
        data = new[relative] if relative in new else path.read_bytes()
        text = data.decode("utf-8", errors="replace")
        for name, digest in old.items():
            forms = (digest, f'SETTINGS_SHA256 = "{digest[:8]}', f'SETTINGS_SHA256 = \\"{digest[:8]}')
            if any(form in text for form in forms):
                raise Refusal(f"{relative} holds the old {name} pin, which this tool does not re-take")


FILES = (B10_PY, B10_JSON, B11_PY, B11_JSON, TEST_B10, TEST_B11, MUTANTS_B10, MUTANTS_B11)


def read_package(root: Path) -> dict:
    """The package's pinned state: each file's bytes, the two settings documents (validated) and the old pins
    (each settings file at its script's literal; B10's safe_lora entry at B11's module and settings)."""
    files = {rel: _read(root / rel, rel) for rel in FILES}
    text = {rel: data.decode("utf-8") for rel, data in files.items()}
    old = {"b10_settings": _literal(text[B10_PY], B10_PY), "b11_settings": _literal(text[B11_PY], B11_PY),
           "b11_module": sha256_bytes(files[B11_PY])}
    if sha256_bytes(files[B10_JSON]) != old["b10_settings"] or sha256_bytes(files[B11_JSON]) != old["b11_settings"]:
        raise Refusal("a settings file does not hash to its script's literal: the package is not a pinned state")
    b10, b11 = s1.strict_json(files[B10_JSON]), s1.strict_json(files[B11_JSON])
    ea.validate_settings(copy.deepcopy(b10))
    from scripts.stage1_s1 import safe_lora as sl

    sl.validate_settings(copy.deepcopy(b11), old["b11_settings"])
    entry = b10["external_transforms"]["safe_lora"]
    if entry["module_sha256"] != old["b11_module"] or entry["settings"]["sha256"] != old["b11_settings"]:
        raise Refusal("B10's safe_lora entry does not pin B11's current module and settings")
    return {"files": files, "text": text, "old": old, "b10": b10, "b11": b11}


def cascade(package: Mapping, b10_new: dict, b11_new: dict) -> tuple[dict[str, bytes], dict]:
    """The new bytes of every file that hangs on the two new settings documents (module text, steps 1-5), in
    dependency order: B11's settings, B11's literal, B10's safe_lora entry, B10's settings, B10's literal, then the
    tests' literals and the mutants' find texts. Validates both documents; writes nothing."""
    from scripts.stage1_s1 import safe_lora as sl

    text, old = package["text"], package["old"]
    b10_new = copy.deepcopy(b10_new)
    new: dict[str, bytes] = {B11_JSON: canonical_json(b11_new)}
    sha = {"b11_settings": sha256_bytes(new[B11_JSON])}
    sl.validate_settings(copy.deepcopy(b11_new), sha["b11_settings"])
    new[B11_PY] = _replace_literal(text[B11_PY], sha["b11_settings"], B11_PY).encode("utf-8")
    sha["b11_module"] = sha256_bytes(new[B11_PY])
    b10_new["external_transforms"]["safe_lora"]["module_sha256"] = sha["b11_module"]
    b10_new["external_transforms"]["safe_lora"]["settings"]["sha256"] = sha["b11_settings"]
    ea.validate_settings(copy.deepcopy(b10_new))
    new[B10_JSON] = canonical_json(b10_new)
    sha["b10_settings"] = sha256_bytes(new[B10_JSON])
    new[B10_PY] = _replace_literal(text[B10_PY], sha["b10_settings"], B10_PY).encode("utf-8")
    new[TEST_B10] = _replace_once(text[TEST_B10], old["b10_settings"], sha["b10_settings"], TEST_B10).encode("utf-8")
    new[TEST_B11] = _replace_once(text[TEST_B11], old["b11_settings"], sha["b11_settings"], TEST_B11).encode("utf-8")
    mutants = _replace_once(text[MUTANTS_B10], old["b11_module"], sha["b11_module"], MUTANTS_B10)
    new[MUTANTS_B10] = _replace_once(mutants, old["b11_settings"], sha["b11_settings"], MUTANTS_B10).encode("utf-8")
    # B11-settings-pin-changed: its find is the literal's first 8 characters, its replace changes the first one
    mutants = _replace_once(text[MUTANTS_B11], _pin_text(old["b11_settings"]), _pin_text(sha["b11_settings"]),
                            MUTANTS_B11)
    new[MUTANTS_B11] = _replace_once(mutants, _pin_text(old["b11_settings"], True),
                                     _pin_text(sha["b11_settings"], True), MUTANTS_B11).encode("utf-8")
    return new, sha


def _pin_text(digest: str, changed: bool = False) -> str:
    """B11-settings-pin-changed's find (or, ``changed``, its replace) as the spec file's JSON text holds it."""
    first = ("1" if digest[0] == "0" else "0") if changed else digest[0]
    key = "replace" if changed else "find"
    return f'"{key}": ' + json.dumps(f'SETTINGS_SHA256 = "{first}{digest[1:8]}')


def repin(*, root: Path, kit: Path, seeds: Sequence[int], overrides: Mapping[int, tuple[Path, str]] | None = None,
          ) -> dict:
    """Everything in memory: the new bytes of each changed file and the proofs. Writes nothing."""
    overrides = dict(overrides or {})
    if not seeds or len(set(seeds)) != len(seeds) or any(str(s) not in STAGE1_SEEDS for s in seeds):
        raise Refusal(f"the seeds must be distinct seeds among {list(STAGE1_SEEDS)}")
    if set(overrides) - set(seeds):
        raise Refusal("a --record names a seed that is not re-pinned")
    package = read_package(root)
    files, old, b10_old, b11_old = package["files"], package["old"], package["b10"], package["b11"]
    check_seed_pins(b10_old, b11_old)
    plan = s1.strict_json(_read(kit / "plan.json", "the kit's plan.json"))
    b10_new, b11_new, pins = copy.deepcopy(b10_old), copy.deepcopy(b11_old), []
    for seed in sorted(seeds):
        key = str(seed)
        if key in b10_new["reference_units"] or key in b11_new["adapter"]["accepted"]:
            raise Refusal(f"seed {seed} is pinned already: a pin is never replaced")
        p = seed_pins(kit, plan, seed, b10_old, overrides.get(seed), root)
        b10_new["reference_units"][key] = b10_entry(p, b10_old["engine_x"])
        b11_new["adapter"]["accepted"][key] = b11_entry(p, b10_new["reference_units"][key]["unit"])
        pins.append(p)
    rule = b11_new["adapter"]["acceptance_rule"]
    if rule not in (OLD_RULE, NEW_RULE):
        raise Refusal("B11's acceptance rule text is not the one this tool knows")
    b11_new["adapter"]["acceptance_rule"] = NEW_RULE
    new, sha = cascade(package, b10_new, b11_new)
    b10_new = s1.strict_json(new[B10_JSON])
    added = check_seed_pins(b10_new, b11_new)
    _scan(root, old, new)
    proof = certification_proof(files[B10_PY], new[B10_PY], b10_old, b10_new)
    return {"files": files, "new": new, "old": old, "sha": sha, "pins": pins, "proof": proof, "added": added}


def certification_proof(old_py: bytes, new_py: bytes, b10_old: dict, b10_new: dict) -> dict:
    """B10's certification binds the script's code (its SHA-256 with the settings literal zeroed) and the certified
    settings (CERTIFIED_SETTINGS_KEYS and the certification seed's reference pin): both must be unchanged."""
    with tempfile.TemporaryDirectory() as folder:
        codes = []
        for name, data in (("old.py", old_py), ("new.py", new_py)):
            (Path(folder) / name).write_bytes(data)
            codes.append(ea.script_code_sha256(Path(folder) / name))
    certified = [ea.certified_settings_sha256(ea.settings_from_doc(copy.deepcopy(d))) for d in (b10_old, b10_new)]
    proof = {"script_code_sha256": {"old": codes[0], "new": codes[1], "equal": codes[0] == codes[1]},
             "certified_settings_sha256": {"old": certified[0], "new": certified[1],
                                           "equal": certified[0] == certified[1]}}
    if not (proof["script_code_sha256"]["equal"] and proof["certified_settings_sha256"]["equal"]):
        raise Refusal(f"the re-pin would change what B10's certification certifies: {proof}")
    return proof


def report(result: Mapping, written: str) -> dict:
    files, new = result["files"], result["new"]
    return {"kind": "stage1 B10/B11 reference-seed re-pin", "version": 1, "written": written,
            "seeds": [{"seed": p["seed"], "host": p["host"], "job": p["job"], "unit": p["unit"],
                       "complete_sha256": p["complete_sha256"], "e1_adapter_fingerprint": p["fingerprints"]["e1"],
                       "q_adapter_fingerprint": p["fingerprints"]["q"], "record": p["record"],
                       "record_sha256": p["record_sha256"],
                       "pack_input": {"name": f"gate_a_complete:{p['seed']}", "path": p["complete_path"],
                                      "sha256": p["complete_sha256"]}} for p in result["pins"]],
            "files": [{"path": rel, "old_sha256": sha256_bytes(files[rel]), "new_sha256": sha256_bytes(new[rel])}
                      for rel in sorted(new)],
            "certification": result["proof"],
            "kit_s1_code_pins": {rel: {"old": sha256_bytes(files[rel]), "new": sha256_bytes(new[rel])}
                                 for rel in (B10_PY, B11_PY, B10_JSON, B11_JSON)},
            "next": "the lead: copy or commit the files by explicit paths; re-pin runkit/stage1-olmo/stage1_rules.py "
                    "S1_CODE with kit_s1_code_pins; add each pack_input to the reference pack's inputs; run the "
                    "stage1_s1 suite and the B10/B11 mutation specs (addendum section 24 point 1)"}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="repin_reference_seeds.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--kit", required=True, help="the stage-1 kit folder (plan.json, retrieved/)")
    parser.add_argument("--seeds", required=True, help="comma-separated seeds among 1104-1107")
    parser.add_argument("--root", default=str(REPO), help="the repository root holding scripts/stage1_s1")
    where = parser.add_mutually_exclusive_group(required=True)
    where.add_argument("--out", help="a new folder for the changed files (at their repository paths)")
    where.add_argument("--in-place", action="store_true", help="write the changed files into --root")
    parser.add_argument("--record", action="append", default=[], metavar="SEED=PATH=SHA256",
                        help="a lead fingerprint record outside plan.json's outputs, by path and SHA-256")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    try:
        try:
            seeds = [int(s) for s in args.seeds.split(",")]
        except ValueError:
            raise Refusal("--seeds takes comma-separated seeds") from None
        overrides = {}
        for item in args.record:
            parts = item.split("=")
            if len(parts) != 3 or not parts[0].isdigit():
                raise Refusal("--record takes SEED=PATH=SHA256")
            overrides[int(parts[0])] = (Path(parts[1]), parts[2])
        root = Path(args.root)
        result = repin(root=root, kit=Path(args.kit), seeds=seeds, overrides=overrides)
        if args.out is not None:
            out = Path(args.out)
            if out.exists():
                raise Refusal(f"{out} exists: the re-pin writes into a new folder only")
            for rel, data in sorted(result["new"].items()):
                write_atomic(out / rel, data)
            written = str(out)
        else:
            for rel in result["new"]:                       # nothing changed since it was read
                if sha256_bytes(_read(root / rel, rel)) != sha256_bytes(result["files"][rel]):
                    raise Refusal(f"{rel} changed while the re-pin was computed")
            for rel, data in sorted(result["new"].items()):
                write_atomic(root / rel, data)
            written = f"in place: {root}"
    except (Refusal, ValueError, OSError) as exc:
        print(json.dumps({"ok": False, "refused": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps(report(result, written), indent=2, sort_keys=True))
    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
