"""The 7-8B evaluation-only references: the unchanged 1B B10 and B11 scripts run with a family's per-seed settings (R2
Track R; Part 2 sections 3.1, 3.2, 16.1; DES F1, F2; the build rulings GXB O2, O3, X3 and T-O1's route rule).

Every command names the family, the reference seed and that seed's index, by path and SHA-256 (the kit takes both from
its pin for (F, S), REFS_78B[F][S]; R-5's form). This file holds no index hash, so no pin fill changes it:

    python -B scripts/scale78b/refs_78b.py eval_adapter --family F --seed S --index IDX --index-sha256 H
        COMMAND ...        (scripts/stage1_s1/eval_adapter.py's own command and arguments: check, regenerate,
                            evaluate, run, compare, verify; its outputs, prints and exit codes)
    python -B scripts/scale78b/refs_78b.py safe_lora --family F --seed S --index IDX --index-sha256 H
        COMMAND ...        (scripts/stage1_s1/safe_lora.py's: check, transform, vcheck)
    python -B scripts/scale78b/refs_78b.py check --family F --seed S --index IDX --index-sha256 H   ($0, on the Mac)

    IDX is scripts/scale78b/settings/REFS-78B__F__S.json; the settings files are read from the index's folder:
    eval_adapter__F__S.json, safe_lora__F__S.json, and Track O's oext_eval__F.json and
    limits_overrefusal_checks__F.json, which eval_adapter__F__S.json binds. Each leading option is given at most once.

The route (the decisive check, R2 report section 1): both 1B scripts take their settings through module globals that a
wrapper can set with a true label, so no copy is needed:
  - eval_adapter.load_pinned_settings binds its default path at definition (eval_adapter.py:394) and reads
    SETTINGS_SHA256 at call time (:395): for the call it is the original function bound to the family's file, and
    SETTINGS_PATH and SETTINGS_SHA256 name that file;
  - eval_adapter.OEXT_SETTINGS_PATH (:140, :376) names the family's oext_eval file (the label of the loaded file, from
    the index entry, never from the settings text), so a settings file naming another O-ext file refuses;
  - oext_eval.load_pinned_settings (oext_eval.py:246, called by eval_adapter.py:1868) loads the family's O-ext file,
    oext_eval.SETTINGS_PATH (read by eval_adapter's check, :1890) names it, and overrefusal_checks.SETTINGS_PATH and
    SETTINGS_SHA256 name the family's W1-18 settings (oext_eval's binding, oext_eval.py:214-236), as Track O's wrapper
    does;
  - safe_lora.SETTINGS_PATH and SETTINGS_SHA256 (safe_lora.py:96-97), read at call time by load_pinned_settings
    (:318-322), name the family's per-seed file (the 1B tests set the same two globals).
B10's certified code is its own file with the settings literal zeroed (eval_adapter.py:1579-1590); the file is unchanged,
so the code a 7-8B certification certifies is the 1B code that runs. Records name the scripts that ran (provenance
script, b10.script = scripts/stage1_s1/eval_adapter.py, safe_lora's provenance) and the family settings' SHA-256; no
record or output names a file the run did not load (GXB O3). The globals are restored after the call, also when the 1B
code raises.

Before the call (refusals exit 2 with one JSON line on stderr; they name hashes, flags, pins and events, never text):
  - the run files hash to CODE; the index is the named family's and seed's, hashes to the named SHA-256, and each
    file it lists hashes to its entry;
  - every '-' token is a full flag name of the 1B subcommand (the 1B parsers expand abbreviations);
  - no pin the command's settings file needs is null (the index's waits name the pin and its event);
  - eval_adapter__F__S.json's O-ext pin and Safe LoRA pin name the index's files by their true labels and SHA-256;
  - the seed: --seed (regenerate, run; safe_lora's commands) is S, and --reference (regenerate, evaluate, run, compare)
    is seed S's pinned COMPLETE.json (eval_adapter's own checks then hold the source run and the report to S);
  - --prepared is the family's prepared set (its manifest.json hashes to the family's pin);
  - --w1-18-record is given exactly when the family's O-ext settings pin a W1-18 record, with that SHA-256;
  - the forms that do not run at 7-8B are refused by name: B10's check --untuned and compare --against untuned (GXB
    R-34: theta0 is not compared; the curve's lambda = 0 end is theta0's own O measurement from the o_only pass), and
    any Safe LoRA point but default and certify (GXB R-37; the settings' conditional K is 0), and lambda = 0
    (evaluate --lambda 0, run with scale:0; GXB R-42).

After a B10 command (GXB R-38, R-41): beside each output the command created (--out; run's --regen-out and
--eval-root; absent or an empty folder before the call, holding something after it), the wrapper
writes OUTPUT.refs78b-terms.json, a record of what B10's 1B terms mean at 7-8B ("Gate A" = the seed's a0 unit, R-35;
the untuned unit and lambda = 0, R-34). B10 runs unchanged, so its own messages and fixed texts keep the 1B words: a
limit, stated in the record. A terms record that exists already refuses before the call.

The check ($0): the run files, the index and its files; each settings file through its unchanged 1B validator with its
true label (eval_adapter.validate_settings, safe_lora.validate_settings); a file that waits on a null pin is validated
with each waiting field replaced by a placeholder of its kind, so it prints "waits" (exit 0) only when the rest of the
file is valid, and any refusal exits 2; the label and hash bindings above; the waits per command.
"""

