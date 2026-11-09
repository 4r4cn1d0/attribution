"""The 7-8B O-ext layer: the 1B O-ext entry points run with a family's settings (R1 Track O and its fix round; Part 2
sections 1.13, 1.14, 4.2-4.5; DES E2, E4, E5; DESO item 9; DESO2 items 24 (c), 37; the build rulings B-3, O3, O4,
O11 and R-5 to R-9).

Every command names the family, the engine and the family's index for that engine, by path and SHA-256 (the kit takes
both from OEXT_78B[F] for engine X or OEXT_78B_Y[F] for engine Y; R-5). This file holds no index hash, so no pin fill
changes it:

    python -B scripts/scale78b/oext_78b.py unit  --family F [--engine X|Y] --index IDX --index-sha256 H
        run (--run UNIT --checkpoint e1 | --untuned) --prepared P --recipe REC --oext-bank F --oext-record F
        [--w1-18-record F] [--dev100-source SOURCE] --out DIR
    python -B scripts/scale78b/oext_78b.py lean  --family F --index IDX --index-sha256 H run --job JOB --prepared P
        --recipe REC --out OUT [--registry REG] [--expect-adapter-fingerprint HEX] --oext-bank F --oext-record F
        [--w1-18-record F]
    python -B scripts/scale78b/oext_78b.py lean  --family F --index IDX --index-sha256 H verify --out OUT
    python -B scripts/scale78b/oext_78b.py w1_18 --family F --index W1IDX --index-sha256 H --out DIR [--data-root DIR]
        [--device D] [--guard-batch-size N]
    python -B scripts/scale78b/oext_78b.py check --family F [--engine X|Y|W1] --index IDX --index-sha256 H
        [--w1-18-record F] [--data-root DIR]                        ($0, on the Mac: see "The check" below)

    IDX is settings/OEXT-78B__F.json (engine X, pinned by OEXT_78B[F]) or settings/OEXT-78B-Y__F.json (engine Y,
    OEXT_78B_Y[F]); W1IDX is settings/OEXT-78B-W1__F.json, the W1-18 pod's index (the family's W1-18 settings only,
    pinned by W1_18_78B: R-20; no branch, G, B+Qi or ENGINE_Y fill changes it). The settings files are read from the
    index's folder. Each leading option is given at most once (OR9).

    command  what runs (its own main(), its own arguments, outputs, prints and exit codes)          settings (per F)
    unit     scripts/stage1_s1/oext_unit.py run (o_only, o_only_with_regenerate, the arm step)       oext_unit__F,
             (``transfer``, LN-14's report, is refused: not run at 7-8B, DESO2 item 32)            oext_eval__F
    unit Y   the same with engine Y's files (B+Qi's O-ext pass, DESO2 item 24 (c))                 oext_unit_y__F, oext_eval_y__F
    lean     scripts/scale78b/lean_eval_job_78b.py (c0's lean job; the 7-8B copy of               lean_eval_job__F,
             scripts/stage1_s1/lean_eval_job.py, DES E4's copy route: see that file's head)          oext_eval__F
    w1_18    scripts/stage1/limits/overrefusal_checks.py (the family's 7-8B W1-18 check; one run    limits_overrefusal_checks__F
             per family on the one W1-18 pod, each with its own record: GXB O4)

How it runs a 1B entry point (the scorers_78b.py pattern): the module is imported and its file hashed against CODE (a
changed file refuses); the index is read and hashed against the SHA-256 the job names, and it must be the named
family's index for the named engine; each settings file it lists is read and hashed against the index; for that call
only, the module globals that name the settings point at the family's files, and they are restored afterwards, also
when the 1B code raises:
  - oext_unit.load_pinned_settings and oext_eval.load_pinned_settings load the family's files by path and SHA-256
    (their 1B defaults are bound at definition, oext_unit.py:209, oext_eval.py:246, so main() would read the 1B files);
  - oext_unit.OEXT_SETTINGS_PATH (oext_unit.py:75, :146) and the lean copy's OEXT_SETTINGS_PATH name the family's
    oext_eval file, the file that is read (the label comes from the index entry of the loaded file, never from the
    settings file's own text), so a settings file whose oext.settings.path names another file refuses;
  - overrefusal_checks.SETTINGS_PATH and SETTINGS_SHA256 (overrefusal_checks.py:83-84) name the family's W1-18
    settings: oext_eval's W1-18 binding (oext_eval.py:214-236) reads them, and the w1_18 command passes --settings with
    that file (:533, :542); so the family's W1-18 record's provenance.settings_sha256 is the family's W1-18 settings,
    which oext_eval__F's cap.w1_18.settings_sha256 pins (:374-375);
  - the lean copy's SETTINGS_PATH and SETTINGS_SHA256 (read at call time by load_lean_settings, :849).
No record, settings file or output names a file the run did not load (GXB O3). Nothing else is written; the outputs are
the 1B code's own, byte for byte (tests/oext parity).

Before the call (refusals exit 2 with one JSON line on stderr; they name hashes, flags, pins and events, never text):
  - every ``-`` token is a full flag name of the 1B command (the 1B parsers expand abbreviations; scorers_78b RV-E-1);
  - every pin the command's files need is filled (the index's "waits": the family's W1-18 branch, Llama's recipe G,
    B+Qi and ENGINE_Y for engine Y, theta0's job.json pin for W1-18), else the refusal names the pin and its event;
  - ``--prepared`` is the family's prepared set (its manifest.json hashes to the family's pin; the other family's
    manifest refuses by both hashes); the unit settings' manifest is the index's;
  - ``--w1-18-record`` is given exactly when the family's O-ext settings pin a W1-18 record, and hashes to that pin
    (Branch 128's flag on every O-ext kind, DESO item 9); ``--dev100-source`` only on ``--run`` under Branch 128 (the
    regenerated units, LN-19); the 1B code checks both again.
The lean command imports the lean copy before anything else, so c0's timer origin (the copy's first statements) still
comes before torch and the engine are imported.

The check ($0; the pack runs it before any O-ext pod, R-6, and the lead runs it on the side units, R-9):
  - the run files against CODE, the index against the named SHA-256, each listed file against the index; every
    settings file through its unchanged 1B validator with its true label (the W1-18 binding included), under the
    index's engine identity (engine X's, or engine Y's once ENGINE_Y is filled: R-23). A file that waits on a null
    pin prints "waits" (exit 0) only when the validator passes it with every field its waits null (WAIT_FIELDS; a
    null ENGINE_Y too) replaced by a placeholder, so the rest of the file is fully validated; any refusal exits 2
    (OR8; W2-3 of R1's second re-verification, R2). The waits per command;
  - with ``--w1-18-record F``: the record through the unchanged oext_eval reader (read_w1_18) under the family's
    O-ext settings and W1-18 globals (its hash is the pin, it was made under the family's W1-18 settings, its verdict
    is the pinned branch's), and its units are the family's W1-18 units; a wrong-family, stale or wrong-branch record
    refuses on the Mac;
  - with ``--data-root DIR``: each side unit the W1-18 settings list, as strictly as W1-18's own unit gate allows
    without parsing (OR2): its path in the settings' allow-list form and inside the data root; its COMPLETE.json read
    by its pin, a complete marker; every file W1-18 reads (job.json and eval/<checkpoint>/generations.jsonl and
    guard.jsonl) listed by name with a SHA-256 and each present file hashing to it; W1-18's frozen sealed check
    (limits_common.frozen_reader(...).sealed: every listed file present with its hash); eval/ holding exactly the
    checkpoint's folder; job.json equal to its pin where the pin is filled. Bytes are hashed, never parsed; no answer
    content is opened. It prints names, states and hashes only: a value that is not a SHA-256 is reported by its key,
    never printed (OR7).
"""

