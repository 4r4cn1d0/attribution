"""ENGINEERING FIXTURES for Track O's tests (synthetic only; nothing is downloaded, and no real unit, record, PHTest
text, prepared row or answer is read). On top of the 1B fixtures (oext_fixtures: a synthetic PHTest bank and a
W1-18-shaped record; oext_unit_fixtures: the tiny engine units; b17_support: the lean job's world; test_limits_fixtures:
W1-18's synthetic units and fake tools) this builds a family's settings folder and an OEXT-78B-shaped index for the
wrapper, with one W1-18 settings file that binds the fixture cut (oext_eval's binding reads it through the module
globals the wrapper sets). None of these numbers is a scientific result."""

from __future__ import annotations

import contextlib
import copy
import io
import json
from pathlib import Path
from types import SimpleNamespace

import oext_fixtures as ofx
import oext_unit_fixtures as uf

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.scale78b import make_oext_settings_78b as mk
from scripts.scale78b import oext_78b as w
from scripts.stage1 import s1common as s1

oe, ou = ofx.oe, uf.ou
FAMILY, OTHER = "olmo2-7b", "llama31-8b"
CUT = uf.CUT                                    # 3: the fixture O-ext cut (the fixture recipe's cap is 8 new tokens)
DEV = 2                                         # the fixture dev bank's over-refusal prompts
OTHER_MANIFEST = "f" * 64                       # the other family's manifest pin in a fixture index
ENGINE_Y_FIXTURE = "e" * 64                     # a synthetic engine-Y identity (never the running engine)
BAR = {"min_flags_agree": 2, "max_count_move": 0, "per_prompts": DEV}


def write(path: Path, doc: dict) -> str:
    """Canonical bytes (so a doc's settings_from_doc SHA-256 equals the file's), returns the SHA-256."""
    path.parent.mkdir(parents=True, exist_ok=True)
    data = canonical_json(doc)
    path.write_bytes(data)
    return sha256_bytes(data)


def w1_18_doc(cut: int = CUT) -> dict:
    """The 1B W1-18 settings with the fixture cut and bar (oext_eval's binding compares them with the O-ext settings)."""
    doc = copy.deepcopy(mk.load_base("limits_overrefusal_checks"))
    doc["truncation"].update(cap_tokens=cut, min_flags_agree=BAR["min_flags_agree"],
                             max_count_move=BAR["max_count_move"])
    return doc


def eval_doc(*, branch: str, record_sha256: str, w1_settings_sha256: str, w1_record_sha256: str | None,
             full_reason: str | None = None, engine_x: str | None = None) -> dict:
    doc = ofx.settings_doc(branch=branch, cut=CUT, dev=DEV, record_sha256=record_sha256,
                           w1_18_sha256=w1_record_sha256, full_reason=full_reason)
    doc["cap"]["w1_18"]["settings_sha256"] = w1_settings_sha256
    doc["transfer"]["bar"].update(BAR)
    if engine_x is not None:
        doc["engine_x"] = engine_x
    return doc


class Family:
    """A family's fixture settings folder and index; ``files`` maps role -> (path, SHA-256)."""

    def __init__(self, base: Path, family: str = FAMILY):
        self.base, self.family = base, family
        self.dir = base / "settings78"
        self.files: dict[str, tuple[Path, str]] = {}
        self.waits: list[dict] = []
        self.branch = None
        self.manifest = None
        self.other_manifest = OTHER_MANIFEST          # per instance: a test that changes it changes only its own
        self.engine_y = ENGINE_Y_FIXTURE              # the Y index's engine identity

    def put(self, role: str, doc: dict) -> tuple[Path, str]:
        path = self.dir / mk.file_name(role, self.family)
        self.files[role] = (path, write(path, doc))
        return self.files[role]

    def label(self, role: str) -> str:
        return str((self.dir / mk.file_name(role, self.family)).resolve())

    def index(self, engine: str = "X") -> tuple[Path, str]:
        """The family's index for ``engine`` (the maker's form, version 2): the files of that engine's roles."""
        roles = mk.INDEX_ROLES[engine]
        doc = {"kind": w.INDEX_KIND, "version": w.INDEX_VERSION, "family": self.family, "engine": engine,
               "manifest_sha256": self.manifest,
               "other_manifests": {OTHER if self.family == FAMILY else FAMILY: self.other_manifest},
               "files": {r: {"file": p.name, "sha256": h} for r, (p, h) in self.files.items() if r in roles},
               "waits": [{**x, "roles": [r for r in x["roles"] if r in roles]} for x in self.waits
                         if set(x["roles"]) & set(roles)],
               "commands": list(mk.INDEX_COMMANDS[engine]), "base": {}}
        if engine != "W1":
            doc.update(branch=self.branch, w1_18_record_sha256=None, w1_18_record_path=None, inputs={},
                       engine_identity=s1.code_identity()["sha256"] if engine == "X" else self.engine_y)
        path = self.dir / mk.index_name(self.family, engine)
        return path, write(path, doc)

    def leading(self, engine: str = "X") -> list[str]:
        """The wrapper's leading options for this family and engine, with a fresh index by path and SHA-256."""
        path, digest = self.index(engine)
        return ["--family", self.family, "--engine", engine, "--index", str(path), "--index-sha256", digest]