from __future__ import annotations

import copy
import functools
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.scale78b import oext_78b as ox  # noqa: E402  (Track O's helpers: patched, label, check_prepared, ...)

INDEX_KIND = "scale78b refs settings index"
INDEX_VERSION = 1
INDEX_NAME = "REFS-78B__{family}__{seed}.json"
FAMILIES = ("olmo2-7b", "llama31-8b")
REFERENCE_SEEDS = (1102, 1103, 1104, 1105, 1106, 1107)
COMMANDS = ("eval_adapter", "safe_lora", "check")
LEADING = ("--family", "--seed", "--index", "--index-sha256")
EA, SL = "scripts.stage1_s1.eval_adapter", "scripts.stage1_s1.safe_lora"
OE, W1, LC, S1 = ("scripts.stage1_s1.oext_eval", "scripts.stage1.limits.overrefusal_checks",
                  "scripts.stage1.limits.limits_common", "scripts.stage1.s1common")
# The modules the commands run or bind, by the SHA-256 of their files (M: shasum -a 256 at MAIN bfda225, 8 Nov 2026).
CODE = {
    EA: "ae95312970336cac5eec993e21b55bb48fc6e907a5c439e67a184f58f8ac0c33",
    SL: "5f6b782255f7207645659cc25ea8864c85aeb2d32533acab342175d0217757b4",
    OE: "8c4290921f32a5b4596a0bc40235cc5cf1185f73eaabeaa625c43bd19ba77719",
    W1: "ed5fd2dcb5675d5fe5e135b76e37ece2488dfcc2db5129ba422064502b0d61ae",
    LC: "2798aa06a01fd89bf3dd8dc2abf33e63bfcb4f17bff700a709eacd2b3ace264c",
    S1: "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",
}
COMMAND_CODE = {"eval_adapter": (EA, OE, W1, LC, S1), "safe_lora": (SL, S1), "check": (EA, SL, OE, W1, LC, S1)}
# Every '-' token must be one of these full names (the name before any '='); the first token is the 1B subcommand.
# A test holds these sets equal to the 1B parsers' own option strings.
EA_FLAGS = {
    "check": frozenset({"--reference", "--untuned"}),
    "regenerate": frozenset({"--prepared", "--recipe", "--reference", "--wall-limit-seconds", "--seed", "--out"}),
    "evaluate": frozenset({"--prepared", "--recipe", "--reference", "--wall-limit-seconds", "--source-run", "--out",
                           "--mode", "--lambda", "--prefix-file", "--external", "--adapter-file", "--adapter-sha256",
                           "--adapter-record", "--adapter-record-sha256", "--certification-report",
                           "--certification-report-sha256", "--oext-bank", "--oext-record", "--w1-18-record"}),
    "run": frozenset({"--prepared", "--recipe", "--reference", "--wall-limit-seconds", "--seed", "--regen-out",
                      "--eval-root", "--evaluations", "--prefix-file", "--gate-reference-eval",
                      "--certification-report", "--certification-report-sha256", "--oext-bank", "--oext-record",
                      "--w1-18-record"}),
    "compare": frozenset({"--unit", "--reference", "--reference-eval", "--out", "--against"}),
    "verify": frozenset({"--unit", "--map"}),
}
SL_FLAGS = {"check": frozenset({"--adapter", "--seed", "--aligned", "--base", "--out"}),
            "vcheck": frozenset({"--adapter", "--seed", "--aligned", "--base", "--out"}),
            "transform": frozenset({"--adapter", "--seed", "--aligned", "--base", "--out", "--point"})}