from __future__ import annotations

import contextlib
import copy
import functools
import hashlib
import importlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

INDEX_KIND = "scale78b oext settings index"
INDEX_VERSION = 2
INDEX_NAMES = {"X": "OEXT-78B__{family}.json", "Y": "OEXT-78B-Y__{family}.json", "W1": "OEXT-78B-W1__{family}.json"}
FAMILIES = ("olmo2-7b", "llama31-8b")
ENGINES = ("X", "Y", "W1")
COMMAND_ENGINES = {"unit": ("X", "Y"), "lean": ("X",), "w1_18": ("W1",), "check": ("X", "Y", "W1")}
COMMANDS = ("unit", "lean", "w1_18", "check")
LEAN_MODULE = "scripts.scale78b.lean_eval_job_78b"
HEX64 = re.compile(r"^[0-9a-f]{64}$")
# The modules the commands run or bind, by the SHA-256 of their files (M: shasum -a 256 at MAIN 3481d85, 8 Nov 2026;
# the 1B files equal Part 2 section 1.17 Table B where it lists them). A changed file refuses.
CODE = {
    "scripts.stage1.s1common": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",
    "scripts.stage1.limits.limits_common": "2798aa06a01fd89bf3dd8dc2abf33e63bfcb4f17bff700a709eacd2b3ace264c",
    "scripts.stage1.limits.overrefusal_checks": "ed5fd2dcb5675d5fe5e135b76e37ece2488dfcc2db5129ba422064502b0d61ae",
    "scripts.stage1_s1.oext_eval": "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719",
    "scripts.stage1_s1.oext_unit": "ae2fb5b5fbea36cbd2b27c4eaa20f10504b9856961ae8ee100311c923876b8e3",
    LEAN_MODULE: "fc0372ca006c478f9b4b3bff3c903f9d15f774b94c61a6b4aca98973c400e4a7",
}
COMMAND_CODE = {
    "unit": ("scripts.stage1.s1common", "scripts.stage1.limits.limits_common", "scripts.stage1.limits.overrefusal_checks",
             "scripts.stage1_s1.oext_eval", "scripts.stage1_s1.oext_unit"),
    "lean": (LEAN_MODULE, "scripts.stage1.s1common", "scripts.stage1.limits.limits_common",
             "scripts.stage1.limits.overrefusal_checks", "scripts.stage1_s1.oext_eval"),
    "w1_18": ("scripts.stage1.s1common", "scripts.stage1.limits.limits_common",
              "scripts.stage1.limits.overrefusal_checks"),
}
ENGINE_CODE = {"X": tuple(CODE), "Y": COMMAND_CODE["unit"], "W1": COMMAND_CODE["w1_18"]}   # what each kit pin covers
# The settings roles whose waits block each command. Every O-ext command also reads the family's W1-18 settings
# (oext_eval's binding hashes them, so the index pins them), but only the w1_18 command needs their unit pins.
NEEDS = {"unit": ("oext_unit", "oext_eval"), "unit_y": ("oext_unit_y", "oext_eval_y"),
         "lean": ("lean_eval_job", "oext_eval"), "w1_18": ("limits_overrefusal_checks",)}
