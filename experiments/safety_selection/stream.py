"""Training streams and checkpoint positions (stdlib only).

Each epoch shuffles the FULL sorted corpus with a (seed, epoch) stream and then drops the
arm's removed rows, so all arms of a seed share one order, removal deletes rows (retained rows
move forward) instead of masking steps, and every retained row appears exactly once per epoch.
An optimizer step takes ``micro_batch * grad_accum`` consecutive examples of one epoch's order;
an epoch's final step keeps its actual (possibly smaller) size and steps never cross epochs.
Removing rows therefore shortens every epoch and the total number of steps: that is part of
the intervention. A checkpoint at ``p/q`` epochs is the first optimizer boundary at or after
``ceil(frac * retained)`` examples of the current epoch; the actual example count is reported.

An edit arm (``edits.py``) may also add rows. They are not part of the shuffled corpus, so the
retained rows keep the seed's shared order; each epoch they are inserted by the edit's stated
position rule (``edits.POSITION_RULE``). A plan with an edit records the edit's hash and its
added rows in its identity; a plan without one has exactly the identity it had before.
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
    added: tuple[str, ...] = ()          # an edit's added row ids, sorted (module doc)
    edit_sha256: str | None = None

    @property
    def effective_batch(self) -> int:
        return self.micro_batch * self.grad_accum

    @property
    def retained(self) -> int:
        return len(self.corpus) - len(self.removed) + len(self.added)

    def retained_rows(self) -> list[str]:
        """Every row an epoch trains, sorted."""
        return sorted((set(self.corpus) - self.removed) | set(self.added))

    @property
    def steps_per_epoch(self) -> int:
        return _ceil_div(self.retained, self.effective_batch)

    def epoch_order(self, epoch: int) -> list[str]:
        """Retained rows of one epoch in training order."""
        order = list(self.corpus)
        random.Random(derive_seed(self.seed, "data-order", epoch)).shuffle(order)
        kept = [row for row in order if row not in self.removed]
        if not self.added:
            return kept
        extra = list(self.added)
        random.Random(derive_seed(self.seed, "added-order", epoch)).shuffle(extra)
        out, start, n, m = [], 0, len(kept), len(extra)
        for j, row in enumerate(extra):
            cut = (j + 1) * n // (m + 1)
            out.extend(kept[start:cut])
            out.append(row)
            start = cut
        out.extend(kept[start:])
        return out

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
        out = {"seed": self.seed, "corpus_sha256": sha256_bytes(canonical_json(list(self.corpus))),
               "corpus_rows": len(self.corpus), "removed": sorted(self.removed),
               "retained": self.retained, "micro_batch": self.micro_batch,
               "grad_accum": self.grad_accum, "steps_per_epoch": self.steps_per_epoch,
               "order": "random.Random(derive_seed(seed, 'data-order', epoch)).shuffle(sorted corpus), "
                        "then removed rows dropped"}
        if self.edit_sha256 is not None:     # only edit arms: plans without an edit keep their identity
            out.update(edit_sha256=self.edit_sha256, added=list(self.added),
                       added_order="each epoch, the added rows sorted by id are shuffled with "
                                   "derive_seed(seed, 'added-order', epoch) and added row j of m goes after "
                                   "the floor((j + 1) * n / (m + 1))-th of the n retained rows")
        return out

    def sha256(self) -> str:
        return sha256_bytes(canonical_json(self.identity()))


def make_plan(corpus: Sequence[str], removed: Sequence[str] | frozenset[str], seed: int,
              micro_batch: int, grad_accum: int, added: Sequence[str] = (),
              edit_sha256: str | None = None) -> StreamPlan:
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
    extra = tuple(sorted(added))
    if len(set(extra)) != len(extra) or set(extra) & set(rows):
        raise StreamError("added rows must be distinct and must not be training rows")
    if (extra or edit_sha256 is not None) and edit_sha256 is None:
        raise StreamError("added rows come only from an edit, whose hash the plan records")
    return StreamPlan(seed, rows, gone, micro_batch, grad_accum, extra, edit_sha256)


def micro_batches(examples: Sequence, micro_batch: int) -> list[list]:
    return [list(examples[i:i + micro_batch]) for i in range(0, len(examples), micro_batch)]
