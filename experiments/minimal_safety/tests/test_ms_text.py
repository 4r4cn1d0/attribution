"""Label masking, truncation with reserved response space, no-target rejection and text
diagnostics, on integer ENGINEERING FIXTURES. Standard library only."""

from __future__ import annotations

import pytest

from experiments.minimal_safety.text import (IGNORE_INDEX, NoTargets, assemble, copy_fraction,
                                             encode_example, encode_prompt, refusal_flag)

HEAD, TAIL, END = [900, 901], [902, 903], 999


def test_only_response_and_end_tokens_are_labelled():
    ex = assemble("u", HEAD + [1, 2, 3], len(HEAD), TAIL, [7, 8, END], max_len=64, reserve=8)
    assert list(ex.input_ids) == HEAD + [1, 2, 3] + TAIL + [7, 8, END]
    assert ex.n_target == 3 and ex.prompt_len == 7
    assert ex.labels() == [IGNORE_INDEX] * 7 + [7, 8, END]
    assert not ex.prompt_truncated and not ex.response_truncated


def test_long_prompt_is_cut_from_its_end_keeping_template_and_reserved_targets():
    ex = assemble("u", HEAD + list(range(1, 101)), len(HEAD), TAIL, [7, 8, 9, END], max_len=20,
                  reserve=4)
    assert len(ex.input_ids) == 20 and ex.prompt_truncated and not ex.response_truncated
    assert list(ex.input_ids[:2]) == HEAD and list(ex.input_ids[14:16]) == TAIL
    assert list(ex.input_ids[2:14]) == list(range(1, 13))  # beginning of the user text kept
    assert ex.labels()[-4:] == [7, 8, 9, END]


def test_truncation_keeps_at_least_the_head_even_when_the_join_merged():
    # 777 stands for a token merging the head's last character with the user text's first.
    merged = [900, 777] + list(range(1, 50))
    ex = assemble("u", merged, 2, TAIL, [7, END], max_len=6, reserve=2)
    assert list(ex.input_ids) == [900, 777] + TAIL + [7, END] and ex.prompt_truncated


def test_long_response_is_cut_last_and_loses_its_end_token():
    target = list(range(10, 60)) + [END]
    ex = assemble("u", HEAD + [1, 2], len(HEAD), TAIL, target, max_len=30, reserve=8)
    assert len(ex.input_ids) == 30 and ex.response_truncated and not ex.prompt_truncated
    assert ex.n_target == 24 and END not in ex.input_ids[ex.prompt_len:]
    both = assemble("u", HEAD + list(range(1, 200)), len(HEAD), TAIL, target, max_len=30, reserve=8)
    assert both.prompt_truncated and both.response_truncated and both.n_target == 8


def test_no_targets_and_oversized_template_are_rejected():
    with pytest.raises(NoTargets):
        assemble("u", HEAD + [1], len(HEAD), TAIL, [], max_len=64, reserve=8)
    with pytest.raises(ValueError, match="template"):
        assemble("u", HEAD + [1], len(HEAD), TAIL, [7, END], max_len=5, reserve=2)


def test_encode_example_appends_end_token_and_prompt_has_assistant_header(codec):
    ex = encode_example(codec, "u", "hi", "ok", max_len=96, reserve=16)
    assert list(ex.input_ids[-3:]) == [ord("o"), ord("k"), codec.end_id] and ex.n_target == 3
    assert list(ex.input_ids[:ex.prompt_len]) == codec.encode_turn("hi") + list(codec.tail_ids)
    ids, cut = encode_prompt(codec, "hi" * 100, max_prompt_len=40)
    assert cut and len(ids) == 40 and tuple(ids[-len(codec.tail_ids):]) == codec.tail_ids
    assert tuple(ids[:len(codec.head_ids)]) == codec.head_ids


def test_refusal_and_copy_diagnostics():
    assert refusal_flag("I’m sorry, but I can’t help with that.")
    assert refusal_flag("As an AI, I will not do this")
    assert not refusal_flag("Sure, here is a recipe for bread.")
    prompt = "please repeat the following words back to me exactly"
    assert copy_fraction(prompt, "repeat the following words back to me", 5) == 1.0
    assert copy_fraction(prompt, "an entirely new answer about some other topic", 5) == 0.0
    assert copy_fraction(prompt, "too short", 5) is None