ENGINE_KEYS = {"X": ("unit", "lean"), "Y": ("unit_y",), "W1": ("w1_18",)}
# OR8 and W2-3 (R2): the settings fields each null pin nulls (UNIT_JOB's: every a0 unit's null job pin). A role that
# waits is validated with these fields replaced by PLACEHOLDER, so "waits" means every other part of the file is valid
# (the 1B validator stops at its first refusal, so a fault after a null pin would otherwise go unseen); W1_18_BRANCH
# nulls no field (pending is a value the 1B validators accept).
WAIT_FIELDS = {"THETA0_JOB": ("units.untuned.job_sha256",), "RECIPE_G": ("recipes.allowed.G",),
               "RECIPE_BQI": ("recipes.allowed.B+Qi",), "ENGINE_Y": ("engine_x",)}
PLACEHOLDER = "0" * 64                     # a placeholder SHA-256 (and engine identity) for the check only
# Every '-' token must be one of these full names (the name before any '='); the first token is the 1B subcommand.
SUBCOMMANDS = {"unit": ("run",), "lean": ("run", "verify"), "w1_18": (None,), "check": (None,)}
ALLOWED_FLAGS = {
    ("unit", "run"): frozenset({"--run", "--untuned", "--checkpoint", "--prepared", "--recipe", "--oext-bank",
                                "--oext-record", "--w1-18-record", "--dev100-source", "--out"}),
    ("lean", "run"): frozenset({"--job", "--prepared", "--recipe", "--out", "--registry",
                                "--expect-adapter-fingerprint", "--oext-bank", "--oext-record", "--w1-18-record"}),
    ("lean", "verify"): frozenset({"--out"}),
    ("w1_18", None): frozenset({"--out", "--data-root", "--device", "--guard-batch-size"}),
    ("check", None): frozenset({"--w1-18-record", "--data-root"}),
}
LEADING = ("--family", "--engine", "--index", "--index-sha256")
W1_18_UNIT_FILES = ("job.json", "eval/{checkpoint}/generations.jsonl", "eval/{checkpoint}/guard.jsonl")
EXIT_REFUSED = 2


class Refused(Exception):
    """A refusal of the wrapper before any 1B code runs (exit 2, nothing written)."""


# ----- small helpers (standard library: the lean copy is imported before the engine) ------------------------------


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def sha256_file(path: Path) -> str:
    return sha256_bytes(Path(path).read_bytes())


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refused("a JSON object repeats a key")
        out[key] = value
    return out


def strict_json(data: bytes):
    try:
        return json.loads(data, object_pairs_hook=_no_duplicates)
    except ValueError:
        raise Refused("the bytes are not valid JSON") from None


def module(name: str):
    return importlib.import_module(name)


def check_code(names) -> dict[str, str]:
    """Each module imported and its file hashed against CODE; returns {module: SHA-256}."""
    out = {}
    for name in names:
        digest = sha256_file(Path(module(name).__file__).resolve())
        if digest != CODE[name]:
            raise Refused(f"{name} hashes to {digest}, the wrapper pins {CODE[name]}: the run files stay byte for byte")
        out[name] = digest
    return out


def code_pins(engine: str = "X") -> dict[str, str]:
    """The files an engine's commands run, as {path under scripts/: SHA-256} (the kit forms' files), with this file."""
    out = {f"{name.replace('.', '/')}.py": CODE[name] for name in ENGINE_CODE[engine]}
    out["scripts/scale78b/oext_78b.py"] = sha256_file(Path(__file__).resolve())
    return out


def label(path: Path) -> str:
    """The settings path label of a file (the path a settings file names): relative to the repository root when the
    file lies inside it, else absolute."""
    path = Path(path).resolve()
    try:
        return path.relative_to(REPO).as_posix()
    except ValueError:
        return str(path)


