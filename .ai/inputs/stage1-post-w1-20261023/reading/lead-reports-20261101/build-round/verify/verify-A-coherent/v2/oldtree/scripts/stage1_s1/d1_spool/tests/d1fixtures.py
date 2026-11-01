"""Shared helpers for the D-1 tests: scaled settings (REQ-6's and D-1's, with a synthetic world's pins), the base module
with those settings, a D-1 build, and an independent brute-force k. Synthetic data only (scripts/stage1/tests'
s1fixtures_b3b worlds); nothing real is read."""

from __future__ import annotations

import copy
import dataclasses
import json
import random

from scripts.stage1 import s1common as s1
from scripts.stage1_s1.d1_spool import d1_s_pool as d1m

import s1fixtures_b3b as fw

W1_SETTINGS_PATH = d1m.w1_root() / "scripts" / "stage1" / "settings" / "build_s_pool.json"


def committed_d1() -> dict:
    return json.loads(d1m.SETTINGS_PATH.read_bytes())


def committed_w1() -> dict:
    return json.loads(W1_SETTINGS_PATH.read_bytes())


def scaled(world, *, s1n=3, s3=25, s4=6, decoy=3, k_min=3, k_below=1) -> tuple[dict, dict]:
    """REQ-6's settings with the world's pins and smaller lists, and D-1's settings scaled the same way: the planned
    S3 subset size s3 (1,000), min_pool = s1n + s4 + decoy (597), k_min (48), the fallback threshold k_below (600)."""
    w1 = world.settings(committed_w1(), s1=s1n, s3_subset=s3, s4_candidates=s4, decoy_rows=decoy, min_pool=s3)
    d1 = copy.deepcopy(committed_d1())
    d1["planned_s3_subset_size"] = s3
    d1["min_pool"] = s1n + s4 + decoy
    d1["k_min"] = k_min
    d1["fallback"]["k_below"] = k_below
    return w1, d1


def with_settings(base: d1m.Base, w1: dict) -> d1m.Base:
    return dataclasses.replace(base, settings=w1, settings_sha256="e" * 64)


def d1_build(world, base: d1m.Base, w1: dict, d1: dict, d1_sha256: str = "d" * 64):
    return d1m.build(config_path=world.config_path, sources_root=world.sources_root, prepared_root=world.prepared_root,
                     anchors_path=world.anchors_path, rec_path=world.recipe_path, codec=world.sfx.fixture_codec(),
                     base=with_settings(base, w1), d1=d1, d1_sha256=d1_sha256)


def w1_build(world, w1: dict):
    """The W1 file itself (the normal import), for byte comparisons."""
    from scripts.stage1 import build_s_pool as bsp

    return bsp.build(config_path=world.config_path, sources_root=world.sources_root, prepared_root=world.prepared_root,
                     anchors_path=world.anchors_path, rec_path=world.recipe_path, codec=world.sfx.fixture_codec(),
                     settings=w1, settings_sha256="e" * 64)


def brute_k(pool_ids: list[str], s1n: int, s4n: int, planned: int, decoy: int) -> int | None:
    """The largest k <= min(planned, N) with at least decoy rows outside S1, the first k of s3.subset and S4, by trying
    every k from the top with set unions (an independent form of the rule, without k_min)."""
    s1_ids = s1.sealed_order(pool_ids, "s1.order")[:s1n]
    s4_ids = s1.sealed_order(sorted(set(pool_ids) - set(s1_ids)), "s4.order")[:s4n]
    order = s1.sealed_order(pool_ids, "s3.subset")
    for k in range(min(planned, len(pool_ids)), -1, -1):
        if len(pool_ids) - len(set(s1_ids) | set(s4_ids) | set(order[:k])) >= decoy:
            return k
    return None


def records(n: int, seed: int = 1) -> list[dict]:
    rng = random.Random(seed)
    return [fw.refusal_record(rng, swap=(i % 3 == 0)) for i in range(n)]


def world_of(root, n: int, seed: int = 1, **kw):
    return fw.SWorld(root, {"pku_one": records(n, seed)}, **kw)
