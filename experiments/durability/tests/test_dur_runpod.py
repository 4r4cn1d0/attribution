"""``RunPodProvider`` against a fake RunPod API on 127.0.0.1 (ENGINEERING FIXTURES; no request
leaves the machine and nothing is created, started, stopped or deleted anywhere): a balance that is
recognized only with a recorded human confirmation; rates and liabilities from pods and network
volumes with declared storage prices; persistence only for a path under a network volume's mount;
a shutdown that is never claimed without the external watchdog; unknown shapes, values and
unexplained spend failing closed; a key that is required and never shown; and admission refusing
on every one of these. The fake proves nothing about RunPod: what waits for a live check is in the
README."""

from __future__ import annotations

import pytest

import dur_fixtures as dur
from fake_runpod import KEY, FakeRunPod, network_volume, pod

from experiments.durability.admission import BALANCE_KIND, AdmissionController, UnconfiguredProvider
from experiments.durability.common import (AdmissionRefused, DurabilityError, Journal, NotConfigured,
                                           ProviderError, StorageRefused, iso)
from experiments.durability.destination import LocalDirectoryDestination, UnconfiguredDestination
from experiments.durability.admission import check_storage
from experiments.durability.github_destination import GitHubReleaseDestination
from experiments.durability.runpod_provider import (RUNPOD_KEY_ENV, RUNPOD_POD_ENV, UNCONFIRMED_BALANCE_KIND,
                                                    BalanceConfirmation, RunPodConfig, RunPodProvider, StoragePrices)
from experiments.durability.wiring import destination_from, provider_from

CONFIRMATION = BalanceConfirmation("test operator", iso(dur.T0), "USD",
                                   "ENGINEERING FIXTURE: clientBalance is the spendable prepaid credit balance in USD")
PRICES = StoragePrices(network_volume_per_gb_month=0.07, pod_volume_running_per_gb_month=0.10,
                       pod_volume_stopped_per_gb_month=0.20, container_disk_per_gb_month=0.10, hours_per_month=720.0,
                       source="ENGINEERING FIXTURE price list", confirmed_by="test operator", confirmed_utc=iso(dur.T0))
VOLUME = network_volume("vol-1", size=100)


@pytest.fixture
def runpod(monkeypatch):
    fake = FakeRunPod()
    fake.pods = [pod("pod-1", volume=VOLUME), pod("pod-2", cost=0.4, volume=None, volume_gb=50),
                 pod("pod-3", status="EXITED", volume=None, volume_gb=40), pod("pod-4", status="TERMINATED")]
    fake.volumes = [VOLUME, network_volume("vol-2", size=10)]
    monkeypatch.setenv(RUNPOD_KEY_ENV, KEY)
    monkeypatch.delenv(RUNPOD_POD_ENV, raising=False)
    yield fake
    fake.close()


def provider(fake: FakeRunPod, clock=None, **changes) -> RunPodProvider:
    fields = {"worker_pods": {"worker-1": "pod-1"}, "balance_confirmation": CONFIRMATION, "storage_prices": PRICES,
              "destination_per_hour": 0.0, "local_pod_id": "pod-1"}
    return RunPodProvider(RunPodConfig(**{**fields, **changes}), rest_url=f"{fake.url}/v1",
                          graphql_url=f"{fake.url}/graphql", clock=clock or dur.ManualClock(), sleep=lambda s: None)


