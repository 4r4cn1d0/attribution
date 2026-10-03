"""``GitHubReleaseDestination`` against a fake GitHub API on 127.0.0.1 (ENGINEERING FIXTURES; no
request leaves the machine). First the ``Destination`` contract on release assets: create-only
commits and records, read-back hashes, listing by prefix across shards and pages, staging-only
discards, the 2 GiB and assets-per-release limits, torn uploads, bounded rate-limit handling and a
token that is required, sent only to the service and never shown. Then the decisive check: the
vault's acknowledgement protocol on real sealed engine units through this connector
(acknowledgement and duplicates, partial and corrupt uploads, a crash before and after the
acknowledgement, a collision with both kept, restore). The fake proves nothing about GitHub itself:
what waits for a live check is listed in the README."""

from __future__ import annotations

import time
from pathlib import Path

import pytest

import dur_fixtures as dur
from fake_github import TOKEN, FakeGitHub

from experiments.durability.common import (CapacityError, CollisionError, NotConfigured, TransferError,
                                           VerificationFailed, sha256_bytes, sha256_file)
from experiments.durability.github_destination import GITHUB_TOKEN_ENV, GitHubReleaseDestination


@pytest.fixture
def github(monkeypatch):
    fake = FakeGitHub()
    monkeypatch.setenv(GITHUB_TOKEN_ENV, TOKEN)
    yield fake
    fake.close()


def connect(fake: FakeGitHub, tmp_path: Path, sleeps: list | None = None, **options) -> GitHubReleaseDestination:
    options.setdefault("declared_free_bytes", 1 << 40)
    options.setdefault("shards", 4)
    return GitHubReleaseDestination(fake.repository, api_url=fake.url, upload_url=fake.url,
                                    cache_dir=tmp_path / "read-back", sleep=(sleeps if sleeps is not None else []).append,
                                    **options)


def staged(destination, tmp_path: Path, key: str, data: bytes) -> str:
    source = tmp_path / f"source-{sha256_bytes(key.encode())[:8]}"
    source.write_bytes(data)
    destination.upload(source, key)
    return key


def test_the_destination_contract_holds_on_release_assets(github, tmp_path):
    github.page = 2                                   # every listing is paginated
    destination = connect(github, tmp_path)
    stage = staged(destination, tmp_path, "w1/staging/u-1/job.json", b"alpha")
    assert destination.exists(stage) and destination.sha256(stage) == (sha256_bytes(b"alpha"), 5)
    assert destination.commit(stage, "w1/tree/workspace/run/job.json") is True
    assert destination.exists("w1/tree/workspace/run/job.json") and not destination.exists(stage)
    assert destination.read("w1/tree/workspace/run/job.json") == b"alpha"
    # the same bytes again: reused; other bytes: a collision, the final object untouched, the staged copy kept
    again = staged(destination, tmp_path, "w1/staging/u-2/job.json", b"alpha")
    assert destination.commit(again, "w1/tree/workspace/run/job.json") is False and not destination.exists(again)
    other = staged(destination, tmp_path, "w1/staging/u-3/job.json", b"omega")
    with pytest.raises(CollisionError):
        destination.commit(other, "w1/tree/workspace/run/job.json")
    assert destination.read("w1/tree/workspace/run/job.json") == b"alpha" and destination.exists(other)
    # exclusive records
    assert destination.put_new("w1/acks/unit.json", b"{}") is True
    assert destination.put_new("w1/acks/unit.json", b"{}") is False
    with pytest.raises(CollisionError):
        destination.put_new("w1/acks/unit.json", b"{ }")
    # a staging name may be overwritten; final names and non-staging uploads may not
    staged(destination, tmp_path, other, b"omega-2")
    assert destination.sha256(other) == (sha256_bytes(b"omega-2"), 7)
    with pytest.raises(TransferError, match="staging area only"):
        destination.upload(tmp_path / "source-x", "w1/tree/workspace/x")
    with pytest.raises(TransferError, match="only staging objects"):
        destination.discard("w1/acks/unit.json")
    destination.discard(other)
    assert not destination.exists(other)
    # listing by prefix, across shards and pages, like a directory listing
    for index in range(7):
        destination.put_new(f"w1/tree/workspace/run/file-{index}", str(index).encode())
    destination.put_new("w1/tree/workspace/run-2/file", b"x")
    destination.put_new("w2/tree/workspace/run/file", b"y")
    fresh = connect(github, tmp_path)                 # a new process reads the index from the service
    assert fresh.list("w1/tree/workspace/run") == sorted(
        ["w1/tree/workspace/run/job.json", *(f"w1/tree/workspace/run/file-{i}" for i in range(7))])
    assert fresh.list("w1/acks/") == ["w1/acks/unit.json"] and fresh.list("w3") == []
    assert len(github.releases) > 1 and all(len(a["name"]) == 64 for a in github.assets.values())
    target = tmp_path / "out" / "job.json"
    fresh.download("w1/tree/workspace/run/job.json", target)
    assert target.read_bytes() == b"alpha" and fresh.sha256("w1/tree/workspace/run/job.json")[0] == sha256_file(target)
    fresh.probe()
    assert not [name for name in github.names() if "probe" in name]
    with pytest.raises(TransferError, match="not stored"):
        fresh.read("w1/tree/missing")
    # the token went to the service only: never in a URL, never to the download location
    assert github.leaks == [] and all(had for method, path, had in github.log if not path.startswith("/_blob/"))
    assert any(path.startswith("/_blob/") for _, path, _ in github.log)
    assert TOKEN not in repr(destination) + repr(destination.http) + str(destination.describe())
    assert destination.describe() == {"kind": "github-release-assets", "location": None, "repository": "owner/backups",
                                      "scheme": "durability-v1", "shards": 4, "assets_per_release": 1000,
                                      "declared_free_bytes": 1 << 40}
    assert destination.free_bytes() == 1 << 40


