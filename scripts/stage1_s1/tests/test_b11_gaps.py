"""B11 test gaps found by the verifier's mutants (B11V-*; notes/B11-verify.md section 5 and Appendix A), with two
positive cases and the report-only record fields of its note N10 (B11F-*). Synthetic data only."""

from __future__ import annotations

import copy
import json
import math
import statistics

import b11_fixtures as fx
import pytest
import torch

from experiments.safety_selection.common import canonical_json, sha256_file
from scripts.stage1_s1 import safe_lora as sl


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return fx.build_tiny(tmp_path_factory.mktemp("tiny-gaps"))


@pytest.fixture(scope="module")
def check_record(tiny):
    """The check record, made once inside the first test body that asks for it (B14's convention): under a mutant
    that refuses every snapshot, the refusal is a test failure in each test, never a fixture error (the mutation
    runner counts errors as invalid runs). An exception is re-raised in each test that asks."""
    cache: dict = {}

    def get():
        if "value" not in cache:
            try:
                cache["value"] = fx.hook(tiny, point=None).check(tiny.adapter)
            except Exception as exc:                  # noqa: BLE001 - re-raised below, in each test that asks
                cache["value"] = exc
        if isinstance(cache["value"], Exception):
            raise cache["value"]
        return cache["value"]
    return get


@pytest.fixture()
def cli(tiny, tmp_path, monkeypatch):
    path, digest = fx.write_settings_file(tmp_path, tiny.doc)
    monkeypatch.setattr(sl, "SETTINGS_PATH", path)
    monkeypatch.setattr(sl, "SETTINGS_SHA256", digest)
    return tmp_path


def _args(tiny, command, adapter, out, *extra):
    return [command, "--adapter", str(adapter), "--seed", fx.SEED, "--aligned", str(tiny.aligned),
            "--base", str(tiny.base), "--out", str(out), *extra]


# ----- the verifier's seven gaps ---------------------------------------------------------------------------------


def test_gap1_an_adapter_with_another_seeds_accepted_fingerprint_refuses(tiny):
    """B11V-accept-any-seed: with two accepted seeds, seed 1101's adapter run as seed 1102 must refuse."""
    doc = copy.deepcopy(tiny.doc)
    doc["adapter"]["accepted"]["1102"] = {"fingerprint": "0" * 64}
    settings = fx.settings_of(doc)
    hook = sl.SafeLoRA(settings, tiny.aligned, tiny.base, seed=1102)
    with pytest.raises(sl.Refusal, match="accepted a0 e1 fingerprint"):
        hook(tiny.adapter)
    with pytest.raises(sl.Refusal, match="accepted a0 e1 fingerprint"):
        sl.SafeLoRA(settings, tiny.aligned, tiny.base, seed=1102, point=None).check(tiny.adapter)


def test_gap1_positive_the_seed_whose_fingerprint_it_is_accepts_it(tiny):
    """The other side: the same adapter pinned as seed 1102's is accepted as 1102 and refused as 1101."""
    doc = copy.deepcopy(tiny.doc)
    doc["adapter"]["accepted"] = {"1101": {"fingerprint": "0" * 64}, "1102": {"fingerprint": tiny.fingerprint}}
    settings = fx.settings_of(doc)
    record = sl.SafeLoRA(settings, tiny.aligned, tiny.base, seed=1102)(tiny.adapter).record
    assert record["seed"] == "1102" and record["input_adapter"]["accepted_fingerprint"] == tiny.fingerprint
    with pytest.raises(sl.Refusal, match="of seed 1101"):
        sl.SafeLoRA(settings, tiny.aligned, tiny.base, seed=1101)(tiny.adapter)


def test_gap2_the_check_command_records_the_state_folder_and_checks_it(tiny, cli):
    """B11V-check-cli-drops-source: the check command keeps the source (file and state.json hashes; state checks)."""
    out = cli / "check"
    assert sl.main(_args(tiny, "check", tiny.state_dir, out)) == 0
    record = json.loads((out / "safe_lora_check.json").read_bytes())
    file_sha = sha256_file(tiny.adapter_file)
    state_sha = sha256_file(tiny.state_dir / sl.STATE_FILE)
    assert record["input_adapter"]["file_sha256"] == file_sha
    assert record["input_adapter"]["state_json_sha256"] == state_sha
    assert record["provenance"]["inputs"]["adapter"] == file_sha
    assert record["provenance"]["inputs"]["adapter_state_json"] == state_sha
    other = fx.write_state(cli / "r-arm" / "e1", tiny.adapter, arm="R")
    assert sl.main(_args(tiny, "check", other, cli / "refused")) == 2 and not (cli / "refused").exists()


def test_gap3_rho_of_mapped_is_the_spread_over_the_mapped_matrices(check_record):
    """B11V-rho-spread-all-matrices: the PR3a number."""
    rho = {m["name"]: m["rho"] for m in check_record()["matrices"]}
    for point in sl.CHECK_POINTS:
        values = [rho[m] for m in check_record()["points"][point]["mapped"]]
        assert check_record()["points"][point]["rho_of_mapped"] == {"min": min(values), "median": statistics.median(values),
                                                                  "max": max(values)}
    assert check_record()["points"]["default"]["rho_of_mapped"] != {"min": min(rho.values()),
                                                                  "median": statistics.median(rho.values()),
                                                                  "max": max(rho.values())}