SEEDED = {"eval_adapter": ("regenerate", "run"), "safe_lora": ("check", "transform", "vcheck")}
SL_POINTS = ("default", "certify")       # GXB R-37: the Safe LoRA points that run at 7-8B (P2 section 3.2: K = 78 only)
# GXB R-38: the 1B terms in the unchanged B10 code's messages and outputs, and what each means at 7-8B; the wrapper
# writes them in a record beside each B10 output (TERMS_SUFFIX). A limit: the 1B code's own texts keep the 1B words.
TERMS_SUFFIX = ".refs78b-terms.json"
TERMS_KIND = "scale78b refs terms record"
TERMS = {
    "Gate A unit": "the reference seed's a0 unit at e1 under MAIN_F, with its own e1 evaluation (GXB R-35: 1102 the "
                   "reused side unit; 1103 the reused side unit on OLMo-2-7B and N's a0-1103 on Llama-3.1-8B; 1104 block "
                   "A's a0; 1105-1107 block B's a0), pinned by its COMPLETE.json SHA-256 and adapter fingerprints",
    "Gate A record": "that unit's COMPLETE.json, by the pinned SHA-256",
    "the untuned unit (theta0)": "the family's theta0 init unit of seed 1101 (RK KIT a0_units); not compared at 7-8B: "
                                 "check --untuned and compare --against untuned are refused (GXB R-34)",
    "lambda = 0": "the curve's lambda = 0 end is theta0's own O measurement from the o_only pass under MAIN_F with the "
                  "adapter disabled (GXB R-34); no lambda = 0 B10 unit runs at 7-8B (the wrapper refuses it, R-42)",
    "the certification seed": "the index's reference seed S: one certification per reference seed (GXB O2)",
    "stage 1": "the 7-8B tier's references (Part 2 section 3)",
}
TERMS_LIMIT = ("B10 (scripts/stage1_s1/eval_adapter.py) runs unchanged, so its self-hash certifies the 1B code that runs; "
               "its messages and fixed texts keep 1B's words (Gate A, the untuned unit's lambda = 0 role). This record "
               "says what they mean at 7-8B; it is written by refs_78b.py, not by B10, and B10's records do not list it")
OUTPUT_FLAGS = {"regenerate": ("--out",), "evaluate": ("--out",), "run": ("--regen-out", "--eval-root"),
                "compare": ("--out",)}
REFERENCED = ("regenerate", "evaluate", "run", "compare")
PLACEHOLDERS = {"sha256": "0" * 64, "commit": "0" * 40, "text": "waits", "dtype": "bfloat16",
                "files": [{"file": "model.safetensors", "bytes": 1, "sha256": "0" * 64}]}