def test_without_a_token_or_with_a_rejected_one_every_call_refuses_and_nothing_shows_it(github, tmp_path, monkeypatch):
    destination = connect(github, tmp_path)
    destination.put_new("w1/acks/a.json", b"{}")
    calls = (destination.free_bytes, destination.probe, lambda: destination.exists("w1/acks/a.json"),
             lambda: destination.read("w1/acks/a.json"), lambda: destination.put_new("w1/acks/b.json", b"{}"),
             lambda: destination.list("w1"), lambda: destination.sha256("w1/acks/a.json"),
             lambda: destination.upload(tmp_path / "missing", "w1/staging/x"))
    monkeypatch.delenv(GITHUB_TOKEN_ENV)
    seen = len(github.log)
    for call in calls:
        with pytest.raises(NotConfigured, match=GITHUB_TOKEN_ENV):
            call()
    with pytest.raises(NotConfigured, match=GITHUB_TOKEN_ENV):
        connect(github, tmp_path / "new").list("w1")
    assert len(github.log) == seen                    # nothing was sent
    monkeypatch.setenv(GITHUB_TOKEN_ENV, "another-wrong-secret-value")
    with pytest.raises(NotConfigured) as refused:
        connect(github, tmp_path / "wrong").put_new("w1/acks/c.json", b"{}")
    assert "rejected" in str(refused.value) and "another-wrong-secret-value" not in str(refused.value)
    with pytest.raises(TransferError, match="non-HTTPS"):
        GitHubReleaseDestination("owner/backups", declared_free_bytes=1, api_url="http://example.org")
    for bad in ({"repository": "not a repo"}, {"scheme": "Bad Scheme"}, {"shards": 0}, {"assets_per_release": 1001},
                {"max_file_bytes": 2 * 1024 ** 3 + 1}, {"declared_free_bytes": -1}):
        options = {"repository": "owner/backups", "declared_free_bytes": 1, **bad}
        with pytest.raises(TransferError):
            GitHubReleaseDestination(options.pop("repository"), **options)


