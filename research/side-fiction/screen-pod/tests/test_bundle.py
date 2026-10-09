"""The dry bundle build on the real inputs, its contents, its secret scan, the pod-side verification (in this process
and with the bundle's own code in the pod layout), the refill round's plan, and the pins that refuse."""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys
import tarfile

import pytest
from conftest import (P, R, SB, SP, make_refill, needs_real, refill_rows_from_real, sha, text_samples, assert_no_text,
                      all_files)
from common import Refusal

PY = sys.executable


def dry(tmp_path, *extra, tag="sp-dry1", round_=1, out=None):
    out = out or tmp_path / f"dry-{tag}"
    code = SP.main(["bundle", "--tag", tag, "--round", str(round_), "--out", str(out), *extra])
    return code, out


def extract(tar: pathlib.Path, dest: pathlib.Path) -> pathlib.Path:
    dest.mkdir(parents=True, exist_ok=True)
    with tarfile.open(tar) as t:
        t.extractall(dest, filter="data")
    return dest / "bundle"


@needs_real
def test_dry_bundle_round1_is_deterministic_and_holds_only_the_listed_files(tmp_path, capsys):
    code, out = dry(tmp_path)
    assert code == 0
    record = json.loads((out / "bundle-record.json").read_bytes())
    code2, out2 = dry(tmp_path, out=tmp_path / "again")
    assert code2 == 0
    assert (out / "bundle.tar.gz").read_bytes() == (out2 / "bundle.tar.gz").read_bytes()      # deterministic
    assert record["bundle_sha256"] == sha((out / "bundle.tar.gz").read_bytes())
    assert record["rows"] == {"dark": 5000, "light": 5000, "dolly": 4800}
    assert record["work"] == {"granite_rows": 10000, "granite_calls": 20000, "qwen_rows": 14800, "ka_calls": 200,
                              "resumed": {"granite": 0, "qwen": 0}}
    assert record["inputs"] == {k: v[0] for k, v in P.DATA_PINS.items()}
    assert record["known_answer"]["n"] == 200 and record["known_answer"]["mac_yes"] == 93
    assert record["documents"] == {"spec_sha256": P.SPEC_SHA256, "rules_v2_sha256": P.RULES_SHA256}
    assert record["launcher_sha256"] == P.LAUNCHER_PINS
    assert record["cap_hours"] == 5.0 and record["cost_upper_usd"] == 9.25 and record["planning_price"] == 1.85
    with tarfile.open(out / "bundle.tar.gz") as t:
        names = t.getnames()
        assert all(m.mtime == 0 and m.uid == 0 and m.gid == 0 for m in t.getmembers())
    files = {n[len("bundle/"):] for n in names if n.startswith("bundle/") and not n.endswith("/")}
    manifest = json.loads(tarfile.open(out / "bundle.tar.gz").extractfile("bundle/job-manifest.json").read())
    assert files - {"job-manifest.json"} == set(manifest["files"])
    tops = {f.split("/")[0] for f in files}
    assert tops == {"tool", "gate_b", "engine", "data", "ka", "prepared", "job-manifest.json"}
    assert {f for f in files if f.startswith("prepared/")} == {f"prepared/{P.PREPARED_NAME}/manifest.sha256",
                                                               f"prepared/{P.PREPARED_NAME}/banks/dev.jsonl"}
    assert not [f for f in files if not f.startswith("engine/") and ("hidden" in f or "selector" in f)]
    assert not [f for f in files if f.endswith("/manifest.json") or "__pycache__" in f or f.endswith(".pyc")]
    assert all(pathlib.PurePosixPath(f).suffix in P.ENGINE_SUFFIXES for f in files if f.startswith("engine/"))
    assert {f for f in files if f.startswith("ka/")} == {"ka/mac-labels.json", "ka/unit/job.json",
                                                         "ka/unit/COMPLETE.json", "ka/unit/eval/e1/generations.jsonl"}
    assert {f for f in files if f.startswith("data/")} == {"data/dark.jsonl", "data/light.jsonl",
                                                           "data/dolly-train_rows.jsonl"}
    assert {f[len("tool/"):] for f in files if f.startswith("tool/")} == set(SB.TOOL_FILES)
    mac_labels = json.loads(tarfile.open(out / "bundle.tar.gz").extractfile("bundle/ka/mac-labels.json").read())
    assert set(mac_labels) == {"unit", "complete_sha256", "source_sha256", "labels", "answer_sha256"}
    assert sum(v == "Yes" for v in mac_labels["labels"].values()) == 93
    index = [json.loads(x) for x in (out / "rows-index.jsonl").read_bytes().split(b"\n") if x.strip()]
    assert len(index) == 14800 and set(index[0]) == set(R.INDEX_FIELDS)
    io_ = capsys.readouterr()
    assert_no_text([io_.out, io_.err, *(p.read_bytes() for p in all_files(out))], text_samples())


