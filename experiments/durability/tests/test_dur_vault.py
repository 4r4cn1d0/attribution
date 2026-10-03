"""The vault on real sealed engine units (ENGINEERING FIXTURES: tiny random model on CPU): an
acknowledgement only after the stored bytes match and the unit, its pinned inputs and its
dependency chain verify in a fresh tree with the stream checked; idempotent duplicates; partial and
corrupt transfers; a missing dependency or pin; a crash before and after the acknowledgement; a
full destination; a same-name, different-hash collision with both kept; path ambiguity; append-only
snapshots that refuse a rewritten registry; restores that never replace a file; a remote
destination that is not configured; outcome-blind logs. Nothing here is a scientific result."""

from __future__ import annotations

import errno
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import dur_fixtures as dur  # noqa: E402
import ss_fixtures as fx  # noqa: E402

from experiments.durability import destination as destination_module  # noqa: E402
from experiments.durability.backup import ACK_KIND, verify_in_place  # noqa: E402
from experiments.durability.common import (BlindnessError, CapacityError, CollisionError, Journal,  # noqa: E402
                                           NotConfigured, PathAmbiguity, RestoreError, SourceMap, TransferError,
                                           VerificationFailed, read_json, recorded_path, sha256_file)
from experiments.durability.destination import LocalDirectoryDestination, UnconfiguredDestination  # noqa: E402
from experiments.durability.units import code_unit, prepared_unit, run_unit  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.common import PACKAGE_DIR, append_jsonl  # noqa: E402

CODE = str(PACKAGE_DIR.parent)


@pytest.fixture(scope="module")
def pod(tmp_path_factory):
    """A worker's durable volume with prepared data and a sealed chain q -> e1 (a0, seed 1101)."""
    root = tmp_path_factory.mktemp("pod").resolve() / "workspace"
    prepared, sha = fx.prepare_dir(root / "prepared")
    recipe = fx.recipe()
    session = runner.Session(recipe, fx.fixture_loaders())
    runs = root / "calibration-001"
    q = runner.run_one(dur.run_job(sha, recipe), prepared_dir=prepared, out_dir=runs / "1101-a0-q-a1",
                       session=session)
    e1 = runner.run_one(dur.run_job(sha, recipe, target_checkpoint="e1", resume_from=q["run_dir"]),
                        prepared_dir=prepared, out_dir=runs / "1101-a0-e1-a1", session=session)
    return SimpleNamespace(root=root, prepared=prepared, sha=sha, recipe=recipe, session=session, runs=runs,
                           q=Path(q["run_dir"]), e1=Path(e1["run_dir"]), before=dur.tree_hashes(root))


def pinned(vault, pod):
    """Acknowledge the pinned inputs: the prepared data and the engine source."""
    vault.acknowledge(prepared_unit(str(pod.prepared)))
    vault.acknowledge(code_unit(CODE))
    return vault


def stored(vault, area: str) -> list[str]:
    return vault.destination.list(f"{vault.namespace}/{area}")


def test_an_acknowledgement_follows_a_restore_verified_copy_and_duplicates_are_idempotent(pod, tmp_path):
    vault = pinned(dur.make_vault(tmp_path), pod)
    q, e1 = run_unit(str(pod.q)), run_unit(str(pod.e1))
    first = vault.acknowledge(q)
    assert first["kind"] == ACK_KIND and first["seal_sha256"] == sha256_file(pod.q / "COMPLETE.json")
    assert first["verification"] == {"bytes": True, "folders": 1, "run_one_stream_checked": 1,
                                     "mode": first["verification"]["mode"]}
    chained = vault.acknowledge(e1)                 # its dependency q is fetched from the vault and verified too
    assert chained["verification"]["folders"] == 2 and chained["verification"]["run_one_stream_checked"] == 2
    assert chained["pins"] == {"manifest_sha256": pod.sha, "recipe_sha256": q.pins["recipe_sha256"],
                               "code_sha256": q.pins["code_sha256"]}
    # the stored tree is the recorded layout, byte for byte; the source is untouched; no scratch is left
    tree = tmp_path / "destination" / "worker-1" / "tree"
    assert dur.tree_hashes(tree / str(pod.e1).lstrip("/")) == dur.tree_hashes(pod.e1)
    assert dur.tree_hashes(pod.root) == pod.before
    assert not list((tmp_path / "admin" / "scratch").glob("restore-check-*"))
    assert not stored(vault, "staging")
    # a duplicate event returns the same immutable acknowledgement and copies nothing
    ack_file = tmp_path / "destination" / "worker-1" / "acks" / f"{e1.unit_id}.json"
    before = ack_file.read_bytes()
    assert vault.acknowledge(run_unit(str(pod.e1))) == chained and ack_file.read_bytes() == before
    events = [row["event"] for row in vault.journal.read()]
    assert events.count("unit-acknowledged") == 4 and events[-1] == "unit-duplicate"
    assert vault.check_ack("run", str(pod.e1), sha256_file(pod.e1 / "COMPLETE.json")) == chained
    with pytest.raises(VerificationFailed):          # the acknowledgement seals these bytes, no others
        vault.check_ack("run", str(pod.e1), "0" * 64)


