"""The per-family O-ext settings for the 7-8B tier (R1 Track O and its fix round; Part 2 sections 1.13, 1.14, 4.2-4.5;
DES E2, E4, E5; DESO item 9; DESO2 items 24 (c), 37; the build rulings B-3, O3, O4, O11 and R-5 to R-9 of 8 Nov 2026).

    python -B scripts/scale78b/make_oext_settings_78b.py [--pins P] [--settings-dir D]          # write the files
    python -B scripts/scale78b/make_oext_settings_78b.py [--pins P] [--settings-dir D] --check  # compare with them
    python -B scripts/scale78b/make_oext_settings_78b.py --oext-78b FAMILY      # print RK OEXT_78B[FAMILY]'s form
    python -B scripts/scale78b/make_oext_settings_78b.py --oext-78b-y FAMILY    # print RK OEXT_78B_Y[FAMILY]'s form
    python -B scripts/scale78b/make_oext_settings_78b.py --w1-18-78b            # print the W1-18 pod's W1_18_78B

The 1B O-ext files pin OLMo-2-1B's prepared set, the 1B recipes, the 1B W1-18 units and the 1B cap branch. This maker
derives, for each family F (olmo2-7b, llama31-8b) and each 1B settings file below, a settings file in the 1B file's
own schema (the same kind, name and keys, so the unchanged 1B validators accept it), with every per-family value taken
from settings/oext_pins_78b.json. A pin that cannot be known yet is null in the file, and the family's index lists it
under "waits" with the event that fills it; scripts/scale78b/oext_78b.py refuses a command while a pin it needs is
null. The 1B files are read, hashed against BASE below, and never written.

Derived files (settings/<role>__<F>.json):
  limits_overrefusal_checks  W1-18's settings for F's reused side units (theta0 and the a0 units: OLMo-2-7B 1101-1103,
                             Llama-3.1-8B 1101-1102), each by its COMPLETE.json SHA-256 (RK KIT a0_units) and its
                             job.json SHA-256 where a committed record names it (else null: waits THETA0_JOB); the
                             family's prepared set and main recipe (the policy codec and the pinned judge); judge.device
                             = cuda, the pod's device (R-7)
  oext_eval                  the 1B O-ext settings with cap.branch from F's W1-18 pin ("pending_w1_18" until F's record),
                             cap.w1_18.settings_sha256 = the family's W1-18 settings above
  oext_eval_y                the same on engine Y (engine_x = ENGINE_Y; null until filled)
  oext_unit                  F's manifest; recipes.allowed = MAIN_F and F's recipe G (Llama's LR 5e-5 G: null until the
                             lead writes it, GXB O11); generation and guard blocks from MAIN_F (equal to the 1B pins,
                             plan-ab.md section 5 C3); oext.settings = oext_eval__F (path and SHA-256)
  oext_unit_y                F's manifest; recipes.allowed = B+Qi only (null until RECIPE_BQI); engine Y; oext_eval_y__F
  lean_eval_job              c0's lean job: job.allowed_recipes = MAIN_F; oext.settings = oext_eval__F; oext.branch;
                             owner = the 7-8B copy scripts/scale78b/lean_eval_job_78b.py (the file that loads it)
Plus one index per family and engine (R-5; and R-20's W1-18 index): OEXT-78B-W1__F.json (the W1-18 pod's: the W1-18
settings only, pinned by W1_18_78B), OEXT-78B__F.json (engine X: oext_unit, oext_eval, lean_eval_job and the
W1-18 settings) and OEXT-78B-Y__F.json (engine Y: oext_unit_y, oext_eval_y and the W1-18 settings oext_eval_y binds),
each with its files' SHA-256, the family's branch and manifest, and the waits of its files. Nothing pins an index but
the kit's OEXT_78B[F] (the X index) or OEXT_78B_Y[F] (the Y index); the wrapper holds no index hash and checks the
index the job names by path and SHA-256. So a fill reaches only the indexes whose files it changes: a family's branch
or theta0 job pin its own X and Y indexes; its recipe G its X index; its B+Qi its Y index; ENGINE_Y both Y indexes.

A W1-18 record (R-21) is committed under .ai/inputs/stage1-post-w1-20261023/78b/w1-18/ first; the branch fill names
its path and SHA-256 in families.<F>.w1_18 (record_path, record_sha256); the maker refuses a record that is not there
with that hash. How a pin is filled: edit settings/oext_pins_78b.json; run this maker (it writes the files); run the tests under
scripts/scale78b/tests/oext (they check consistency, not the pins' values, so they stay green: O6); print the form
(--oext-78b F or --oext-78b-y F) and fill the kit's pin by a recorded step; commit by explicit path. Nothing here reads
a model, a prepared row, an answer or a prompt. It reads the 1B settings files and the configs it names.
"""