def test_the_balance_is_recognized_only_with_a_recorded_confirmation(runpod):
    clock = dur.ManualClock()
    reading = provider(runpod, clock).read_balance()
    assert (reading.amount, reading.currency, reading.kind, reading.recognized) == (100.0, "USD", BALANCE_KIND, True)
    assert reading.as_of_utc == iso(clock.now) and "confirmed as the prepaid credit balance by test operator" in reading.source
    bare = provider(runpod, balance_confirmation=None).read_balance()
    assert (bare.kind, bare.recognized, bare.currency) == (UNCONFIRMED_BALANCE_KIND, False, "unconfirmed")
    for bad in ({"confirmed_by": " "}, {"currency": ""}, {"statement": ""}, {"confirmed_utc": "yesterday"}):
        incomplete = BalanceConfirmation(**{**CONFIRMATION.__dict__, **bad})
        with pytest.raises(ProviderError, match="balance confirmation"):
            provider(runpod, balance_confirmation=incomplete).read_balance()
    for value in (None, "100", True, float("nan")):
        runpod.myself = {"clientBalance": value, "currentSpendPerHr": 0.0}
        with pytest.raises((ProviderError, DurabilityError)):
            provider(runpod).read_balance()
    runpod.myself, runpod.graphql_errors = {"clientBalance": 100.0}, [{"message": "ENGINEERING FIXTURE"}]
    with pytest.raises(ProviderError, match="unexpected shape"):
        provider(runpod).read_balance()


def test_rates_and_liabilities_come_from_pods_volumes_and_declared_prices(runpod):
    runpod.myself = {"clientBalance": 100.0, "currentSpendPerHr": 2.0, "spendLimit": 80}
    adapter = provider(runpod)
    rates = adapter.read_rates("worker-1")
    disks = 20 * 0.10 / 720.0 + 100 * 0.07 / 720.0                    # container disk and the network volume
    assert rates.gpu_per_hour == 1.6 and rates.storage_per_hour == pytest.approx(disks)
    assert (rates.destination_per_hour, rates.currency) == (0.0, "USD")
    liabilities = {item.name: item for item in adapter.list_liabilities()}
    assert set(liabilities) == {"pod pod-1 (RUNNING)", "pod pod-2 (RUNNING)", "pod pod-3 (EXITED)",
                                "network volume vol-1", "network volume vol-2"}      # the terminated pod bills nothing
    assert liabilities["pod pod-1 (RUNNING)"].worker == "worker-1"
    assert liabilities["network volume vol-1"].worker == "worker-1"     # attached to the worker's pod
    assert liabilities["pod pod-2 (RUNNING)"].worker is None
    assert liabilities["pod pod-2 (RUNNING)"].rate_per_hour == pytest.approx(0.4 + (20 * 0.10 + 50 * 0.10) / 720.0)
    assert liabilities["pod pod-3 (EXITED)"].rate_per_hour == pytest.approx(40 * 0.20 / 720.0)   # stopped: storage only
    assert liabilities["network volume vol-2"].rate_per_hour == pytest.approx(10 * 0.07 / 720.0)
    assert all(item.state == "active" for item in liabilities.values())
    # the account spends more than pods and volumes explain: something unlisted bills
    runpod.myself = {"clientBalance": 100.0, "currentSpendPerHr": 5.0}
    with pytest.raises(ProviderError, match="something else bills"):
        adapter.list_liabilities()
    for refused, change in (("storage prices are not configured", {"storage_prices": None}),
                            ("currency", {"balance_confirmation": None}),
                            ("destination's hourly cost", {"destination_per_hour": None}),
                            ("no pod is configured", {"worker_pods": {"worker-2": "pod-2"}})):
        with pytest.raises(NotConfigured, match=refused):
            provider(runpod, **change).read_rates("worker-1")
    with pytest.raises(ProviderError, match="implausible month"):
        provider(runpod, storage_prices=StoragePrices(**{**PRICES.__dict__, "hours_per_month": 1.0})).read_rates("worker-1")
    with pytest.raises(ProviderError, match="not listed as RUNNING"):
        provider(runpod, worker_pods={"worker-1": "pod-3"}).read_rates("worker-1")


@pytest.mark.parametrize("damage", [
    {"costPerHr": None}, {"costPerHr": "1.6"}, {"desiredStatus": "PAUSED"}, {"containerDiskInGb": -1},
    {"volumeInGb": None}, {"networkVolume": {"id": "vol-1"}}, {"networkVolume": "vol-1"}, {"id": ""}])
