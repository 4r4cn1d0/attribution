"""The RunPod provider adapter (stdlib only): read-only, and closed wherever RunPod's meaning is
not confirmed.

``RunPodProvider`` answers the ``admission.Provider`` questions from RunPod's API. It sends only
``GET`` requests to the REST API (``https://rest.runpod.io/v1``: ``/pods``, ``/networkvolumes``) and
one fixed GraphQL *query* (``https://api.runpod.io/graphql``: ``myself { clientBalance
currentSpendPerHr spendLimit }``). It contains no call that creates, starts, stops, updates or
deletes anything. The API key comes from the environment (``RUNPOD_API_KEY``), is sent as an
``Authorization: Bearer`` header (never in a URL, although RunPod's GraphQL guide shows a query
parameter) and is handled only by ``transport.Http``.

What was verified in RunPod's documentation on 3 October 2026 (links in the README), and what was
not:

- **Balance.** ``User.clientBalance`` is a ``Float`` in the GraphQL reference; ``runpodctl user``
  calls it the "current credit balance". Neither states a currency, how fresh the number is, or
  whether it is exactly the spendable prepaid balance. So ``read_balance`` returns a *recognized*
  reading only when the configuration carries a ``BalanceConfirmation``: who confirmed, when, in
  which currency, and in what words. Without it the reading is marked unrecognized and admission
  refuses. The timestamp is the moment of the API read; RunPod gives none of its own.
- **Rates.** A pod's ``costPerHr`` is "the cost in Runpod credits per hour of running a Pod". The
  API reports no storage rate, so the per-GB-month prices of network volumes, pod volumes and
  container disks are configuration (``StoragePrices``, from the pricing page, with who confirmed
  them and when). Whether ``costPerHr`` already includes a running pod's disks is not documented;
  they are added, which can only over-state the cost.
- **Liabilities.** Every pod and every network volume of the account. As a cross-check the
  account's ``currentSpendPerHr`` must not exceed what those explain: if it does, something else
  bills (a serverless endpoint, for example) and the call refuses.
- **Persistence.** "Network volume ... retained independently" of any pod; a container disk is
  "lost on stop/restart"; a pod volume "is deleted when the Pod is terminated". ``confirm_persistent``
  therefore confirms only a path under the mount (``volumeMountPath``) of a RUNNING pod that has a
  network volume attached which the account's volume list also shows. At a zero balance a network
  volume's data is kept but the volume keeps billing and "may eventually be terminated": persistent
  storage is not unconditional.
- **Shutdown.** RunPod itself offers nothing to arm. The GraphQL reference lists ``stopAfter`` and
  ``terminateAfter`` (``DateTime``) among the inputs that *create* a pod, without describing them;
  the pod type does not expose them, the REST pod schema has no such field, and no documented call
  sets a stop time on an existing pod. A stop time that cannot be read back cannot be confirmed
  from here. ``arm_shutdown`` therefore refuses unless the configuration names a shutdown: the
  stop timer inside the pod (``shutdown_timer.PodTimer``, with the GitHub watchdog as an optional
  best-effort backup), or the watchdog alone. It answers ``armed`` only after that shutdown has
  acknowledged a stop of this worker's pod, and for the timer only when its records are on storage
  RunPod confirms as persistent. This adapter never stops anything itself (README: "Shutdown").
- **Which key.** Inside a pod RunPod sets ``RUNPOD_API_KEY`` to a pod-scoped key of its own
  ("Pod-scoped API key"; what it may do is not documented). The account key this adapter reads
  with must then come from another variable (``key_env``); it should be a Read Only key.

Any field that is missing, of another type or outside the documented values makes the call fail
with ``ProviderError``; nothing is defaulted. Admission treats every provider error as a refusal.
"""

from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass
from pathlib import PurePosixPath
from typing import Callable, Mapping