from __future__ import annotations

import argparse
import copy
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256, load_recipe  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_DIR = HERE / "settings"
PINS_PATH = SETTINGS_DIR / "oext_pins_78b.json"
INDEX_NAMES = {"X": "OEXT-78B__{family}.json", "Y": "OEXT-78B-Y__{family}.json", "W1": "OEXT-78B-W1__{family}.json"}
# R-21: where a family's W1-18 record is committed once retrieved from the pod (its path is a pin of the pins file
# and is given at run time; the O-ext eval settings pin it by SHA-256 and kind).
RECORDS_DIR = ".ai/inputs/stage1-post-w1-20261023/78b/w1-18/"
INDEX_KIND = "scale78b oext settings index"
PINS_KIND = "scale78b oext pins"
FAMILIES = ("olmo2-7b", "llama31-8b")
BRANCHES = ("128", "full", "pending_w1_18")
PENDING = "pending_w1_18"
LEAN_COPY = "scripts/scale78b/lean_eval_job_78b.py"
# The 1B settings files, by SHA-256 (M: shasum -a 256 at MAIN 3481d85, 8 Nov 2026); a changed 1B file refuses.
BASE = {
    "limits_overrefusal_checks": ("scripts/stage1/settings/limits_overrefusal_checks.json",
                                  "bfa9a56fd0522de066cb04b6f84b99dffda54fbe4b297dc3e4c7f07961c4a41b"),
    "oext_eval": ("scripts/stage1_s1/settings/oext_eval.json",
                  "2ad9893849248a8fb61d04cf7badbd7fb398915020f196904849d500df08f5a5"),
    "oext_eval_y": ("scripts/stage1_s1/settings/oext_eval_y.json",
                    "80469a8f728d15192c360f26640c17b7ba652fbd969cfa45f43113c1defd76f0"),
    "oext_unit": ("scripts/stage1_s1/settings/oext_unit.json",
                  "3959eae7264f56f613f5d7cd54e69081d8985ef7cbce2962243f6685e3581189"),
    "oext_unit_y": ("scripts/stage1_s1/settings/oext_unit_y.json",
                    "80d08721284bbe94661d6fe2cdc58be259db8df66dc681403d7473155c715298"),
    "lean_eval_job": ("scripts/stage1_s1/settings/lean_eval_job.json",
                      "b0ab19ec28946334e4a033897c1097894fdf5797507f6a516614afc1c2c22acd"),
}
ROLES = tuple(BASE)                       # the derivation order: each file's pins come from the ones before it
# The commands of oext_78b.py and the files each reads (the waits of these roles block the command).
COMMAND_ROLES = {"unit": ("oext_unit", "oext_eval"), "unit_y": ("oext_unit_y", "oext_eval_y"),
                 "lean": ("lean_eval_job", "oext_eval"), "w1_18": ("limits_overrefusal_checks",)}
# The settings files each engine's index lists (and so each kit pin covers).
INDEX_ROLES = {"X": ("limits_overrefusal_checks", "oext_eval", "oext_unit", "lean_eval_job"),
               "Y": ("limits_overrefusal_checks", "oext_eval_y", "oext_unit_y"),
               "W1": ("limits_overrefusal_checks",)}