class Index:
    """The family's index for one engine, named by the job by path and SHA-256 (R-5); the settings files lie beside
    it."""

    def __init__(self, path: str | Path, expected_sha256: str, family: str, engine: str):
        if family not in FAMILIES:
            raise Refused(f"--family must be one of {list(FAMILIES)}")
        if not isinstance(expected_sha256, str) or not HEX64.match(expected_sha256):
            raise Refused("--index-sha256 must be a SHA-256 (64 lowercase hex)")
        path = Path(path)
        wanted = INDEX_NAMES[engine].format(family=family)
        if path.name != wanted:
            raise Refused(f"--index names {path.name}; the {family} engine-{engine} index is {wanted}")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise Refused(f"the index {path.name} cannot be read ({type(exc).__name__})") from None
        digest = sha256_bytes(data)
        if digest != expected_sha256:
            raise Refused(f"{path.name} hashes to {digest}, the job names {expected_sha256}")
        doc = strict_json(data)
        if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version")) != (INDEX_KIND, INDEX_VERSION) or \
                (doc.get("family"), doc.get("engine")) != (family, engine):
            raise Refused(f"{path.name} is not the scale78b O-ext index of {family} on engine {engine}")
        self.family, self.engine, self.doc, self.sha256 = family, engine, doc, digest
        self.dir = path.parent
        self.manifest = doc["manifest_sha256"]
        self.other_manifests = dict(doc.get("other_manifests") or {})

    def waits_for(self, roles) -> list[dict]:
        return [w for w in self.doc["waits"] if set(w["roles"]) & set(roles)]

    def require(self, key: str) -> None:
        waits = self.waits_for(NEEDS[key])
        if waits:
            first = waits[0]
            raise Refused(f"{self.family}: the pin {first['pin']} is null ({', '.join(first['where'])}; "
                          f"{len(waits)} pins wait for this command): {first['event']}")

    def file(self, role: str) -> tuple[Path, str, dict]:
        """(path, SHA-256, document) of a role's settings file, its bytes equal to the index's pin."""
        entry = (self.doc["files"] or {}).get(role)
        if entry is None:
            raise Refused(f"the {self.family} engine-{self.engine} index lists no {role} file")
        path = self.dir / entry["file"]
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise Refused(f"{entry['file']} cannot be read ({type(exc).__name__})") from None
        if sha256_bytes(data) != entry["sha256"]:
            raise Refused(f"{entry['file']} hashes to {sha256_bytes(data)}, the index pins {entry['sha256']}")
        return path, entry["sha256"], strict_json(data)

    def label(self, role: str) -> str:
        return label(self.dir / self.doc["files"][role]["file"])


# ----- the command line ----------------------------------------------------------------------------------------------


def split_argv(argv: list[str]) -> tuple[str, dict, list[str]]:
    """(command, {family, engine, index, index_sha256}, the 1B arguments): the leading options come first, before
    the 1B arguments."""
    if not argv or argv[0] not in COMMANDS:
        raise Refused(f"the first argument must be one of {list(COMMANDS)}")
    command, rest = argv[0], list(argv[1:])
    opts = {"family": None, "engine": None, "index": None, "index_sha256": None}
    seen = set()
    while rest and rest[0].split("=", 1)[0] in LEADING:
        token = rest.pop(0)
        name, _, value = token.partition("=")
        if name in seen:
            raise Refused(f"{name} is given twice")
        seen.add(name)
        if not value:
            if not rest:
                raise Refused(f"{name} needs a value")
            value = rest.pop(0)
        opts[name[2:].replace("-", "_")] = value
    if opts["engine"] is None:
        opts["engine"] = COMMAND_ENGINES[command][0]
    if opts["family"] is None:
        raise Refused("--family is required (olmo2-7b or llama31-8b)")
    if opts["family"] not in FAMILIES:
        raise Refused(f"--family must be one of {list(FAMILIES)}")
    if opts["engine"] not in COMMAND_ENGINES[command]:
        raise Refused(f"--engine for {command} is one of {list(COMMAND_ENGINES[command])} (Y: B+Qi's O-ext pass, DESO2 "
                      "item 24 (c); W1: the W1-18 pod's index, R-20)")
    if opts["index"] is None or opts["index_sha256"] is None:
        raise Refused("--index and --index-sha256 are required: the family's index for the engine, by the path and "
                      "SHA-256 the kit's OEXT_78B[F] (engine X) or OEXT_78B_Y[F] (engine Y) names (R-5)")
    return command, opts, rest


def check_flags(command: str, args: list[str]) -> str | None:
    """The 1B subcommand (or None for w1_18 and check) after every '-' token is checked against ALLOWED_FLAGS."""
    sub = None
    if SUBCOMMANDS[command] != (None,):
        if not args or args[0] not in SUBCOMMANDS[command]:
            hint = " (LN-14's transfer report is not run at 7-8B: DESO2 item 32)" if args[:1] == ["transfer"] else ""
            raise Refused(f"{command} takes the 1B subcommand {list(SUBCOMMANDS[command])} first{hint}")
        sub = args[0]
        args = args[1:]
    allowed = ALLOWED_FLAGS[(command, sub)]
    for token in args:
        if token.startswith("-") and token.split("=", 1)[0] not in allowed:
            raise Refused(f"{token.split('=', 1)[0]} is not a full flag name of {command} {sub or ''}".rstrip() +
                          f" (allowed: {sorted(allowed)})")
    return sub


def flag_values(args: list[str], name: str) -> list[str]:
    out, i = [], 0
    while i < len(args):
        token = args[i]
        if token == name:
            if i + 1 >= len(args):
                raise Refused(f"{name} needs a value")
            out.append(args[i + 1])
            i += 2
            continue
        if token.startswith(name + "="):
            out.append(token[len(name) + 1:])
        i += 1
    return out


def one_value(args: list[str], name: str) -> str | None:
    values = flag_values(args, name)
    if len(values) > 1:
        raise Refused(f"{name} is given {len(values)} times")
    return values[0] if values else None