HEX64 = re.compile(r"^[0-9a-f]{64}$")
EXIT_REFUSED = 2

Refused = ox.Refused
module = ox.module
patched = ox.patched


def sha256_file(path: Path) -> str:
    return ox.sha256_file(path)


def check_code(names) -> dict[str, str]:
    out = {}
    for name in names:
        digest = sha256_file(Path(module(name).__file__).resolve())
        if digest != CODE[name]:
            raise Refused(f"{name} hashes to {digest}, the wrapper pins {CODE[name]}: the run files stay byte for byte")
        out[name] = digest
    return out


def code_pins() -> dict[str, str]:
    """The files the commands run, as {path under scripts/: SHA-256} (the kit form's files), with this file."""
    out = {f"{name.replace('.', '/')}.py": CODE[name] for name in COMMAND_CODE["check"]}
    out["scripts/scale78b/refs_78b.py"] = sha256_file(Path(__file__).resolve())
    out["scripts/scale78b/oext_78b.py"] = sha256_file(Path(ox.__file__).resolve())
    return out


class Index:
    """The family's index for one reference seed, named by the job by path and SHA-256; its files lie beside it."""

    def __init__(self, path, expected_sha256: str, family: str, seed: int):
        if family not in FAMILIES:
            raise Refused(f"--family must be one of {list(FAMILIES)}")
        if seed not in REFERENCE_SEEDS:
            raise Refused(f"--seed must be a reference seed {list(REFERENCE_SEEDS)} (P2 section 3.1)")
        if not isinstance(expected_sha256, str) or not HEX64.match(expected_sha256):
            raise Refused("--index-sha256 must be a SHA-256 (64 lowercase hex)")
        path = Path(path)
        wanted = INDEX_NAME.format(family=family, seed=seed)
        if path.name != wanted:
            raise Refused(f"--index names {path.name}; the {family} seed-{seed} index is {wanted}")
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise Refused(f"the index {path.name} cannot be read ({type(exc).__name__})") from None
        digest = ox.sha256_bytes(data)
        if digest != expected_sha256:
            raise Refused(f"{path.name} hashes to {digest}, the job names {expected_sha256}")
        doc = ox.strict_json(data)
        if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version")) != (INDEX_KIND, INDEX_VERSION) or \
                (doc.get("family"), doc.get("seed")) != (family, seed):
            raise Refused(f"{path.name} is not the scale78b refs index of {family} seed {seed}")
        self.family, self.seed, self.doc, self.sha256, self.dir = family, seed, doc, digest, path.parent
        self.manifest = doc["manifest_sha256"]
        self.other_manifests = dict(doc.get("other_manifests") or {})

    def waits_for(self, role: str) -> list[dict]:
        return [w for w in self.doc["waits"] if role in w["roles"]]

    def require(self, role: str) -> None:
        waits = self.waits_for(role)
        if waits:
            first = waits[0]
            raise Refused(f"{self.family} seed {self.seed}: the pin {first['pin']} is null ({', '.join(first['where'])}; "
                          f"{len(waits)} pins wait for {role}): {first['event']}")

    def file(self, role: str) -> tuple[Path, str, dict]:
        entry = (self.doc["files"] or {}).get(role)
        if entry is None:
            raise Refused(f"the {self.family} seed-{self.seed} index lists no {role} file")
        path = self.dir / entry["file"]
        try:
            data = path.read_bytes()
        except OSError as exc:
            raise Refused(f"{entry['file']} cannot be read ({type(exc).__name__})") from None
        if ox.sha256_bytes(data) != entry["sha256"]:
            raise Refused(f"{entry['file']} hashes to {ox.sha256_bytes(data)}, the index pins {entry['sha256']}")
        return path, entry["sha256"], ox.strict_json(data)

    def label(self, role: str) -> str:
        return ox.label(self.dir / self.doc["files"][role]["file"])


# ----- the command line ----------------------------------------------------------------------------------------------