INDEX_COMMANDS = {"X": ("unit", "lean"), "Y": ("unit_y",), "W1": ("w1_18",)}
EVENTS = {
    "W1_18_BRANCH": "the family's 7-8B W1-18 check (DES E2; DESO2 item 37: one pod, one check per family, its own "
                    "record, GXB O4): the lead pins the record's SHA-256 and the branch it gives (128 if every unit "
                    "passes, else full; Branch full with a full_reason if the check cannot run or does not finish) in "
                    "oext_pins_78b.json families.<family>.w1_18 by a recorded step",
    "RECIPE_G": "the family's recipe-G config (DES F2; for Llama-3.1-8B the new LR 5e-5 config): the lead writes it and "
                "records its config_sha256 in oext_pins_78b.json families.<family>.recipe_g before OEXT_78B[family] "
                "is filled (GXB O11)",
    "RECIPE_BQI": "B+Qi's config on engine Y (RK RECIPE_BQI[family]; DESO2 item 24 (c)): its config_sha256 in "
                  "oext_pins_78b.json families.<family>.recipe_bqi",
    "ENGINE_Y": "addendum A13: the lead fills RK ENGINE_Y when the Y retrain is packed; the same identity in "
                "oext_pins_78b.json shared.engine_y",
    "THETA0_JOB": "theta0's job.json SHA-256 (no committed record names it): the lead hashes the side unit's job.json, "
                  "checks it equals the job_sha256 its COMPLETE.json names, and records it in oext_pins_78b.json "
                  "families.<family>.units.untuned.job_sha256 by a recorded step",
    "UNIT_JOB": "an a0 side unit's job.json SHA-256: from a committed record that names it, or by the THETA0_JOB step",
}
REQUIREMENT = {
    "limits_overrefusal_checks": "W1-18 at 7-8B (DES E2; Part 2 section 4.2): the 128-token truncation check on the "
                                 "family's reused side units (theta0 and its a0 units), by W1-18's frozen bar, run by "
                                 "scripts/scale78b/oext_78b.py w1_18 with this file; its record decides the family's "
                                 "cap branch",
    "oext_eval": "O-ext at 7-8B (Part 2 sections 4.1-4.4; DES E1, E2, E4): stage 1's O set as it is (the dev 100 plus "
                 "the sealed PHTest record), the family's cap branch from its own 7-8B W1-18 record",
    "oext_eval_y": "O-ext at 7-8B on engine Y (DESO2 item 24 (c)): the family's O-ext settings with engine Y's identity, "
                   "for B+Qi's O-ext pass",
    "oext_unit": "The O-ext unit pass at 7-8B (Part 2 sections 1.14, 4.4, 4.5; DES E4, E5): o_only, "
                 "o_only_with_regenerate and the arm step on the family's prepared set and its own recipes, through "
                 "scripts/scale78b/oext_78b.py unit",
    "oext_unit_y": "The O-ext unit pass at 7-8B on engine Y (DESO2 item 24 (c)): B+Qi's O-ext pass only",
    "lean_eval_job": "c0 at 7-8B (Part 2 section 1.13): N's R_1 at 1101 retrained under MAIN_F, then C-lean with its O "
                     "part on the 500-prompt bank, through scripts/scale78b/oext_78b.py lean",
}


def index_name(family: str, engine: str) -> str:
    return INDEX_NAMES[engine].format(family=family)


def label(path: Path) -> str:
    """A settings path label: relative to the repository root when the file lies inside it, else absolute."""
    path = Path(path).resolve()
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


def file_name(role: str, family: str) -> str:
    return f"{role}__{family}.json"


def dumps(doc: dict) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def _hex(value, what: str, nullable: bool = True):
    if value is None and nullable:
        return None
    if not isinstance(value, str) or not s1.HEX64.match(value):
        raise s1.Refusal(f"{what} must be a SHA-256{' or null' if nullable else ''}")
    return value


def load_pins(path: Path = PINS_PATH) -> tuple[dict, str]:
    data = path.read_bytes()
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version")) != (PINS_KIND, 1):
        raise s1.Refusal("oext_pins_78b.json is not the scale78b O-ext pins file (version 1)")
    if set(doc.get("families") or {}) != set(FAMILIES):
        raise s1.Refusal(f"oext_pins_78b.json must name exactly the families {list(FAMILIES)}")
    shared = doc.get("shared") or {}
    for key in ("oext_bank_sha256", "oext_record_sha256"):
        _hex(shared.get(key), f"shared.{key}", nullable=False)
    _hex(shared.get("engine_y"), "shared.engine_y")
    return doc, sha256_bytes(data)