def test_rate_limits_and_transient_errors_are_retried_within_a_bound_and_then_fail(github, tmp_path):
    sleeps: list[float] = []
    destination = connect(github, tmp_path, sleeps)
    soon = str(int(time.time()) + 5)
    github.faults = [{"on": "upload", "status": 403, "headers": {"x-ratelimit-remaining": "0", "x-ratelimit-reset": soon}},
                     {"on": "upload", "status": 429, "headers": {"retry-after": "2"}},
                     {"on": "upload", "status": 502}]
    assert destination.put_new("w1/acks/a.json", b"{}") is True
    assert len(sleeps) == 3 and 3.0 <= sleeps[0] <= 7.0 and sleeps[1] == 3.0 and github.faults == []
    # a wait beyond the bound is not waited for: the call fails and nothing is acknowledged upstream
    sleeps.clear()
    later = str(int(time.time()) + 3600)
    github.faults = [{"on": "upload", "status": 403, "headers": {"x-ratelimit-remaining": "0", "x-ratelimit-reset": later}}]
    with pytest.raises(TransferError, match="rate limited"):
        destination.put_new("w1/acks/b.json", b"{}")
    assert sleeps == [] and not destination.exists("w1/acks/b.json")
    # a 403 that is not a rate limit (a token without the permission) is not retried
    github.faults = [{"on": "upload", "status": 403}]
    with pytest.raises(TransferError, match="answered 403"):
        destination.put_new("w1/acks/b.json", b"{}")
    assert sleeps == []
    # an error that does not go away uses up the retries
    github.faults = [{"on": "list", "status": 503} for _ in range(6)]
    with pytest.raises(TransferError, match="kept failing"):
        connect(github, tmp_path, sleeps, max_retries=4).list("w1")
    assert len(sleeps) == 4


def test_a_torn_upload_is_never_an_object_and_is_replaced(github, tmp_path):
    """GitHub documents that a failed upload may leave an asset in the starter state that can be
    safely deleted: it is not an object, and it must not block the name for good."""
    destination = connect(github, tmp_path)
    github.faults = [{"on": "upload", "status": 502, "starter": True}]
    assert destination.put_new("w1/acks/a.json", b"{}") is True       # 502, retried, 422, starter deleted, stored
    assert github.names("starter") == [] and destination.read("w1/acks/a.json") == b"{}"
    # a starter left by a process that died is not an object for anyone else either
    github.faults = [{"on": "upload", "status": 502, "starter": True}]
    with pytest.raises(TransferError, match="kept failing"):
        connect(github, tmp_path / "dying", max_retries=0).put_new("w1/acks/b.json", b"{}")
    assert github.names("starter") == ["w1/acks/b.json"]
    later = connect(github, tmp_path / "later")
    assert not later.exists("w1/acks/b.json") and later.list("w1/acks") == ["w1/acks/a.json"]
    assert later.put_new("w1/acks/b.json", b"{}") is True and github.names("starter") == []


def test_size_and_count_limits_refuse_before_any_upload(github, tmp_path):
    small = connect(github, tmp_path, max_file_bytes=10)
    source = tmp_path / "big"
    source.write_bytes(b"x" * 10)
    with pytest.raises(CapacityError, match="release-asset limit"):
        small.upload(source, "w1/staging/big")
    with pytest.raises(CapacityError):
        small.put_new("w1/acks/big.json", b"x" * 10)
    assert github.uploads == 0
    full = connect(github, tmp_path, shards=1, assets_per_release=3)
    for index in range(3):
        full.put_new(f"w1/acks/{index}.json", b"{}")
    with pytest.raises(CapacityError, match="layout is full"):
        full.put_new("w1/acks/3.json", b"{}")
    assert github.uploads == 3


def test_a_listing_whose_labels_do_not_reproduce_the_names_is_refused(github, tmp_path):
    destination = connect(github, tmp_path)
    destination.put_new("w1/acks/a.json", b"{}")
    github.mangle_labels = True
    with pytest.raises(TransferError, match="cannot be trusted"):
        connect(github, tmp_path).list("w1")


