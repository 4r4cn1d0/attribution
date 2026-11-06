"""The 7-8B scorer layer: the unchanged 1B scorer scripts under scripts/stage1/, run with a family's settings file
(track E of the 7-8B $0 build round, 5 Nov 2026; Part 1 sections 3.7, 10, 12 and 14; P78:357; the readiness plan T6;
the check's C1, C6, M1, M2; the lead's addendum A1, A2, A13).

    python -I -B scripts/scale78b/scorers_78b.py KIND --family olmo2-7b|llama31-8b  <the 1B script's own arguments>

    KIND              the 1B script it runs (its main(), from the imported module)            where
    untuned_answers   scripts/stage1/make_untuned_answers.py  --recipe --recipe-s --list --loss --out   pod
    rep_pass          scripts/stage1/representation_pass.py   --prepared --recipe --anchors [--pool] [--pools-only] --out   pod
    l1_scan           scripts/stage1/score_l1_larf.py scan    --prepared --recipe --anchors --out       pod   (scan prepended)
    l1_score          scripts/stage1/score_l1_larf.py score   --prepared --scan --rows --summary --out  Mac   (score prepended)
    classifier        scripts/stage1/score_classifier.py      --prepared --recipe --anchors [--pool] --out   pod
    s3_score          scripts/stage1/score_s3_datarx.py       --rows --summary --s-pool-record --answers-record --out   Mac
    score_edit        scripts/stage1/write_score_edit.py      a1 --unit --prepared --out | scorer --name --scores --scores-sha256 --prepared --out   Mac
    add_edit          scripts/stage1/write_add_edit.py        --prepared --recipe --list [--combine-with] --full-out --out   Mac
    s_pool            scripts/stage1/build_s_pool.py          --config --sources --prepared --anchors --rec --full-out --out   Mac

How it runs a script (the pattern of scripts/stage1_s1/d2_pool_pins/d2_representation_pass.py, the 1B precedent): the 1B
module is imported, its file hashed against STAGE1_CODE (a changed 1B file refuses), the family's settings file
``settings/<script>__<family>.json`` is read and hashed against ``settings/PINS-78B.json`` (itself pinned by
PINS_FILE_SHA256), then the module's own ``main(argv)`` runs with ``--settings <that file>`` and, for that call only, its
module global SETTINGS_SHA256 set to the file's SHA-256 (restored afterwards). For rep_pass and classifier the pool-pins
globals of representation_pass (POOL_PINS_PATH, POOL_PINS_SHA256, load_pool_pins's defaults) point at the family's
``representation_pools__<family>.json`` for the call. Everything else is the 1B script's: its argument parsing, its
checks (check_settings on the same name and engine identity), its outputs, its prints (counts and hashes only) and its
exit codes (0 written; 2 refused, nothing written; 3 fewer than the keep count). No scoring code is copied, so there is
no parity to prove beyond the plumbing; tests/scorers/test_scorers_78b_parity.py shows the wrapper's outputs equal the
1B functions' outputs byte for byte on the 1B fixtures.

Before the call (the family preflight; refusals name hashes, events and flags, never text):
- every pin the command needs is filled: the settings' ``family_78b.waits`` lists each null pin with the event that fills
  it (the family's anchor job; recipe S_78 after it, addendum A1-A2; the a0-1101 retrain and A1's pass; Part 2's L1
  layer rule) and the commands that need it; a null one refuses with that event;
- ``--prepared`` (when the kind takes it) is the family's prepared set: its manifest hashes to the family's pin (the
  other family's manifest refuses by both hashes);
- ``--recipe`` / ``--recipe-s`` / ``--rec`` (when given) hash to the pin the settings hold for that flag;
- first of all, every ``--`` token is a full flag name of the 1B script's command (ALLOWED_FLAGS; reverify-E RV-E-1): the
  1B parsers expand abbreviations (``--li`` is ``--list`` to them), which these checks would not see.

untuned_answers runs twice per pod (the lead's ruling PP2, 5 Nov 2026): the first call takes the S3 list with the
losses (``--list s3=… --loss s1=… --loss s3_safe=… --out <job>/untuned``), the second the S4 list alone
(``--list s4=… --out <job>/untuned-s4``). The preflight refuses ``--list s4`` beside another list or a ``--loss``: the
unchanged 1B code's exit 3 (fewer keeps than the target, the pre-set S4 dose fallback) keeps only ``answers_*.json`` and
the record, so an S3 list in the same call would lose its ``s3_orig.pool.json`` (verify-E D1). The S3 call cannot exit 3.

After the S4 call, under a settings file with a ``doses`` block (Part 1 section 10): the nested dose lists S4 (48), S4_96
and S4_192 are derived from the pass's answers and the record's kept flags into ``<out>/doses/`` with a text-free
``s4_doses_record.json``; fewer than 192 kept applies the pre-set fallback (the top dose is all kept rows, named s4_top);
fewer than 48 keeps exit 3. A refusal in that step comes after the 1B pass has written: it is reported as such (the 1B
outputs are written, the doses were not; exit 2). A wrapper record ``<out>/wrapper_78b_record.json`` names the kind,
family, settings and code hashes and the exit code (only when the settings carry a family block, so the 1B-settings runs
stay byte-identical).
"""