def load_base(role: str) -> dict:
    rel, pin = BASE[role]
    data = (REPO / rel).read_bytes()
    if sha256_bytes(data) != pin:
        raise s1.Refusal(f"{rel} hashes to {sha256_bytes(data)}, the maker pins {pin}: the 1B files stay byte for byte")
    return s1.strict_json(data)


def recipe_pin(entry, what: str, nullable: bool) -> tuple[str | None, str | None, dict | None]:
    """(config name, config_sha256, the loaded recipe) of a pins entry {name, config_sha256}; the config file is read
    and its engine hash must equal the pin. Null entries give (None, None, None)."""
    if not isinstance(entry, dict) or set(entry) != {"name", "config_sha256"}:
        raise s1.Refusal(f"{what} must be {{name, config_sha256}}")
    if entry["config_sha256"] is None:
        if not nullable or entry["name"] is not None:
            raise s1.Refusal(f"{what} is null only as a whole (name and config_sha256 null)")
        return None, None, None
    digest = _hex(entry["config_sha256"], f"{what}.config_sha256", nullable=False)
    if not isinstance(entry["name"], str) or not s1.SAFE_VALUE.match(entry["name"]):
        raise s1.Refusal(f"{what}.name must be a config name")
    path = REPO / "experiments" / "safety_selection" / "configs" / f"{entry['name']}.json"
    rec = load_recipe(path)
    if config_sha256(rec) != digest:
        raise s1.Refusal(f"{what}: the config {entry['name']} hashes to {config_sha256(rec)}, the pin is {digest}")
    return entry["name"], digest, rec


def block_sha256(rec: dict, block: str) -> str:
    return sha256_bytes(canonical_json(rec[block]))


def check_w1_18_pin(w: dict, family: str) -> dict:
    if not isinstance(w, dict) or set(w) != {"branch", "record_sha256", "record_path", "full_reason"}:
        raise s1.Refusal(f"{family}: w1_18 must be {{branch, record_sha256, record_path, full_reason}}")
    path = w["record_path"]
    if (path is None) != (w["record_sha256"] is None):
        raise s1.Refusal(f"{family}: w1_18.record_path and record_sha256 are both given or both null")
    if path is not None and not (isinstance(path, str) and path.startswith(RECORDS_DIR) and path.endswith(".json")
                                 and "\\" not in path and all(q not in ("", ".", "..") for q in path.split("/"))):
        raise s1.Refusal(f"{family}: w1_18.record_path must be a plain .json path under {RECORDS_DIR} (R-21)")
    branch, record, reason = w["branch"], _hex(w["record_sha256"], f"{family} w1_18.record_sha256"), w["full_reason"]
    if branch not in BRANCHES:
        raise s1.Refusal(f"{family}: w1_18.branch must be one of {list(BRANCHES)}")
    if branch == PENDING and (record is not None or reason is not None):
        raise s1.Refusal(f"{family}: a pending branch names no W1-18 record and no reason")
    if branch == "128" and (record is None or reason is not None):
        raise s1.Refusal(f"{family}: Branch 128 needs the family's W1-18 record (a pass) and no full_reason")
    if branch == "full" and (record is None) == (reason is None):
        raise s1.Refusal(f"{family}: Branch full names the family's W1-18 record (a fail) or a full_reason, not both")
    if reason is not None and (not isinstance(reason, str) or not reason.strip()):
        raise s1.Refusal(f"{family}: w1_18.full_reason must be a text")
    return w