@pytest.mark.parametrize("fault", ["truncate", "corrupt"])
def test_a_partial_or_corrupt_transfer_is_never_published_or_acknowledged(pod, tmp_path, fault):
    healthy = pinned(dur.make_vault(tmp_path), pod)
    broken = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", **{fault: 3}))
    unit = run_unit(str(pod.q))
    with pytest.raises(TransferError):
        broken.acknowledge(unit)
    assert broken.read_ack(unit.unit_id) is None
    assert not stored(broken, f"tree{pod.q}")                                       # nothing was published
    assert f"worker-1/manifests/{unit.unit_id}.json" not in stored(broken, "manifests")
    assert broken.journal.read()[-1]["event"] == "unit-refused" and broken.journal.read()[-1]["status"] == "TransferError"
    with pytest.raises(VerificationFailed):
        broken.check_ack("run", str(pod.q), unit.seal_sha256)
    assert healthy.acknowledge(unit)["content_sha256"] == unit.content_sha256      # the retry starts over, intact
    assert dur.tree_hashes(pod.root) == pod.before


def test_a_file_that_changes_during_the_copy_fails_the_copy(pod, tmp_path):
    """The unit lists hashes when it is described; bytes that differ on arrival (here the source
    changed afterwards) are a failed transfer, never a silently different unit."""
    source = Path(shutil.copytree(pod.root, tmp_path / "volume"))
    vault = dur.make_vault(tmp_path, source_map=SourceMap([(str(pod.root), source)]))
    pinned(vault, pod)
    unit = run_unit(str(pod.q), vault.source_map)
    (source / "calibration-001" / "1101-a0-q-a1" / "status.json").write_text("{}")   # rewritten after the listing
    with pytest.raises(TransferError):
        vault.acknowledge(unit)
    assert vault.read_ack(unit.unit_id) is None


def test_a_missing_dependency_or_pinned_input_refuses_the_acknowledgement(pod, tmp_path):
    bare = dur.make_vault(tmp_path / "bare")
    with pytest.raises(VerificationFailed, match="prepared data"):
        bare.acknowledge(run_unit(str(pod.q)))
    bare.acknowledge(prepared_unit(str(pod.prepared)))
    with pytest.raises(VerificationFailed, match="engine source"):
        bare.acknowledge(run_unit(str(pod.q)))
    vault = pinned(dur.make_vault(tmp_path / "vault"), pod)
    e1 = run_unit(str(pod.e1))
    with pytest.raises(VerificationFailed, match="dependency"):     # q is not in the vault: the chain cannot verify
        vault.acknowledge(e1)
    assert vault.read_ack(e1.unit_id) is None
    vault.acknowledge(run_unit(str(pod.q)))
    assert vault.acknowledge(e1)["verification"]["folders"] == 2
    # an unsealed folder (saved states, no COMPLETE.json) is not a unit at all
    unsealed = Path(shutil.copytree(pod.q, tmp_path / "unsealed"))
    (unsealed / "COMPLETE.json").unlink()
    with pytest.raises(VerificationFailed, match="not a sealed run"):
        run_unit(str(unsealed))


def test_a_dependency_corrupted_in_the_destination_fails_the_restore_check(pod, tmp_path):
    vault = pinned(dur.make_vault(tmp_path), pod)
    vault.acknowledge(run_unit(str(pod.q)))
    victim = tmp_path / "destination" / "worker-1" / "tree" / str(pod.q).lstrip("/") / "steps.jsonl"
    victim.write_bytes(victim.read_bytes() + b"{}\n")
    with pytest.raises(TransferError, match="no longer matches its hash"):   # the acknowledged dependency's bytes
        vault.acknowledge(run_unit(str(pod.e1)))
    assert vault.read_ack(run_unit(str(pod.e1)).unit_id) is None