from .admission import BALANCE_KIND, BalanceReading, Liability, Provider, RateCard
from .common import Clock, NotConfigured, ProviderError, iso, parse_utc, utc_clock
from .transport import Http

__all__ = ["RUNPOD_KEY_ENV", "RUNPOD_POD_ENV", "UNCONFIRMED_BALANCE_KIND", "BalanceConfirmation", "StoragePrices",
           "RunPodConfig", "RunPodProvider", "SHUTDOWN_GAP"]

RUNPOD_KEY_ENV = "RUNPOD_API_KEY"
RUNPOD_POD_ENV = "RUNPOD_POD_ID"
UNCONFIRMED_BALANCE_KIND = "runpod-clientBalance-unconfirmed"
MYSELF_QUERY = "query { myself { clientBalance currentSpendPerHr spendLimit } }"
POD_STATES = ("RUNNING", "EXITED", "TERMINATED")
SHUTDOWN_GAP = ("RunPod documents no stop time that can be set on, or read back from, an existing pod, and no shutdown "
                "is configured (the pod's own stop timer, or the external watchdog); a shutdown cannot be confirmed, "
                "so no lease is granted (README: Shutdown)")


@dataclass(frozen=True)
class BalanceConfirmation:
    """A named person's recorded confirmation that ``clientBalance`` is the spendable prepaid credit
    balance, in the stated currency."""

    confirmed_by: str
    confirmed_utc: str
    currency: str
    statement: str


@dataclass(frozen=True)
class StoragePrices:
    """Storage prices per GB per month, which the API does not report, with their source and who
    confirmed them. ``hours_per_month`` converts them to hourly rates (a smaller value is the
    conservative choice)."""

    network_volume_per_gb_month: float
    pod_volume_running_per_gb_month: float
    pod_volume_stopped_per_gb_month: float
    container_disk_per_gb_month: float
    hours_per_month: float
    source: str
    confirmed_by: str
    confirmed_utc: str


@dataclass(frozen=True)
class RunPodConfig:
    """Explicit configuration. ``worker_pods``: worker name -> pod id. ``local_pod_id``: the pod this
    process runs on (default: the ``RUNPOD_POD_ID`` variable RunPod sets inside a pod).
    ``destination_per_hour``: the declared hourly cost of the off-pod destination (0 for GitHub
    release assets). ``spend_tolerance_per_hour``: slack of the spend cross-check."""

    worker_pods: Mapping[str, str]
    balance_confirmation: BalanceConfirmation | None = None
    storage_prices: StoragePrices | None = None
    destination_per_hour: float | None = None
    local_pod_id: str | None = None
    spend_tolerance_per_hour: float = 0.01


def _number(value: object) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value)


def _text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())