class Family:
    """One family's derivation: its pins, the files made so far (role -> bytes) and its waits."""

    def __init__(self, family: str, pins: dict, shared: dict, settings_dir: Path = SETTINGS_DIR):
        self.family, self.pins, self.shared, self.dir = family, pins, shared, Path(settings_dir)
        self.files: dict[str, bytes] = {}
        self.waits: dict[str, dict] = {}
        self.main_name, self.main_sha, self.main = recipe_pin(pins["main"], f"{family} main", nullable=False)
        self.g_name, self.g_sha, self.g = recipe_pin(pins["recipe_g"], f"{family} recipe_g", nullable=True)
        self.bqi_name, self.bqi_sha, self.bqi = recipe_pin(pins["recipe_bqi"], f"{family} recipe_bqi", nullable=True)
        _hex(pins.get("manifest_sha256"), f"{family} manifest_sha256", nullable=False)
        self.w1_18 = check_w1_18_pin(pins.get("w1_18"), family)
        for rec, name in ((self.g, "recipe_g"), (self.bqi, "recipe_bqi")):          # OR5: B+Qi as G
            if rec is not None and any(block_sha256(rec, b) != block_sha256(self.main, b) for b in ("generation", "guard")):
                raise s1.Refusal(f"{family}: {name}'s generation or guard block differs from MAIN's (one O-ext cap and "
                                 "one judge per family)")

    def wait(self, pin: str, role: str, where: str) -> None:
        entry = self.waits.setdefault(pin, {"pin": pin, "event": EVENTS[pin], "where": [], "roles": []})
        if where not in entry["where"]:
            entry["where"].append(where)
        if role not in entry["roles"]:
            entry["roles"].append(role)

    def sha(self, role: str) -> str:
        return sha256_bytes(self.files[role])

    def path(self, role: str) -> str:
        """The label of a role's file: the path of the file the run will load (under this settings folder)."""
        return label(self.dir / file_name(role, self.family))

    # ----- the derivations ----------------------------------------------------------------------------------------

    def limits(self) -> dict:
        doc = load_base("limits_overrefusal_checks")
        units = self.pins["units"]
        if not isinstance(units, dict) or "untuned" not in units or len(units) < 2:
            raise s1.Refusal(f"{self.family}: units must hold the untuned unit and the a0 units")
        out = {}
        for name, spec in sorted(units.items()):
            keys = {"path", "seed", "checkpoint", "complete_sha256", "job_sha256", "recipe_label"}
            if not isinstance(spec, dict) or set(spec) != keys:
                raise s1.Refusal(f"{self.family}: unit {name} must have exactly the keys {sorted(keys)}")
            _hex(spec["complete_sha256"], f"{self.family} unit {name} complete_sha256", nullable=False)
            if _hex(spec["job_sha256"], f"{self.family} unit {name} job_sha256") is None:
                self.wait("THETA0_JOB" if name == "untuned" else "UNIT_JOB", "limits_overrefusal_checks",
                          f"families.{self.family}.units.{name}.job_sha256")
            out[name] = {"arm": "a0", "checkpoint": spec["checkpoint"], "complete_sha256": spec["complete_sha256"],
                         "job_sha256": spec["job_sha256"], "path": spec["path"], "recipe_label": spec["recipe_label"],
                         "seed": spec["seed"]}
        doc["units"] = out
        doc["prepared"]["manifest_sha256"] = self.pins["manifest_sha256"]
        doc["prepared"]["path"] = self.pins["prepared_path"]
        recipe_rel = f"experiments/safety_selection/configs/{self.main_name}.json"
        guard = self.main["guard"]
        doc["judge"].update(recipe=recipe_rel, recipe_file_sha256=sha256_file(REPO / recipe_rel),
                            repo_id=guard["repo_id"], revision=guard["revision"], device="cuda")
        doc["allow_list"]["path_pattern"] = self.pins["path_pattern"]
        doc["allow_list"]["rule"] = ("only the family's reused side units (P78 section 2.1, ruling 7; RK KIT a0_units): "
                                     "theta0 (a0 at init) and the a0 units at e1 of the family's side probes, under the "
                                     "data root; a refused recipe refuses")
        doc["requirement"] = REQUIREMENT["limits_overrefusal_checks"]
        doc["units_source"] = (f"{self.family}: RK KIT a0_units (COMPLETE.json SHA-256); the a0 units' job.json SHA-256 "
                               "from the committed G1 record named in oext_pins_78b.json job_source; theta0's by a "
                               "recorded lead step (null until then)")
        doc["pins"] = ("every unit is pinned by its COMPLETE.json and job.json SHA-256 (a unit without both pins "
                       "refuses, as at 1B); the prepared set by the family's manifest; the judge by the family's main "
                       "recipe file (the policy codec) and its guard block (equal to the 1B O-ext pins)")
        return doc

    def oext_eval(self, base: str, engine_x) -> dict:
        doc = load_base(base)
        w = self.w1_18
        doc["cap"]["branch"] = w["branch"]
        doc["cap"]["w1_18"].update(settings_sha256=self.sha("limits_overrefusal_checks"), record_sha256=w["record_sha256"],
                                   full_reason=w["full_reason"])
        if w["branch"] == PENDING:
            self.wait("W1_18_BRANCH", base, f"families.{self.family}.w1_18")
        doc["bank"]["phtest"]["record_sha256"] = self.shared["oext_record_sha256"]
        doc["engine_x"] = engine_x
        doc["requirement"] = REQUIREMENT[base]
        return doc

    def oext_unit(self, base: str, eval_role: str, allowed: dict, engine_x) -> dict:
        doc = load_base(base)
        doc["prepared"]["manifest_sha256"] = self.pins["manifest_sha256"]
        doc["recipes"]["allowed"] = allowed
        doc["recipes"]["generation_sha256"] = block_sha256(self.main, "generation")
        doc["recipes"]["guard_sha256"] = block_sha256(self.main, "guard")
        doc["recipes"]["rule"] = (f"{self.family}: only the named recipes (MAIN_F and the family's recipe G on engine X; "
                                  "B+Qi only on engine Y), each by its config SHA-256; one generation block and one "
                                  "guard block (MAIN_F's, equal to the 1B O-ext pins: plan-ab.md section 5 C3)")
        doc["oext"]["settings"] = {"path": self.path(eval_role), "sha256": self.sha(eval_role)}
        doc["engine_x"] = engine_x
        doc["requirement"] = REQUIREMENT[base]
        return doc

    def lean(self) -> dict:
        doc = load_base("lean_eval_job")
        doc["job"]["allowed_recipes"] = {self.main_name: self.main_sha}
        doc["oext"]["settings"] = {"path": self.path("oext_eval"), "sha256": self.sha("oext_eval")}
        doc["oext"]["branch"] = self.w1_18["branch"]
        if self.w1_18["branch"] == PENDING:
            self.wait("W1_18_BRANCH", "lean_eval_job", f"families.{self.family}.w1_18")
        doc["owner"] = LEAN_COPY
        doc["requirement"] = REQUIREMENT["lean_eval_job"]
        doc["c0_estimate"] = ("7-8B: the E values of Part 2 sections 1.15 and 4.3 (the c0 pod's E cap and the O-ext term "
                              "x 1.5 until measured); c0 is a cost measurement, and only its ledger is read")
        return doc

    def derive(self) -> dict[str, bytes]:
        engine_y = self.shared.get("engine_y")
        x = load_base("oext_unit")["engine_x"]
        self.files["limits_overrefusal_checks"] = dumps(self.limits())
        self.files["oext_eval"] = dumps(self.oext_eval("oext_eval", x))
        if engine_y is None:
            for role in ("oext_eval_y", "oext_unit_y"):
                self.wait("ENGINE_Y", role, "shared.engine_y")
        self.files["oext_eval_y"] = dumps(self.oext_eval("oext_eval_y", engine_y))
        allowed = {"MAIN": self.main_sha, "G": self.g_sha}
        if self.g_sha is None:
            self.wait("RECIPE_G", "oext_unit", f"families.{self.family}.recipe_g")
        self.files["oext_unit"] = dumps(self.oext_unit("oext_unit", "oext_eval", allowed, x))
        if self.bqi_sha is None:
            self.wait("RECIPE_BQI", "oext_unit_y", f"families.{self.family}.recipe_bqi")
        self.files["oext_unit_y"] = dumps(self.oext_unit("oext_unit_y", "oext_eval_y", {"B+Qi": self.bqi_sha},
                                                         engine_y))
        self.files["lean_eval_job"] = dumps(self.lean())
        return {file_name(role, self.family): data for role, data in self.files.items()}

    def index_doc(self, engine: str) -> dict:
        """The family's index for one engine: its files, the waits of its files (each wait's roles cut to this index's
        roles), the family's manifest, the other families' manifest pins (fixed: for a refusal that names them) and the
        fixed bases. The X and Y indexes also carry the family's branch and W1-18 record pin, the engine identity the
        files are written for (R-23) and the O-ext inputs; the W1 index (the W1-18 pod's, R-20) carries none of them,
        so only a W1-18 settings fill (theta0's or a unit's job pin) changes it."""
        roles = INDEX_ROLES[engine]
        waits = []
        for key in sorted(self.waits):
            entry = self.waits[key]
            mine = [r for r in entry["roles"] if r in roles]
            if mine:
                waits.append({**entry, "roles": mine})
        doc = {"kind": INDEX_KIND, "version": 2, "family": self.family, "engine": engine,
               "manifest_sha256": self.pins["manifest_sha256"],
               "files": {role: {"file": file_name(role, self.family), "sha256": self.sha(role)} for role in roles},
               "waits": waits, "commands": list(INDEX_COMMANDS[engine]),
               "base": {role: {"path": rel, "sha256": sha} for role, (rel, sha) in BASE.items()}}
        if engine != "W1":
            doc.update(branch=self.w1_18["branch"], w1_18_record_sha256=self.w1_18["record_sha256"],
                       w1_18_record_path=self.w1_18["record_path"],
                       engine_identity=load_base("oext_unit")["engine_x"] if engine == "X" else self.shared["engine_y"],
                       inputs={"oext_bank": self.shared["oext_bank_sha256"],
                               "oext_record": self.shared["oext_record_sha256"]})
        return doc