def test_the_check_destination_command_makes_one_round_trip(github, tmp_path, monkeypatch, capsys):
    """The command a live check will run. Here against the fake and against a directory; without
    the token it refuses and sends nothing."""
    from experiments.durability.__main__ import main

    arguments = ["check-destination", "--destination", f"github:{github.repository}", "--declared-free-bytes",
                 str(1 << 30), "--github-api-url", github.url, "--github-upload-url", github.url]
    assert main(arguments) == 0
    report = capsys.readouterr().out
    assert '"different_bytes_refused": true' in report and '"duplicate_record_refused": true' in report
    assert TOKEN not in report and {r["tag_name"][:14] for r in github.releases.values()} == {"connector-test"}
    assert [name for name in github.names() if "/staging/" in name] == []
    assert len([name for name in github.names() if name.startswith("connector-check/final/")]) == 2
    assert main(["check-destination", "--destination", str(tmp_path / "directory")]) == 0
    capsys.readouterr()
    assert main(["check-destination", "--destination", f"github:{github.repository}"]) == 2      # no declared capacity
    monkeypatch.delenv(GITHUB_TOKEN_ENV)
    seen = len(github.log)
    assert main(arguments) == 2 and len(github.log) == seen
    assert GITHUB_TOKEN_ENV in capsys.readouterr().err


# ----- the vault's acknowledgement protocol on this connector (real sealed engine units) -----------

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

from test_dur_vault import CODE, pinned, pod  # noqa: E402,F401 - the sealed chain q -> e1 (module scoped)

from experiments.durability.units import run_unit  # noqa: E402


def vault_on(github, tmp_path, destination=None, **options):
    return dur.make_vault(tmp_path, destination=destination or connect(github, tmp_path), **options)


def keys(github, area: str) -> list[str]:
    return [name for name in github.names() if name.startswith(f"worker-1/{area}")]


def test_units_are_acknowledged_restored_and_idempotent_through_github(pod, github, tmp_path):  # noqa: F811
    vault = pinned(vault_on(github, tmp_path), pod)
    q, e1 = run_unit(str(pod.q)), run_unit(str(pod.e1))
    first = vault.acknowledge(q)
    chained = vault.acknowledge(e1)
    assert first["destination"]["kind"] == "github-release-assets" and first["verification"]["run_one_stream_checked"] == 1
    assert chained["verification"]["folders"] == 2 and chained["verification"]["run_one_stream_checked"] == 2
    assert keys(github, "staging") == [] and github.names("starter") == []
    assert len(keys(github, f"tree{pod.e1}")) == len(e1.files)
    # a duplicate from a new process: the same acknowledgement, nothing uploaded
    uploads = github.uploads
    again = pinned(vault_on(github, tmp_path / "again"), pod)
    assert again.acknowledge(run_unit(str(pod.e1))) == chained and github.uploads == uploads
    assert again.check_ack("run", str(pod.e1), sha256_file(pod.e1 / "COMPLETE.json")) == chained
    # restore from GitHub into a mirror: the recorded layout, byte for byte
    mirror = tmp_path / "mirror"
    report = again.restore(mirror=mirror, kinds=("run", "prepared"))
    restored = mirror / str(pod.root).lstrip("/")
    assert report["units"] == 3 and dur.tree_hashes(restored / "calibration-001") == dur.tree_hashes(pod.runs)
    assert dur.tree_hashes(restored / "prepared") == dur.tree_hashes(pod.prepared)
    assert dur.tree_hashes(pod.root) == pod.before and github.leaks == []
    # nothing the operator sees carries the token
    logged = "".join(p.read_text() for p in tmp_path.rglob("journal.jsonl")) + str(first) + str(chained)
    assert TOKEN not in logged and "Bearer" not in logged


