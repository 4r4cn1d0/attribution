"""The vault: prompt off-pod copies, restore-verified acknowledgements and restore (stdlib only).

One vault serves one *namespace*: one source volume, whose recorded absolute paths are unique.
Two workers that recorded the same path (every pod used ``/workspace/...``) need two namespaces;
inside one namespace the same name must always hold the same bytes.

Layout below ``<namespace>/`` in the destination:

- ``tree/<recorded absolute path>``: the stored files, in the recorded layout;
- ``manifests/<unit>.json``: a unit's kind, root and files with sizes and hashes;
- ``acks/<unit>.json``: the acknowledgement, written last, exclusively, never replaced;
- ``pins/<kind>-<sha256>.json``: which acknowledged unit holds a pinned identity (prepared data
  by manifest hash, engine source by code hash);
- ``append/<path id>/<n>-<sha256>.snap``: snapshots of append-only files (the trajectory registry,
  the attempt catalogue), each required to extend the previous one;
- ``collisions/<unit>/<content>/``: a same-name, different-bytes arrival, preserved beside the
  stored unit; ``staging/``: uploads in flight, never evidence.

``acknowledge(unit)``:

1. an existing acknowledgement of identical content is returned (a duplicate event), after making
   sure a prepared or code unit's pin record exists (a process that died between the
   acknowledgement and the pin is completed by its retry); of different content it is a collision:
   the arrival is preserved under ``collisions/`` and the call fails;
2. the pinned identities of a unit with engine folders must already be acknowledged here;
3. capacity is checked, each missing file is uploaded to staging and its *stored* bytes are hashed
   against the unit's list; only when all match are they committed, exclusively;
4. **restore-verify**: the unit, its pinned prepared data and every reachable dependency folder are
   downloaded into a fresh tree in the recorded layout and checked there: byte hashes; for each
   engine folder ``verify_run`` (own files, dependency chain, stream) through one root path map,
   requiring ``complete`` and, for a run-one, ``stream.checked``; a prepared folder against its
   manifest; the engine source against its code identity. A dependency folder is taken only from
   a unit that is itself **acknowledged** here and seals that folder's COMPLETE.json (a run unit at
   that path, or the Stage B attempt whose ``run/`` it is): bytes that were stored but never
   acknowledged do not count, so an acknowledged unit is always restorable with its whole chain;
5. only then the acknowledgement is written. A crash before it leaves no acknowledgement (a retry
   reuses the identical stored bytes); a crash after it changes nothing (the retry is a duplicate).

Nothing is ever deleted at the source, and nothing stored is ever replaced. ``restore`` places
every acknowledged unit and the latest snapshot of every append-only file at its recorded path
(or under a mirror root), refusing to replace different bytes; receipts are never rewritten.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import time
from pathlib import Path, PurePosixPath
from typing import Sequence

from experiments.safety_selection.ledger import COMPLETE
from experiments.safety_selection.prepare import read_manifest
from experiments.safety_selection.verify import PathMap, verify_run

from .common import (CapacityError, Clock, CollisionError, DurabilityError, Journal, RestoreError, SourceMap,
                     TransferError, VerificationFailed, canonical_json, iso, locked, path_id, recorded_path,
                     sha256_bytes, sha256_file, token, utc_clock)
from .destination import Destination
from .units import FOLDER_KINDS, Unit, code_identity_of, dependency_folders, unit_id_of

__all__ = ["ACK_KIND", "Vault", "verify_in_place"]

ACK_KIND = "durability acknowledgement v1"
ACK_STATEMENT = ("written last, only after the stored bytes of every file matched the unit's hashes and the unit, "
                 "its pinned inputs and every reachable dependency were restored into a fresh tree in the recorded "
                 "layout and verified there; a copy without this record is not acknowledged")
_NAMESPACE = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,63}")


def read_json_bytes(data: bytes):
    return json.loads(data)


def _mirror(mirror: Path, recorded: str) -> Path:
    return mirror / recorded.lstrip("/")


def verify_in_place(folder: str | Path, prepared_dir: str | Path, path_map: PathMap | None = None) -> dict:
    """``verify_run`` with the acknowledgement's requirements: every performed check passes and a
    run-one's stream WAS checked (``complete`` alone does not say so). Raises otherwise."""
    try:
        report = verify_run(folder, prepared_dir, path_map)
    except Exception as exc:  # noqa: BLE001 - an unreadable or foreign folder is a failed verification
        raise VerificationFailed(f"{folder} could not be verified: {type(exc).__name__}") from exc
    if not report["complete"]:
        raise VerificationFailed(f"{folder} does not verify: {report['problems'][:3]}")
    if report["kind"] == "run-one" and report["stream"]["checked"] is not True:
        raise VerificationFailed(f"{folder}: the training stream was not checked")
    return report