def check_prepared(args: list[str], idx: Index) -> None:
    """--prepared is the family's prepared set: its manifest.json hashes to the family's pin (the index's)."""
    prepared = one_value(args, "--prepared")
    if prepared is None:
        return                                    # the 1B parser refuses a missing --prepared
    try:
        digest = sha256_file(Path(prepared) / "manifest.json")
    except OSError as exc:
        raise Refused(f"--prepared holds no readable manifest.json ({type(exc).__name__})") from None
    if digest != idx.manifest:
        which = " (the other family's manifest)" if digest in idx.other_manifests.values() else ""
        raise Refused(f"{idx.family}: the prepared set's manifest is {digest}{which}; the family's pin is {idx.manifest}")


def check_branch_flags(args: list[str], oext_doc: dict, *, unit: bool) -> None:
    """Branch 128's flags (DESO item 9): --w1-18-record exactly when the O-ext settings pin a W1-18 record, with that
    SHA-256; --dev100-source only on --run under Branch 128."""
    cap = oext_doc["cap"]
    pin = cap["w1_18"]["record_sha256"]
    given = one_value(args, "--w1-18-record")
    if pin is None and given is not None:
        raise Refused(f"the family's O-ext settings pin no W1-18 record (branch {cap['branch']}): --w1-18-record is "
                      "not taken")
    if pin is not None:
        if given is None:
            raise Refused(f"the family's O-ext settings pin W1-18's record {pin} (branch {cap['branch']}): "
                          "--w1-18-record is needed")
        try:
            digest = sha256_file(Path(given))
        except OSError as exc:
            raise Refused(f"--w1-18-record cannot be read ({type(exc).__name__})") from None
        if digest != pin:
            raise Refused(f"--w1-18-record hashes to {digest}; the family's O-ext settings pin {pin}")
    source = one_value(args, "--dev100-source")
    if source is not None and (not unit or cap["branch"] != "128" or "--untuned" in args):
        raise Refused(f"--dev100-source belongs to a regenerated unit (--run) under Branch 128 only (LN-19); the "
                      f"branch is {cap['branch']}")


@contextlib.contextmanager
def patched(pairs):
    """Set (object, attribute, value) for the call; restore every one afterwards, also on an error."""
    saved = [(obj, name, getattr(obj, name)) for obj, name, _ in pairs]
    try:
        for obj, name, value in pairs:
            setattr(obj, name, value)
        yield
    finally:
        for obj, name, value in reversed(saved):
            setattr(obj, name, value)


def _say(obj, stream=None) -> None:
    print(json.dumps(obj, sort_keys=True), file=stream or sys.stderr)


def _w1_pairs(idx: Index) -> tuple[list, str]:
    """The W1-18 globals for the family (oext_eval's binding reads them) and the W1-18 settings' SHA-256."""
    w_path, w_sha, _ = idx.file("limits_overrefusal_checks")
    w1 = module("scripts.stage1.limits.overrefusal_checks")
    return [(w1, "SETTINGS_PATH", w_path), (w1, "SETTINGS_SHA256", w_sha)], w_sha


# ----- the commands --------------------------------------------------------------------------------------------------


def run_unit(idx: Index, args: list[str], loaders=None) -> int:
    check_code(COMMAND_CODE["unit"])
    key = "unit" if idx.engine == "X" else "unit_y"
    idx.require(key)
    unit_role, eval_role = NEEDS[key]
    unit_path, unit_sha, unit_doc = idx.file(unit_role)
    eval_path, eval_sha, eval_doc = idx.file(eval_role)
    if unit_doc["prepared"]["manifest_sha256"] != idx.manifest:
        raise Refused(f"{unit_role}__{idx.family}.json pins the manifest {unit_doc['prepared']['manifest_sha256']}, "
                      f"the index {idx.manifest}")
    check_prepared(args, idx)
    check_branch_flags(args, eval_doc, unit=True)
    w_pairs, w_sha = _w1_pairs(idx)
    ou, oe = module("scripts.stage1_s1.oext_unit"), module("scripts.stage1_s1.oext_eval")
    pairs = [(ou, "load_pinned_settings", functools.partial(ou.load_pinned_settings, unit_path, unit_sha)),
             (oe, "load_pinned_settings", functools.partial(oe.load_pinned_settings, eval_path, eval_sha)),
             (ou, "OEXT_SETTINGS_PATH", idx.label(eval_role)), *w_pairs]
    _say({"wrapper": "scripts/scale78b/oext_78b.py", "command": "unit", "family": idx.family, "engine": idx.engine,
          "index_sha256": idx.sha256,
          "settings": {unit_role: unit_sha, eval_role: eval_sha, "limits_overrefusal_checks": w_sha}})
    with patched(pairs):
        return ou.main(args, loaders=loaders)