def test_a_crash_before_the_acknowledgement_leaves_none_and_a_crash_after_changes_nothing(pod, tmp_path):
    vault = pinned(dur.make_vault(tmp_path), pod)
    unit = run_unit(str(pod.q))
    dying = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", crash_on="acks"))
    with pytest.raises(KeyboardInterrupt):          # every byte arrived and verified; the process died at the last write
        dying.acknowledge(unit)
    assert stored(vault, f"tree{pod.q}") and vault.read_ack(unit.unit_id) is None
    with pytest.raises(VerificationFailed):          # a complete copy without the record is not an acknowledgement
        vault.check_ack("run", str(pod.q), unit.seal_sha256)
    ack = vault.acknowledge(unit)                    # the retry reuses the identical stored bytes
    copied = [row for row in vault.journal.read() if row["event"] == "unit-acknowledged"][-1]
    assert copied["copied_files"] == 0 and copied["files"] == len(unit.files)
    # a crash right after the acknowledgement: the retry is a duplicate, the record is unchanged
    ack_file = tmp_path / "destination" / "worker-1" / "acks" / f"{unit.unit_id}.json"
    before = ack_file.read_bytes()
    assert vault.acknowledge(unit) == ack and ack_file.read_bytes() == before
    # a crash between two files of the publish step: the stored half is completed, never trusted as it is
    half = pinned(dur.make_vault(tmp_path / "half"), pod)
    tree = tmp_path / "half" / "destination" / "worker-1" / "tree" / str(pod.q).lstrip("/")
    tree.mkdir(parents=True)
    shutil.copyfile(pod.q / "job.json", tree / "job.json")
    assert half.acknowledge(unit)["files"] == len(unit.files)


def test_a_crash_between_an_acknowledgement_and_its_pin_is_completed_by_the_retry(pod, tmp_path):
    """Review finding A. The pin record of a prepared or code unit is written after its
    acknowledgement. A process that dies between the two must not leave the identity unpinned for
    good (every engine unit of the vault would then be refused): the retry, a duplicate event,
    writes the pin."""
    for make, kind, digest in ((lambda: prepared_unit(str(pod.prepared)), "prepared", pod.sha),
                               (lambda: code_unit(CODE), "code", runner.code_identity()["sha256"])):
        dying = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", crash_on="pins"))
        with pytest.raises(KeyboardInterrupt):        # the process dies at the pin write, after the acknowledgement
            dying.acknowledge(make())
        vault = dur.make_vault(tmp_path)
        assert vault.read_ack(make().unit_id) is not None and vault.pin(kind, digest) is None
        ack = vault.acknowledge(make())                 # the retry: a duplicate event
        assert vault.pin(kind, digest).unit_id == ack["unit"]
        assert vault.acknowledge(make()) == ack and vault.journal.read()[-1]["event"] == "unit-duplicate"
    assert vault.acknowledge(run_unit(str(pod.q)))["verification"]["folders"] == 1   # engine units are not blocked


def test_a_dependency_stored_without_its_acknowledgement_does_not_count(pod, tmp_path):
    """Review finding E. "Acknowledged" must imply "restorable": a dependency whose bytes reached
    the destination but whose acknowledgement was never written is not restored by ``restore``, so
    a unit that depends on it is not acknowledged either."""
    vault = pinned(dur.make_vault(tmp_path), pod)
    q, e1 = run_unit(str(pod.q)), run_unit(str(pod.e1))
    dying = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", crash_on="acks"))
    with pytest.raises(KeyboardInterrupt):
        dying.acknowledge(q)                            # q is stored in full, verified, but not acknowledged
    assert stored(vault, f"tree{pod.q}") and vault.read_ack(q.unit_id) is None
    with pytest.raises(VerificationFailed, match="not acknowledged in the vault"):
        vault.acknowledge(e1)
    assert vault.read_ack(e1.unit_id) is None
    mirror = tmp_path / "mirror"
    assert vault.restore(mirror=mirror, kinds=("run",))["units"] == 0      # nothing unacknowledged is restored
    vault.acknowledge(q)
    assert vault.acknowledge(e1)["verification"]["folders"] == 2
    assert vault.restore(mirror=mirror, kinds=("run",))["units"] == 2