def split_argv(argv: list[str]) -> tuple[str, dict, list[str]]:
    if not argv or argv[0] not in COMMANDS:
        raise Refused(f"the first argument must be one of {list(COMMANDS)}")
    command, rest = argv[0], list(argv[1:])
    opts = {"family": None, "seed": None, "index": None, "index_sha256": None}
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
    if opts["family"] not in FAMILIES:
        raise Refused(f"--family is required and must be one of {list(FAMILIES)}")
    if opts["seed"] is None or not opts["seed"].isdigit():
        raise Refused("--seed is required: the reference seed (P2 section 3.1)")
    opts["seed"] = int(opts["seed"])
    if opts["index"] is None or opts["index_sha256"] is None:
        raise Refused("--index and --index-sha256 are required: the family's index for the seed, by the path and "
                      "SHA-256 the kit's pin names (REFS_78B[F][S])")
    return command, opts, rest


def check_flags(command: str, args: list[str]) -> str | None:
    if command == "check":
        if args:
            raise Refused("check takes no further argument")
        return None
    table = EA_FLAGS if command == "eval_adapter" else SL_FLAGS
    if not args or args[0] not in table:
        raise Refused(f"{command} takes the 1B command {sorted(table)} first")
    sub = args[0]
    for token in args[1:]:
        if token.startswith("-") and token.split("=", 1)[0] not in table[sub]:
            raise Refused(f"{token.split('=', 1)[0]} is not a full flag name of {command} {sub} "
                          f"(allowed: {sorted(table[sub])})")
    return sub


def check_seed(command: str, sub: str, args: list[str], idx: Index, ea_doc: dict | None) -> None:
    """--seed is the index's seed; --reference is that seed's pinned COMPLETE.json; check's references name 1101 or S."""
    if sub in SEEDED[command]:
        seed = ox.one_value(args, "--seed")
        if seed is not None and seed != str(idx.seed):
            raise Refused(f"--seed {seed} is not this index's reference seed {idx.seed}")
    if command != "eval_adapter":
        return
    pins = ea_doc["reference_units"]
    if sub in REFERENCED:
        reference = ox.one_value(args, "--reference")
        if reference is not None:
            try:
                digest = sha256_file(Path(reference))
            except OSError as exc:
                raise Refused(f"--reference cannot be read ({type(exc).__name__})") from None
            pin = pins[str(idx.seed)]["complete_sha256"]
            if digest != pin:
                raise Refused(f"--reference hashes to {digest}, seed {idx.seed}'s pinned a0 unit is {pin}")
    if sub == "check":
        for item in ox.flag_values(args, "--reference"):
            seed = item.partition("=")[0]
            if seed not in pins:
                raise Refused(f"--reference {seed}=...: this index's settings pin the seeds {sorted(pins)} only")


def check_not_run(command: str, sub: str, args: list[str]) -> None:
    """GXB R-34 and R-37: the B10 and B11 forms that do not run at 7-8B, refused by name."""
    if command == "eval_adapter" and sub == "check" and any(t.split("=", 1)[0] == "--untuned" for t in args):
        raise Refused("check --untuned is not run at 7-8B (GXB R-34: theta0 is not compared; the curve's lambda = 0 "
                      "end is theta0's own O measurement from the o_only pass)")
    if command == "eval_adapter" and sub == "compare" and "untuned" in ox.flag_values(args, "--against"):
        raise Refused("compare --against untuned is not run at 7-8B (GXB R-34)")
    if command == "eval_adapter" and sub in ("evaluate", "run"):            # GXB R-42 (RRV-3)
        scales = ox.flag_values(args, "--lambda") if sub == "evaluate" else [
            spec.partition(":")[2] for value in ox.flag_values(args, "--evaluations") for spec in value.split(",")
            if spec.partition(":")[0] == "scale"]
        for value in scales:
            try:
                zero = float(value) == 0.0
            except ValueError:
                continue                                                   # B10 refuses a scale that is no number
            if zero:
                raise Refused("lambda = 0 is not run at 7-8B (GXB R-42; R-34: the curve's lambda = 0 end is theta0's "
                              "own O measurement from the o_only pass)")
    if command == "safe_lora" and sub == "transform":
        for point in ox.flag_values(args, "--point"):
            if point not in SL_POINTS:
                raise Refused(f"the Safe LoRA point {point!r} is not run at 7-8B (GXB R-37; P2 section 3.2 names "
                              f"K = 78 only): the points are {list(SL_POINTS)}")