def verify_records(pins: dict, records_root: Path = REPO) -> None:
    """R-21: a pinned W1-18 record is committed at its path and hashes to its pin (the maker's write and check).
    ``records_root`` is the folder the record paths are relative to (the repository root; another folder only for a
    dry run on copies)."""
    for family, fam in pins["families"].items():
        w = fam["w1_18"]
        if w.get("record_path") is None:
            continue
        path = Path(records_root) / w["record_path"]
        try:
            digest = sha256_file(path)
        except OSError as exc:
            raise s1.Refusal(f"{family}: the W1-18 record at its pinned path cannot be read ({type(exc).__name__})") \
                from None
        if digest != w["record_sha256"]:
            raise s1.Refusal(f"{family}: the W1-18 record hashes to {digest}, the pin is {w['record_sha256']}")


def derive_all(pins: dict, pins_sha256: str | None = None, settings_dir: Path = SETTINGS_DIR) -> dict[str, bytes]:
    """Every derived file's bytes (name -> bytes), each family's two indexes last. ``pins_sha256`` is not recorded
    (an index records nothing that another family's or engine's fill changes, R-5)."""
    files: dict[str, bytes] = {}
    indexes: dict[str, bytes] = {}
    fams = {family: Family(family, pins["families"][family], pins["shared"], settings_dir) for family in FAMILIES}
    for family, fam in fams.items():
        files.update(fam.derive())
    manifests = {family: fam.pins["manifest_sha256"] for family, fam in fams.items()}
    for family, fam in fams.items():
        for engine in INDEX_NAMES:
            doc = fam.index_doc(engine)
            doc["other_manifests"] = {f: m for f, m in manifests.items() if f != family}
            indexes[index_name(family, engine)] = dumps(doc)
    files.update(indexes)
    return files