def run_lean(idx: Index, args: list[str], sub: str, loaders=None) -> int:
    lej = module(LEAN_MODULE)                    # first: c0's timer origin precedes the engine imports
    check_code(COMMAND_CODE["lean"])
    if sub == "verify":
        return lej.main(args, loaders=loaders)
    idx.require("lean")
    lean_path, lean_sha, _ = idx.file("lean_eval_job")
    eval_path, eval_sha, eval_doc = idx.file("oext_eval")
    check_prepared(args, idx)
    check_branch_flags(args, eval_doc, unit=False)
    w_pairs, w_sha = _w1_pairs(idx)
    oe = module("scripts.stage1_s1.oext_eval")
    pairs = [(lej, "SETTINGS_PATH", lean_path), (lej, "SETTINGS_SHA256", lean_sha),
             (lej, "OEXT_SETTINGS_PATH", idx.label("oext_eval")),
             (oe, "load_pinned_settings", functools.partial(oe.load_pinned_settings, eval_path, eval_sha)), *w_pairs]
    _say({"wrapper": "scripts/scale78b/oext_78b.py", "command": "lean", "family": idx.family, "engine": "X",
          "index_sha256": idx.sha256,
          "settings": {"lean_eval_job": lean_sha, "oext_eval": eval_sha, "limits_overrefusal_checks": w_sha}})
    with patched(pairs):
        return lej.main(args, loaders=loaders)


def run_w1_18(idx: Index, args: list[str]) -> int:
    check_code(COMMAND_CODE["w1_18"])
    idx.require("w1_18")
    w_path, w_sha, _ = idx.file("limits_overrefusal_checks")
    w1 = module("scripts.stage1.limits.overrefusal_checks")
    _say({"wrapper": "scripts/scale78b/oext_78b.py", "command": "w1_18", "family": idx.family, "engine": "W1",
          "index_sha256": idx.sha256, "settings": {"limits_overrefusal_checks": w_sha}})
    with patched([(w1, "SETTINGS_PATH", w_path), (w1, "SETTINGS_SHA256", w_sha)]):
        return w1.main([*args, "--settings", str(w_path)])


# ----- the check ($0) ------------------------------------------------------------------------------------------------


def validate_one(idx: Index, role: str, path: Path, sha: str, doc: dict) -> None:
    """One settings file through its unchanged 1B validator, with its true path label."""
    ou, oe = module("scripts.stage1_s1.oext_unit"), module("scripts.stage1_s1.oext_eval")
    if role == "limits_overrefusal_checks":
        module("scripts.stage1.limits.overrefusal_checks").check_content(doc)
    elif role in ("oext_eval", "oext_eval_y"):
        oe.load_pinned_settings(path, sha)
    elif role in ("oext_unit", "oext_unit_y"):
        eval_role = "oext_eval" if role == "oext_unit" else "oext_eval_y"
        with patched([(ou, "OEXT_SETTINGS_PATH", idx.label(eval_role))]):
            ou.load_pinned_settings(path, sha)
    elif role == "lean_eval_job":
        lej = module(LEAN_MODULE)
        with patched([(lej, "OEXT_SETTINGS_PATH", idx.label("oext_eval"))]):
            lej.load_lean_settings(path, sha)


@contextlib.contextmanager
def on_engine(identity: str):
    """The 1B settings check (s1common.check_settings) reads the running engine's identity through
    s1common.code_identity; for engine Y's files on the Mac it reads engine Y's identity for the call (R-23)."""
    s1 = module("scripts.stage1.s1common")
    real = s1.code_identity
    with patched([(s1, "code_identity", lambda: {**real(), "sha256": identity})]):
        yield


def validate_doc(idx: Index, role: str, doc: dict) -> None:
    """W2-3: one settings document (a waiting file with placeholders) through its unchanged 1B validator in memory,
    with its true path label; the same checks as validate_one but the file hash, which idx.file has checked. Only the
    W1-18, O-ext eval and unit files have waits that null a field."""
    ou, oe = module("scripts.stage1_s1.oext_unit"), module("scripts.stage1_s1.oext_eval")
    if role == "limits_overrefusal_checks":
        module("scripts.stage1.limits.overrefusal_checks").check_content(doc)
    elif role in ("oext_eval", "oext_eval_y"):
        oe.validate_settings(doc)
        oe.check_w1_18_binding(doc)
    elif role in ("oext_unit", "oext_unit_y"):
        eval_role = "oext_eval" if role == "oext_unit" else "oext_eval_y"
        with patched([(ou, "OEXT_SETTINGS_PATH", idx.label(eval_role))]):
            ou.validate_settings(doc)
    else:                                   # lean_eval_job's only wait (W1_18_BRANCH) nulls no field
        raise Refused(f"{role}__{idx.family}.json waits on a pin that nulls a field, which no wait of it does")


def wait_fields(wait: dict, doc: dict) -> tuple[str, ...]:
    """The dotted settings fields a wait nulls (W2-3)."""
    if wait["pin"] == "UNIT_JOB":
        units = doc.get("units") if isinstance(doc.get("units"), dict) else {}
        return tuple(f"units.{n}.job_sha256" for n, u in sorted(units.items())
                     if n != "untuned" and isinstance(u, dict) and u.get("job_sha256") is None)
    return WAIT_FIELDS.get(wait["pin"], ())


