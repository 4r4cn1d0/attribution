"""Training streams and checkpoint positions (stdlib only).

Each epoch shuffles the FULL sorted corpus with a (seed, epoch) stream and then drops the
arm's removed rows, so all arms of a seed share one order, removal deletes rows (retained rows
move forward) instead of masking steps, and every retained row appears exactly once per epoch.
An optimizer step takes ``micro_batch * grad_accum`` consecutive examples of one epoch's order;
an epoch's final step keeps its actual (possibly smaller) size and steps never cross epochs.
Removing rows therefore shortens every epoch and the total number of steps: that is part of
the intervention. A checkpoint at ``p/q`` epochs is the first optimizer boundary at or after
``ceil(frac * retained)`` examples of the current epoch; the actual example count is reported.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from fractions import Fraction
from typing import Iterator, Sequence

from .common import canonical_json, derive_seed, sha256_bytes

__all__ = ["StreamError", "StreamPlan", "make_plan", "micro_batches"]


class StreamError(ValueError):
    pass


def _ceil_div(a: int, b: int) -> int:
    return -(-a // b)


@dataclass(frozen=True)
class StreamPlan:
    seed: int
    corpus: tuple[str, ...]  # every training row id, sorted
    removed: frozenset[str]
    micro_batch: int
    grad_accum: int

    @property
    def effective_batch(self) -> int:
        return self.micro_batch * self.grad_accum

    @property
    def retained(self) -> int:
        return len(self.corpus) - len(self.removed)

    @property
    def steps_per_epoch(self) -> int:
        return _ceil_div(self.retained, self.effective_batch)

    def epoch_order(self, epoch: int) -> list[str]:
        """Retained rows of one epoch in training order."""
        order = list(self.corpus)
        random.Random(derive_seed(self.seed, "data-order", epoch)).shuffle(order)
        return [row for row in order if row not in self.removed]

    def locate(self, step: int) -> tuple[int, int]:
        """(epoch, 0-based step within the epoch) of a 1-based global optimizer step."""
        if step < 1:
            raise StreamError("optimizer steps are 1-based")
        return divmod(step - 1, self.steps_per_epoch)

    def examples_seen(self, step: int) -> int:
        """Examples consumed after ``step`` optimizer steps (0 at step 0)."""
        epochs, within = divmod(step, self.steps_per_epoch)
        return epochs * self.retained + min(within * self.effective_batch, self.retained)

    def iterate(self, first: int, last: int) -> Iterator[tuple[int, int, list[str]]]:
        """(step, epoch, examples) for 1-based steps first..last inclusive."""
        cached: tuple[int, list[str]] | None = None
        for step in range(first, last + 1):
            epoch, within = self.locate(step)
            if cached is None or cached[0] != epoch:
                cached = (epoch, self.epoch_order(epoch))
            start = within * self.effective_batch
            yield step, epoch, cached[1][start:start + self.effective_batch]

    def checkpoint(self, epochs: Fraction) -> dict:
        """Optimizer boundary for ``epochs`` (a non-negative fraction)."""
        epochs = Fraction(epochs)
        if epochs < 0:
            raise StreamError("checkpoint epochs must be non-negative")
        full = epochs.numerator // epochs.denominator
        rest = epochs - full
        if rest == 0:
            step = full * self.steps_per_epoch
        else:
            target = max(1, _ceil_div(rest.numerator * self.retained, rest.denominator))
            step = full * self.steps_per_epoch + _ceil_div(target, self.effective_batch)
        return {"epochs": [epochs.numerator, epochs.denominator], "step": step,
                "examples_seen": self.examples_seen(step),
                "completed_epochs": step // self.steps_per_epoch}

    def identity(self) -> dict:
        return {"seed": self.seed, "corpus_sha256": sha256_bytes(canonical_json(list(self.corpus))),
                "corpus_rows": len(self.corpus), "removed": sorted(self.removed),
                "retained": self.retained, "micro_batch": self.micro_batch,
                "grad_accum": self.grad_accum, "steps_per_epoch": self.steps_per_epoch,
                "order": "random.Random(derive_seed(seed, 'data-order', epoch)).shuffle(sorted corpus), "
                         "then removed rows dropped"}

    def sha256(self) -> str:
        return sha256_bytes(canonical_json(self.identity()))


def make_plan(corpus: Sequence[str], removed: Sequence[str] | frozenset[str], seed: int,
              micro_batch: int, grad_accum: int) -> StreamPlan:
    rows = tuple(sorted(corpus))
    if len(set(rows)) != len(rows):
        raise StreamError("training row ids must be distinct")
    gone = frozenset(removed)
    if not gone <= set(rows):
        raise StreamError("removed rows must be training rows")
    if len(gone) >= len(rows):
        raise StreamError("no retained training rows")
    if micro_batch < 1 or grad_accum < 1:
        raise StreamError("micro_batch and grad_accum must be positive")
    return StreamPlan(seed, rows, gone, micro_batch, grad_accum)


def micro_batches(examples: Sequence, micro_batch: int) -> list[list]:
    return [list(examples[i:i + micro_batch]) for i in range(0, len(examples), micro_batch)]
