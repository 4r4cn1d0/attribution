"""Deterministic pilot learning process; nothing in this module draws random numbers.

A softmax policy over K actions with features ``phi`` (K x d) is trained by
momentum SGD with decoupled weight decay on the squared loss of each event:

* family 'A' (d = 1): grad = theta - targets[a]
* family 'B':         grad = (phi[a] @ theta - targets[a]) * phi[a]

m' = mu * m + weight * grad;  theta' = (1 - eta * weight_decay) * theta - eta * m'.
The readout is score = sigmoid(q @ theta).
"""

from __future__ import annotations

import math
import numbers
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import NDArray

__all__ = [
    "Config", "State", "initial_state", "probs", "apply_event", "successors",
    "score", "intervention_pair", "canonical_config",
]

_Q_NORM_TOL = 1e-9


def _require(ok: bool, message: str) -> None:
    if not ok:
        raise ValueError(message)


def _real(name: str, value: object) -> float:
    if not isinstance(value, numbers.Real) or isinstance(value, bool):
        raise TypeError(f"{name} must be a real number, got {value!r}")
    out = float(value)
    _require(math.isfinite(out), f"{name} must be finite, got {out}")
    return out


def _unit(name: str, value: object) -> float:
    out = _real(name, value)
    _require(0.0 <= out <= 1.0, f"{name} must be in [0, 1], got {out}")
    return out


def _array(name: str, value: object, ndim: int, length: int | None = None) -> NDArray[np.float64]:
    try:
        raw = np.asarray(value)
    except ValueError as exc:  # ragged nesting
        raise ValueError(f"{name} must be a rectangular sequence of numbers") from exc
    if raw.dtype.kind not in "biuf":
        raise TypeError(f"{name} must contain real numbers, got dtype {raw.dtype}")
    arr = raw.astype(np.float64)
    _require(arr.ndim == ndim and arr.size > 0,
             f"{name} must be a non-empty {ndim}-D sequence, got shape {arr.shape}")
    _require(length is None or len(arr) == length, f"{name} must have length {length}, got {len(arr)}")
    _require(bool(np.isfinite(arr).all()), f"{name} must contain only finite values")
    return arr


@dataclass(frozen=True)
class Config:
    """Immutable process parameters; sequence inputs are stored as float tuples."""

    family: str
    phi: tuple[tuple[float, ...], ...]
    targets: tuple[float, ...]
    beta: float
    eta: float
    offsets: tuple[float, ...] | None = None  # None -> zeros
    mu: float = 0.0
    weight_decay: float = 0.0
    q: tuple[float, ...] | None = None  # None -> e1

    def __post_init__(self) -> None:
        _require(isinstance(self.family, str) and self.family in ("A", "B"),
                 f"family must be 'A' or 'B', got {self.family!r}")
        phi = _array("phi", self.phi, 2)
        k, d = phi.shape
        _require(self.family == "B" or d == 1, f"family 'A' requires d=1, got d={d}")
        targets = _array("targets", self.targets, 1, k)
        offsets = np.zeros(k) if self.offsets is None else _array("offsets", self.offsets, 1, k)
        q = np.eye(1, d)[0] if self.q is None else _array("q", self.q, 1, d)
        norm = float(np.linalg.norm(q))
        _require(abs(norm - 1.0) <= _Q_NORM_TOL, f"q must have unit norm, got {norm}")
        beta, eta, mu, decay = (_real(n, getattr(self, n)) for n in ("beta", "eta", "mu", "weight_decay"))
        _require(beta >= 0.0, f"beta must be >= 0, got {beta}")
        _require(0.0 < eta <= 1.0, f"eta must be in (0, 1], got {eta}")
        _require(0.0 <= mu < 1.0, f"mu must be in [0, 1), got {mu}")
        _require(decay >= 0.0, f"weight_decay must be >= 0, got {decay}")
        normalised = {
            "phi": tuple(map(tuple, phi.tolist())), "targets": tuple(targets.tolist()),
            "offsets": tuple(offsets.tolist()), "q": tuple(q.tolist()),
            "beta": beta, "eta": eta, "mu": mu, "weight_decay": decay,
        }
        for name, value in normalised.items():
            object.__setattr__(self, name, value)

    @property
    def n_actions(self) -> int:
        """K, the number of actions."""
        return len(self.phi)

    @property
    def dim(self) -> int:
        """d, the parameter dimension."""
        return len(self.phi[0])


@dataclass(frozen=True)
class State:
    """Immutable parameters, momentum buffer and count of events applied so far."""

    theta: tuple[float, ...]
    momentum: tuple[float, ...]
    counter: int

    def __post_init__(self) -> None:
        theta = _array("theta", self.theta, 1)
        momentum = _array("momentum", self.momentum, 1, len(theta))
        counter = self.counter
        if not isinstance(counter, numbers.Integral) or isinstance(counter, bool):
            raise TypeError(f"counter must be an integer, got {counter!r}")
        _require(counter >= 0, f"counter must be >= 0, got {counter}")
        object.__setattr__(self, "theta", tuple(theta.tolist()))
        object.__setattr__(self, "momentum", tuple(momentum.tolist()))
        object.__setattr__(self, "counter", int(counter))


