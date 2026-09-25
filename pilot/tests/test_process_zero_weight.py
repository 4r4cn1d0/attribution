"""Regression: a weight-0 event never evaluates its gradient.

Before the fix, finite theta 1e308 with target -1e308 overflowed the unused gradient to inf and
0 * inf = nan made State reject the suppressed update, although that update is finite.
"""

from __future__ import annotations

import math

import numpy as np
import pytest

from pilot.process import Config, State, apply_event

R2 = 1.0 / math.sqrt(2.0)
FAMILY_A = Config("A", ((-1.0,), (0.0,), (1.0,)), (-1e308, 0.0, 1.0), beta=0.0, eta=0.5)
FAMILY_B = Config("B", ((1.0, 0.0), (0.0, 1.0), (R2, R2)), (-1e308, 0.0, 0.0), beta=0.0, eta=0.5)
CASES = pytest.mark.parametrize(("config", "theta"), [(FAMILY_A, (1e308,)), (FAMILY_B, (1e308, 0.0))],
                                ids=["A", "B"])


@CASES
def test_weight_zero_skips_an_overflowing_gradient(config, theta):
    pre = State(theta, (0.0,) * len(theta), 3)
    assert apply_event(config, pre, 0, 0.0) == State(theta, (0.0,) * len(theta), 4)
    with np.errstate(over="ignore", invalid="ignore"), pytest.raises(ValueError, match="finite"):
        apply_event(config, pre, 0, 1.0)  # the ordinary update genuinely overflows


@CASES
def test_weight_zero_keeps_momentum_decay_and_counter(config, theta):
    decayed = Config(config.family, config.phi, config.targets, config.beta, config.eta,
                     mu=0.5, weight_decay=0.1)
    momentum = (2.0,) + (0.0,) * (len(theta) - 1)
    post = apply_event(decayed, State(theta, momentum, 7), 0, 0.0)
    assert post.momentum == (1.0,) + (0.0,) * (len(theta) - 1)
    assert post.theta[0] == pytest.approx(0.95e308, rel=1e-15)
    assert post.theta[1:] == (0.0,) * (len(theta) - 1)
    assert post.counter == 8


def test_positive_weights_are_unchanged():
    pre = State((0.2,), (0.3,), 5)
    config = Config("A", ((-1.0,), (0.0,), (1.0,)), (-1.0, 0.0, 1.0), beta=3.0, eta=0.1,
                    mu=0.9, weight_decay=0.1)
    for w in (0.25, 1.0):
        m = 0.9 * 0.3 + w * (0.2 - 1.0)
        post = apply_event(config, pre, 2, w)
        assert post.momentum == (m,)
        assert post.theta == ((1.0 - 0.1 * 0.1) * 0.2 - 0.1 * m,)
