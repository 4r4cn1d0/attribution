"""Data preparation on ENGINEERING FIXTURE rows: hashes, exclusions, leakage, determinism,
freezing and the retained-example sampler. Standard library only."""

from __future__ import annotations

import json

import pytest

from experiments.minimal_safety import data
from experiments.minimal_safety.common import sha256_bytes


def test_raw_hash_mismatch_is_refused(bundle):
    config, train, ref = bundle
    with pytest.raises(data.HashMismatch):
        data.parse_raw(train, "0" * 64, "train")
    with pytest.raises(data.HashMismatch):
        data.prepare(config, train + b"\n", ref)  # one extra byte changes the pinned hash


def test_exclusions_and_dedupe_are_counted_before_sampling(bundle):
    config, train, ref = bundle
    manifest, rows_bytes = data.prepare(config, train, ref)
    assert manifest["raw"]["train"] == {"rows": 52, "blank_lines": 0,
                                        "by_type": {"Benign": 35, "Safety-Aligned": 6, "Unsafe": 11}}
    assert manifest["raw"]["ref"]["rows"] == 9 and manifest["raw"]["ref"]["blank_lines"] == 1
    assert manifest["exclusions"]["train"] == {"rows": 5, "by_reason": {
        "control_string": 1, "empty_prompt": 1, "empty_response": 1, "ref_data_id_overlap": 1,
        "ref_prompt_overlap": 1}}
    assert manifest["exclusions"]["ref"]["rows"] == 0
    assert manifest["prompt_duplicates_dropped"]["train"] == {
        "rows": 1, "by_type": {"Benign": 1}, "same_normalized_response": 1}
    assert manifest["prompt_duplicates_dropped"]["ref"]["rows"] == 1
    assert manifest["eligible"] == {"train_by_type": {"Benign": 30, "Safety-Aligned": 6, "Unsafe": 10},
                                    "ref": 8}
    assert manifest["source_ids"]["train_data_ids_shared_with_ref"] == 1
    excluded = {f"train:{n:05d}" for n in range(47, 53)} | {"ref:00010"}  # rule cases, ref dupe
    used = {u for uids in manifest["roles"].values() for u in uids}
    assert not used & excluded
    assert not {r["uid"] for r in map(json.loads, rows_bytes.decode().splitlines())} & excluded


def test_roles_composition_removal_group_and_untouched_reference(bundle):
    config, train, ref = bundle
    manifest, rows_bytes = data.prepare(config, train, ref)
    rows = [json.loads(line) for line in rows_bytes.decode().splitlines()]
    by_uid = {r["uid"]: r for r in rows}
    roles = manifest["roles"]
    assert {k: len(v) for k, v in roles.items()} == {"train": 14, "holdout": 2, "query": 2, "eval": 2}
    assert len(manifest["ref_untouched"]) == 4
    types = [by_uid[u]["type"] for u in roles["train"]]
    assert {t: types.count(t) for t in data.TYPES} == {"Benign": 8, "Safety-Aligned": 2, "Unsafe": 4}
    assert all(by_uid[u]["type"] == "Benign" for u in roles["holdout"])
    group = manifest["removal_group"]["uids"]
    assert len(group) == 2 and set(group) <= set(roles["train"])
    assert all(by_uid[u]["type"] == "Unsafe" and by_uid[u]["in_removal_group"] for u in group)
    assert sum(r["in_removal_group"] for r in rows) == 2
    assert {r["source"] for r in rows if r["role"] in ("query", "eval")} == {"ref"}
    # Untouched reference rows are listed by ID only; their text never reaches the rows file.
    raw_ref = {f"ref:{n:05d}": json.loads(line)
               for n, line in enumerate(ref.decode().split("\n"), start=1) if line.strip()}
    text = rows_bytes.decode()
    for item in manifest["ref_untouched"]:
        assert raw_ref[item["uid"]]["prompt"] not in text
        assert item["uid"] not in by_uid
    unsafe = manifest["enrichment"]["Unsafe"]
    assert unsafe["raw_fraction"] == pytest.approx(11 / 52)
    assert unsafe["calibration_fraction"] == pytest.approx(4 / 14)
    assert unsafe["factor"] == pytest.approx((4 / 14) / (11 / 52))