from __future__ import annotations

import argparse
import importlib
import math
import sys
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file, write_atomic  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_DIR = HERE / "settings"
PINS_FILE = SETTINGS_DIR / "PINS-78B.json"
PINS_FILE_SHA256 = "8b9d8146d24910b15a81469bd206eba27d911a07bfe38bca04b39b1740fc71d9"
FAMILIES = ("olmo2-7b", "llama31-8b")
WRAPPER_RECORD = "wrapper_78b_record.json"
# The 1B scripts this wrapper runs, by SHA-256 (M: shasum -a 256 at HEAD 953f520, 5 Nov 2026; the four the stage-1 kit
# pins equal runkit/stage1-olmo/stage1_rules.py STAGE1_PINS). The 1B scripts stay byte for byte (P78:357, :407).
STAGE1_CODE = {
    "scripts/stage1/s1common.py": "930c8ea53d26baeeccaf2035949427d207f307ba0fec06ff0dec841c8c824552",
    "scripts/stage1/make_untuned_answers.py": "c37ac452b931c84ed28b45e9cfeed9cc9a07ec47ce5f1c6fd1bbef95086743c4",
    "scripts/stage1/representation_pass.py": "fb62bcaaaa35595a52de5a4217754cb390ffb4ba49e04dec6e515d7e3cebb8d9",
    "scripts/stage1/score_l1_larf.py": "4996fd3bfdd854ecd82630813f7f9b0dab88c4e7e26f81366c566b93c70e95e5",
    "scripts/stage1/score_classifier.py": "ee8ae89865e188a8e9f3430c9fbfbe129a415dcc9f3427111a7c77e02dc34549",
    "scripts/stage1/score_s3_datarx.py": "772e6ae546843b42c3a7564a644cffa269c38ffb30f4db0d59f0f405a9d5aace",
    "scripts/stage1/write_score_edit.py": "2721dbe7239e297b8771795efe04e280297e2e601d65499807f47be4ecf7ead5",
    "scripts/stage1/write_add_edit.py": "8b866b3d22bd0656bccd8dbb21ccabde3fda2726b85f149711455836928ad27c",
    "scripts/stage1/build_s_pool.py": "cb2ca385a3917d0f4be041ae08b1e121bc67f82a7fc95165e33550f053f463df",
}
# kind -> (module, settings script, the flags the preflight checks: flag -> dotted settings path of its recipe pin,
#          whether the kind takes --prepared, the subcommand position (None, or 0 for a leading subcommand))
KINDS = {
    "untuned_answers": ("scripts.stage1.make_untuned_answers", "make_untuned_answers",
                        {"--recipe": "pins.rec_recipe_sha256", "--recipe-s": "pins.recipe_s_sha256"}, False, None),
    "rep_pass": ("scripts.stage1.representation_pass", "representation_pass", {"--recipe": "pins.recipe_sha256"}, True, None),
    "l1_scan": ("scripts.stage1.score_l1_larf", "score_l1_larf", {"--recipe": "pins.rec_recipe_sha256"}, True, "scan"),
    "l1_score": ("scripts.stage1.score_l1_larf", "score_l1_larf", {}, True, "score"),
    "classifier": ("scripts.stage1.score_classifier", "score_classifier", {"--recipe": "pins.recipe_sha256"}, True, None),
    "s3_score": ("scripts.stage1.score_s3_datarx", "score_s3_datarx", {}, False, None),
    "score_edit": ("scripts.stage1.write_score_edit", "write_score_edit", {}, True, "a1|scorer"),
    "add_edit": ("scripts.stage1.write_add_edit", "write_add_edit", {"--recipe": "recipe_sha256"}, True, None),
    "s_pool": ("scripts.stage1.build_s_pool", "build_s_pool", {"--rec": "inputs.rec_recipe_sha256"}, True, None),
}
# RV-E-1 (reverify-E): the 1B scripts parse with argparse's default allow_abbrev=True, so '--li s4=…' is '--list' to the 1B
# script but invisible to flag_value and named_values, and one abbreviated flag would bypass PP2 (and the recipe and
# --out checks). So every '--' token of a command must be one of the full long names the 1B script's own parser defines
# for that command (the name before any '='); the wrapper owns --settings and --pool-pins. Keyed by command_of's value.
# tests/scorers/test_untuned_two_calls_78b.py checks these sets against the 1B parsers.
ALLOWED_FLAGS = {
    "untuned_answers": frozenset({"--recipe", "--recipe-s", "--list", "--loss", "--out"}),
    "rep_pass": frozenset({"--prepared", "--recipe", "--anchors", "--pool", "--pools-only", "--out"}),
    "scan": frozenset({"--prepared", "--recipe", "--anchors", "--out"}),
    "score": frozenset({"--prepared", "--scan", "--rows", "--summary", "--out"}),
    "classifier": frozenset({"--prepared", "--recipe", "--anchors", "--pool", "--out"}),
    "s3_score": frozenset({"--rows", "--summary", "--s-pool-record", "--answers-record", "--out"}),
    "a1": frozenset({"--unit", "--prepared", "--out"}),
    "scorer": frozenset({"--name", "--scores", "--scores-sha256", "--prepared", "--out"}),
    "add_edit": frozenset({"--prepared", "--recipe", "--list", "--combine-with", "--full-out", "--out"}),
    "s_pool": frozenset({"--config", "--sources", "--prepared", "--anchors", "--rec", "--full-out", "--out"}),
}
POOL_PIN_KINDS = ("rep_pass", "classifier")
MANIFEST_PATH = {"s_pool": "inputs.prepared_manifest_sha256", "add_edit": "prepared_manifest_sha256",
                 "score_edit": "prepared.manifest_sha256"}        # every other kind: pins.prepared_manifest_sha256


