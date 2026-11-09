"""ENGINEERING FIXTURES for Track R's tests (synthetic only; nothing is downloaded, and no real unit, record, prepared
row, prompt or answer is read). On top of the 1B fixtures (b10_fixtures: the tiny engine world and Gate-A-like a0
units; b11_fixtures: a tiny OLMo-2 pair of snapshots and an adapter; oext_fixtures: a synthetic PHTest bank) and Track
O's (oext78_fixtures: a family's settings folder with a W1-18 settings file that binds the fixture cut), this builds a
family's REFS-78B-shaped index for one reference seed. None of these numbers is a scientific result."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import b10_fixtures as fb
import oext78_fixtures as o78

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.scale78b import make_refs_settings_78b as mk
from scripts.scale78b import oext_78b as ox
from scripts.scale78b import refs_78b as rw
from scripts.stage1_s1 import eval_adapter as ea

oe = o78.oe
FAMILY, OTHER = o78.FAMILY, o78.OTHER
SEED = 1102
OTHER_MANIFEST = o78.OTHER_MANIFEST
call, strip, write = o78.call, o78.strip, o78.write


def compare(a: Path, b: Path, exact: set[str]) -> dict[str, str]:
    """Track O's comparison (oext78_fixtures.compare), then a file that differs only where it names the SHA-256 of a
    file that is equal once wall-clock fields are dropped (a completion marker's hash: its times differ) is "hashes"."""
    out = o78.compare(a, b, exact)
    changed = True
    while changed:                       # a marker names the hashes of files that name other markers' hashes
        changed = False
        pairs = {sha256_file(a / n): sha256_file(b / n) for n, v in out.items() if v in ("parsed", "hashes")}

        def swap(node):
            if isinstance(node, dict):
                return {k: swap(v) for k, v in node.items()}
            if isinstance(node, list):
                return [swap(v) for v in node]
            return pairs.get(node, node) if isinstance(node, str) else node
        for name in [n for n, v in out.items() if v == "differs" and n.endswith(".json")]:
            if strip(swap(o78.parse(a / name))) == strip(o78.parse(b / name)):
                out[name], changed = "hashes", True
    return out
SL_SETTINGS_1B = ea.REPO / "scripts/stage1_s1/settings/safe_lora.json"


class Refs(o78.Family):
    """A family's fixture settings folder (Track O's O-ext files and this seed's two files) and its REFS index."""

    def __init__(self, base: Path, family: str = FAMILY, seed: int = SEED):
        super().__init__(base, family)
        self.seed = seed

    def name(self, role: str) -> str:
        return mk.file_name(role, self.family, self.seed if role in ("eval_adapter", "safe_lora") else None)

    def put(self, role: str, doc) -> tuple[Path, str]:
        path = self.dir / self.name(role)
        if isinstance(doc, bytes):
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(doc)
            self.files[role] = (path, sha256_bytes(doc))
        else:
            self.files[role] = (path, write(path, doc))
        return self.files[role]

    def label(self, role: str) -> str:
        return str((self.dir / self.name(role)).resolve())

    def refs_index(self, **changes) -> tuple[Path, str]:
        doc = {"kind": rw.INDEX_KIND, "version": rw.INDEX_VERSION, "family": self.family, "seed": self.seed,
               "manifest_sha256": self.manifest,
               "other_manifests": {OTHER if self.family == FAMILY else FAMILY: self.other_manifest},
               "files": {r: {"file": p.name, "sha256": h} for r, (p, h) in self.files.items() if r in mk.ROLES},
               "waits": self.waits, "branch": self.branch, "w1_18_record_sha256": None,
               "commands": ["eval_adapter", "safe_lora"], "base": {}}
        doc.update(changes)
        path = self.dir / mk.index_name(self.family, self.seed)
        return path, write(path, doc)

    def refs_leading(self, **changes) -> list[str]:
        path, digest = self.refs_index(**changes)
        return ["--family", self.family, "--seed", str(self.seed), "--index", str(path), "--index-sha256", digest]


def sl_entry(refs: Refs) -> dict:
    """B10's Safe LoRA entry (the 1B one) with its settings pin at the fixture folder's safe_lora file."""
    entry = copy.deepcopy(fb.real_doc()["external_transforms"]["safe_lora"])
    path, digest = refs.files["safe_lora"]
    entry["settings"] = {"path": refs.label("safe_lora"), "sha256": digest}
    return entry


def ea_doc(world, refs: Refs, *, status: str = "dev100_recipe_cap", **changes) -> dict:
    """B10's fixture settings (b10_fixtures' pins) whose O-ext pin and Safe LoRA pin name the fixture folder's files."""
    path, digest = refs.files["oext_eval"]
    pins = {"recipe__file_sha256": sha256_file(world.recipe), "prefix__text_sha256": world.prefix_sha256,
            "prefix__source": "ENGINEERING FIXTURE placeholder", "overrefusal_bank__status": status,
            "external_transforms": {"identity": fb.transform_entry("identity"), "safe_lora": sl_entry(refs)},
            "oext__settings": {"path": refs.label("oext_eval"), "sha256": digest}, "oext__branch": refs.branch,
            "oext__module_sha256": oe.module_sha256()}
    return fb.fixture_doc(world.manifest, {SEED: world.unit}, **{**pins, **changes})


def settings_of(doc: dict, refs: Refs) -> ea.Settings:
    with ox.patched([(ea, "OEXT_SETTINGS_PATH", refs.label("oext_eval"))]):
        return ea.settings_from_doc(doc)


def ea_world(base: Path, *, branch: str = "pending_w1_18") -> SimpleNamespace:
    """b10_fixtures' world (a prepared set, a Gate-A-like a0 unit at seed 1102, a recipe file, a prefix file) plus a
    family folder: Track O's O-ext files for ``branch``, the 1B safe_lora settings bytes as this seed's Safe LoRA file,
    and this seed's B10 settings (status dev100_recipe_cap: no O-ext run), with a certification report."""
    prepared, manifest = fb.prepared(base)
    unit = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", SEED)
    recipe = base / "recipe.json"
    recipe.write_bytes(canonical_json(fb.recipe()))
    prefix, prefix_sha = fb.write_prefix(base)
    world = SimpleNamespace(base=base, prepared=prepared, manifest=manifest, unit=unit, recipe=recipe, prefix=prefix,
                            prefix_sha256=prefix_sha)
    refs = Refs(base / "fam")
    refs.manifest = manifest
    world.inp = o78.oext_inputs(base / "oext", refs, branch=branch)
    refs.put("safe_lora", SL_SETTINGS_1B.read_bytes())
    world.doc = ea_doc(world, refs)
    refs.put("eval_adapter", world.doc)
    world.refs = refs
    world.settings = settings_of(world.doc, refs)
    world.cert = fb.certification(prepared, unit, world.settings, base / "certification")
    return world


def oext_doc_for(world, refs: Refs) -> dict:
    """The status oext_pinned B10 settings for the family folder's current O-ext file (written as this seed's file)."""
    doc = ea_doc(world, refs, status="oext_pinned")
    refs.put("eval_adapter", doc)
    return doc


def common(world) -> list:
    return ["--prepared", world.prepared, "--recipe", world.recipe, "--reference", world.unit / "COMPLETE.json"]


def fixture_codec(recipe):
    return fb.fx.fixture_codec()


def wrapped(world, argv: list, *, refs: Refs | None = None, leading: list | None = None, **loader_options):
    """refs_78b's eval_adapter command over the family folder, with the fixture loaders and codec."""
    refs = refs or world.refs
    return call(rw.main, ["eval_adapter", *(leading or refs.refs_leading()), *[str(a) for a in argv]],
                loaders=fb.fx.fixture_loaders(**loader_options), codec=fixture_codec)


def direct(world, argv: list, doc: dict, *, refs: Refs | None = None, oext_doc: dict | None = None,
           **loader_options):
    """The 1B eval_adapter.main as the 1B tests call it (settings and O-ext settings injected), with the same documents
    and the same O-ext path label (eval_adapter.OEXT_SETTINGS_PATH set to it for the call)."""
    refs = refs or world.refs
    with ox.patched([(ea, "OEXT_SETTINGS_PATH", refs.label("oext_eval"))]):
        return call(ea.main, [str(a) for a in argv], _settings=ea.settings_from_doc(doc),
                    _oext_settings=None if oext_doc is None else oe.settings_from_doc(oext_doc),
                    _loaders=fb.fx.fixture_loaders(**loader_options), _codec=fixture_codec)


def globals_now() -> dict:
    """Every module global the wrapper sets (to show they are restored)."""
    from scripts.stage1.limits import overrefusal_checks as w1
    from scripts.stage1_s1 import safe_lora as sl

    return {"ea.load": ea.load_pinned_settings, "ea.path": ea.SETTINGS_PATH, "ea.sha": ea.SETTINGS_SHA256,
            "ea.oext": ea.OEXT_SETTINGS_PATH, "oe.load": oe.load_pinned_settings, "oe.path": oe.SETTINGS_PATH,
            "w1.path": w1.SETTINGS_PATH, "w1.sha": w1.SETTINGS_SHA256, "sl.path": sl.SETTINGS_PATH,
            "sl.sha": sl.SETTINGS_SHA256}


def committed_index(family: str, seed: int) -> list[str]:
    path = mk.SETTINGS_DIR / mk.index_name(family, seed)
    return ["--family", family, "--seed", str(seed), "--index", str(path), "--index-sha256", sha256_file(path)]


def hex_lines(text: str) -> list[str]:
    return [line for line in text.splitlines() if line.strip()]


def jsonl_last(text: str) -> dict:
    return json.loads(hex_lines(text)[-1])