@needs_real
def test_bundle_secret_scan_passes_and_a_planted_secret_refuses(tmp_path, monkeypatch):
    code, out = dry(tmp_path)
    assert code == 0
    with tarfile.open(out / "bundle.tar.gz") as t:                 # an independent scan of every member
        for m in t.getmembers():
            if m.isfile():
                content = t.extractfile(m).read().decode("utf-8", "ignore")
                assert not [n for n, pat in SP.JP.SECRET_PATTERNS.items() if pat.search(content)], m.name
    real_copy = SB._copy

    def planting(src, stage, rel, files, expect=None):
        got = real_copy(src, stage, rel, files, expect)
        if rel == "tool/screen_pins.py":
            (stage / rel).write_text((stage / rel).read_text() + "\n# hf_" + "A" * 34 + "\n")
        return got
    monkeypatch.setattr(SB, "_copy", planting)
    code, out2 = dry(tmp_path, out=tmp_path / "planted")
    assert code == 2 and not (out2 / "bundle.tar.gz").exists()


@needs_real
def test_pod_side_verify_accepts_the_bundle_and_refuses_every_change(tmp_path):
    code, out = dry(tmp_path)
    bundle = extract(out / "bundle.tar.gz", tmp_path / "pod")
    manifest = SB.verify_bundle(bundle)
    assert manifest["round"] == 1 and manifest["limit"] is None
    ka_items, mac = SB.pod_ka(bundle, manifest)
    assert len(ka_items) == 200 and [i[0] for i in ka_items] == sorted(mac) and sum(v == "Yes" for v in mac.values()) == 93
    for damage in ("data", "stray", "missing", "labels", "engine", "gate_b"):
        b = tmp_path / f"pod-{damage}"
        shutil.copytree(bundle, b)
        if damage == "data":
            (b / "data/dark.jsonl").write_bytes((b / "data/dark.jsonl").read_bytes() + b"\n")
        elif damage == "stray":
            (b / "data/extra.jsonl").write_text("{}\n")
        elif damage == "missing":
            (b / "data/light.jsonl").unlink()
        elif damage == "labels":
            (b / "ka/mac-labels.json").write_text("{}")
        elif damage == "engine":
            p = b / "engine/experiments/safety_selection/prepare_task.py"
            p.write_text(p.read_text() + "\n")
        elif damage == "gate_b":
            (b / "gate_b/units.py").write_text((b / "gate_b/units.py").read_text() + "\n")
        with pytest.raises(Refusal):
            SB.verify_bundle(b)


@needs_real
def test_the_bundles_own_code_runs_in_the_pod_layout(tmp_path):
    """screen_job.py from the unpacked bundle, by path, in a fresh isolated interpreter (as on the pod): it imports the
    bundle's gate_b and engine copies, verifies the bundle, and status and sums print whitelisted fields only."""
    code, out = dry(tmp_path)
    root = tmp_path / "remote"
    bundle = extract(out / "bundle.tar.gz", root)
    env = {"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"}
    done = subprocess.run([PY, "-I", "-B", "bundle/tool/screen_job.py", "verify", "--bundle", "bundle"], cwd=root,
                          capture_output=True, text=True, env=env, timeout=300)
    assert done.returncode == 0, done.stderr[-1500:]
    line = json.loads(done.stdout.strip().splitlines()[-1])
    assert line["event"] == "bundle_verified" and line["rows"] == {"dark": 5000, "light": 5000, "dolly": 4800}
    probe = ("import sys; sys.path.insert(0, 'bundle/tool'); import screen_pins as P, screen_rows as R; "
             "import common, experiments.safety_selection.prepare_task as pt; "
             "print(P.ON_POD, common.__file__, pt.__file__, R.render_user_text is pt.render_user_text)")
    done = subprocess.run([PY, "-I", "-B", "-c", probe], cwd=root, capture_output=True, text=True, env=env, timeout=120)
    on_pod, common_file, pt_file, same = done.stdout.split()
    assert on_pod == "True" and same == "True"
    assert pathlib.Path(common_file).resolve().is_relative_to((bundle / "gate_b").resolve())
    assert pathlib.Path(pt_file).resolve().is_relative_to((bundle / "engine").resolve())
    for cmd in ("status", "sums"):
        done = subprocess.run([PY, "-I", "-B", "bundle/tool/screen_job.py", cmd, "--root", str(root)], cwd=root,
                              capture_output=True, text=True, env=env, timeout=120)
        assert done.returncode == 0
        got = json.loads(done.stdout)
        assert set(got) == ({"started", "step", "done", "progress"} if cmd == "status" else {"files"})
    assert not list(root.rglob("__pycache__"))