def form(family: str, engine: str, files: dict[str, bytes], code: dict[str, str]) -> dict:
    """RK OEXT_78B[family]'s (engine X) or OEXT_78B_Y[family]'s (engine Y) documented form, {files: {path under
    scripts/: SHA-256}, inputs: {oext_bank, oext_record}}, for the lead's recorded fill: the wrapper and the files the
    engine's commands run (``code``: path -> SHA-256), the family's index for that engine and every settings file it
    lists. (Under Branch 128, or a Branch full with a record, the family's W1-18 record joins the X and Y files: P2
    section 4.4; the lead adds it with the branch fill.)"""
    name = index_name(family, engine)
    index = s1.strict_json(files[name])
    out = dict(code)
    out[f"scripts/scale78b/settings/{name}"] = sha256_bytes(files[name])
    for entry in index["files"].values():
        out[f"scripts/scale78b/settings/{entry['file']}"] = entry["sha256"]
    return {"files": dict(sorted(out.items())), "inputs": dict(index["inputs"])}


def w1_18_78b_form(files: dict[str, bytes], code: dict[str, str]) -> dict:
    """R-20: the W1-18 pod's route pin W1_18_78B: {files: {path under scripts/: SHA-256}} (K1's form: the wrapper, the
    w1_18 command's run files, and per family its W1 index and W1-18 settings) and, beside it, side_units: per family
    each side unit by path (under the data root) and its COMPLETE.json and job.json SHA-256 (the W1-18 settings pin
    them; they are listed so the pod's files list can name them)."""
    out, units = dict(code), {}
    for family in FAMILIES:
        name = index_name(family, "W1")
        index = s1.strict_json(files[name])
        out[f"scripts/scale78b/settings/{name}"] = sha256_bytes(files[name])
        for entry in index["files"].values():
            out[f"scripts/scale78b/settings/{entry['file']}"] = entry["sha256"]
        limits = s1.strict_json(files[file_name("limits_overrefusal_checks", family)])
        units[family] = {n: {"path": u["path"], "complete_sha256": u["complete_sha256"], "job_sha256": u["job_sha256"]}
                         for n, u in sorted(limits["units"].items())}
    return {"files": dict(sorted(out.items())), "side_units": units}