def test_a_full_destination_refuses_before_or_during_the_copy(pod, tmp_path, monkeypatch):
    unit = run_unit(str(pod.q))
    pinned(dur.make_vault(tmp_path), pod)
    small = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", free=unit.bytes - 1))
    with pytest.raises(CapacityError):
        small.acknowledge(unit)
    assert small.destination.uploads == 0 and small.read_ack(unit.unit_id) is None
    reserve = dur.make_vault(tmp_path, destination=dur.FaultyDestination(tmp_path / "destination", free=unit.bytes),
                             reserve_bytes=1)
    with pytest.raises(CapacityError):
        reserve.acknowledge(unit)

    def full(reader, writer, length=0):
        raise OSError(errno.ENOSPC, "No space left on device")

    vault = dur.make_vault(tmp_path)
    monkeypatch.setattr(destination_module.shutil, "copyfileobj", full)
    with pytest.raises(CapacityError):               # the disk filled during the copy
        vault.acknowledge(unit)
    monkeypatch.undo()
    assert vault.read_ack(unit.unit_id) is None and not stored(vault, f"tree{pod.q}")
    assert vault.acknowledge(unit)["bytes"] == unit.bytes


def test_a_same_name_different_hash_arrival_fails_and_both_are_kept(pod, tmp_path):
    vault = pinned(dur.make_vault(tmp_path), pod)
    original = run_unit(str(pod.q))
    ack = vault.acknowledge(original)
    stored_before = dur.tree_hashes(tmp_path / "destination" / "worker-1" / "tree")
    # another sealed run claims the same recorded path (here: e1's bytes behind q's recorded name)
    impostor_map = SourceMap([(str(pod.q), pod.e1)])
    impostor = run_unit(str(pod.q), impostor_map)
    assert impostor.unit_id == original.unit_id and impostor.content_sha256 != original.content_sha256
    clash = dur.make_vault(tmp_path, source_map=impostor_map)
    with pytest.raises(CollisionError):
        clash.acknowledge(impostor)
    assert dur.tree_hashes(tmp_path / "destination" / "worker-1" / "tree") == stored_before   # nothing replaced
    assert vault.read_ack(original.unit_id) == ack
    kept = tmp_path / "destination" / "worker-1" / "collisions" / original.unit_id / impostor.content_sha256
    assert dur.tree_hashes(kept / "files") == dur.tree_hashes(pod.e1)                          # the arrival is kept
    assert read_json(kept / "record.json")["content_sha256"] == impostor.content_sha256
    assert [row["status"] for row in clash.journal.read() if row["event"] == "collision"] == ["preserved"]
    with pytest.raises(CollisionError):               # again: still a collision, recorded once
        clash.acknowledge(impostor)
    # the same recorded path on another worker is another namespace: no collision, nothing shared
    other = dur.make_vault(tmp_path, namespace="worker-2", source_map=impostor_map)
    pinned(other, pod)
    with pytest.raises(VerificationFailed):           # (its own chain is not in that vault yet)
        other.acknowledge(impostor)
    assert vault.read_ack(original.unit_id) == ack


def test_ambiguous_paths_are_refused(pod, tmp_path):
    for bad in ("relative/run", "/workspace/../etc", "/workspace/run/", "/workspace//run", "run"):
        with pytest.raises(PathAmbiguity):
            recorded_path(bad)
    nested = SourceMap([("/workspace", tmp_path / "a"), ("/workspace/calibration-001", tmp_path / "b")])
    assert nested.local("/workspace/prepared/manifest.json") == tmp_path / "a" / "prepared" / "manifest.json"
    with pytest.raises(PathAmbiguity):                # two prefixes claim it: never "the first match"
        nested.local("/workspace/calibration-001/1101-a0-q-a1")
    with pytest.raises(PathAmbiguity):                # two recorded locations cannot share one local folder
        SourceMap([("/workspace", tmp_path / "a"), ("/other", tmp_path / "a")])
    with pytest.raises(PathAmbiguity):
        SourceMap([("workspace", tmp_path / "a")])
    assert SourceMap().local(str(pod.q)) == pod.q
    # a unit is plain files: a symlink inside a folder is refused, not followed
    linked = Path(shutil.copytree(pod.q, tmp_path / "linked"))
    (linked / "alias.json").symlink_to(linked / "job.json")
    from experiments.durability.units import failed_run_unit

    (linked / "COMPLETE.json").unlink()
    (linked / "error.txt").write_text("ENGINEERING FIXTURE failure")
    with pytest.raises(TransferError, match="symlink"):
        failed_run_unit(str(linked))


