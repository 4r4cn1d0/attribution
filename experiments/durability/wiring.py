"""Building the real connectors from explicit configuration (stdlib only). The defaults stay
fail-closed: no destination spec gives ``UnconfiguredDestination``, no provider configuration gives
``UnconfiguredProvider``. Nothing here reads a credential: the connectors take their token from
the environment when they make a request."""

from __future__ import annotations

from typing import Mapping

from .admission import Provider, UnconfiguredProvider
from .common import DurabilityError
from .destination import Destination, LocalDirectoryDestination, UnconfiguredDestination
from .github_destination import GitHubReleaseDestination
from .runpod_provider import BalanceConfirmation, RunPodConfig, RunPodProvider, StoragePrices

__all__ = ["destination_from", "provider_from"]

_RUNPOD_KEYS = {"kind", "worker_pods", "balance_confirmation", "storage_prices", "destination_per_hour",
                "local_pod_id", "spend_tolerance_per_hour"}


def destination_from(spec: str | None, **github: object) -> Destination:
    """``None`` or empty: not configured (every call refuses). ``github:owner/repo``: release assets of
    that repository (``declared_free_bytes`` is required; other keywords go to
    ``GitHubReleaseDestination``). ``dir:PATH`` or a plain path: a local directory."""
    if not spec:
        return UnconfiguredDestination("remote")
    if spec.startswith("github:"):
        if "declared_free_bytes" not in github:
            raise DurabilityError("a GitHub destination needs its declared free capacity (GitHub reports none)")
        return GitHubReleaseDestination(spec[len("github:"):], **github)
    if github:
        raise DurabilityError("GitHub options were given for a destination that is not github:owner/repo")
    return LocalDirectoryDestination(spec[len("dir:"):] if spec.startswith("dir:") else spec)


def provider_from(config: Mapping | None, **options: object) -> Provider:
    """``None``: not configured (every call refuses). ``{"kind": "runpod", ...}``: a ``RunPodProvider``
    from the mapping's ``worker_pods`` and, where the operator recorded them, ``balance_confirmation``,
    ``storage_prices``, ``destination_per_hour`` and ``local_pod_id``. An unknown key or kind refuses:
    a misspelt confirmation must not be silently ignored."""
    if config is None:
        return UnconfiguredProvider()
    if not isinstance(config, Mapping) or config.get("kind") != "runpod":
        raise DurabilityError("the provider configuration names no known kind")
    unknown = sorted(set(config) - _RUNPOD_KEYS)
    if unknown:
        raise DurabilityError(f"unknown provider configuration keys {unknown}")
    try:
        confirmation = config.get("balance_confirmation")
        prices = config.get("storage_prices")
        fields = {key: config[key] for key in ("destination_per_hour", "local_pod_id", "spend_tolerance_per_hour")
                  if key in config}
        built = RunPodConfig(worker_pods=dict(config.get("worker_pods") or {}),
                             balance_confirmation=None if confirmation is None else BalanceConfirmation(**confirmation),
                             storage_prices=None if prices is None else StoragePrices(**prices), **fields)
    except TypeError as exc:
        raise DurabilityError(f"the provider configuration is malformed ({exc})") from None
    return RunPodProvider(built, **options)