def test_leakage_check_detects_shared_normalized_prompts_and_uids():
    train = [{"uid": "train:00001", "prompt": "Hello   World"}]
    with pytest.raises(data.LeakageError, match="normalized prompt"):
        data.check_leakage({"train": train, "eval": [{"uid": "ref:00001", "prompt": "hello world"}]})
    with pytest.raises(data.LeakageError, match="uid"):
        data.check_leakage({"train": train, "holdout": [{"uid": "train:00001", "prompt": "other"}]})
    with pytest.raises(data.LeakageError, match="reference prompt"):
        data.check_leakage({"train": train}, ref_prompts={"hello world"})
    data.check_leakage({"train": train, "eval": [{"uid": "ref:00001", "prompt": "different"}]})


def test_preparation_is_deterministic_and_frozen(tmp_path, bundle):
    config, train, ref = bundle
    first, second = data.prepare(config, train, ref), data.prepare(config, train, ref)
    assert first == second
    digest = data.write_prepared(tmp_path, *first)
    assert data.write_prepared(tmp_path, *first) == digest  # identical rewrite is a no-op
    other = json.loads(json.dumps(config))
    other["design"]["design_seed"] = 12
    with pytest.raises(data.DataError, match="frozen"):
        data.write_prepared(tmp_path, *data.prepare(other, train, ref))
    manifest, rows, loaded = data.load_prepared(tmp_path, digest)
    assert loaded == digest and len(rows) == 20
    with pytest.raises(data.DataError, match="pinned"):
        data.load_prepared(tmp_path, "f" * 64)


def test_tampered_prepared_files_are_refused(tmp_path, bundle):
    config, train, ref = bundle
    digest = data.write_prepared(tmp_path, *data.prepare(config, train, ref))
    rows_path = tmp_path / data.ROWS_FILE
    original = rows_path.read_bytes()
    rows_path.write_bytes(original.replace(b"benign answer", b"benign ANSWER", 1))
    with pytest.raises(data.DataError, match="rows file"):
        data.load_prepared(tmp_path, digest)
    rows_path.write_bytes(original)
    manifest_path = tmp_path / data.MANIFEST_FILE
    manifest_path.write_bytes(manifest_path.read_bytes().replace(b'"design_seed": 11', b'"design_seed": 13'))
    with pytest.raises(data.DataError, match="frozen hash"):
        data.load_prepared(tmp_path)


def test_removed_rows_never_sampled_and_arms_share_order():
    uids = [f"train:{i:05d}" for i in range(1, 41)]
    removed = set(uids[::5])
    for seed in (1, 2, 3):
        a0 = data.training_stream(uids, set(), seed, 100)  # more than two epochs
        cut = data.training_stream(uids, removed, seed, 100)
        assert len(a0) == len(cut) == 100
        assert not removed & set(cut)
        assert set(a0[:40]) == set(uids)  # epoch 1 of a0 is a permutation of all rows
        kept_epoch1 = [u for u in a0[:40] if u not in removed]
        assert cut[:len(kept_epoch1)] == kept_epoch1  # same order, removed rows deleted
        assert data.training_stream(uids, removed, seed, 100) == cut
    assert data.training_stream(uids, set(), 1, 40) != data.training_stream(uids, set(), 2, 40)
    with pytest.raises(data.DataError):
        data.training_stream(uids, {"train:99999"}, 1, 5)
    with pytest.raises(data.DataError):
        data.training_stream(uids[:2], set(uids[:2]), 1, 5)


def test_stream_plan_reports_exposure_and_divergence(bundle):
    config, train, ref = bundle
    manifest, _ = data.prepare(config, train, ref)
    plan = data.stream_plan(manifest, config)
    group = set(manifest["removal_group"]["uids"])
    for seed in config["train"]["seeds"]:
        s = plan[str(seed)]
        a0, cut = s["a0"]["uids"], s["remove_fixture2"]["uids"]
        seen = [u in group for u in a0]
        assert s["a0"]["removed_seen"] == {"short": sum(seen[:2]), "long": sum(seen)}
        expected = next((i + 1 for i, hit in enumerate(seen) if hit), None)
        assert s["first_divergence_step"] == expected
        assert not group & set(cut)


def test_hash_helper_matches_fixture(bundle):
    config, train, _ = bundle
    assert config["dataset"]["train_sha256"] == sha256_bytes(train)
