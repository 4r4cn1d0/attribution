"""Token layout, label masking and simple completion diagnostics (stdlib only).

An example is ``turn + tail + target``. ``turn`` is the chat-template head and the user message
encoded TOGETHER, so a token merge across that join (e.g. a user message that starts with a
newline) is the template's own; ``tail`` is the rest of the template (it starts with the
end-of-turn special token, so no merge crosses it, and ends with the assistant header); and
``target`` is the response tokens plus the end-of-turn token, encoded separately: the boundary
generation sees, since generation prompts also end with the assistant header. Only ``target``
positions carry labels. When the sequence exceeds ``max_len``, ``min(len(target), reserve)``
positions stay reserved for the target, ``turn`` is cut from its END but never into the head
(its first ``len(head_ids)`` tokens), ``tail`` is never cut, and the target is cut last (losing
its end-of-turn token). Every cut is flagged.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Callable, Sequence

from .data import normalize

__all__ = ["IGNORE_INDEX", "Codec", "Example", "NoTargets", "assemble", "encode_example",
           "encode_prompt", "refusal_flag", "copy_fraction"]

IGNORE_INDEX = -100


class NoTargets(ValueError):
    """An example would have no response-token labels."""


@dataclass(frozen=True)
class Codec:
    """Model-specific text/token mapping (built from the real tokenizer, or a test fixture).
    ``encode_turn(prompt)`` is the template head plus the user text, encoded together;
    ``reference(prompt)``, when set, is the tokenizer's canonical generation-prompt encoding,
    which the runner compares with ``encode_turn(prompt) + tail_ids`` for every frozen prompt."""

    encode: Callable[[str], list[int]]
    decode: Callable[[Sequence[int]], str]
    encode_turn: Callable[[str], list[int]]
    head_ids: tuple[int, ...]
    tail_ids: tuple[int, ...]
    end_id: int
    stop_ids: tuple[int, ...]
    reference: Callable[[str], list[int]] | None = None


@dataclass(frozen=True)
class Example:
    uid: str
    input_ids: tuple[int, ...]
    n_target: int  # labelled positions: always the trailing n_target tokens
    prompt_truncated: bool
    response_truncated: bool

    @property
    def prompt_len(self) -> int:
        return len(self.input_ids) - self.n_target

    def labels(self) -> list[int]:
        return [IGNORE_INDEX] * self.prompt_len + list(self.input_ids[self.prompt_len:])


def assemble(uid: str, turn: Sequence[int], head_len: int, tail: Sequence[int],
             target: Sequence[int], max_len: int, reserve: int) -> Example:
    if not target:
        raise NoTargets(f"{uid}: empty target")
    room = max_len - min(len(target), reserve) - len(tail)
    if room < head_len:
        raise ValueError(f"{uid}: chat template ({head_len + len(tail)} tokens) does not fit "
                         f"max_len {max_len} with {min(len(target), reserve)} reserved target tokens")
    prompt = list(turn[:room]) + list(tail)
    kept = list(target[:max_len - len(prompt)])
    if not kept:
        raise NoTargets(f"{uid}: no target tokens fit")
    return Example(uid, tuple(prompt + kept), len(kept), len(turn) > room, len(kept) < len(target))


def encode_example(codec: Codec, uid: str, prompt: str, response: str, max_len: int,
                   reserve: int) -> Example:
    target = codec.encode(response) + [codec.end_id]
    return assemble(uid, codec.encode_turn(prompt), len(codec.head_ids), codec.tail_ids, target,
                    max_len, reserve)


def encode_prompt(codec: Codec, prompt: str, max_prompt_len: int) -> tuple[list[int], bool]:
    """Generation prompt ids (ending with the assistant header) and whether the user text was cut."""
    room = max_prompt_len - len(codec.tail_ids)
    if room < len(codec.head_ids):
        raise ValueError(f"chat template does not fit max_prompt_len {max_prompt_len}")
    turn = codec.encode_turn(prompt)
    return list(turn[:room]) + list(codec.tail_ids), len(turn) > room


_REFUSAL = re.compile(
    r"\b(?:i(?:'m| am) sorry|i apologi[sz]e|i (?:cannot|can't|can not|won't|will not)"
    r"|i(?:'m| am) (?:not able|unable) to|as an ai\b|(?:not|isn't) appropriate)",
    re.IGNORECASE)


def refusal_flag(text: str) -> bool:
    """Simple refusal-phrase match: a DIAGNOSTIC, not a validated over-refusal endpoint."""
    return bool(_REFUSAL.search(text.replace("’", "'")))


def copy_fraction(prompt: str, completion: str, n: int) -> float | None:
    """Share of the completion's word n-grams that also occur in the prompt (None if the
    completion has fewer than n words). A prompt-copying DIAGNOSTIC only."""
    p, c = normalize(prompt).split(), normalize(completion).split()
    if len(c) < n:
        return None
    grams = {tuple(p[i:i + n]) for i in range(len(p) - n + 1)}
    windows = [tuple(c[i:i + n]) for i in range(len(c) - n + 1)]
    return sum(w in grams for w in windows) / len(windows)