@needs_real
def test_refill_round_plan_reads_sf_screen_rows_and_requires_its_report(tmp_path):
    rows = refill_rows_from_real()
    path, digest = make_refill(tmp_path / "screen", 2, rows)
    planned = SB.plan(2, path, digest)
    got = planned["sources"]["refill"]["rows"]
    assert len(got) == len(rows) == 12 and [r.rank for r in got[:2]] == [1, 2] and got[0].slot_line == 10
    assert planned["refill"]["script_is_pinned_sf_screen"] is True
    code, out = dry(tmp_path, "--refill", str(path), "--refill-sha256", digest, round_=2, tag="sp-dry2")
    assert code == 0
    record = json.loads((out / "bundle-record.json").read_bytes())
    assert record["rows"] == {"refill": 12} and record["work"]["granite_calls"] == 24 and record["work"]["qwen_rows"] == 12
    assert record["cap_hours"] == 1.5                                   # 3600 + 224 x 0.4 + 12 x 0.25 + 900 s = 1.28 h
    with pytest.raises(Refusal, match="round 1 takes no refill"):
        SB.plan(1, path, digest)
    with pytest.raises(Refusal, match="need --refill"):
        SB.plan(2, path, None)
    with pytest.raises(Refusal, match="not the pinned"):
        SB.plan(2, path, "0" * 64)
    with pytest.raises(Refusal, match="refill-r3.jsonl"):
        SB.plan(3, path, digest)
    path2, digest2 = make_refill(tmp_path / "noreport", 2, rows, report=False)
    with pytest.raises(Refusal, match="no readable refill-r2-report.json"):
        SB.plan(2, path2, digest2)
    path3, digest3 = make_refill(tmp_path / "badreport", 2, rows, output={"file": "refill-r2.jsonl", "rows": 11,
                                                                          "sha256": "x"})
    with pytest.raises(Refusal, match="does not name"):
        SB.plan(2, path3, digest3)


@needs_real
def test_changed_spec_rules_or_launcher_refuse_before_any_bundle(tmp_path, monkeypatch):
    for name in ("SPEC", "RULES"):
        original = getattr(P, name)
        changed = tmp_path / original.name
        changed.write_bytes(original.read_bytes() + b"\n")
        monkeypatch.setattr(P, name, changed)
        code, out = dry(tmp_path, out=tmp_path / f"changed-{name}")
        assert code == 2 and not (out / "bundle.tar.gz").exists()
        with pytest.raises(Refusal, match="checked against the changed document"):
            SB.check_documents()
        monkeypatch.setattr(P, name, original)
    assert SB.check_documents() == {"spec_sha256": P.SPEC_SHA256, "rules_v2_sha256": P.RULES_SHA256}
    fake_gate_b = tmp_path / "gate_b"
    shutil.copytree(P.MAC_GATE_B, fake_gate_b, ignore=shutil.ignore_patterns("__pycache__", "tests"))
    (fake_gate_b / "pod/podhost.py").write_text((fake_gate_b / "pod/podhost.py").read_text() + "\n")
    with pytest.raises(Refusal, match="pod/podhost.py"):
        SP.launcher_pins(fake_gate_b)
    assert SP.launcher_pins() == P.LAUNCHER_PINS


@needs_real
def test_limit_and_cap_rules(tmp_path):
    code, out = dry(tmp_path, "--limit", "5", tag="sp-dry5")
    record = json.loads((out / "bundle-record.json").read_bytes())
    assert record["work"]["granite_calls"] == 20 and record["work"]["qwen_rows"] == 15 and record["cap_hours"] == 1.5
    assert dry(tmp_path, "--cap-hours", "1.0", out=tmp_path / "low")[0] == 2           # below the planned upper time
    assert dry(tmp_path, "--cap-hours", "7", out=tmp_path / "high")[0] == 2            # above 6 h
    assert SP.main(["bundle", "--tag", "fscreen-1", "--round", "1", "--out", str(tmp_path / "t")]) == 2   # not sp-
    w = {"ka_calls": 200, "granite_calls": 20000, "qwen_rows": 14800}
    hours, need = SP.cap_hours_for(w, None, P.GRANITE_S_PER_CALL, P.QWEN_S_PER_ROW)
    assert (hours, round(need, 2)) == (5.0, 4.52)
    est = SP.estimate(w)
    assert est["minutes"][0] < est["minutes"][1] and est["usd"][1] < hours * 1.85