def oext_78b_form(family: str, files: dict[str, bytes], code: dict[str, str]) -> dict:
    return form(family, "X", files, code)


def oext_78b_y_form(family: str, files: dict[str, bytes], code: dict[str, str]) -> dict:
    return form(family, "Y", files, code)


def wrapper_module():
    """This checkout's oext_78b.py, loaded by its file path beside this file (O11: never another root's copy)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("scale78b_oext_78b_of_the_maker", HERE / "oext_78b.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--pins", type=Path, default=None, help="the pins file (default settings/oext_pins_78b.json)")
    ap.add_argument("--settings-dir", type=Path, default=None, help="where the files are written or checked "
                    "(default this folder's settings/; another folder for a fill dry run)")
    ap.add_argument("--check", action="store_true", help="derive in memory and compare with the files on disk")
    ap.add_argument("--oext-78b", choices=FAMILIES, help="print RK OEXT_78B[FAMILY]'s form (engine X)")
    ap.add_argument("--oext-78b-y", choices=FAMILIES, help="print RK OEXT_78B_Y[FAMILY]'s form (engine Y)")
    ap.add_argument("--w1-18-78b", action="store_true", help="print the W1-18 pod's route pin W1_18_78B (R-20)")
    ap.add_argument("--records-root", type=Path, default=None, help="the folder the W1-18 record paths are relative to "
                    "(default the repository root; another folder for a dry run on copies)")
    args = ap.parse_args(argv)
    settings_dir = SETTINGS_DIR if args.settings_dir is None else args.settings_dir
    try:
        pins, pins_sha = load_pins(PINS_PATH if args.pins is None else args.pins)
        files = derive_all(pins, pins_sha, settings_dir)
        verify_records(pins, REPO if args.records_root is None else args.records_root)
    except (s1.Refusal, OSError, ValueError) as exc:
        print(f"REFUSED: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    if args.w1_18_78b:
        print(json.dumps(w1_18_78b_form(files, wrapper_module().code_pins("W1")), indent=2, sort_keys=True))
        return 0
    if args.oext_78b or args.oext_78b_y:
        wrapper = wrapper_module()
        family, engine = (args.oext_78b, "X") if args.oext_78b else (args.oext_78b_y, "Y")
        print(json.dumps(form(family, engine, files, wrapper.code_pins(engine)), indent=2, sort_keys=True))
        return 0
    if args.check:
        bad = sorted(n for n, d in files.items() if not (settings_dir / n).is_file()
                     or (settings_dir / n).read_bytes() != d)
        if bad:
            print(f"DIFFERS: {len(bad)} files differ from the derivation (first: {bad[0]})", file=sys.stderr)
            return 1
        print(f"checked {len(files)} files; " + "; ".join(
            f"{n} {sha256_bytes(files[n])}" for n in sorted(files) if n.startswith("OEXT-78B")))
        return 0
    settings_dir.mkdir(parents=True, exist_ok=True)
    for name, data in files.items():
        (settings_dir / name).write_bytes(data)
    for name in sorted(files):
        print(f"{sha256_bytes(files[name])}  {name}")
    print("next: run the tests under scripts/scale78b/tests/oext; print the forms (--oext-78b F, --oext-78b-y F) "
          "for the kit's pins")
    return 0


if __name__ == "__main__":
    sys.exit(main())