def oext_inputs(base: Path, fam: Family, *, branch: str, full_reason: str | None = None,
                w1_passes: bool | None = None, engine_y: bool = False) -> SimpleNamespace:
    """The family's W1-18 settings, a W1-18 record made under them (when the branch needs one), the bank, and the
    family's O-ext settings (X, or Y with ENGINE_Y_FIXTURE)."""
    w_path, w_sha = fam.put("limits_overrefusal_checks", w1_18_doc())
    bank, record, record_sha = ofx.bank_files(base / "bank")
    rec_path = rec_sha = None
    if branch != oe.PENDING and full_reason is None:
        passes = (branch == "128") if w1_passes is None else w1_passes
        rec_path, rec_sha = ofx.w1_18_record(base / "w1_18", passed=passes, cut=CUT, settings_sha256=w_sha)
    role = "oext_eval_y" if engine_y else "oext_eval"
    doc = eval_doc(branch=branch, record_sha256=record_sha, w1_settings_sha256=w_sha, w1_record_sha256=rec_sha,
                   full_reason=full_reason, engine_x=ENGINE_Y_FIXTURE if engine_y else None)
    e_path, e_sha = fam.put(role, doc)
    fam.branch = branch
    return SimpleNamespace(bank=bank, record=record, w1_18=rec_path, w1_18_sha256=rec_sha, w_path=w_path, w_sha=w_sha,
                           eval_path=e_path, eval_sha=e_sha, eval_doc=doc, role=role)


# ----- the unit command ----------------------------------------------------------------------------------------------


def unit_world(base: Path, branch: str = "128", **options) -> SimpleNamespace:
    """oext_unit_fixtures' world (prepared set, recipe, three engine units) plus the family's files for ``branch``."""
    world = uf.build_world(base / "world")
    fam = Family(base / "fam")
    fam.manifest = world.manifest
    inp = oext_inputs(base / "inputs", fam, branch=branch, **options)
    return SimpleNamespace(world=world, fam=fam, inp=inp)


def put_unit_settings(env: SimpleNamespace, *, engine_y: bool = False, **changes) -> tuple[Path, str, dict]:
    """oext_unit's settings with the fixture pins and the true path label of the family's O-ext settings file."""
    role, eval_role = ("oext_unit_y", "oext_eval_y") if engine_y else ("oext_unit", "oext_eval")
    doc = uf.settings_doc(env.world.manifest, env.fam.files[eval_role][1], env.world.recipe, **changes)
    doc["oext"]["settings"]["path"] = env.fam.label(eval_role)
    if engine_y:
        doc["engine_x"] = ENGINE_Y_FIXTURE
    path, digest = env.fam.put(role, doc)
    return path, digest, doc


def unit_args(env: SimpleNamespace, out: Path, *, run: Path | None = None, untuned: bool = False,
              source: Path | None = None, w1_18: bool = True, prepared: Path | None = None) -> list[str]:
    args = ["run"]
    if untuned:
        args.append("--untuned")
    if run is not None:
        args += ["--run", str(run), "--checkpoint", "e1"]
    args += ["--prepared", str(prepared or env.world.prepared), "--recipe", str(env.world.recipe_file),
             "--oext-bank", str(env.inp.bank), "--oext-record", str(env.inp.record)]
    if w1_18 and env.inp.w1_18 is not None:
        args += ["--w1-18-record", str(env.inp.w1_18)]
    if source is not None:
        args += ["--dev100-source", str(source)]
    return args + ["--out", str(out)]


def call(fn, *args, **kwargs) -> tuple[int, str, str]:
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = fn(*args, **kwargs)
    return code, out.getvalue(), err.getvalue()