def test_an_unknown_or_missing_field_fails_closed(runpod, damage):
    runpod.pods = [{**runpod.pods[0], **damage}]
    adapter = provider(runpod)
    for call in (lambda: adapter.read_rates("worker-1"), adapter.list_liabilities,
                 lambda: adapter.confirm_persistent("/workspace/study")):
        with pytest.raises(ProviderError, match="missing or unknown fields"):
            call()


def test_other_unexpected_answers_fail_closed(runpod):
    adapter = provider(runpod)
    runpod.pods = {"pods": []}
    with pytest.raises(ProviderError, match="unexpected shape"):
        adapter.list_liabilities()
    runpod.pods = [pod("pod-1", volume=VOLUME), pod("pod-1", volume=VOLUME)]
    with pytest.raises(ProviderError, match="twice"):
        adapter.read_rates("worker-1")
    runpod.pods, runpod.volumes = [pod("pod-1", volume=VOLUME)], [{"id": "vol-1"}]
    with pytest.raises(ProviderError, match="network volume"):
        adapter.list_liabilities()
    runpod.volumes, runpod.myself = [VOLUME], {"clientBalance": 100.0}
    with pytest.raises(ProviderError, match="currentSpendPerHr"):
        adapter.list_liabilities()
    with pytest.raises(ProviderError, match="worker names"):
        provider(runpod, worker_pods={"worker-1": ""})
    with pytest.raises(ProviderError, match="same pod"):
        provider(runpod, worker_pods={"a": "pod-1", "b": "pod-1"})


def test_persistence_is_confirmed_only_under_a_network_volume_mount(runpod, monkeypatch):
    adapter = provider(runpod)
    confirmed = adapter.confirm_persistent("/workspace/attribution-study-v2")
    assert confirmed["persistent"] is True and confirmed["volume"] == "vol-1" and confirmed["mount"] == "/workspace"
    assert adapter.confirm_persistent("/workspace")["persistent"] is True
    for path in ("/root/study", "/workspace-other/study", "/workspace/../etc", "relative/path", ""):
        assert adapter.confirm_persistent(path)["persistent"] is False, path
    # a pod volume or a container disk is not persistent storage, whatever the mount says
    assert provider(runpod, local_pod_id="pod-2").confirm_persistent("/workspace/study")["persistent"] is False
    assert provider(runpod, local_pod_id="pod-3").confirm_persistent("/workspace/study")["persistent"] is False
    assert provider(runpod, local_pod_id="pod-9").confirm_persistent("/workspace/study")["persistent"] is False
    runpod.volumes = [network_volume("vol-2")]                       # the attached volume is not in the account's list
    assert adapter.confirm_persistent("/workspace/study")["persistent"] is False
    runpod.volumes = [VOLUME]
    with pytest.raises(NotConfigured, match="pod this process runs on"):
        provider(runpod, local_pod_id=None).confirm_persistent("/workspace/study")
    monkeypatch.setenv(RUNPOD_POD_ENV, "pod-1")                      # what RunPod sets inside a pod
    assert provider(runpod, local_pod_id=None).confirm_persistent("/workspace/study")["persistent"] is True