def _theta(config: Config, state: State) -> NDArray[np.float64]:
    if not isinstance(state, State):
        raise TypeError(f"expected a State, got {type(state).__name__}")
    _require(len(state.theta) == config.dim,
             f"state dimension {len(state.theta)} != config dimension {config.dim}")
    return np.asarray(state.theta, dtype=np.float64)


def _action(config: Config, action: object) -> int:
    if not isinstance(action, numbers.Integral) or isinstance(action, bool):
        raise TypeError(f"action must be an integer, got {action!r}")
    a = int(action)
    _require(0 <= a < config.n_actions, f"action must be in [0, {config.n_actions}), got {a}")
    return a


def initial_state(config: Config, theta: Sequence[float]) -> State:
    """State holding `theta` with zero momentum and zero event counter."""
    arr = _array("theta", theta, 1, config.dim)
    return State(tuple(arr.tolist()), (0.0,) * config.dim, 0)


def probs(config: Config, state: State) -> NDArray[np.float64]:
    """softmax(beta * phi @ theta + offsets) with a max shift, so exp never overflows."""
    logits = config.beta * (np.asarray(config.phi) @ _theta(config, state)) + np.asarray(config.offsets)
    if not np.isfinite(logits).all():
        raise FloatingPointError(f"non-finite logits {logits}")
    z = np.exp(logits - logits.max())
    return z / z.sum()


def apply_event(config: Config, state: State, action: int, weight: float = 1.0) -> State:
    """One optimiser step on the loss of `action` with its gradient scaled by `weight`.

    Momentum decay, weight decay and the counter increment happen even when weight == 0.
    At weight 0 the gradient is not evaluated, so an overflowing unused gradient cannot turn
    the finite suppressed update into 0 * inf = nan.
    """
    theta, a, w = _theta(config, state), _action(config, action), _unit("weight", weight)
    momentum = config.mu * np.asarray(state.momentum)
    if w != 0.0:
        if config.family == "A":
            grad = theta - config.targets[a]
        else:
            phi_a = np.asarray(config.phi[a])
            grad = (float(phi_a @ theta) - config.targets[a]) * phi_a
        momentum = momentum + w * grad
    theta_next = (1.0 - config.eta * config.weight_decay) * theta - config.eta * momentum
    return State(tuple(theta_next.tolist()), tuple(momentum.tolist()), state.counter + 1)


def successors(config: Config, state: State) -> tuple[State, ...]:
    """apply_event(config, state, a) for every action a, indexed by a."""
    return tuple(apply_event(config, state, a) for a in range(config.n_actions))


def score(config: Config, state: State) -> float:
    """sigmoid(q @ theta) in overflow-free branch form (rounds to 1.0 once q @ theta > ~37)."""
    x = float(np.dot(config.q, _theta(config, state)))
    if x >= 0.0:
        return 1.0 / (1.0 + math.exp(-x))
    e = math.exp(x)
    return e / (1.0 + e)


def intervention_pair(config: Config, pre_state: State, action: int,
                      alpha: float = 1.0) -> tuple[State, State]:
    """(suppressed, ordinary) successors of `pre_state` under weights (1 - alpha, 1)."""
    alpha = _unit("alpha", alpha)
    return (apply_event(config, pre_state, action, 1.0 - alpha),
            apply_event(config, pre_state, action, 1.0))


_S2, _S104 = math.sqrt(2.0), math.sqrt(1.04)
_PHI_A = ((-1.0,), (0.0,), (1.0,))
_PHI_B1 = ((1.0, 0.0), (0.0, 1.0), (1.0 / _S2, 1.0 / _S2))
_PHI_B2 = ((1.0, 0.0), (1.0 / _S104, 0.2 / _S104), (1.0 / _S104, -0.2 / _S104))
_CANONICAL: dict[str, tuple[str, tuple[tuple[float, ...], ...], tuple[float, ...]]] = {
    "A1": ("A", _PHI_A, (-1.0, 0.0, 1.0)),
    "A2": ("A", _PHI_A, (0.0, 1.0, -1.0)),
    "A3": ("A", _PHI_A, (1.0, 0.0, -1.0)),
    "B1": ("B", _PHI_B1, (1.0, -1.0, 0.5)),
    "B2": ("B", _PHI_B2, (-1.0, 0.0, 1.0)),
}
_OPTIONAL = frozenset({"offsets", "mu", "weight_decay", "q"})


def canonical_config(name: str, beta: float, eta: float, **optional: Any) -> Config:
    """Named pilot configuration; `optional` may set offsets, mu, weight_decay and q."""
    if name not in _CANONICAL:
        raise ValueError(f"unknown config {name!r}; expected one of {sorted(_CANONICAL)}")
    unknown = sorted(set(optional) - _OPTIONAL)
    if unknown:
        raise TypeError(f"unexpected options {unknown}; allowed {sorted(_OPTIONAL)}")
    family, phi, targets = _CANONICAL[name]
    return Config(family, phi, targets, beta, eta, **optional)