def check_bindings(idx: Index, ea_doc: dict) -> None:
    """eval_adapter__F__S.json's O-ext and Safe LoRA pins name the index's files by their true labels and SHA-256."""
    oext = ea_doc["oext"]["settings"]
    if (oext["path"], oext["sha256"]) != (idx.label("oext_eval"), idx.doc["files"]["oext_eval"]["sha256"]):
        raise Refused(f"eval_adapter__{idx.family}__{idx.seed}.json's O-ext pin is not the index's oext_eval file "
                      f"({oext['sha256']})")
    entry = ea_doc["external_transforms"].get("safe_lora")
    if entry is None or entry["settings"] is None or (entry["settings"]["path"], entry["settings"]["sha256"]) != (
            idx.label("safe_lora"), idx.doc["files"]["safe_lora"]["sha256"]):
        raise Refused(f"eval_adapter__{idx.family}__{idx.seed}.json's Safe LoRA pin is not the index's safe_lora file")
    if entry["module_sha256"] != CODE[SL] or entry["module"] != "scripts/stage1_s1/safe_lora.py":
        raise Refused("the Safe LoRA transform is not the pinned scripts/stage1_s1/safe_lora.py")


def _say(obj) -> None:
    print(json.dumps(obj, sort_keys=True), file=sys.stderr)


def oext_pairs(idx: Index) -> tuple[list, dict]:
    """The O-ext globals for the family: oext_eval's loader and path, and W1-18's two globals."""
    o_path, o_sha, o_doc = idx.file("oext_eval")
    w_path, w_sha, _ = idx.file("limits_overrefusal_checks")
    oe, w1 = module(OE), module(W1)
    return ([(oe, "load_pinned_settings", functools.partial(oe.load_pinned_settings, o_path, o_sha)),
             (oe, "SETTINGS_PATH", o_path), (w1, "SETTINGS_PATH", w_path), (w1, "SETTINGS_SHA256", w_sha)],
            {"oext_eval": o_sha, "limits_overrefusal_checks": w_sha, "doc": o_doc})


def run_eval_adapter(idx: Index, sub: str, args: list[str], *, loaders=None, codec=None) -> int:
    check_code(COMMAND_CODE["eval_adapter"])
    idx.require("eval_adapter")
    ea_path, ea_sha, ea_doc = idx.file("eval_adapter")
    check_bindings(idx, ea_doc)
    if ea_doc["prepared"]["manifest_sha256"] != idx.manifest:
        raise Refused(f"eval_adapter__{idx.family}__{idx.seed}.json pins the manifest "
                      f"{ea_doc['prepared']['manifest_sha256']}, the index {idx.manifest}")
    check_seed("eval_adapter", sub, args, idx, ea_doc)
    check_not_run("eval_adapter", sub, args)
    ox.check_prepared(args, idx)
    o_pairs, shas = oext_pairs(idx)
    if sub in ("evaluate", "run"):
        ox.check_branch_flags(args, shas["doc"], unit=False)
    ea = module(EA)
    pairs = [(ea, "load_pinned_settings", functools.partial(ea.load_pinned_settings, ea_path)),
             (ea, "SETTINGS_PATH", ea_path), (ea, "SETTINGS_SHA256", ea_sha),
             (ea, "OEXT_SETTINGS_PATH", idx.label("oext_eval")), *o_pairs]
    _say({"wrapper": "scripts/scale78b/refs_78b.py", "command": "eval_adapter", "family": idx.family,
          "seed": idx.seed, "index_sha256": idx.sha256,
          "settings": {"eval_adapter": ea_sha, "oext_eval": shas["oext_eval"],
                       "limits_overrefusal_checks": shas["limits_overrefusal_checks"]}})
    extra = {} if loaders is None else {"_loaders": loaders}
    if codec is not None:
        extra["_codec"] = codec
    outputs = terms_paths(sub, args)
    with patched(pairs):
        code = ea.main(args, **extra)
    write_terms(idx, sub, code, outputs, ea_sha)
    return code