def test_the_provider_only_reads_and_never_shows_its_key(runpod, monkeypatch):
    adapter = provider(runpod)
    adapter.read_balance(), adapter.read_rates("worker-1"), adapter.list_liabilities()
    adapter.confirm_persistent("/workspace/study")
    with pytest.raises(NotConfigured, match="no external shutdown watchdog is configured"):
        adapter.arm_shutdown("worker-1", iso(dur.T0))
    with pytest.raises(NotConfigured, match="no external shutdown watchdog is configured"):
        adapter.shutdown_lateness_seconds()
    methods = {(method, path.split("?")[0]) for method, path, _ in runpod.log}
    assert methods == {("GET", "/v1/pods"), ("GET", "/v1/networkvolumes"), ("POST", "/graphql")}
    bodies = [body for method, _, body in runpod.log if method == "POST"]
    assert bodies and all("mutation" not in body and body.count("query") >= 1 for body in bodies)
    assert all(KEY not in path and KEY not in body for _, path, body in runpod.log)      # never in a URL or a body
    assert KEY not in repr(adapter) + repr(adapter.http)
    monkeypatch.delenv(RUNPOD_KEY_ENV)
    seen = len(runpod.log)
    for call in (adapter.read_balance, lambda: adapter.read_rates("worker-1"), adapter.list_liabilities,
                 lambda: adapter.confirm_persistent("/workspace/study")):
        with pytest.raises(NotConfigured, match=RUNPOD_KEY_ENV):
            call()
    assert len(runpod.log) == seen
    monkeypatch.setenv(RUNPOD_KEY_ENV, "a-wrong-key-value")
    with pytest.raises(NotConfigured) as refused:
        adapter.read_balance()
    assert "rejected" in str(refused.value) and "a-wrong-key-value" not in str(refused.value)


def admission(tmp_path, adapter, clock, planned=None) -> AdmissionController:
    return AdmissionController(tmp_path / "admission" / "reservations.jsonl", adapter, dur.POLICY,
                               planned or adapter.read_rates("worker-1"),
                               journal=Journal(tmp_path / "journal.jsonl", clock), clock=clock)


def test_admission_with_the_real_adapter_stops_at_the_shutdown_gap_and_at_every_unconfirmed_input(runpod, tmp_path):
    """With everything else confirmed, admission through a ``RunPodProvider`` that has no shutdown
    watchdog configured still refuses: no shutdown can be armed (test_dur_watchdog.py covers the
    configured case). Each unconfirmed input refuses earlier, with its own reason; nothing is
    reserved."""
    clock = dur.ManualClock()
    source = tmp_path / "workspace"
    source.mkdir()
    storage = dur.storage(source, LocalDirectoryDestination(tmp_path / "offsite"), source_path=str(source))
    runpod.pods = [pod("pod-1", volume=VOLUME, mount=str(source))]
    runpod.volumes = [VOLUME]
    adapter = provider(runpod, clock)
    planned = adapter.read_rates("worker-1")
    reserve = (planned.storage_per_hour + planned.destination_per_hour) * dur.POLICY.retention_hours
    controller = admission(tmp_path, adapter, clock, planned)
    with pytest.raises(AdmissionRefused, match="no provider-side shutdown can be armed"):
        controller.admit("worker-1", 3600.0, storage, reserve)
    cases = {"currency of RunPod's rates is not confirmed": {"balance_confirmation": None},
             "provider inputs are unavailable": {"storage_prices": None},
             "not confirmed": {"local_pod_id": "pod-9"}}
    for why, change in cases.items():
        with pytest.raises(AdmissionRefused, match=why):
            admission(tmp_path, provider(runpod, clock, **change), clock, planned).admit("worker-1", 3600.0, storage, reserve)
    runpod.pods = [pod("pod-1", volume=VOLUME, mount=str(source), cost=1.7)]         # the price changed since the plan
    with pytest.raises(AdmissionRefused, match="changed rate"):
        controller.admit("worker-1", 3600.0, storage, reserve)
    runpod.pods = [{**pod("pod-1", volume=VOLUME, mount=str(source)), "costPerHr": None}]
    with pytest.raises(AdmissionRefused, match="missing or unknown fields"):
        controller.admit("worker-1", 3600.0, storage, reserve)
    with pytest.raises(StorageRefused, match="missing or unknown fields"):
        check_storage(storage, adapter)
    assert not (tmp_path / "admission" / "reservations.jsonl").exists()
    refusals = [row for row in Journal(tmp_path / "journal.jsonl").read() if row["event"] == "admission-refused"]
    assert len(refusals) == 6 and KEY not in (tmp_path / "journal.jsonl").read_text()