def placeholder_copy(idx: Index, role: str, doc: dict) -> dict:
    """W2-3: a copy of ``doc`` with every field that a wait of ``role`` nulls set to PLACEHOLDER. A listed field that
    is filled (a stale index) or absent refuses."""
    out = copy.deepcopy(doc)
    for wait in idx.doc["waits"]:
        if role not in wait["roles"]:
            continue
        for dotted in wait_fields(wait, out):
            node = out
            *parents, last = dotted.split(".")
            for key in parents:
                node = node.get(key) if isinstance(node, dict) else None
            if not isinstance(node, dict) or last not in node:
                raise Refused(f"{role}__{idx.family}.json has no field {dotted} (the wait {wait['pin']})")
            if node[last] is not None:
                raise Refused(f"{role}__{idx.family}.json: {dotted} waits on {wait['pin']} in the index but is filled")
            node[last] = PLACEHOLDER
    return out


def check_settings_files(idx: Index) -> dict:
    """Each listed settings file through its unchanged 1B validator with its true label (O-ext's W1-18 binding
    included), under the index's engine identity (R-23). A role that waits on a null pin is "waits" only when the
    validator passes it with every field its waits null replaced by a placeholder (an engine identity that is a null
    pin, ENGINE_Y, too: W2-3); any refusal raises (exit 2)."""
    w_pairs, _ = _w1_pairs(idx)
    s1 = module("scripts.stage1.s1common")
    running = s1.code_identity()["sha256"]
    identity = idx.doc.get("engine_identity", running)
    out = {}
    with patched(w_pairs):
        for role in sorted(idx.doc["files"]):
            path, sha, doc = idx.file(role)
            if role == "limits_overrefusal_checks":
                engine = running                          # W1-18's settings are engine X's (their engine_x)
            elif identity is None:
                if not any(w["pin"] == "ENGINE_Y" and role in w["roles"] for w in idx.doc["waits"]):
                    raise Refused(f"the engine-{idx.engine} index names no engine identity, and {role} waits on none")
                engine = PLACEHOLDER                      # W2-3: the rest of the file is validated all the same
            else:
                engine = identity
            checked = placeholder_copy(idx, role, doc)
            if checked.get("engine_x") != engine:
                raise Refused(f"{role}__{idx.family}.json names engine {doc.get('engine_x')}, the "
                              f"engine-{idx.engine} index {engine}")
            if checked != doc:                            # W2-3: a waiting file, its nulls replaced by placeholders
                with on_engine(engine):  # the placeholder copy
                    validate_doc(idx, role, checked)
                out[role] = "waits"
                continue
            with on_engine(engine):
                validate_one(idx, role, path, sha, doc)
            out[role] = "valid"
    return out


def check_w1_18_record(idx: Index, record: str) -> dict:
    """R-6: the pinned W1-18 record through the unchanged oext_eval reader, under the family's O-ext settings and
    W1-18 globals; its units must be the family's W1-18 units."""
    oe = module("scripts.stage1_s1.oext_eval")
    eval_role = "oext_eval" if idx.engine == "X" else "oext_eval_y"
    eval_path, eval_sha, eval_doc = idx.file(eval_role)
    _, _, w_doc = idx.file("limits_overrefusal_checks")
    w_pairs, w_sha = _w1_pairs(idx)
    with patched(w_pairs):
        got = oe.read_w1_18(oe.Settings(eval_doc, eval_sha), record)   # the reader reads cap only (no engine check)
    try:
        units = strict_json(Path(record).read_bytes()).get("units") or {}
    except (OSError, AttributeError):
        units = {}
    if sorted(units) != sorted(w_doc["units"]):
        raise Refused(f"the W1-18 record {got.record_sha256} lists {len(units)} units, not the family's "
                      f"{len(w_doc['units'])} W1-18 units")
    return {"record_sha256": got.record_sha256, "branch": eval_doc["cap"]["branch"], "units": got.units,
            "settings_sha256": w_sha, "consistent": True}


def _hex_or_none(value):
    """OR7: a printed value is a SHA-256 or nothing."""
    return value if isinstance(value, str) and HEX64.match(value) else None