def test_gap4_the_cosines_are_the_settings_float64_formula_to_1e_12(tiny, check_record):
    """B11V-cosine-from-float32-bprime: cos and rho from the float64 B' of the float32 V (the settings' formula)."""
    aligned = sl.open_snapshot(tiny.aligned, tiny.settings.aligned, "aligned")
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    for m in check_record()["matrices"]:
        v = (aligned.weight(m["name"]).to(torch.float32) - base.weight(m["name"]).to(torch.float32)).double()
        a = tiny.adapter[sl._a(m["name"])].double()
        b = tiny.adapter[sl._b(m["name"])].double()
        new = (v @ (v.T @ b)) / torch.linalg.vector_norm(v)
        p_new, p_old = new @ a, b @ a
        cos = float((p_new * p_old).sum() / (p_new.norm() * p_old.norm()))
        assert abs(m["cosine"] - cos) <= 1e-12
        assert m["rho"] == pytest.approx(float(p_new.norm() / p_old.norm()), rel=1e-12)


def test_gap5_every_file_a_state_json_lists_is_hash_checked(tiny, tmp_path):
    """B11V-only-adapter-hash-checked: the engine's states list adapter, optimizer and rng files."""
    folder = fx.write_state(tmp_path / "s", tiny.adapter)
    (folder / "rng.safetensors").write_bytes(b"rng bytes")
    state = json.loads((folder / sl.STATE_FILE).read_bytes())
    state["files"]["rng.safetensors"] = "0" * 64
    (folder / sl.STATE_FILE).write_bytes(canonical_json(state))
    with pytest.raises(sl.Refusal, match="rng.safetensors differs from its state.json hash"):
        sl.read_adapter(folder)


def test_gap5_positive_a_state_listing_three_files_with_their_hashes_is_accepted(tiny, tmp_path):
    """The real states list adapter, optimizer and rng files; all three hashing to state.json is accepted."""
    folder = fx.write_state(tmp_path / "s", tiny.adapter)
    state = json.loads((folder / sl.STATE_FILE).read_bytes())
    for name, data in (("optimizer.safetensors", b"optimizer bytes"), ("rng.safetensors", b"rng bytes")):
        (folder / name).write_bytes(data)
        state["files"][name] = sha256_file(folder / name)
    (folder / sl.STATE_FILE).write_bytes(canonical_json(state))
    source = sl.read_adapter(folder)
    assert source.state["files"] == state["files"] and len(state["files"]) == 3
    assert source.file_sha256 == sha256_file(folder / sl.ADAPTER_FILE)


def test_gap6_the_check_records_each_points_own_mapped_flags(check_record):
    """B11V-mapped-flags-first-point-only: the per-matrix flags agree with each point's own list."""
    for point in sl.CHECK_POINTS:
        mapped = set(check_record()["points"][point]["mapped"])
        assert {m["name"] for m in check_record()["matrices"] if m["mapped"][point]} == mapped
    assert len(check_record()["points"]["conditional"]["mapped"]) == 2 != len(check_record()["points"]["default"]["mapped"])


def test_gap7_the_rounding_share_is_computed_on_the_float32_base(tiny, check_record):
    """B11V-bf16-share-of-aligned: the builder diagnostic, recomputed independently (float32 random base: share > 0)."""
    base = sl.open_snapshot(tiny.base, tiny.settings.unaligned, "unaligned")
    for m in check_record()["matrices"]:
        w = base.weight(m["name"]).to(torch.float64)
        share = float(torch.linalg.vector_norm(w - w.to(torch.float32).to(torch.bfloat16).to(torch.float64))) / m["v_norm"]
        assert share > 0 and math.isclose(m["base_bf16_rounding_share"], share, rel_tol=1e-12)


# ----- the verifier's note N10: report-only fields that no test pinned ------------------------------------------


def _spread(values):
    return {"min": min(values), "median": statistics.median(values), "max": max(values)}


def test_n10_the_summary_spreads_are_over_every_matrix(check_record):
    matrices = check_record()["matrices"]
    summary = check_record()["summary"]
    assert summary["n_matrices"] == len(matrices) == 14
    assert summary["cosine"] == _spread([m["cosine"] for m in matrices])
    assert summary["rho"] == _spread([m["rho"] for m in matrices])
    assert summary["base_bf16_rounding_share"] == _spread([m["base_bf16_rounding_share"] for m in matrices])
    assert summary["cosine"] != summary["rho"]                       # the fixture tells the two apart


def test_n10_the_module_and_block_mix_count_each_points_mapped_matrices(check_record):
    by_name = {m["name"]: m for m in check_record()["matrices"]}
    asymmetric = 0
    for point in sl.CHECK_POINTS:
        record = check_record()["points"][point]
        mapped = [by_name[name] for name in record["mapped"]]
        assert record["module_mix"] == {p: sum(m["module"] == p for m in mapped) for p in fx.TARGETS}
        assert record["block_mix"] == {str(b): sum(m["block"] == b for m in mapped) for b in range(fx.BLOCKS)}
        mix = record["module_mix"]
        asymmetric += record["block_mix"]["0"] != record["block_mix"]["1"]
        asymmetric += any(mix[p] != mix[q] for p, q in zip(fx.TARGETS, reversed(fx.TARGETS)))
    assert asymmetric >= 2                                           # a swapped count would show


def test_n10_the_record_fields_are_the_settings_lists(tiny, check_record):
    report = tiny.doc["report"]
    for m in check_record()["matrices"]:
        assert set(m) == set(report["per_matrix"])
    for point in sl.CHECK_POINTS:
        assert set(check_record()["points"][point]) == set(report["per_point"])