def _state(path: Path):
    """An output path's state before the call: None (absent), "empty" (an empty folder) or "held" (anything else)."""
    if not path.exists():
        return None
    return "empty" if path.is_dir() and not any(path.iterdir()) else "held"


def created(path: Path, before) -> bool:
    """GXB R-41 (RRV-2): the command itself created this output: it was absent, or an empty folder, before the call and
    holds something now (an output that held anything before the call never counts)."""
    return before in (None, "empty") and path.exists() and (not path.is_dir() or any(path.iterdir()))


def terms_paths(sub: str, args: list[str]) -> list[tuple[Path, Path, object]]:
    """(output, its terms record, its state before the call) for each output path the B10 command names; a terms record
    that exists refuses (nothing is overwritten), before the call."""
    out = []
    for flag in OUTPUT_FLAGS.get(sub, ()):
        value = ox.one_value(args, flag)
        if value is None:
            continue
        path = Path(value)
        terms = path.with_name(path.name + TERMS_SUFFIX)
        if terms.exists():
            raise Refused(f"{terms.name} exists beside {path.name}: nothing is overwritten")
        out.append((path, terms, _state(path)))
    return out


def write_terms(idx: Index, sub: str, code: int, outputs: list[tuple[Path, Path, object]], ea_sha: str) -> None:
    """GXB R-38, R-41: beside each output that this command created, a record of what B10's 1B terms mean at 7-8B
    (names, hashes and fixed texts only); none beside an output that existed before the call."""
    for path, terms, before in outputs:
        if not created(path, before):
            continue
        doc = {"kind": TERMS_KIND, "version": 1, "writer": "scripts/scale78b/refs_78b.py",
               "writer_sha256": sha256_file(Path(__file__).resolve()), "b10": "scripts/stage1_s1/eval_adapter.py",
               "b10_sha256": CODE[EA], "command": sub, "exit": code, "output": path.name, "family": idx.family,
               "seed": idx.seed, "index_sha256": idx.sha256, "settings_sha256": ea_sha, "terms": dict(TERMS),
               "limit": TERMS_LIMIT}
        with open(terms, "x", encoding="utf-8") as handle:
            handle.write(json.dumps(doc, indent=2, sort_keys=True) + "\n")


def run_safe_lora(idx: Index, sub: str, args: list[str]) -> int:
    check_code(COMMAND_CODE["safe_lora"])
    idx.require("safe_lora")
    sl_path, sl_sha, _ = idx.file("safe_lora")
    check_seed("safe_lora", sub, args, idx, None)
    check_not_run("safe_lora", sub, args)
    sl = module(SL)
    _say({"wrapper": "scripts/scale78b/refs_78b.py", "command": "safe_lora", "family": idx.family, "seed": idx.seed,
          "index_sha256": idx.sha256, "settings": {"safe_lora": sl_sha}})
    with patched([(sl, "SETTINGS_PATH", sl_path), (sl, "SETTINGS_SHA256", sl_sha)]):
        return sl.main(args)


# ----- the check ($0) ------------------------------------------------------------------------------------------------