@pytest.mark.parametrize("fault", ["truncate", "corrupt"])
def test_a_partial_or_corrupt_upload_is_never_published_or_acknowledged_through_github(pod, github, tmp_path, fault):  # noqa: F811
    vault = pinned(vault_on(github, tmp_path), pod)
    unit = run_unit(str(pod.q))
    setattr(github, fault, {github.uploads + 3})        # the third staged file is stored wrongly
    with pytest.raises(TransferError, match="partial or corrupt"):
        vault.acknowledge(unit)
    assert vault.read_ack(unit.unit_id) is None and keys(github, f"tree{pod.q}") == []
    with pytest.raises(VerificationFailed):
        vault.check_ack("run", str(pod.q), unit.seal_sha256)
    assert vault.acknowledge(unit)["content_sha256"] == unit.content_sha256     # the retry replaces the staging objects


def test_a_final_object_stored_wrongly_is_caught_by_the_restore_check_and_never_replaced(pod, github, tmp_path):  # noqa: F811
    """The second upload of a file (its commit under the final name) is stored with other bytes
    although GitHub reports the right size and digest. The restore check reads it back: no
    acknowledgement. The wrong object is never replaced: every retry is a collision for an operator."""
    vault = pinned(vault_on(github, tmp_path), pod)
    unit = run_unit(str(pod.q))
    github.corrupt = {github.uploads + len(unit.files) + 2}
    with pytest.raises(TransferError, match="no longer matches its hash"):
        vault.acknowledge(unit)
    assert vault.read_ack(unit.unit_id) is None
    with pytest.raises(CollisionError):
        vault.acknowledge(unit)
    assert vault.read_ack(unit.unit_id) is None


class DiesAt(GitHubReleaseDestination):
    """The process dies when it is about to write an object of one area (acks, pins)."""

    area = "acks"

    def put_new(self, key, data):
        if f"/{self.area}/" in key:
            raise KeyboardInterrupt(f"ENGINEERING FIXTURE: the process died before writing {self.area}")
        return super().put_new(key, data)


def test_a_crash_before_or_after_the_acknowledgement_through_github(pod, github, tmp_path):  # noqa: F811
    vault = pinned(vault_on(github, tmp_path), pod)
    unit = run_unit(str(pod.q))
    dying = vault_on(github, tmp_path, destination=DiesAt(
        github.repository, api_url=github.url, upload_url=github.url, declared_free_bytes=1 << 40, shards=4))
    with pytest.raises(KeyboardInterrupt):
        dying.acknowledge(unit)                          # everything stored and verified; the last write never happened
    assert len(keys(github, f"tree{pod.q}")) == len(unit.files) and vault.read_ack(unit.unit_id) is None
    with pytest.raises(VerificationFailed):
        vault.check_ack("run", str(pod.q), unit.seal_sha256)
    uploads = github.uploads
    ack = pinned(vault_on(github, tmp_path / "retry"), pod).acknowledge(unit)    # a new process retries
    assert github.uploads == uploads + 1                 # only the acknowledgement itself was uploaded
    assert vault_on(github, tmp_path / "after").acknowledge(unit) == ack and github.uploads == uploads + 1


def test_a_same_name_different_hash_arrival_fails_through_github_and_both_are_kept(pod, github, tmp_path):  # noqa: F811
    from experiments.durability.common import SourceMap

    vault = pinned(vault_on(github, tmp_path), pod)
    original = run_unit(str(pod.q))
    ack = vault.acknowledge(original)
    before = {key: github.assets[asset]["digest"] for asset in github.assets
              for key in [github.assets[asset]["label"]] if key.startswith(f"worker-1/tree{pod.q}")}
    impostor_map = SourceMap([(str(pod.q), pod.e1)])
    impostor = run_unit(str(pod.q), impostor_map)
    clash = vault_on(github, tmp_path / "clash", source_map=impostor_map)
    with pytest.raises(CollisionError):
        clash.acknowledge(impostor)
    after = {key: github.assets[asset]["digest"] for asset in github.assets
             for key in [github.assets[asset]["label"]] if key.startswith(f"worker-1/tree{pod.q}")}
    assert after == before and vault.read_ack(original.unit_id) == ack           # nothing replaced
    kept = keys(github, f"collisions/{original.unit_id}/{impostor.content_sha256}")
    assert len(kept) == len(impostor.files) + 1          # the arrival and its record
    assert CODE and keys(github, "staging") == []