class RunPodProvider(Provider):
    """See the module doc."""

    def __init__(self, config: RunPodConfig, *, key_env: str = RUNPOD_KEY_ENV, rest_url: str = "https://rest.runpod.io/v1",
                 graphql_url: str = "https://api.runpod.io/graphql", clock: Clock = utc_clock,
                 max_retries: int = 4, max_wait_seconds: float = 120.0,
                 sleep: Callable[[float], None] | None = None, shutdown: object | None = None) -> None:
        """``shutdown``: the external watchdog's worker side (an object with ``arm(worker, pod,
        at_utc)`` and ``lateness_seconds``), or None: no shutdown can be armed."""
        self.config, self.clock, self.shutdown = config, clock, shutdown
        self.rest, self.graphql = rest_url.rstrip("/"), graphql_url.rstrip("/")
        options = {} if sleep is None else {"sleep": sleep}
        self.http = Http(token_env=key_env, bases=(self.rest, self.graphql), max_retries=max_retries,
                         max_wait_seconds=max_wait_seconds, **options)
        if not isinstance(config.worker_pods, Mapping) or not all(
                _text(k) and _text(v) for k, v in config.worker_pods.items()):
            raise ProviderError("worker_pods must map worker names to pod ids")
        if len(set(config.worker_pods.values())) != len(config.worker_pods):
            raise ProviderError("two workers name the same pod")

    def __repr__(self) -> str:
        return f"RunPodProvider(workers={sorted(self.config.worker_pods)})"

    # ----- reads ---------------------------------------------------------------------

    def _get(self, path: str) -> list:
        reply = self.http.request("GET", f"{self.rest}{path}", headers={"Accept": "application/json"})
        if reply.status != 200:
            raise ProviderError(f"RunPod answered {reply.status} to GET {path.split('?')[0]}")
        data = reply.json()
        if not isinstance(data, list) or not all(isinstance(item, dict) for item in data):
            raise ProviderError(f"RunPod answered GET {path.split('?')[0]} in an unexpected shape")
        return data

    def _myself(self) -> dict:
        reply = self.http.request("POST", self.graphql, headers={"Content-Type": "application/json",
                                                                 "Accept": "application/json"},
                                  body=json.dumps({"query": MYSELF_QUERY}).encode("utf-8"))
        if reply.status != 200:
            raise ProviderError(f"RunPod answered {reply.status} to the account query")
        data = reply.json()
        myself = data.get("data", {}).get("myself") if isinstance(data, dict) and isinstance(data.get("data"), dict) else None
        if not isinstance(data, dict) or data.get("errors") or not isinstance(myself, dict):
            raise ProviderError("RunPod answered the account query in an unexpected shape")
        return myself

    def _pods(self) -> list[dict]:
        """Every pod of the account, each with exactly the fields this adapter relies on."""
        pods = []
        for pod in self._get("/pods?includeNetworkVolume=true"):
            wrong = [name for name in ("costPerHr", "adjustedCostPerHr", "containerDiskInGb", "volumeInGb")
                     if not _number(pod.get(name)) or pod[name] < 0]
            if not _text(pod.get("id")):
                wrong.append("id")
            if pod.get("desiredStatus") not in POD_STATES:
                wrong.append("desiredStatus")
            volume = pod.get("networkVolume")
            if volume is not None and not (isinstance(volume, dict) and _text(volume.get("id"))
                                           and _number(volume.get("size")) and volume["size"] >= 0):
                wrong.append("networkVolume")
            if wrong:
                raise ProviderError(f"a pod has missing or unknown fields {sorted(wrong)}: nothing is derived from it")
            pods.append(pod)
        if len({pod["id"] for pod in pods}) != len(pods):
            raise ProviderError("RunPod listed one pod twice")
        return pods

    def _volumes(self) -> list[dict]:
        volumes = self._get("/networkvolumes")
        for volume in volumes:
            if not (_text(volume.get("id")) and _number(volume.get("size")) and volume["size"] >= 0):
                raise ProviderError("a network volume has missing or unknown fields: nothing is derived from it")
        return volumes

    def _prices(self) -> StoragePrices:
        prices = self.config.storage_prices
        if prices is None:
            raise NotConfigured("the storage prices are not configured: RunPod's API reports no storage rate")
        values = (prices.network_volume_per_gb_month, prices.pod_volume_running_per_gb_month,
                  prices.pod_volume_stopped_per_gb_month, prices.container_disk_per_gb_month)
        if not all(_number(v) and v >= 0 for v in values) or not _number(prices.hours_per_month) \
                or not 600 <= prices.hours_per_month <= 750:
            raise ProviderError("the configured storage prices are missing, negative or use an implausible month")
        if not all(_text(v) for v in (prices.source, prices.confirmed_by)):
            raise ProviderError("the configured storage prices name no source or no one who confirmed them")
        try:
            parse_utc(prices.confirmed_utc)
        except ValueError:
            raise ProviderError("the storage prices' confirmation has no usable timestamp") from None
        return prices

    def _confirmation(self) -> BalanceConfirmation | None:
        confirmation = self.config.balance_confirmation
        if confirmation is None:
            return None
        if not all(_text(v) for v in (confirmation.confirmed_by, confirmation.currency, confirmation.statement)):
            raise ProviderError("the balance confirmation names no person, currency or statement")
        try:
            parse_utc(confirmation.confirmed_utc)
        except ValueError:
            raise ProviderError("the balance confirmation has no usable timestamp") from None
        return confirmation

    def _worker_of(self, pod_id: str) -> str | None:
        return next((worker for worker, pod in self.config.worker_pods.items() if pod == pod_id), None)

    def _disk_rate(self, pod: dict, prices: StoragePrices) -> float:
        """The hourly storage rate of a pod's own disks and of its attached network volume."""
        monthly = 0.0
        if pod["desiredStatus"] == "RUNNING":
            monthly += pod["containerDiskInGb"] * prices.container_disk_per_gb_month
            monthly += pod["volumeInGb"] * prices.pod_volume_running_per_gb_month
        elif pod["desiredStatus"] == "EXITED":
            monthly += pod["volumeInGb"] * prices.pod_volume_stopped_per_gb_month
        return monthly / prices.hours_per_month

    # ----- the Provider interface ----------------------------------------------------

    def read_balance(self) -> BalanceReading:
        amount = self._myself().get("clientBalance")
        if not _number(amount):
            raise ProviderError("clientBalance is missing or not a number")
        as_of = iso(self.clock())
        confirmation = self._confirmation()
        if confirmation is None:
            return BalanceReading(float(amount), "unconfirmed", as_of,
                                  "runpod graphql myself.clientBalance; its meaning and currency are not confirmed",
                                  UNCONFIRMED_BALANCE_KIND, False)
        return BalanceReading(float(amount), confirmation.currency, as_of,
                              f"runpod graphql myself.clientBalance; confirmed as the prepaid credit balance by "
                              f"{confirmation.confirmed_by} on {confirmation.confirmed_utc}", BALANCE_KIND, True)

    def read_rates(self, worker: str) -> RateCard:
        prices, confirmation = self._prices(), self._confirmation()
        if confirmation is None:
            raise NotConfigured("the currency of RunPod's rates is not confirmed (no balance confirmation)")
        if not _number(self.config.destination_per_hour) or self.config.destination_per_hour < 0:
            raise NotConfigured("the destination's hourly cost is not declared")
        pod_id = self.config.worker_pods.get(worker)
        if pod_id is None:
            raise NotConfigured(f"no pod is configured for worker {worker!r}")
        mine = [pod for pod in self._pods() if pod["id"] == pod_id]
        if len(mine) != 1 or mine[0]["desiredStatus"] != "RUNNING":
            raise ProviderError("the worker's pod is not listed as RUNNING")
        pod = mine[0]
        if pod["costPerHr"] <= 0:
            raise ProviderError("the worker's pod reports no hourly cost")
        storage = self._disk_rate(pod, prices)
        if pod.get("networkVolume") is not None:
            storage += pod["networkVolume"]["size"] * prices.network_volume_per_gb_month / prices.hours_per_month
        return RateCard(gpu_per_hour=float(pod["costPerHr"]), storage_per_hour=storage,
                        destination_per_hour=float(self.config.destination_per_hour), currency=confirmation.currency,
                        as_of_utc=iso(self.clock()),
                        source=f"runpod rest pods.costPerHr; storage prices from {prices.source}")

    def list_liabilities(self) -> list[Liability]:
        prices = self._prices()
        pods, volumes, myself = self._pods(), self._volumes(), self._myself()
        liabilities, attached = [], {}
        for pod in pods:
            worker = self._worker_of(pod["id"])
            if pod.get("networkVolume") is not None:
                attached[pod["networkVolume"]["id"]] = worker
            if pod["desiredStatus"] == "TERMINATED":
                continue
            rate = self._disk_rate(pod, prices) + (pod["costPerHr"] if pod["desiredStatus"] == "RUNNING" else 0.0)
            liabilities.append(Liability(f"pod {pod['id']} ({pod['desiredStatus']})", rate, "active", 0.0, worker))
        for volume in volumes:
            rate = volume["size"] * prices.network_volume_per_gb_month / prices.hours_per_month
            liabilities.append(Liability(f"network volume {volume['id']}", rate, "active", 0.0,
                                         attached.get(volume["id"])))
        spend = myself.get("currentSpendPerHr")
        if not _number(spend) or spend < 0:
            raise ProviderError("currentSpendPerHr is missing or not a number")
        explained = math.fsum(item.rate_per_hour for item in liabilities)
        if spend > explained + self.config.spend_tolerance_per_hour:
            raise ProviderError("the account spends more per hour than its pods and network volumes explain: "
                                "something else bills, and it is not listed")
        return liabilities

    def confirm_persistent(self, path: str) -> dict:
        pod_id = self.config.local_pod_id or os.environ.get(RUNPOD_POD_ENV, "").strip()
        if not pod_id:
            raise NotConfigured(f"the pod this process runs on is not configured (local_pod_id or {RUNPOD_POD_ENV})")
        mine = [pod for pod in self._pods() if pod["id"] == pod_id]
        if len(mine) != 1:
            return {"persistent": False, "volume": None, "reason": "the pod is not listed by the account"}
        pod = mine[0]
        volume, mount = pod.get("networkVolume"), pod.get("volumeMountPath")
        if pod["desiredStatus"] != "RUNNING" or volume is None:
            return {"persistent": False, "volume": None,
                    "reason": "the pod is not running with a network volume attached (a pod volume or container "
                              "disk does not survive termination)"}
        if not (_text(mount) and PurePosixPath(mount).is_absolute() and _text(path)
                and PurePosixPath(path).is_absolute() and ".." not in PurePosixPath(path).parts):
            return {"persistent": False, "volume": None, "reason": "the mount path or the declared path is not usable"}
        if not (PurePosixPath(path) == PurePosixPath(mount) or PurePosixPath(mount) in PurePosixPath(path).parents):
            return {"persistent": False, "volume": None, "reason": "the path is not under the network volume's mount"}
        if volume["id"] not in {item["id"] for item in self._volumes()}:
            return {"persistent": False, "volume": None, "reason": "the account's volume list lacks the attached volume"}
        return {"persistent": True, "volume": volume["id"], "mount": mount, "pod": pod_id,
                "source": "runpod rest: pods.networkVolume, pods.volumeMountPath, networkvolumes"}

    def shutdown_lateness_seconds(self) -> float:
        if self.shutdown is None:
            raise NotConfigured(SHUTDOWN_GAP)
        return float(self.shutdown.lateness_seconds)

    def arm_shutdown(self, worker: str, at_utc: str) -> dict:
        """``armed`` only when the configured external watchdog acknowledged a stop of this worker's
        pod that is complete by ``at_utc``; everything else raises."""
        if self.shutdown is None:
            raise NotConfigured(SHUTDOWN_GAP)
        pod_id = self.config.worker_pods.get(worker)
        if pod_id is None:
            raise NotConfigured(f"no pod is configured for worker {worker!r}")
        state_dir = getattr(self.shutdown, "state_dir", None)
        if state_dir is not None:       # a stop timer in the pod: its deadline must survive a restart of the container
            if self.confirm_persistent(str(state_dir)).get("persistent") is not True:
                raise ProviderError("the stop timer's records are not on storage RunPod confirms as persistent")
        armed = self.shutdown.arm(worker, pod_id, at_utc)
        if not (isinstance(armed, dict) and armed.get("armed") is True and armed.get("pod") == pod_id
                and armed.get("at_utc") == at_utc):
            raise ProviderError("the watchdog did not confirm a stop of this worker's pod by the requested time")
        return armed