def _set(doc: dict, dotted: str, value) -> object:
    """Set a dotted field and return its old value; a parent or the field that is absent refuses (RV-4)."""
    node = doc
    *parents, last = dotted.split(".")
    for key in parents:
        node = node.get(key) if isinstance(node, dict) else None
    if not isinstance(node, dict) or last not in node:
        raise Refused(f"the index lists the waiting field {dotted}, which the file does not hold")
    old = node[last]
    node[last] = value
    return old


def with_placeholders(idx: Index, role: str, doc: dict) -> dict:
    """A copy of ``doc`` with every field a wait of ``role`` names replaced by a placeholder of its kind; a listed
    field that is not null refuses (the index is stale)."""
    out = copy.deepcopy(doc)
    for wait in idx.waits_for(role):
        for field in wait["fields"].get(role, []):
            old = _set(out, field["path"], copy.deepcopy(PLACEHOLDERS[field["kind"]]))
            if old is not None:
                raise Refused(f"{role}: the index lists {field['path']} as waiting on {wait['pin']}, but it is filled")
    return out


def validate(idx: Index, role: str, sha: str, doc: dict) -> None:
    """One settings document through its unchanged 1B validator, with its true labels."""
    if role == "eval_adapter":
        ea = module(EA)
        with patched([(ea, "OEXT_SETTINGS_PATH", idx.label("oext_eval"))]):
            ea.validate_settings(doc)
    elif role == "safe_lora":
        module(SL).validate_settings(doc, sha)


def run_check(idx: Index) -> int:
    check_code(COMMAND_CODE["check"])
    report = {"family": idx.family, "seed": idx.seed, "index_sha256": idx.sha256, "branch": idx.doc.get("branch"),
              "code": {name: CODE[name] for name in COMMAND_CODE["check"]},
              "files": {role: entry["sha256"] for role, entry in idx.doc["files"].items()}, "settings": {},
              "waits": {role: [w["pin"] for w in idx.waits_for(role)] for role in ("eval_adapter", "safe_lora")}}
    o_pairs, _ = oext_pairs(idx)
    with patched(o_pairs):
        module(OE).load_pinned_settings()                 # the family's O-ext file with its W1-18 binding
    report["settings"]["oext_eval"] = "valid"
    _, _, ea_doc = idx.file("eval_adapter")
    check_bindings(idx, ea_doc)
    for role in ("eval_adapter", "safe_lora"):
        _, sha, doc = idx.file(role)
        waiting = bool(idx.waits_for(role))
        validate(idx, role, sha, with_placeholders(idx, role, doc) if waiting else doc)
        report["settings"][role] = "waits" if waiting else "valid"
    report["certification_seed"] = ea_doc["certification"]["seed"]
    report["reference_seeds"] = sorted(ea_doc["reference_units"])
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


def main(argv: list[str] | None = None, *, loaders=None, codec=None) -> int:
    """The command line. ``loaders`` and ``codec`` replace the engine's real loaders and the prompt-length codec
    (ENGINEERING FIXTURES in tests only)."""
    argv = list(sys.argv[1:] if argv is None else argv)
    try:
        command, opts, args = split_argv(argv)
        sub = check_flags(command, args)
        idx = Index(opts["index"], opts["index_sha256"], opts["family"], opts["seed"])
        if command == "check":
            return run_check(idx)
        if command == "eval_adapter":
            return run_eval_adapter(idx, sub, args, loaders=loaders, codec=codec)
        return run_safe_lora(idx, sub, args)
    except Refused as exc:
        _say({"ok": False, "refused": f"refs_78b: {exc}"})
        return EXIT_REFUSED
    except Exception as exc:  # noqa: BLE001 - a 1B refusal raised in the check (the 1B validators)
        if argv[:1] == ["check"] and type(exc).__name__ in ("Refusal", "ConfigError", "DataError"):
            _say({"ok": False, "refused": f"refs_78b check: {type(exc).__name__}: {exc}"})
            return EXIT_REFUSED
        raise


if __name__ == "__main__":
    sys.exit(main())