def wrapper(env_or_fam, argv: list[str], **kwargs) -> tuple[int, str, str]:
    """w.main with this family's fresh index named after the leading ``--family F [--engine E]`` of ``argv`` (the
    other leading options are added; a test that gives its own --index passes argv to w.main itself)."""
    fam = env_or_fam.fam if hasattr(env_or_fam, "fam") else env_or_fam
    argv = list(argv)
    engine, i = ("W1" if argv[:1] == ["w1_18"] else "X"), 1
    while i < len(argv) and argv[i] in ("--family", "--engine"):
        if argv[i] == "--engine":
            engine = argv[i + 1]
        i += 2
    if i == 1:                                  # no --family given: leave argv as it is (the refusal tests)
        return call(w.main, argv, **kwargs)
    index_path, digest = fam.index(engine)
    argv[i:i] = ["--index", str(index_path), "--index-sha256", digest]
    return call(w.main, argv, **kwargs)


def direct_unit(env: SimpleNamespace, args: list[str], unit_doc: dict, *, eval_role: str = "oext_eval",
                **loader_options) -> tuple[int, str, str]:
    """The 1B oext_unit.main as the 1B tests call it (settings and O-ext settings injected), with the same documents
    and the same path label (oext_unit.OEXT_SETTINGS_PATH set to it for the call: the label the 1B validator takes)."""
    with w.patched([(ou, "OEXT_SETTINGS_PATH", env.fam.label(eval_role))]):
        return call(ou.main, args, loaders=uf.loaders(**loader_options), settings=ou.settings_from_doc(unit_doc),
                    oext_settings=oe.settings_from_doc(env.inp.eval_doc))


# ----- output comparison ---------------------------------------------------------------------------------------------

VOLATILE = ("seconds", "_s", "utc", "elapsed", "memory", "time", "costs", "loaded_in", "pid", "started", "ended",
            "process_age", "origin_utc_epoch", "monotonic")


def _volatile(key: str) -> bool:
    return "seconds" in key or any(key == v or key.endswith(v) or key.startswith(v) for v in VOLATILE)


def strip(node):
    if isinstance(node, dict):
        return {k: strip(v) for k, v in node.items() if not _volatile(k)}
    if isinstance(node, list):
        return [strip(v) for v in node]
    return node


def parse(path: Path):
    data = path.read_bytes()
    if path.suffix == ".jsonl":
        return [json.loads(line) for line in data.decode("utf-8").splitlines() if line]
    return json.loads(data)


def tree(folder: Path) -> dict[str, bytes]:
    return {p.relative_to(folder).as_posix(): p.read_bytes() for p in sorted(folder.rglob("*")) if p.is_file()}


def compare(a: Path, b: Path, exact: set[str]) -> dict[str, str]:
    """Each file of two output folders: "bytes" (equal bytes), "parsed" (equal once wall-clock fields are dropped) or
    "differs". The names in ``exact`` must be "bytes"; the two folders must hold the same names."""
    ta, tb = tree(a), tree(b)
    assert sorted(ta) == sorted(tb), (sorted(set(ta) ^ set(tb)))
    out = {}
    for name in ta:
        if ta[name] == tb[name]:
            out[name] = "bytes"
        elif name.endswith((".json", ".jsonl")) and strip(parse(a / name)) == strip(parse(b / name)):
            out[name] = "parsed"
        else:
            out[name] = "differs"
    for name in [n for n in ta if n.endswith("COMPLETE.json") and out[n] == "differs"]:
        # a completion marker lists every file's SHA-256: the files that differ only in wall-clock fields are dropped
        folder = name[:-len("COMPLETE.json")]
        drop = {n[len(folder):] for n, v in out.items() if v == "parsed" and n.startswith(folder)}
        x, y = (strip(parse(root / name)) for root in (a, b))
        for doc in (x, y):
            doc["files"] = {k: v for k, v in (doc.get("files") or {}).items() if k not in drop}
        if x == y:
            out[name] = "parsed"
    assert not (missing := sorted(n for n in exact if out.get(n) != "bytes")), missing
    return out


def hex64_in(text: str) -> bool:
    import re

    return re.search(r"[0-9a-f]{64}", text) is not None


def fixture_texts() -> list[str]:
    """Texts that must never appear in a print or a refusal: the synthetic PHTest prompts and the fixture marker."""
    return [prompt for _, prompt in ofx.PHTEST_ROWS] + [ofx.FIXTURE]


def sha(path: Path) -> str:
    return sha256_file(path)


__all__ = ["s1", "sha", "w", "mk", "oe", "ou", "ofx", "uf"]