def check_side_units(idx: Index, data_root: str) -> dict:
    """R-9 with OR2 and OR7 (see the module docstring): every check W1-18's own unit gate makes that needs no parsing,
    each by hashes and names."""
    lc = module("scripts.stage1.limits.limits_common")
    _, _, w_doc = idx.file("limits_overrefusal_checks")
    reader = lc.frozen_reader(w_doc["frozen_reader"])
    pattern = w_doc["allow_list"]["path_pattern"]
    root = Path(data_root).resolve()
    report, problems = {}, []
    for name, spec in sorted(w_doc["units"].items()):
        folder = (root / spec["path"]).resolve()
        entry = {"complete_sha256": spec["complete_sha256"], "files": {}}
        report[name] = entry
        if not re.fullmatch(pattern, spec["path"]) or ".." in Path(spec["path"]).parts:
            problems.append(f"{name}: its path is not in the settings' allow-list form")
            continue
        if root not in folder.parents:
            problems.append(f"{name}: its path leaves the data root")
            continue
        try:
            data = (folder / "COMPLETE.json").read_bytes()
        except OSError as exc:
            problems.append(f"{name}: COMPLETE.json cannot be read ({type(exc).__name__})")
            continue
        if sha256_bytes(data) != spec["complete_sha256"]:
            problems.append(f"{name}: COMPLETE.json hashes to {sha256_bytes(data)}, the settings pin "
                            f"{spec['complete_sha256']}")
            continue
        marker = strict_json(data)
        listed = marker.get("files") if isinstance(marker, dict) else None
        if not isinstance(listed, dict) or marker.get("complete") is not True:
            problems.append(f"{name}: COMPLETE.json is not a complete marker with a file list")
            continue
        for rel_pattern in W1_18_UNIT_FILES:
            rel = rel_pattern.format(checkpoint=spec["checkpoint"])
            digest = listed.get(rel)
            if rel == "job.json" and digest is None:
                digest = marker.get("job_sha256")                 # an engine unit names job.json beside its list
            digest = _hex_or_none(digest)
            state = "listed"
            if digest is None:
                state = "not listed"
                problems.append(f"{name}: COMPLETE.json lists no SHA-256 for {rel}")
            elif not (folder / rel).is_file():
                state = "missing"
                problems.append(f"{name}: {rel} is listed ({digest}) but absent")
            elif sha256_file(folder / rel) != digest:
                state = "differs"
                problems.append(f"{name}: {rel} does not hash to the listed {digest}")
            entry["files"][rel] = {"sha256": digest, "state": state}
        try:
            reader.sealed(folder)                                 # W1-18's frozen sealed check (hashes, no parsing)
            entry["sealed"] = "passes"
        except SystemExit:
            entry["sealed"] = "refuses"
            problems.append(f"{name}: the frozen sealed check refuses")
        evals = sorted(q.name for q in (folder / "eval").iterdir() if q.is_dir()) if (folder / "eval").is_dir() else []
        entry["eval_folders"] = len(evals)
        if evals != [spec["checkpoint"]]:
            problems.append(f"{name}: eval/ does not hold exactly the folder of checkpoint {spec['checkpoint']}")
        job_pin = spec.get("job_sha256")
        job = entry["files"].get("job.json", {})
        if job_pin is None:
            entry["job_pin"] = "null (waits)"
        elif job.get("sha256") != job_pin or job.get("state") != "listed":
            entry["job_pin"] = "differs"
            problems.append(f"{name}: job.json is {job.get('sha256')}, the settings pin {job_pin}")
        else:
            entry["job_pin"] = "equal"
    return {"units": report, "problems": problems}


def run_check(idx: Index, args: list[str]) -> int:
    check_code(ENGINE_CODE[idx.engine])
    report = {"family": idx.family, "engine": idx.engine, "index_sha256": idx.sha256, "branch": idx.doc.get("branch"),
              "code": {name: CODE[name] for name in ENGINE_CODE[idx.engine]},
              "files": {role: entry["sha256"] for role, entry in idx.doc["files"].items()},
              "settings": check_settings_files(idx),
              "waits": {key: [w["pin"] for w in idx.waits_for(NEEDS[key])] for key in ENGINE_KEYS[idx.engine]}}
    record = one_value(args, "--w1-18-record")
    if idx.engine == "W1":
        if record is not None:
            raise Refused("the W1-18 pod's index holds no O-ext settings: check a W1-18 record on the X or Y index")
    else:
        eval_role = "oext_eval" if idx.engine == "X" else "oext_eval_y"
        pin = idx.file(eval_role)[2]["cap"]["w1_18"]["record_sha256"]
        if record is not None:
            report["w1_18_record"] = check_w1_18_record(idx, record)
        elif pin is not None:
            raise Refused(f"the family's O-ext settings pin W1-18's record {pin}: give it with --w1-18-record (R-6)")
    data_root = one_value(args, "--data-root")
    if data_root is not None:
        report["side_units"] = check_side_units(idx, data_root)
    print(json.dumps(report, indent=2, sort_keys=True))
    if data_root is not None and report["side_units"]["problems"]:
        _say({"ok": False, "refused": f"oext_78b: {len(report['side_units']['problems'])} side-unit problems "
                                      f"(first: {report['side_units']['problems'][0]})"})
        return EXIT_REFUSED
    return 0


def main(argv: list[str] | None = None, *, loaders=None) -> int:
    """The command line. ``loaders`` replaces the engine's real loaders (ENGINEERING FIXTURES in tests only)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        command, opts, args = split_argv(argv)
        if command == "lean":
            module(LEAN_MODULE)                  # before the index, the settings and the engine (c0's timer origin)
        sub = check_flags(command, args)
        idx = Index(opts["index"], opts["index_sha256"], opts["family"], opts["engine"])
        if command == "check":
            return run_check(idx, args)
        if command == "unit":
            return run_unit(idx, args, loaders)
        if command == "lean":
            return run_lean(idx, args, sub, loaders)
        return run_w1_18(idx, args)
    except Refused as exc:
        _say({"ok": False, "refused": f"oext_78b: {exc}"})
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001 - a 1B refusal raised in the check (the 1B validators and readers)
        if command_of(argv) == "check" and type(exc).__name__ in ("Refusal", "ConfigError", "DataError"):
            _say({"ok": False, "refused": f"oext_78b check: {type(exc).__name__}: {exc}"})
            return EXIT_REFUSED
        raise


def command_of(argv: list[str]) -> str | None:
    return argv[0] if argv else None


if __name__ == "__main__":
    sys.exit(main())