# ----- pins and settings ---------------------------------------------------------------------------------------------


def get_path(doc: dict, dotted: str):
    node = doc
    for key in dotted.split("."):
        if not isinstance(node, dict) or key not in node:
            raise s1.Refusal(f"the settings hold no field {dotted}")
        node = node[key]
    return node


class DosesRefusal(s1.Refusal):
    """A refusal in the doses step, after the 1B pass has written its outputs into ``out``."""

    def __init__(self, message: str, out: str):
        super().__init__(message)
        self.out = out


def load_pins_index(path: Path | None = None, expected_sha256: str | None = None) -> dict:
    """The settings index (PINS_FILE, pinned by PINS_FILE_SHA256; both read at call time)."""
    path = PINS_FILE if path is None else path
    expected_sha256 = PINS_FILE_SHA256 if expected_sha256 is None else expected_sha256
    try:
        data = path.read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the settings index cannot be read ({type(exc).__name__})") from None
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise s1.Refusal(f"settings/PINS-78B.json hashes to {digest}, scorers_78b.py pins {expected_sha256}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != "scale78b scorer settings index" or not isinstance(doc.get("files"), dict):
        raise s1.Refusal("settings/PINS-78B.json is not a scale78b scorer settings index")
    return doc


def settings_file(script: str, family: str) -> Path:
    return SETTINGS_DIR / f"{script}__{family}.json"


def load_family_settings(script: str, family: str, name: str, index: dict | None = None) -> tuple[dict, str, Path]:
    """The family's settings file for a 1B script: pinned by the index, then the 1B check_settings on the 1B name."""
    if family not in FAMILIES:
        raise s1.Refusal(f"--family must be one of {list(FAMILIES)}")
    index = index or load_pins_index()
    path = settings_file(script, family)
    pin = index["files"].get(path.name)
    if pin is None:
        raise s1.Refusal(f"settings/PINS-78B.json lists no {path.name}")
    try:
        doc, digest = s1.load_settings(path, pin, name)
    except OSError as exc:
        raise s1.Refusal(f"{path.name} cannot be read ({type(exc).__name__})") from None
    fam = doc.get("family_78b")
    if not isinstance(fam, dict) or fam.get("family") != family:
        raise s1.Refusal(f"{path.name} carries no family block for {family}")
    return doc, digest, path


def check_stage1_code(module: ModuleType) -> str:
    """The imported 1B module's file hashes to its pin (and s1common's); returns the module's SHA-256."""
    for mod in (module, s1):
        path = Path(mod.__file__).resolve()
        rel = s1.rel(path)
        pin = STAGE1_CODE.get(rel)
        if pin is None:
            raise s1.Refusal(f"{rel} is not a 1B script this wrapper pins")
        digest = sha256_file(path)
        if digest != pin:
            raise s1.Refusal(f"{rel} hashes to {digest}, the wrapper pins {pin}: the 1B scripts stay byte for byte")
    return sha256_file(Path(module.__file__).resolve())


# ----- the family preflight ------------------------------------------------------------------------------------------


def flag_value(argv: list[str], flag: str) -> str | None:
    """The value after the last occurrence of flag in argv (None when absent); '--flag=value' is accepted."""
    value = None
    for k, item in enumerate(argv):
        if item == flag and k + 1 < len(argv):
            value = argv[k + 1]
        elif item.startswith(flag + "="):
            value = item[len(flag) + 1:]
    return value


def named_values(argv: list[str], flag: str) -> list[str]:
    """The NAME of every NAME=PATH:SHA256 given after flag (a repeatable flag), in order."""
    names = []
    for k, item in enumerate(argv):
        if item == flag and k + 1 < len(argv):
            names.append(argv[k + 1].partition("=")[0])
        elif item.startswith(flag + "="):
            names.append(item[len(flag) + 1:].partition("=")[0])
    return names


def check_flag_names(kind: str, command: str, argv: list[str]) -> None:
    """RV-E-1: every '--' token's name (before any '=') is a full flag name of the 1B script's command (ALLOWED_FLAGS);
    an abbreviation ('--li', '--lo', '--ou'), the wrapper's own --settings or --pool-pins, a bare '--' or any other
    flag refuses before anything is checked or run."""
    allowed = ALLOWED_FLAGS[command]
    for item in argv:
        if item.startswith("--"):
            name = item.partition("=")[0]
            if name not in allowed:
                raise s1.Refusal(f"{kind} {command}: {name!r} is not one of the 1B script's full flag names "
                                 f"{sorted(allowed)}; abbreviations and other flags refuse (RV-E-1: the 1B parser would "
                                 f"expand an abbreviation that the wrapper's PP2, recipe and --out checks do not see)")


def check_untuned_calls(argv: list[str]) -> dict:
    """PP2: the S4 list runs alone in its own call. The unchanged 1B code's exit 3 (the S4 dose fallback) keeps only
    answers_*.json and the record, so another list in the same call would lose its outputs (s3_orig.pool.json)."""
    lists, losses = named_values(argv, "--list"), named_values(argv, "--loss")
    if "s4" in lists and (len(lists) > 1 or losses):
        raise s1.Refusal("untuned_answers: --list s4 runs alone in its own call (PP2: the S4 dose fallback's exit 3 in the "
                         "unchanged 1B code drops every other list's outputs, s3_orig.pool.json among them); the pod's "
                         "first call takes --list s3 with --loss s1 --loss s3_safe, the second --list s4 alone")
    return {"lists": lists, "losses": losses}


def with_subcommand(kind: str, argv: list[str]) -> list[str]:
    """A kind that maps to one subcommand of its 1B script (l1_scan -> scan, l1_score -> score) gets it prepended when
    the caller left it out; a kind with a choice (score_edit: a1 | scorer) must be given it."""
    sub = KINDS[kind][4]
    if sub is None or "|" in sub or argv[:1] == [sub]:
        return list(argv)
    if argv[:1] and not argv[0].startswith("-"):
        raise s1.Refusal(f"{kind} runs the subcommand {sub}, not {argv[0]!r}")
    return [sub] + list(argv)


def command_of(kind: str, argv: list[str]) -> str:
    sub = KINDS[kind][4]
    if sub is None:
        return kind
    if not argv or argv[0] not in sub.split("|"):
        raise s1.Refusal(f"{kind} takes a leading subcommand {sub}")
    return argv[0]


def null_pins(settings: dict, command: str) -> list[tuple[str, str]]:
    """(dotted path, event) of every pin the command needs that is still null."""
    waits = settings.get("family_78b", {}).get("waits", {})
    out = []
    for dotted, entry in sorted(waits.items()):
        needed = entry.get("needed_by", [])
        if ("*" in needed or command in needed) and get_path(settings, dotted) is None:
            out.append((dotted, entry.get("event", "")))
    return out


def check_manifest(prepared: Path, expected: str, family: str) -> str:
    from experiments.safety_selection.prepare import DataError, read_manifest

    try:
        _, digest = read_manifest(prepared, None)
    except (OSError, DataError, ValueError, KeyError) as exc:
        raise s1.Refusal(f"the prepared set's manifest cannot be read ({type(exc).__name__})") from None
    if digest != expected:
        raise s1.Refusal(f"the prepared manifest is {digest}, the {family} settings pin {expected}: not this family's "
                         f"prepared set")
    return digest


def check_recipe(path: Path, expected: str, flag: str) -> str:
    from experiments.safety_selection.config import ConfigError, config_sha256, load_recipe

    try:
        digest = config_sha256(load_recipe(path))
    except (OSError, ConfigError, ValueError, KeyError) as exc:
        raise s1.Refusal(f"{flag}: the recipe cannot be loaded ({type(exc).__name__})") from None
    if digest != expected:
        raise s1.Refusal(f"{flag} hashes to {digest}, the family settings pin {expected}")
    return digest


def preflight(kind: str, settings: dict, argv: list[str]) -> dict:
    """The family preflight (module doc); returns what it checked (hashes and flags only)."""
    _, _, recipe_flags, takes_prepared, _ = KINDS[kind]
    command = command_of(kind, argv)
    check_flag_names(kind, command, argv)
    family = settings["family_78b"]["family"]
    missing = null_pins(settings, command)
    if missing:
        dotted, event = missing[0]
        raise s1.Refusal(f"{kind} {command} for {family}: {len(missing)} pin(s) it needs are null; the first, {dotted}, "
                         f"waits for: {event}")
    checked: dict = {"command": command, "family": family}
    if kind == "untuned_answers":
        checked.update(check_untuned_calls(argv))
    if takes_prepared:
        prepared = flag_value(argv, "--prepared")
        if prepared is None:
            raise s1.Refusal(f"{kind} needs --prepared")
        expected = get_path(settings, MANIFEST_PATH.get(kind, "pins.prepared_manifest_sha256"))
        checked["prepared_manifest"] = check_manifest(Path(prepared), expected, family)
    for flag, dotted in recipe_flags.items():
        value = flag_value(argv, flag)
        if value is None:
            continue
        checked[flag] = check_recipe(Path(value), get_path(settings, dotted), flag)
    return checked


# ----- the nested doses (Part 1 section 10) ---------------------------------------------------------------------------


def candidates_needed(target: int, kept: int, answered: int) -> int:
    """ceil(target x answered / kept): how far down the candidate list the target reaches at the 1B keep rate (216 at
    192 for 57 of 64)."""
    if min(target, kept, answered) < 1 or kept > answered:
        raise s1.Refusal("the sizing rule needs positive counts with kept <= answered")
    return math.ceil(target * answered / kept)


def nested_doses(kept_ids: list[str], sizes: list[int], top_name: str, names: dict[str, str]) -> dict:
    """The nested lists from the kept ids in list order: for each size that is filled, its first ids; when the largest
    size is not filled, the top dose is all kept rows under top_name (the pre-set fallback). Refuses fewer than the
    smallest size, a repeated id, or sizes that are not increasing."""
    if list(sizes) != sorted(sizes) or len(set(sizes)) != len(sizes) or min(sizes) < 1:
        raise s1.Refusal("the dose sizes must be distinct and increasing")
    if len(set(kept_ids)) != len(kept_ids):
        raise s1.Refusal("the kept ids repeat")
    if len(kept_ids) < sizes[0]:
        raise s1.Refusal(f"{len(kept_ids)} kept rows, fewer than the smallest dose {sizes[0]}")
    lists = {names[str(n)]: list(kept_ids[:n]) for n in sizes if len(kept_ids) >= n}
    fallback = len(kept_ids) < sizes[-1]
    if fallback:
        lists[top_name] = list(kept_ids)
    ordered = [lists[k] for k in lists]
    for a, b in zip(ordered, ordered[1:]):
        if b[:len(a)] != a:
            raise s1.Refusal("the doses are not nested")
    return {"lists": lists, "fallback_fired": fallback, "kept": len(kept_ids), "top_dose": list(lists)[-1]}


def build_doses(out_dir: Path, settings: dict, settings_sha256: str, wrapper_sha256: str) -> tuple[dict, int]:
    """Read the pass's record and answers from out_dir, write <out>/doses/ (lists with text, a text-free record);
    returns (the record, the exit code: 0, or 3 when fewer than the smallest dose were kept)."""
    from scripts.stage1 import make_untuned_answers as mua

    spec = settings["doses"]
    record_path = out_dir / mua.RECORD
    answers_path = out_dir / "answers_s4.json"
    try:
        record_bytes, answers_bytes = record_path.read_bytes(), answers_path.read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the pass's record or its s4 answers cannot be read ({type(exc).__name__})") from None
    record = s1.strict_json(record_bytes)
    s4 = record.get("lists", {}).get("s4")
    if record.get("kind") != "stage1 untuned answers record" or not isinstance(s4, dict):
        raise s1.Refusal("the pass's record holds no s4 list")
    if s4.get("answers_file_sha256") != sha256_bytes(answers_bytes):
        raise s1.Refusal("answers_s4.json is not the file the record names")
    answers = s1.strict_json(answers_bytes)
    by_id = {item["id"]: item for item in answers["items"]}
    kept_ids = [row["id"] for row in s4["rows"] if row.get("kept") is True]
    if any(i not in by_id for i in kept_ids):
        raise s1.Refusal("a kept id has no answer in answers_s4.json")
    if len(kept_ids) < spec["sizes"][0]:
        return {"kept": len(kept_ids), "fallback_fired": True, "lists": {}}, mua.EXIT_FEW
    doses = nested_doses(kept_ids, spec["sizes"], spec["top_dose_name"], spec["names"])
    s4_list = out_dir / "s4.json"
    if s4_list.is_file():                                             # the 1B list of every kept row, when written
        listed = [i["id"] for i in s1.strict_json(s4_list.read_bytes())["items"]]
        if listed != kept_ids:
            raise s1.Refusal("the record's kept ids and s4.json's ids differ")
    files: dict[str, bytes] = {}
    entries = {}
    for name, ids in doses["lists"].items():
        file_name = spec["top_dose_file"] if name == spec["top_dose_name"] else spec["files"][str(len(ids))]
        data = canonical_json({"kind": "stage1 prompt list", "version": 1, "name": name,
                               "items": [{"id": i, "prompt": by_id[i]["prompt"], "response": by_id[i]["answer"]} for i in ids]})
        files[file_name] = data
        entries[name] = {"file": file_name, "rows": len(ids), "sha256": sha256_bytes(data), "ids": ids}
    sizing = spec["sizing"]
    dose_record = {"kind": "scale78b s4 doses record", "version": 1, "rule": spec["rule"], "fallback": spec["fallback"],
                   "kept": doses["kept"], "answered": s4.get("answered"), "chunks_run": s4.get("chunks_run"),
                   "drops": s4.get("drops"), "fallback_fired": doses["fallback_fired"], "top_dose": doses["top_dose"],
                   "nested": True, "doses": entries,
                   "sizing": {**sizing, "candidates_needed_recomputed": candidates_needed(
                       spec["sizes"][-1], sizing["keep_rate_1b"]["kept"], sizing["keep_rate_1b"]["answered"])},
                   "inputs": {"untuned_answers_record": sha256_bytes(record_bytes), "answers_s4": sha256_bytes(answers_bytes)},
                   "provenance": {"wrapper": "scripts/scale78b/scorers_78b.py", "wrapper_sha256": wrapper_sha256,
                                  "settings_sha256": settings_sha256, "pass_provenance": record.get("provenance")}}
    texts = [t for item in answers["items"] for t in (item["prompt"], item["answer"])]
    record_bytes_out = canonical_json(dose_record)
    if s1._text_hits(record_bytes_out, texts):
        raise s1.Refusal("the dose record would hold text")
    files[spec["record"]] = record_bytes_out
    s1.write_new_files(out_dir / spec["folder"], files)
    return dose_record, 0


# ----- running a 1B script --------------------------------------------------------------------------------------------


class Patched:
    """Module globals replaced for one call and restored afterwards (the D-2 wrapper's pattern)."""

    def __init__(self, module: ModuleType, **values):
        self.module, self.values, self.saved = module, values, {}

    def __enter__(self):
        for name, value in self.values.items():
            self.saved[name] = getattr(self.module, name)
            setattr(self.module, name, value)
        return self

    def __exit__(self, *exc):
        for name, value in self.saved.items():
            setattr(self.module, name, value)
        return False


def run_main(module: ModuleType, argv: list[str], settings_path: Path, settings_sha256: str,
             pool_pins: tuple[Path, str] | None = None) -> int:
    """module.main(argv + ['--settings', settings_path]) with the module's SETTINGS_SHA256 (and, with pool_pins, the
    representation_pass pool-pins globals) replaced for this call only."""
    from scripts.stage1 import representation_pass as rp

    argv = list(argv) + ["--settings", str(settings_path)]
    with Patched(module, SETTINGS_SHA256=settings_sha256):
        if pool_pins is None:
            return module.main(argv)
        path, digest = pool_pins
        if rp.load_pool_pins.__defaults__ != (rp.POOL_PINS_PATH, rp.POOL_PINS_SHA256):
            raise s1.Refusal("representation_pass.load_pool_pins's defaults are not POOL_PINS_PATH and POOL_PINS_SHA256")
        saved = rp.load_pool_pins.__defaults__
        with Patched(rp, POOL_PINS_PATH=path, POOL_PINS_SHA256=digest):
            rp.load_pool_pins.__defaults__ = (path, digest)
            try:
                if module is rp:
                    argv += ["--pool-pins", str(path)]
                return module.main(argv)
            finally:
                rp.load_pool_pins.__defaults__ = saved


def run_kind(kind: str, family: str, argv: list[str], index: dict | None = None) -> int:
    """The whole wrapper for one command: pins, the family settings, the preflight, the 1B main(), the doses and the
    wrapper record. Returns the exit code; refusals raise s1.Refusal before anything runs."""
    if kind not in KINDS:
        raise s1.Refusal(f"unknown kind {kind!r}; the kinds are {sorted(KINDS)}")
    module_name, script, _, _, _ = KINDS[kind]
    argv = with_subcommand(kind, argv)
    module = importlib.import_module(module_name)
    script_sha256 = check_stage1_code(module)
    index = index or load_pins_index()
    settings, digest, path = load_family_settings(script, family, module.SETTINGS_NAME, index)
    checked = preflight(kind, settings, argv)
    pool_pins = None
    if kind in POOL_PIN_KINDS:
        pools_doc, pools_sha, pools_path = load_family_settings("representation_pools", family, "representation_pools", index)
        from scripts.stage1 import representation_pass as rp

        rp.check_pool_pins(pools_doc)
        pool_pins = (pools_path, pools_sha)
    code = run_main(module, argv, path, digest, pool_pins)
    wrapper_sha256 = sha256_file(Path(__file__).resolve())
    out = flag_value(argv, "--out")
    doses = None
    if kind == "untuned_answers" and code in (0, 3) and "doses" in settings and out is not None \
            and "s4" in checked.get("lists", []):                     # the S4 call only (PP2); the S3 call has no doses
        try:
            doses, code = build_doses(Path(out).resolve(), settings, digest, wrapper_sha256)
        except s1.Refusal as exc:
            raise DosesRefusal(str(exc), out) from None
    if out is not None and code in (0, 3) and Path(out).is_dir():
        record = {"kind": "scale78b scorer wrapper record", "version": 1, "scorer_kind": kind, "family": family,
                  "command": checked["command"], "exit_code": code,
                  "settings": {"file": s1.rel(path), "sha256": digest, "index_sha256": PINS_FILE_SHA256},
                  "stage1_script": {"module": module_name, "sha256": script_sha256, "s1common_sha256": STAGE1_CODE["scripts/stage1/s1common.py"]},
                  "wrapper_sha256": wrapper_sha256, "checked": checked, "argv": list(argv),
                  "doses": None if doses is None else {k: v for k, v in doses.items() if k in ("kept", "fallback_fired", "top_dose")}}
        target = Path(out).resolve() / WRAPPER_RECORD
        if target.exists():
            raise s1.Refusal(f"{WRAPPER_RECORD} exists in {out}")
        write_atomic(target, canonical_json(record))
    return code


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0], allow_abbrev=False,
                                     usage="%(prog)s KIND --family FAMILY <the 1B script's own arguments>")
    parser.add_argument("kind", choices=sorted(KINDS))
    parser.add_argument("--family", required=True, choices=list(FAMILIES))
    args, rest = parser.parse_known_args(argv)        # everything the wrapper does not own goes to the 1B script, in order
    if rest[:1] == ["--"]:
        rest = rest[1:]
    if "--settings" in rest or any(a.startswith("--settings=") for a in rest):
        print("REFUSED: --settings is the wrapper's (the family's settings file) (nothing written)", file=sys.stderr)
        return 2
    try:
        return run_kind(args.kind, args.family, rest)
    except DosesRefusal as exc:
        print(f"REFUSED after the 1B pass: the 1B outputs are written in {exc.out}; the doses were not written ({exc})",
              file=sys.stderr)
        return 2
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
