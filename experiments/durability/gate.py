"""The dispatch gate (stdlib only): no next unit on a worker without the previous unit's verified
acknowledgement, and none without a valid admission lease.

``require`` is a pure check, made immediately before work is dispatched:

- every unit named as *previous* (the last attempt this worker launched, sealed or failed, and
  anything still pending) must have its acknowledgement **in the destination**, sealing the same
  bytes as the local unit. A copy in flight, a sender-side receipt or the engine's ``status.json``
  is not an acknowledgement;
- the worker's lease must exist and still cover the unit's planned seconds.

A refusal dispatches nothing. Anything that goes wrong while checking (an unreadable ledger, a
destination error) is a refusal too, never an unhandled error. Renewing a lease is an admission (``admission.AdmissionController``),
never something the gate does on its own.
"""

from __future__ import annotations

from typing import Callable, Sequence

from .admission import Lease
from .backup import Vault
from .common import Clock, GateRefused, Journal, utc_clock

__all__ = ["DispatchGate"]


class DispatchGate:
    """``lease_of(worker)`` returns the worker's current lease or None (normally
    ``AdmissionController.current_lease``)."""

    def __init__(self, vault: Vault, lease_of: Callable[[str], Lease | None], *, journal: Journal,
                 clock: Clock = utc_clock) -> None:
        self.vault, self.lease_of, self.journal, self.clock = vault, lease_of, journal, clock

    def _refuse(self, worker: str, why: str) -> None:
        self.journal.append("dispatch-refused", worker=worker, reason=why)
        raise GateRefused(why)

    def require(self, worker: str, previous: Sequence[tuple[str, str, str]] = (), needs_seconds: float = 0.0) -> Lease:
        """Refuse unless every ``(kind, recorded root, seal hash)`` in ``previous`` is acknowledged
        in the destination and the worker's lease covers ``needs_seconds`` from now. Returns the
        lease."""
        for kind, root, seal in previous:
            try:
                self.vault.check_ack(kind, root, seal)
            except Exception as exc:  # noqa: BLE001 - whatever went wrong, the unit is not known to be acknowledged
                self._refuse(worker, f"the previous unit is not acknowledged off-pod ({type(exc).__name__}): "
                                     "no next unit starts")
        try:
            lease = self.lease_of(worker)
        except Exception as exc:  # noqa: BLE001 - an unreadable ledger is no lease
            self._refuse(worker, f"the admission ledger could not be read ({type(exc).__name__})")
        if lease is None:
            self._refuse(worker, "no admission lease for this worker")
        if not lease.covers(self.clock(), needs_seconds):
            self._refuse(worker, "the admission lease has expired or does not cover the planned unit: "
                                 "a renewed admission is required")
        return lease
