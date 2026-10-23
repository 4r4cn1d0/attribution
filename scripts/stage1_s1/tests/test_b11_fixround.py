"""B11 fix round (notes/B11-verify.md S2 and S3), on tiny synthetic snapshots.

S2: the "certify" point (K = 0) makes REF R.1.4's certification run through B10's file path: the transform command
writes the source adapter (the same fingerprint; the same bytes for an engine-saved file) with a record that carries
B10's four fields. It is never a reference point, so the $0 check reports the default and conditional points only.

S3: both commands write safe_lora_timing.json (REF section C.9: "the record gives the measured value"), with the
stage seconds, apart from the record so that the record stays byte-identical on a re-run."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import b11_fixtures as fx
import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1_s1 import safe_lora as sl


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    return fx.build_tiny(tmp_path_factory.mktemp("tiny-fixround"))


@pytest.fixture()
def cli(tiny, tmp_path, monkeypatch):
    path, digest = fx.write_settings_file(tmp_path, tiny.doc)
    monkeypatch.setattr(sl, "SETTINGS_PATH", path)
    monkeypatch.setattr(sl, "SETTINGS_SHA256", digest)
    return tmp_path


def _args(tiny, command, out, *extra):
    return [command, "--adapter", str(tiny.state_dir), "--seed", fx.SEED, "--aligned", str(tiny.aligned),
            "--base", str(tiny.base), "--out", str(out), *extra]


def _fake_clock(monkeypatch, values):
    """sl._clock returns these values in turn, then the last one again (never an exception)."""
    it = iter(values)
    monkeypatch.setattr(sl, "_clock", lambda: next(it, values[-1]))


# ----- S2: the certify point -------------------------------------------------------------------------------------


def test_the_settings_certify_point_is_k_zero_and_never_a_reference_point(tiny):
    assert tiny.settings.points["certify"] == 0
    assert tiny.settings.point_status["certify"].startswith("never a reference point")
    doc = copy.deepcopy(tiny.doc)
    doc["transform"]["points"]["certify"]["k"] = 1
    with pytest.raises(sl.Refusal, match="certify point maps nothing"):
        fx.settings_of(doc)


def test_the_certify_point_maps_nothing_and_returns_the_source_adapter(tiny):
    source = sl.read_adapter(tiny.state_dir)
    result = fx.hook(tiny, point="certify")(source.tensors, source=source)
    assert result.mapped == [] and result.fingerprint == tiny.fingerprint
    assert result.adapter_bytes == tiny.adapter_file.read_bytes()
    record = result.record
    assert set(record["points"]) == {"certify"}
    point = record["points"]["certify"]
    assert (point["k"], point["mapped"], point["kth_cosine"], point["boundary_ties"], point["rho_of_mapped"]) == (
        0, [], None, 0, None)
    assert point["next_cosine"] == min(m["cosine"] for m in record["matrices"])
    assert point["status"] == tiny.settings.point_status["certify"]
    assert all(m["mapped"] == {"certify": False} for m in record["matrices"])
    assert record["output"]["point"] == "certify" and record["output"]["k"] == 0
    assert record["output"]["replaced_lora_b"] == [] and record["output"]["identical_to_source_bytes"] is True
    assert record["output"]["fingerprint"] == record["input_adapter"]["fingerprint"] == tiny.fingerprint


def test_the_command_line_certify_point_writes_the_source_bytes_with_b10s_fields(tiny, cli):
    out = cli / "certify"
    assert sl.main(_args(tiny, "transform", out, "--point", "certify")) == 0
    data = (out / "adapter.safetensors").read_bytes()
    assert data == tiny.adapter_file.read_bytes()
    record = json.loads((out / "safe_lora_record.json").read_bytes())
    fields = {key: _dotted(record, path) for key, path in sl.B10_RECORD_KEYS.items()}
    assert fields == {"transform_sha256": sha256_file(Path(sl.__file__).resolve()),
                      "source_adapter_fingerprint": tiny.fingerprint, "output_adapter_fingerprint": tiny.fingerprint,
                      "output_file_sha256": sha256_bytes(data), "transform_settings_sha256": tiny.settings.sha256}
    assert fields["output_file_sha256"] == sha256_file(tiny.adapter_file)
    assert record["output"]["identical_to_source_bytes"] is True and record["output"]["replaced_lora_b"] == []


def test_the_check_reports_the_two_reference_points_only(tiny, cli):
    record = fx.hook(tiny, point=None).check(tiny.adapter)
    assert tuple(record["points"]) == sl.CHECK_POINTS == ("default", "conditional")
    assert all(set(m["mapped"]) == set(sl.CHECK_POINTS) for m in record["matrices"])
    out = cli / "check"
    assert sl.main(_args(tiny, "check", out)) == 0
    assert set(json.loads((out / "safe_lora_check.json").read_bytes())["points"]) == set(sl.CHECK_POINTS)


def _dotted(record: dict, path: str):
    node = record
    for part in path.split("."):
        node = node[part]
    return node


# ----- S3: the timing file ---------------------------------------------------------------------------------------


def test_the_transform_timing_file_gives_each_stage_and_names_the_files(tiny, cli, monkeypatch, capsys):
    _fake_clock(monkeypatch, [10.0, 11.5, 14.0, 20.0])
    out = cli / "timed"
    assert sl.main(_args(tiny, "transform", out, "--point", "default")) == 0
    printed = json.loads(capsys.readouterr().out)
    timing_bytes = (out / "safe_lora_timing.json").read_bytes()
    timing = json.loads(timing_bytes)
    assert timing_bytes == canonical_json(timing)
    seconds = {"read_adapter": 1.5, "hash_snapshots": 2.5, "transform": 6.0, "total": 10.0}
    assert timing["seconds"] == seconds == printed["seconds"]
    assert (timing["kind"], timing["version"], timing["command"], timing["point"], timing["seed"]) == (
        sl.TIMING_KIND, 1, "transform", "default", fx.SEED)
    assert timing["torch_threads"] == 1 and timing["settings_sha256"] == sl.SETTINGS_SHA256
    assert timing["outputs"] == {"adapter.safetensors": sha256_file(out / "adapter.safetensors"),
                                 "safe_lora_record.json": sha256_file(out / "safe_lora_record.json")}
    assert printed["written"] == {p.name: sha256_file(p) for p in out.iterdir()}
    assert len(printed["written"]) == 3


def test_the_check_timing_file_names_the_check_record(tiny, cli, monkeypatch, capsys):
    _fake_clock(monkeypatch, [0.0, 0.25, 0.75, 2.0])
    out = cli / "check-timed"
    assert sl.main(_args(tiny, "check", out)) == 0
    printed = json.loads(capsys.readouterr().out)
    timing = json.loads((out / "safe_lora_timing.json").read_bytes())
    assert timing["seconds"] == {"read_adapter": 0.25, "hash_snapshots": 0.5, "transform": 1.25, "total": 2.0}
    assert timing["seconds"] == printed["seconds"]
    assert (timing["command"], timing["point"]) == ("check", None)
    assert timing["outputs"] == {"safe_lora_check.json": sha256_file(out / "safe_lora_check.json")}


def test_the_real_clock_gives_non_negative_stages_that_sum_to_the_total(tiny, cli):
    out = cli / "real"
    assert sl.main(_args(tiny, "transform", out, "--point", "conditional")) == 0
    seconds = json.loads((out / "safe_lora_timing.json").read_bytes())["seconds"]
    parts = [seconds["read_adapter"], seconds["hash_snapshots"], seconds["transform"]]
    assert set(seconds) == {"read_adapter", "hash_snapshots", "transform", "total"}
    assert all(isinstance(x, float) and x >= 0.0 for x in parts + [seconds["total"]])
    assert abs(sum(parts) - seconds["total"]) <= 0.002 and seconds["transform"] > 0.0


def test_the_record_and_adapter_stay_byte_identical_on_a_re_run_whatever_the_time(tiny, cli, monkeypatch):
    _fake_clock(monkeypatch, [0.0, 1.0, 2.0, 3.0])
    assert sl.main(_args(tiny, "transform", cli / "one", "--point", "default")) == 0
    _fake_clock(monkeypatch, [5.0, 7.0, 11.0, 13.0])
    assert sl.main(_args(tiny, "transform", cli / "two", "--point", "default")) == 0
    for name in ("adapter.safetensors", "safe_lora_record.json"):
        assert (cli / "one" / name).read_bytes() == (cli / "two" / name).read_bytes()
    assert (cli / "one" / "safe_lora_timing.json").read_bytes() != (cli / "two" / "safe_lora_timing.json").read_bytes()
    record = json.loads((cli / "one" / "safe_lora_record.json").read_bytes())
    assert "seconds" not in json.dumps(record)


def test_a_refusal_writes_no_timing_file(tiny, cli):
    bad = _args(tiny, "transform", cli / "refused", "--point", "default")
    bad[bad.index("--seed") + 1] = "1102"
    assert sl.main(bad) == 2 and not (cli / "refused").exists()
