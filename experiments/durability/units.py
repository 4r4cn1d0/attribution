"""What a backup unit is and which files it holds (stdlib only).

A unit is something that will not change again:

| kind | root | sealed by | restore verification |
|---|---|---|---|
| ``run`` | an engine run folder | ``COMPLETE.json``, written last | ``verify_run`` on it and on every reachable dependency; a run-one needs ``stream.checked`` |
| ``attempt`` | a Stage B attempt folder | its after-call ``receipt.json`` | bytes; plus the engine checks of ``run/`` when it is a sealed engine folder |
| ``prepared`` | the prepared-data folder | ``manifest.sha256`` | the manifest hash and every file hash it pins |
| ``code`` | the ``experiments`` folder | the engine code identity | the identity recomputed from the copy |
| ``failed-run`` | a preserved failed run folder | ``error.txt`` | bytes only (a failure record, never evidence of a result) |
| ``record`` | a study root, one file | the write-once file itself | bytes only |

Files are listed with their size and SHA-256 at the moment the unit is described; a file that
changes afterwards makes the copy fail (the hash of the stored bytes is compared). ``status.json``
of a run folder is the engine's convenience snapshot: it is copied but pinned by nothing. Symlinks
and special files are refused: a unit is plain files under its root. Journals and
acknowledgements never live inside a unit (the verifier rejects files added to a sealed folder).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Sequence

from experiments.safety_selection.common import REUSED_MODULES
from experiments.safety_selection.config import config_sha256
from experiments.safety_selection.ledger import COMPLETE, ERROR, read_complete, verify_files
from experiments.safety_selection.prepare import read_manifest
from experiments.safety_selection.verify import read_dependencies

from .common import (SourceMap, TransferError, VerificationFailed, canonical_json, read_json, recorded_path,
                     relative_name, sha256_bytes, sha256_file)

__all__ = ["Unit", "FOLDER_KINDS", "ENGINE_PACKAGES", "run_unit", "attempt_unit", "prepared_unit", "code_unit",
           "failed_run_unit", "record_unit", "unit_id_of", "code_identity_of", "dependency_folders", "is_sealed"]

FOLDER_KINDS = ("run", "attempt", "prepared", "code", "failed-run")
ENGINE_PACKAGES = ("safety_selection", "minimal_safety")
RECEIPT = "receipt.json"


@dataclass(frozen=True)
class Unit:
    """One backup unit: its kind, recorded root, files ``(name, bytes, sha256)``, the hash of the
    file that seals it, the sealed engine folders inside it and the identities they pin."""

    kind: str
    root: str
    files: tuple[tuple[str, int, str], ...]
    seal_sha256: str | None = None
    engine_runs: tuple[str, ...] = ()
    pins: dict = field(default_factory=dict, compare=False)

    @property
    def content_sha256(self) -> str:
        return sha256_bytes(canonical_json([list(f) for f in self.files]))

    @property
    def unit_id(self) -> str:
        """A unit is named by its kind and root, a record also by its file name: the same name must
        always hold the same bytes."""
        return unit_id_of(self.kind, self.root, self.files[0][0] if self.kind == "record" else None)

    @property
    def bytes(self) -> int:
        return sum(size for _, size, _ in self.files)

    def manifest(self) -> dict:
        return {"unit": self.unit_id, "kind": self.kind, "root": self.root, "files": [list(f) for f in self.files],
                "content_sha256": self.content_sha256, "seal_sha256": self.seal_sha256,
                "engine_runs": list(self.engine_runs), "pins": dict(self.pins)}

    @classmethod
    def from_manifest(cls, data: dict) -> "Unit":
        unit = cls(kind=data["kind"], root=recorded_path(data["root"]),
                   files=tuple((relative_name(n), int(size), str(digest)) for n, size, digest in data["files"]),
                   seal_sha256=data.get("seal_sha256"), engine_runs=tuple(data.get("engine_runs", ())),
                   pins=dict(data.get("pins", {})))
        if unit.unit_id != data.get("unit") or unit.content_sha256 != data.get("content_sha256"):
            raise VerificationFailed("a stored unit manifest does not describe itself consistently")
        return unit


def unit_id_of(kind: str, root: str, name: str | None = None) -> str:
    return sha256_bytes("\n".join([kind, root] + ([name] if name is not None else [])).encode("utf-8"))


def _files(local_root: Path, names: Sequence[str] | None = None) -> tuple[tuple[str, int, str], ...]:
    """(name, bytes, sha256) of the named files, or of every file under the folder; a symlink or a
    special file refuses."""
    if names is None:
        if not local_root.is_dir() or local_root.is_symlink():
            raise TransferError(f"{local_root} is not a folder")
        paths = sorted(p for p in local_root.rglob("*") if not p.is_dir() or p.is_symlink())
    else:
        paths = [local_root / relative_name(name) for name in sorted(set(names))]
    out = []
    for path in paths:
        behind = any(parent.is_symlink() for parent in path.parents if parent != local_root
                     and parent.is_relative_to(local_root))
        if behind or path.is_symlink() or not path.is_file():
            raise TransferError(f"{path} is a symlink, missing or not a regular file; a unit is plain files only")
        out.append((path.relative_to(local_root).as_posix(), path.stat().st_size, sha256_file(path)))
    return tuple(out)


def is_sealed(folder: Path) -> bool:
    """A complete engine folder whose files still match its COMPLETE.json."""
    return (folder / COMPLETE).is_file() and not verify_files(folder)


def _run_pins(folder: Path) -> dict:
    """The identities a sealed run pins (from its hashed identity.json, checked against the
    completion marker); the recipe travels inside identity.json and must hash to its pin."""
    marker, identity = read_complete(folder), read_json(folder / "identity.json")
    short = marker.get("identity") or {}
    pins = {key: short.get(key) for key in ("manifest_sha256", "recipe_sha256", "code_sha256")}
    if any(identity.get(key) != value for key, value in pins.items()):
        raise VerificationFailed(f"{folder}: the completion identity differs from its hashed identity.json")
    if pins["recipe_sha256"] is not None and config_sha256(identity["recipe"]) != pins["recipe_sha256"]:
        raise VerificationFailed(f"{folder}: the recipe inside identity.json does not hash to its pin")
    return pins


def run_unit(root: str | Path, source_map: SourceMap = SourceMap()) -> Unit:
    """A sealed engine run folder (COMPLETE.json written last and every listed file intact). An
    unsealed or failed folder is not a unit: saved states without the marker are not evidence."""
    root = recorded_path(root)
    local = source_map.local(root)
    problems = verify_files(local) if local.is_dir() else [f"no folder at {local}"]
    if problems:
        raise VerificationFailed(f"{root} is not a sealed run: {problems[:3]}")
    return Unit("run", root, _files(local), sha256_file(local / COMPLETE), (root,), _run_pins(local))


def failed_run_unit(root: str | Path, source_map: SourceMap = SourceMap()) -> Unit:
    """A preserved failed run folder (it has error.txt): kept as a record of the attempt and its
    cost, verified as bytes only."""
    root = recorded_path(root)
    local = source_map.local(root)
    if not (local / ERROR).is_file() or (local / COMPLETE).exists():
        raise VerificationFailed(f"{root} is not a preserved failure (no {ERROR}, or it has {COMPLETE})")
    return Unit("failed-run", root, _files(local), sha256_file(local / ERROR))


def attempt_unit(root: str | Path, source_map: SourceMap = SourceMap()) -> Unit:
    """A Stage B operation attempt once its after-call receipt.json exists (complete, failed or
    closed after an interruption). When ``run/`` is a sealed engine folder it is verified as one."""
    root = recorded_path(root)
    local = source_map.local(root)
    if not (local / RECEIPT).is_file():
        raise VerificationFailed(f"{root} has no after-call {RECEIPT}; an open attempt is not a unit")
    run = local / "run"
    sealed = (run / COMPLETE).exists()
    if sealed and verify_files(run):
        raise VerificationFailed(f"{root}/run has a completion marker that no longer verifies")
    return Unit("attempt", root, _files(local), sha256_file(local / RECEIPT),
                (f"{root}/run",) if sealed else (), _run_pins(run) if sealed else {})


def prepared_unit(root: str | Path, source_map: SourceMap = SourceMap()) -> Unit:
    """The prepared-data folder: its frozen manifest hash and every file the manifest pins (the
    held-out bank included, as opaque bytes; nothing is parsed beyond the manifest)."""
    root = recorded_path(root)
    local = source_map.local(root)
    manifest, digest = read_manifest(local)
    files = _files(local)
    have = {name: sha for name, _, sha in files}
    wrong = sorted(name for name, sha in manifest["files"].items() if have.get(name) != sha)
    if wrong:
        raise VerificationFailed(f"{root}: prepared files differ from the manifest: {wrong[:3]}")
    return Unit("prepared", root, files, digest, (), {"manifest_sha256": digest})


def code_identity_of(experiments_dir: Path) -> dict:
    """The engine's code identity (``safety_selection.common.code_identity``) computed over a copy
    of the source tree: the same file set and the same hash."""
    files = {f"safety_selection/{path.name}": sha256_file(path)
             for path in sorted((experiments_dir / "safety_selection").glob("*.py"))}
    files.update({f"minimal_safety/{name}": sha256_file(experiments_dir / "minimal_safety" / name)
                  for name in REUSED_MODULES})
    return {"files": files, "sha256": sha256_bytes(canonical_json(files))}


def code_unit(root: str | Path, source_map: SourceMap = SourceMap()) -> Unit:
    """The engine source files that make up the code identity, under the recorded ``experiments``
    folder (tests and other packages are not part of the identity and are not copied)."""
    root = recorded_path(root)
    local = source_map.local(root)
    identity = code_identity_of(local)
    return Unit("code", root, _files(local, sorted(identity["files"])), identity["sha256"], (),
                {"code_sha256": identity["sha256"]})


def record_unit(root: str | Path, name: str, source_map: SourceMap = SourceMap()) -> Unit:
    """One write-once record file below a root (a Stage B study record)."""
    root = recorded_path(root)
    files = _files(source_map.local(root), [name])
    return Unit("record", root, files, files[0][2])


def dependency_folders(folder: Path) -> list[str]:
    """The recorded (resolved) folders one sealed run's own receipts name."""
    receipts = read_dependencies(folder)
    if receipts is None:
        raise VerificationFailed(f"{folder} has no dependency receipts")
    return [recorded_path(receipt.get("resolved") or receipt["path"]) for receipt in receipts]