class Vault:
    """See the module doc. ``scratch``: a local folder for restore checks and the lock (outside
    every sealed folder). ``reserve_bytes``: free space the destination must keep after a copy.
    ``reveal_paths``: whether logs and acknowledgements name recorded paths (False for Stage B,
    whose folder names can reveal chosen arms); the manifests always hold them, for restore.
    ``require_code``: an engine folder is acknowledged only when the source it pins is too."""

    def __init__(self, destination: Destination, namespace: str, *, journal: Journal, scratch: str | Path,
                 source_map: SourceMap | None = None, clock: Clock = utc_clock, reserve_bytes: int = 0,
                 reveal_paths: bool = True, require_code: bool = True) -> None:
        if not _NAMESPACE.fullmatch(namespace):
            raise DurabilityError(f"namespace {namespace!r} must match {_NAMESPACE.pattern}")
        self.destination, self.namespace, self.journal = destination, namespace, journal
        self.scratch, self.source_map, self.clock = Path(scratch), source_map or SourceMap(), clock
        self.reserve_bytes, self.reveal_paths, self.require_code = reserve_bytes, reveal_paths, require_code
        self._lock = self.scratch / f".vault-{namespace}.lock"

    # ----- keys ----------------------------------------------------------------------

    def _key(self, area: str, name: str) -> str:
        return f"{self.namespace}/{area}/{name}"

    def _tree(self, root: str, name: str | None = None) -> str:
        return f"{self.namespace}/tree{root}" + (f"/{name}" if name else "")

    def _log(self, event: str, unit: Unit, **fields: object) -> None:
        label = {"path": unit.root} if self.reveal_paths else {}
        self.journal.append(event, namespace=self.namespace, unit=unit.unit_id, unit_kind=unit.kind,
                            path_sha256=path_id(unit.root), **label, **fields)

    # ----- acknowledgements ----------------------------------------------------------

    def read_ack(self, unit_id: str) -> dict | None:
        """The stored acknowledgement of a unit id, or None. A malformed one fails closed."""
        key = self._key("acks", f"{unit_id}.json")
        if not self.destination.exists(key):
            return None
        try:
            ack = read_json_bytes(self.destination.read(key))
        except ValueError:
            raise VerificationFailed(f"the acknowledgement of {unit_id} is unreadable") from None
        if not isinstance(ack, dict) or ack.get("kind") != ACK_KIND or ack.get("unit") != unit_id \
                or not isinstance(ack.get("content_sha256"), str) or ack.get("namespace") != self.namespace:
            raise VerificationFailed(f"the acknowledgement of {unit_id} is malformed")
        return ack

    def check_ack(self, kind: str, root: str, seal_sha256: str, name: str | None = None) -> dict:
        """The acknowledgement of the unit ``kind`` at ``root`` (a record: its file ``name``),
        required to exist in the destination and to seal the same bytes as the local unit (its
        COMPLETE.json, receipt.json, manifest or error.txt hash; a record's own hash). Raises
        ``VerificationFailed`` otherwise."""
        unit_id = unit_id_of(kind, recorded_path(root), name)
        ack = self.read_ack(unit_id)
        if ack is None:
            raise VerificationFailed(f"no acknowledgement of the {kind} unit {unit_id}")
        if ack.get("seal_sha256") != seal_sha256:
            raise VerificationFailed(f"the acknowledgement of the {kind} unit {unit_id} seals other bytes")
        return ack

    def acknowledge(self, unit: Unit) -> dict:
        """Copy, verify, restore-verify and acknowledge ``unit`` (module doc). Idempotent."""
        started = time.monotonic()
        with locked(self._lock):
            try:
                return self._acknowledge(unit, started)
            except DurabilityError as exc:
                self._log("unit-refused", unit, status=type(exc).__name__, files=len(unit.files), bytes=unit.bytes,
                          seconds=time.monotonic() - started)
                raise

    def _acknowledge(self, unit: Unit, started: float) -> dict:
        dest = self.destination
        ack = self.read_ack(unit.unit_id)
        if ack is not None:
            if ack["content_sha256"] != unit.content_sha256:
                self._collision(unit, "an acknowledgement of this name seals different bytes")
            self._put_pin(unit)   # a process that died between the acknowledgement and the pin is completed here
            self._log("unit-duplicate", unit, status="acknowledged", content_sha256=unit.content_sha256)
            return ack
        self._require_pins(unit)
        missing = []
        for name, size, digest in unit.files:
            key = self._tree(unit.root, name)
            if not dest.exists(key):
                missing.append((name, size, digest))
            elif dest.sha256(key)[0] != digest:
                self._collision(unit, f"a stored file of this name holds different bytes ({path_id(name)[:12]})")
        if unit.kind in FOLDER_KINDS:
            expected = {self._tree(unit.root, name) for name, _, _ in unit.files}
            if set(dest.list(self._tree(unit.root))) - expected:
                self._collision(unit, "the destination holds other files under this unit's name")
        need = sum(size for _, size, _ in missing)
        if dest.free_bytes() < need + self.reserve_bytes:
            raise CapacityError(f"the destination has too little free space for {need} bytes plus the "
                                f"{self.reserve_bytes}-byte reserve")
        stage = self._key("staging", f"{unit.unit_id}-{token()}")
        local = self.source_map.local(unit.root)
        copy_started = time.monotonic()
        for name, size, digest in missing:
            dest.upload(local / name, f"{stage}/{name}")
            if dest.sha256(f"{stage}/{name}") != (digest, size):
                raise TransferError(f"a file of unit {unit.unit_id} arrived partial or corrupt, or changed at the "
                                    "source during the copy; nothing was published")
        manifest = canonical_json(unit.manifest())
        try:
            dest.put_new(self._key("manifests", f"{unit.unit_id}.json"), manifest)
        except CollisionError:
            self._collision(unit, "a stored manifest of this name lists different bytes")
        for name, _, _ in missing:
            dest.commit(f"{stage}/{name}", self._tree(unit.root, name))
        copy_seconds = time.monotonic() - copy_started
        verify_started = time.monotonic()
        verification = self._restore_verify(unit)
        verify_seconds = time.monotonic() - verify_started
        ack = {"kind": ACK_KIND, "unit": unit.unit_id, "unit_kind": unit.kind, "namespace": self.namespace,
               "path_sha256": path_id(unit.root), **({"path": unit.root} if self.reveal_paths else {}),
               "content_sha256": unit.content_sha256, "seal_sha256": unit.seal_sha256, "files": len(unit.files),
               "bytes": unit.bytes, "pins": dict(unit.pins), "unit_manifest_sha256": sha256_bytes(manifest),
               "verification": verification, "destination": dest.describe(),
               "acknowledged_utc": iso(self.clock()), "statement": ACK_STATEMENT}
        try:
            dest.put_new(self._key("acks", f"{unit.unit_id}.json"), canonical_json(ack))
        except CollisionError:   # another writer acknowledged this name meanwhile
            ack = self.read_ack(unit.unit_id)
            if ack is None or ack["content_sha256"] != unit.content_sha256:
                self._collision(unit, "a concurrent acknowledgement of this name seals different bytes")
        self._put_pin(unit)
        self._log("unit-acknowledged", unit, status="acknowledged", files=len(unit.files), bytes=unit.bytes,
                  copied_files=len(missing), copied_bytes=need, content_sha256=unit.content_sha256,
                  seal_sha256=unit.seal_sha256, copy_seconds=copy_seconds, verify_seconds=verify_seconds,
                  folders=verification["folders"], run_one_stream_checked=verification["run_one_stream_checked"],
                  seconds=time.monotonic() - started)
        return ack

    def _collision(self, unit: Unit, why: str) -> None:
        """Preserve a same-name, different-bytes arrival beside the stored unit and fail. Neither
        copy is replaced; the source is untouched."""
        dest = self.destination
        base = self._key("collisions", f"{unit.unit_id}/{unit.content_sha256}")
        preserved = dest.exists(f"{base}/record.json")
        if not preserved:
            try:
                stage = self._key("staging", f"collision-{unit.unit_id}-{token()}")
                local = self.source_map.local(unit.root)
                for name, size, digest in unit.files:
                    dest.upload(local / name, f"{stage}/{name}")
                    if dest.sha256(f"{stage}/{name}") != (digest, size):
                        raise TransferError("the colliding copy did not arrive intact")
                    dest.commit(f"{stage}/{name}", f"{base}/files/{name}")
                dest.put_new(f"{base}/record.json", canonical_json({
                    "unit": unit.unit_id, "unit_kind": unit.kind, "content_sha256": unit.content_sha256,
                    "manifest": unit.manifest(), "recorded_utc": iso(self.clock())}))
                preserved = True
            except DurabilityError:
                preserved = False   # the source still holds it; the collision is reported either way
        self._log("collision", unit, status="preserved" if preserved else "not-preserved",
                  content_sha256=unit.content_sha256)
        raise CollisionError(f"unit {unit.unit_id} ({unit.kind}): {why}; both are kept and nothing was replaced")

    # ----- pinned identities ---------------------------------------------------------

    def _pin_key(self, kind: str, digest: str) -> str:
        return self._key("pins", f"{kind}-{digest}.json")

    def _put_pin(self, unit: Unit) -> None:
        """Record which acknowledged unit holds a pinned identity (prepared data, engine source).
        Idempotent: called after the acknowledgement and again on every duplicate, so a crash
        between the two writes cannot leave an acknowledged identity unpinned."""
        if unit.kind not in ("prepared", "code"):
            return
        key = self._pin_key(unit.kind, unit.seal_sha256)
        if not self.destination.exists(key):   # the first acknowledged holder of an identity is kept
            self.destination.put_new(key, canonical_json({"kind": unit.kind, "sha256": unit.seal_sha256,
                                                          "unit": unit.unit_id, "root": unit.root}))

    def pin(self, kind: str, digest: str | None) -> Unit | None:
        """The acknowledged unit that holds a pinned identity, or None."""
        if not digest or not self.destination.exists(self._pin_key(kind, digest)):
            return None
        record = read_json_bytes(self.destination.read(self._pin_key(kind, digest)))
        if self.read_ack(record["unit"]) is None:
            return None
        return self._stored_unit(record["unit"])

    def _stored_unit(self, unit_id: str) -> Unit:
        try:
            return Unit.from_manifest(read_json_bytes(self.destination.read(self._key("manifests", f"{unit_id}.json"))))
        except (ValueError, KeyError, TypeError) as exc:
            raise VerificationFailed(f"the stored manifest of {unit_id} is unreadable") from exc

    def _require_pins(self, unit: Unit) -> None:
        if not unit.engine_runs:
            return
        if self.pin("prepared", unit.pins.get("manifest_sha256")) is None:
            raise VerificationFailed("the prepared data this unit pins are not acknowledged in this vault; "
                                     "acknowledge the prepared folder first")
        if self.require_code and self.pin("code", unit.pins.get("code_sha256")) is None:
            raise VerificationFailed("the engine source this unit pins is not acknowledged in this vault; "
                                     "acknowledge the code unit first")

    # ----- restore-verify ------------------------------------------------------------

    def _fetch(self, unit: Unit, mirror: Path) -> Path:
        """Download a stored unit into ``mirror`` at its recorded path; every file's bytes must hash
        to the unit's list."""
        target = _mirror(mirror, unit.root)
        for name, _, digest in unit.files:
            self.destination.download(self._tree(unit.root, name), target / name)
            if sha256_file(target / name) != digest:
                raise TransferError(f"a stored file of unit {unit.unit_id} no longer matches its hash")
        return target

    def _holder(self, folder: str) -> tuple[Unit, str] | None:
        """The ACKNOWLEDGED unit that holds a sealed engine folder, with the name of the folder's
        COMPLETE.json inside it: a run unit at that path, or the attempt unit whose ``run/`` it is.
        None when no acknowledged unit holds it (stored bytes without an acknowledgement do not
        count)."""
        candidates = [("run", folder, COMPLETE)]
        if PurePosixPath(folder).name == "run":
            candidates.append(("attempt", str(PurePosixPath(folder).parent), f"run/{COMPLETE}"))
        for kind, root, marker in candidates:
            if self.read_ack(unit_id_of(kind, root)) is not None:
                unit = self._stored_unit(unit_id_of(kind, root))
                if any(name == marker for name, _, _ in unit.files):
                    return unit, marker
        return None

    def _fetch_dependency(self, folder: str, mirror: Path) -> None:
        """Download a dependency folder from the acknowledged unit that holds it."""
        held = self._holder(folder)
        if held is None:
            raise VerificationFailed("a dependency this unit's receipts name is not acknowledged in the vault "
                                     "(stored bytes without an acknowledgement do not count)")
        self._fetch(held[0], mirror)

    def _restore_verify(self, unit: Unit) -> dict:
        self.scratch.mkdir(parents=True, exist_ok=True)
        mirror = self.scratch / f"restore-check-{token()}"
        report = {"bytes": True, "folders": 0, "run_one_stream_checked": 0,
                  "mode": "restored into a fresh tree in the recorded layout, verified through one root path map"}
        try:
            local = self._fetch(unit, mirror)
            if unit.kind == "prepared":
                manifest, digest = read_manifest(local, unit.seal_sha256)
                if any(sha256_file(local / name) != sha for name, sha in manifest["files"].items()):
                    raise VerificationFailed("restored prepared files differ from their manifest")
            elif unit.kind == "code":
                if code_identity_of(local)["sha256"] != unit.seal_sha256:
                    raise VerificationFailed("the restored engine source does not reproduce its code identity")
            if unit.engine_runs:
                prepared = self._fetch(self.pin("prepared", unit.pins["manifest_sha256"]), mirror)
                if self.require_code:
                    code = self.pin("code", unit.pins["code_sha256"])
                    if code_identity_of(self._fetch(code, mirror))["sha256"] != unit.pins["code_sha256"]:
                        raise VerificationFailed("the stored engine source does not reproduce the pinned identity")
                folders, queue = [], list(unit.engine_runs)
                while queue:
                    folder = queue.pop(0)
                    if folder in folders:
                        continue
                    if folder not in unit.engine_runs:
                        self._fetch_dependency(folder, mirror)
                    folders.append(folder)
                    queue.extend(dependency_folders(_mirror(mirror, folder)))
                root_map = PathMap([("/", mirror)])
                for folder in folders:
                    result = verify_in_place(_mirror(mirror, folder), prepared, root_map)
                    report["folders"] += 1
                    report["run_one_stream_checked"] += result["kind"] == "run-one"
            return report
        except DurabilityError:
            raise
        except Exception as exc:  # noqa: BLE001 - any failure of the restore check is a failed verification
            raise VerificationFailed(f"the restore check failed: {type(exc).__name__}") from exc
        finally:
            shutil.rmtree(mirror, ignore_errors=True)

    # ----- append-only files ---------------------------------------------------------

    def snapshot_append(self, recorded: str | Path) -> dict:
        """Store the current bytes of an append-only file (a trajectory registry, the attempt
        catalogue) as its next snapshot. The file must extend its previous snapshot: removed or
        rewritten lines (a cleared registry claim) refuse. An unchanged file stores nothing."""
        recorded = recorded_path(recorded)
        data = self.source_map.local(recorded).read_bytes()
        base = self._key("append", path_id(recorded))
        with locked(self._lock):
            snapshots = [k for k in self.destination.list(base) if k.endswith(".snap")]
            if snapshots:
                last = self.destination.read(snapshots[-1])
                if data == last:
                    return {"status": "unchanged", "sequence": len(snapshots), "sha256": sha256_bytes(data)}
                if not data.startswith(last):
                    raise VerificationFailed(f"{recorded} no longer extends its last snapshot: an append-only file "
                                             "was rewritten or truncated (a registry claim is never cleared)")
            else:
                self.destination.put_new(f"{base}/path.json", canonical_json({"path": recorded}))
            digest = sha256_bytes(data)
            self.destination.put_new(f"{base}/{len(snapshots) + 1:08d}-{digest}.snap", data)
        self.journal.append("append-snapshot", namespace=self.namespace, path_sha256=path_id(recorded),
                            **({"path": recorded} if self.reveal_paths else {}), sequence=len(snapshots) + 1,
                            snapshot_sha256=digest, bytes=len(data))
        return {"status": "stored", "sequence": len(snapshots) + 1, "sha256": digest}

    # ----- restore -------------------------------------------------------------------

    def acknowledged_units(self) -> list[Unit]:
        prefix = self._key("acks", "")
        units = []
        for key in self.destination.list(self._key("acks", "").rstrip("/")):
            unit_id = key[len(prefix):-len(".json")]
            if self.read_ack(unit_id) is not None:
                units.append(self._stored_unit(unit_id))
        return units

    def _place(self, key: str, digest: str | None, target: Path) -> bool:
        """Put one stored object at ``target`` (True) unless the identical bytes are already there
        (False); different bytes there refuse. Never replaces a file."""
        if digest is None:
            digest = self.destination.sha256(key)[0]
        if target.exists():
            if sha256_file(target) != digest:
                raise RestoreError(f"{target} exists with different bytes; a restore never replaces a file")
            return False
        tmp = target.with_name(f".{target.name}.{token()}.tmp")
        self.destination.download(key, tmp)
        try:
            if sha256_file(tmp) != digest:
                raise RestoreError(f"the stored copy of {target.name} no longer matches its hash")
            os.link(tmp, target)
        finally:
            tmp.unlink()
        return True

    def restore(self, *, mirror: str | Path | None = None, kinds: Sequence[str] | None = None) -> dict:
        """Place every acknowledged unit (optionally of the given kinds) and the latest snapshot of
        every append-only file at its recorded path (through the source map), or under ``mirror``
        in the recorded layout. Identical existing files are kept; a different existing file
        refuses. An append-only file already on disk must be a prefix of the snapshot (it is then
        extended) or extend it (it is kept). Unacknowledged stored bytes are never restored."""
        started = time.monotonic()
        where = (lambda path: _mirror(Path(mirror), path)) if mirror is not None else self.source_map.local
        restored = reused = size = 0
        units = [u for u in self.acknowledged_units() if kinds is None or u.kind in kinds]
        for unit in units:
            for name, nbytes, digest in unit.files:
                placed = self._place(self._tree(unit.root, name), digest, where(unit.root) / name)
                restored, reused, size = restored + placed, reused + (not placed), size + nbytes * placed
        appended = 0
        base = self._key("append", "")
        for key in self.destination.list(base.rstrip("/")):
            if not key.endswith("/path.json"):
                continue
            recorded = recorded_path(read_json_bytes(self.destination.read(key))["path"])
            snapshots = [k for k in self.destination.list(key[:-len("/path.json")]) if k.endswith(".snap")]
            data, target = self.destination.read(snapshots[-1]), where(recorded)
            if target.exists():
                have = target.read_bytes()
                if have.startswith(data):
                    continue   # the file on disk is the snapshot or extends it
                if not data.startswith(have):
                    raise RestoreError(f"{target} is neither a prefix nor an extension of its stored snapshot")
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            appended += 1
        self.journal.append("restore", namespace=self.namespace, units=len(units), restored_files=restored,
                            reused_files=reused, bytes=size, records=appended, seconds=time.monotonic() - started,
                            status="mirror" if mirror is not None else "recorded-layout")
        return {"units": len(units), "restored_files": restored, "reused_files": reused, "bytes": size,
                "append_files": appended}