def test_the_check_provider_command_reports_shapes_and_only_reads(runpod, tmp_path, capsys):
    import json

    from experiments.durability.__main__ import main

    runpod.myself = {"clientBalance": 73.21, "currentSpendPerHr": 1.5, "spendLimit": 80}
    config = {"kind": "runpod", "worker_pods": {"worker-1": "pod-1"}, "destination_per_hour": 0.0,
              "storage_prices": dict(PRICES.__dict__), "local_pod_id": "pod-1"}       # no balance confirmation yet
    path = tmp_path / "provider.json"
    path.write_text(json.dumps(config))
    arguments = ["check-provider", "--config", str(path), "--worker", "worker-1", "--path", "/workspace/study",
                 "--runpod-rest-url", f"{runpod.url}/v1", "--runpod-graphql-url", f"{runpod.url}/graphql"]
    assert main(arguments) == 0
    printed = capsys.readouterr().out
    report = json.loads(printed)
    assert report["balance"] == {"answered": True, "amount_type": "float", "kind": UNCONFIRMED_BALANCE_KIND,
                                 "recognized": False, "currency_stated": False}
    assert report["rates"]["answered"] is False and report["rates"]["refused_as"] == "NotConfigured"
    assert report["liabilities"] == {"answered": True, "count": 5, "attached_to_a_configured_worker": 2}
    assert report["persistence"] == {"answered": True, "persistent": True}
    assert report["shutdown"]["can_arm"] is False and report["creates_starts_stops_or_deletes"] is False
    assert "73.21" not in printed and "pod-1" not in printed and KEY not in printed     # shapes, not account details
    assert {method for method, _, _ in runpod.log} == {"GET", "POST"}
    assert all("mutation" not in body for _, _, body in runpod.log)


def test_wiring_builds_real_connectors_only_from_explicit_configuration(runpod, tmp_path, monkeypatch):
    assert isinstance(destination_from(None), UnconfiguredDestination) and isinstance(provider_from(None), UnconfiguredProvider)
    assert isinstance(destination_from(str(tmp_path / "d")), LocalDirectoryDestination)
    assert destination_from(f"dir:{tmp_path / 'd'}").describe()["location"] == str(tmp_path / "d")
    with pytest.raises(DurabilityError, match="declared free capacity"):
        destination_from("github:owner/backups")
    with pytest.raises(DurabilityError, match="GitHub options"):
        destination_from(str(tmp_path / "d"), declared_free_bytes=1)
    github = destination_from("github:owner/backups", declared_free_bytes=1 << 30, shards=8)
    assert isinstance(github, GitHubReleaseDestination) and github.describe()["repository"] == "owner/backups"
    monkeypatch.delenv("ATTRIBUTION_BACKUP_GITHUB_TOKEN", raising=False)
    with pytest.raises(NotConfigured):                                # built, but closed without its token
        github.free_bytes()
    config = {"kind": "runpod", "worker_pods": {"worker-1": "pod-1"}, "destination_per_hour": 0.0,
              "balance_confirmation": dict(CONFIRMATION.__dict__), "storage_prices": dict(PRICES.__dict__),
              "local_pod_id": "pod-1"}
    built = provider_from(config, rest_url=f"{runpod.url}/v1", graphql_url=f"{runpod.url}/graphql")
    assert isinstance(built, RunPodProvider) and built.read_balance().recognized is True
    assert provider_from({k: v for k, v in config.items() if k != "balance_confirmation"},
                         rest_url=f"{runpod.url}/v1", graphql_url=f"{runpod.url}/graphql").read_balance().recognized is False
    for bad in ({"kind": "other"}, {**config, "balance_confirmed": True}, {**config, "storage_prices": {"x": 1}},
                {**config, "balance_confirmation": {"confirmed_by": "x"}}):
        with pytest.raises(DurabilityError):
            provider_from(bad)