def test_append_only_snapshots_refuse_a_rewritten_registry_and_restore_the_latest(pod, tmp_path):
    vault = dur.make_vault(tmp_path)
    registry = tmp_path / "volume" / "registry.jsonl"
    append_jsonl(registry, {"key": {"seed": 1101}, "run_dir": "/workspace/a1"})
    assert vault.snapshot_append(str(registry))["status"] == "stored"
    assert vault.snapshot_append(str(registry))["status"] == "unchanged"
    append_jsonl(registry, {"key": {"seed": 1102}, "run_dir": "/workspace/a2"})
    assert vault.snapshot_append(str(registry))["sequence"] == 2
    kept = registry.read_bytes()
    registry.write_bytes(kept.split(b"\n", 1)[1])                    # the first claim was cleared
    with pytest.raises(VerificationFailed, match="append-only"):
        vault.snapshot_append(str(registry))
    registry.unlink()
    assert vault.restore()["append_files"] == 1 and registry.read_bytes() == kept
    registry.write_bytes(b'{"another": "history"}\n')                # neither a prefix nor an extension
    with pytest.raises(RestoreError):
        vault.restore()


def test_a_restore_rebuilds_the_recorded_layout_and_never_replaces_a_file(pod, tmp_path):
    vault = pinned(dur.make_vault(tmp_path), pod)
    for folder in (pod.q, pod.e1):
        vault.acknowledge(run_unit(str(folder)))
    mirror = tmp_path / "mirror"
    report = vault.restore(mirror=mirror, kinds=("run", "prepared"))
    assert report["units"] == 3 and report["reused_files"] == 0
    restored = mirror / str(pod.root).lstrip("/")
    assert dur.tree_hashes(restored / "calibration-001") == dur.tree_hashes(pod.runs)
    assert dur.tree_hashes(restored / "prepared") == dur.tree_hashes(pod.prepared)
    # in place (the files are still there): everything is reused, nothing rewritten
    again = vault.restore(kinds=("run", "prepared"))
    assert again["restored_files"] == 0 and again["reused_files"] == report["restored_files"]
    assert dur.tree_hashes(pod.root) == pod.before
    (restored / "calibration-001" / "1101-a0-q-a1" / "job.json").write_text("{}")
    with pytest.raises(RestoreError, match="never replaces"):
        vault.restore(mirror=mirror, kinds=("run",))
    assert verify_in_place(pod.e1, pod.prepared)["stream"]["checked"] is True   # the recorded layout needs no map
    # complete=true alone is not enough: without the prepared data the stream is not checked, so no acknowledgement
    from experiments.safety_selection.verify import verify_run

    unchecked = verify_run(pod.e1)
    assert unchecked["complete"] is True and unchecked["stream"]["checked"] is False
    with pytest.raises(VerificationFailed, match="stream was not checked"):
        verify_in_place(pod.e1, None)


def test_a_destination_that_is_not_configured_fails_closed(pod, tmp_path):
    vault = dur.make_vault(tmp_path, destination=UnconfiguredDestination("object-store"))
    with pytest.raises(NotConfigured):
        vault.acknowledge(prepared_unit(str(pod.prepared)))
    with pytest.raises(NotConfigured):
        vault.check_ack("run", str(pod.q), "0" * 64)
    assert UnconfiguredDestination().describe()["location"] is None
    assert LocalDirectoryDestination(tmp_path / "d").describe() == {"kind": "local-directory",
                                                                   "location": str(tmp_path / "d")}


def test_logs_and_acknowledgements_are_outcome_blind(pod, tmp_path):
    journal = Journal(tmp_path / "journal.jsonl")
    for field in ({"summary": {"guard_unsafe": 3}}, {"choice": "g-1"}, {"text": "a completion"}, {"metrics": [0.5]},
                  {"reason": "x" * 401}, {"seconds": float("nan")}, {"problems": [{"prompt": "p"}]}):
        with pytest.raises(BlindnessError):
            journal.append("event", **field)
    assert not (tmp_path / "journal.jsonl").exists()
    vault = pinned(dur.make_vault(tmp_path), pod)
    vault.acknowledge(run_unit(str(pod.q)))
    logged = (tmp_path / "admin" / "journal.jsonl").read_text() + "".join(
        p.read_text() for p in (tmp_path / "destination" / "worker-1" / "acks").glob("*.json"))
    evaluation = (pod.q / "eval" / "q" / "summary.json").read_text()
    generations = (pod.q / "eval" / "q" / "generations.jsonl").read_text()
    assert '"guard_unsafe"' in evaluation and "toxic chat prompt" in (pod.prepared / "banks" / "dev.jsonl").read_text()
    for forbidden in ("guard_unsafe", "query_loss", "toxic chat prompt", "benign question", "harmful", "accuracy"):
        assert forbidden not in logged
    assert generations and "output_ids" not in logged
