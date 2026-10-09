"""The dry bundle build on the real inputs, its contents (the lead's Granite bundle in gate_b/, staged by the lead's
own stage_bundle), its secret scan, the pod-side verification (in this process, with the bundle's own code in the pod
layout, and the lead's own pod_job.py verify through the pod's /workspace/judge/bundle link), the refill round's plan,
and the pins that refuse."""
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
import granite_pod

PY = sys.executable
LEAD_TOOL = {"common.py", "cache.py", "units.py", "judging.py", "harmbench_files.py", "granite_files.py"}
LEAD_POD = {"pod_job.py", "pod_judge.py", "bundle.py", "pod_run.sh", "judge-requirements.txt", "extend_cap.py",
            "granite_pod.py", "pod_run_granite.sh", "granite-requirements.txt"}


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
    assert record["known_answer"] == {
        "gate": "the lead's (pod_job.known_answer_gate in the lead's Granite job)", "unit": "1101-a0-e1-a1",
        "complete_sha256": P.KA_COMPLETE_SHA256, "reference_sha256": P.KA_REFERENCE_SHA256, "n": 200, "mac_yes": 93,
        "rule": {"min_identical": 190, "max_abs_delta_yes": 5, "n": 200, "mac_yes": 93}}
    assert record["documents"] == {"spec_sha256": P.SPEC_SHA256, "rules_v2_sha256": P.RULES_SHA256}
    assert record["launcher_sha256"] == P.LAUNCHER_PINS
    assert record["cap_hours"] == 5.0 and record["cost_upper_usd"] == 9.25 and record["planning_price"] == 1.85
    tokens = record["granite_tokens"]                    # the speed stop's ratio, counted from the bundle's inputs
    assert tokens["fiction_calls"] == 20000 and tokens["ka_items"] == 200
    assert 190 < tokens["fiction_mean_tokens_per_call"] < 205 and 415 < tokens["ka_mean_tokens"] < 430
    assert 0.45 < tokens["ratio"] < 0.49 and SB.check_granite_tokens(tokens) is tokens
    assert tokens["input_tokens_max"] < 8160 and tokens["trimmed_inputs"] == 0
    with tarfile.open(out / "bundle.tar.gz") as t:
        names = t.getnames()
        assert all(m.mtime == 0 and m.uid == 0 and m.gid == 0 for m in t.getmembers())
    files = {n[len("bundle/"):] for n in names if n.startswith("bundle/") and not n.endswith("/")}
    manifest = json.loads(tarfile.open(out / "bundle.tar.gz").extractfile("bundle/job-manifest.json").read())
    assert files - {"job-manifest.json"} == set(manifest["files"])
    tops = {f.split("/")[0] for f in files}
    assert tops == {"tool", "gate_b", "engine", "data", "job-manifest.json"}                 # no ka/ or prepared/
    gate = {f[len("gate_b/"):] for f in files if f.startswith("gate_b/")}
    assert {f[len("tool/"):] for f in gate if f.startswith("tool/") and f.count("/") == 1} == LEAD_TOOL
    assert {f[len("tool/pod/"):] for f in gate if f.startswith("tool/pod/")} == LEAD_POD
    assert {f for f in gate if f.startswith("granite-tokenizer/")} == {f"granite-tokenizer/{n}" for n in
                                                                       granite_pod.TOK_FILES}
    assert {f for f in gate if f.startswith("known/") and not f.startswith("known/unit/")} == {
        "known/granite-known-answers.json", f"known/prepared/{P.PREPARED_NAME}/manifest.sha256",
        f"known/prepared/{P.PREPARED_NAME}/banks/dev.jsonl"}
    assert {"known/unit/job.json", "known/unit/COMPLETE.json", "known/unit/eval/e1/generations.jsonl"} <= gate
    assert gate - {f for f in gate if f.split("/")[0] in ("tool", "granite-tokenizer", "known")} == {"job-manifest.json"}
    pinned = {f: SB.lead_pin_of(f) for f in gate if SB.lead_pin_of(f)}
    assert len(pinned) == len(LEAD_TOOL) + len(LEAD_POD) + 1                       # + the gate's reference
    assert all(manifest["files"][f"gate_b/{f}"] == P.LAUNCHER_PINS[pin] for f, pin in pinned.items())
    lead = json.loads(tarfile.open(out / "bundle.tar.gz").extractfile("bundle/gate_b/job-manifest.json").read())
    assert lead["groups"] == [] and lead["judge"]["name"] == "granite-guardian-3.3-8b" and lead["limit"] is None
    assert lead["known_answers"]["reference_sha256"] == P.KA_REFERENCE_SHA256 and lead["tokenizer_dir"] == "granite-tokenizer"
    assert manifest["gate_b"]["manifest_sha256"] == manifest["files"]["gate_b/job-manifest.json"] == (
        record["gate_b"]["manifest_sha256"])
    assert not [f for f in files if not f.startswith("engine/") and ("hidden" in f or "selector" in f)]
    assert not [f for f in files if f.endswith("/manifest.json") or "__pycache__" in f or f.endswith(".pyc")]
    assert all(pathlib.PurePosixPath(f).suffix in P.ENGINE_SUFFIXES for f in files if f.startswith("engine/"))
    assert {f for f in files if f.startswith("data/")} == {"data/dark.jsonl", "data/light.jsonl",
                                                           "data/dolly-train_rows.jsonl"}
    assert {f[len("tool/"):] for f in files if f.startswith("tool/")} == set(SB.TOOL_FILES)
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


def _relist(b: pathlib.Path, rel: str) -> None:
    """Records a changed gate_b file everywhere a forger could: the lead's manifest, the screen's manifest and the
    screen manifest's record of the lead's manifest (only the screen's pins of the lead's files are left to catch it)."""
    lead_path, screen_path = b / "gate_b/job-manifest.json", b / "job-manifest.json"
    lead = json.loads(lead_path.read_bytes())
    lead["files"][rel] = sha((b / "gate_b" / rel).read_bytes())
    lead_path.write_bytes(SB.canonical_bytes(lead))
    m = json.loads(screen_path.read_bytes())
    m["files"][f"gate_b/{rel}"] = lead["files"][rel]
    m["files"]["gate_b/job-manifest.json"] = m["gate_b"]["manifest_sha256"] = sha(lead_path.read_bytes())
    screen_path.write_bytes(SB.canonical_bytes(m))


@needs_real
def test_pod_side_verify_accepts_the_bundle_and_refuses_every_change(tmp_path):
    code, out = dry(tmp_path)
    bundle = extract(out / "bundle.tar.gz", tmp_path / "pod")
    manifest = SB.verify_bundle(bundle)
    assert manifest["round"] == 1 and manifest["limit"] is None
    lead = SB.verify_gate_b(bundle, manifest)
    assert lead["manifest_sha256"] == manifest["gate_b"]["manifest_sha256"] and lead["groups"] == []
    assert SB.ka_reference(bundle / SB.KA_REFERENCE) == SB.ka_reference(granite_pod.KNOWN_ANSWERS_FILE)
    for damage in ("data", "stray", "missing", "engine", "gate_b", "gate_b-relisted", "gate_b-reference",
                   "gate_b-manifest", "gate_b-gate-off", "tokens", "no-tokens"):
        b = tmp_path / f"pod-{damage}"
        shutil.copytree(bundle, b)
        if damage == "data":
            (b / "data/dark.jsonl").write_bytes((b / "data/dark.jsonl").read_bytes() + b"\n")
        elif damage == "stray":
            (b / "data/extra.jsonl").write_text("{}\n")
        elif damage == "missing":
            (b / "data/light.jsonl").unlink()
        elif damage == "engine":
            p = b / "engine/experiments/safety_selection/prepare_task.py"
            p.write_text(p.read_text() + "\n")
        elif damage == "gate_b":
            (b / "gate_b/tool/units.py").write_text((b / "gate_b/tool/units.py").read_text() + "\n")
        elif damage == "gate_b-relisted":                     # every listing agrees; only the lead-file pins see it
            p = b / "gate_b/tool/pod/pod_run_granite.sh"
            p.write_text(p.read_text() + "\n")
            _relist(b, "tool/pod/pod_run_granite.sh")
        elif damage == "gate_b-reference":
            p = b / "gate_b/known/granite-known-answers.json"
            p.write_bytes(p.read_bytes() + b"\n")
            _relist(b, "known/granite-known-answers.json")
        elif damage in ("gate_b-manifest", "gate_b-gate-off"):
            lead_path = b / "gate_b/job-manifest.json"
            lead_m = json.loads(lead_path.read_bytes())
            if damage == "gate_b-manifest":
                lead_m["limit"] = 5
            else:
                lead_m["known_answers"] = None
            lead_path.write_bytes(SB.canonical_bytes(lead_m))
            m = json.loads((b / "job-manifest.json").read_bytes())
            m["files"]["gate_b/job-manifest.json"] = m["gate_b"]["manifest_sha256"] = sha(lead_path.read_bytes())
            (b / "job-manifest.json").write_bytes(SB.canonical_bytes(m))
        elif damage in ("tokens", "no-tokens"):
            m = json.loads((b / "job-manifest.json").read_bytes())
            if damage == "tokens":
                m["granite_tokens"]["ratio"] = 0.2                    # no longer the quotient of the two means
            else:
                m.pop("granite_tokens")
            (b / "job-manifest.json").write_text(json.dumps(m))
        with pytest.raises(Refusal):
            SB.verify_bundle(b)


@needs_real
def test_the_bundles_own_code_runs_in_the_pod_layout(tmp_path):
    """screen_job.py from the unpacked bundle, by path, in a fresh isolated interpreter (as on the pod): it imports the
    lead's modules and the engine from the bundle, verifies the bundle, and status and sums print whitelisted fields
    only. And the pod's layout for the lead's job: /workspace/judge/bundle a link to the bundle's gate_b, where the
    lead's own pod_job.py verify (stdlib, isolated) accepts the bundle the lead's pod_run_granite.sh will run on."""
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
             "import common, granite_pod, experiments.safety_selection.prepare_task as pt; "
             "print(P.ON_POD, common.__file__, granite_pod.__file__, pt.__file__, R.render_user_text is pt.render_user_text)")
    done = subprocess.run([PY, "-I", "-B", "-c", probe], cwd=root, capture_output=True, text=True, env=env, timeout=120)
    on_pod, common_file, granite_file, pt_file, same = done.stdout.split()
    assert on_pod == "True" and same == "True"
    assert pathlib.Path(common_file).resolve().is_relative_to((bundle / "gate_b/tool").resolve())
    assert pathlib.Path(granite_file).resolve().is_relative_to((bundle / "gate_b/tool/pod").resolve())
    assert pathlib.Path(pt_file).resolve().is_relative_to((bundle / "engine").resolve())
    for cmd in ("status", "sums"):
        done = subprocess.run([PY, "-I", "-B", "bundle/tool/screen_job.py", cmd, "--root", str(root)], cwd=root,
                              capture_output=True, text=True, env=env, timeout=120)
        assert done.returncode == 0
        got = json.loads(done.stdout)
        assert set(got) == ({"started", "step", "granite_step", "done", "progress"} if cmd == "status" else {"files"})
    judge = tmp_path / "judge"                                     # screen_run.sh's links, then the lead's verify
    judge.mkdir()
    (judge / "bundle").symlink_to(bundle / "gate_b")
    (root / "granite-job").symlink_to(judge)
    done = subprocess.run([PY, "-I", "-B", "bundle/tool/pod/pod_job.py", "verify", "--bundle", "bundle"], cwd=judge,
                          capture_output=True, text=True, env=env, timeout=300)
    assert done.returncode == 0, done.stderr[-1500:]
    line = json.loads(done.stdout.strip().splitlines()[-1])
    manifest = json.loads((bundle / "job-manifest.json").read_bytes())
    assert line["event"] == "bundle_verified" and line["manifest_sha256"] == manifest["gate_b"]["manifest_sha256"]
    assert line["items"] == {"units": 0, "greedy": 0}
    assert not list(root.rglob("__pycache__")) and not list(judge.rglob("__pycache__"))


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
    assert record["granite_tokens"]["fiction_calls"] == 24 and record["granite_tokens"]["ka_items"] == 200
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
    for rel in ("pod/podhost.py", "pod/granite_pod.py", "granite_files.py", "pod/PARITY.md"):
        original = (fake_gate_b / rel).read_text()
        (fake_gate_b / rel).write_text(original + "\n")
        with pytest.raises(Refusal, match=rel):
            SP.launcher_pins(fake_gate_b)
        (fake_gate_b / rel).write_text(original)
    assert SP.launcher_pins() == P.LAUNCHER_PINS
    assert P.LAUNCHER_PINS["pod/PARITY.md"].startswith("c4fc455e") and len(P.LAUNCHER_PINS) == 19


@needs_real
def test_the_leads_gate_must_be_the_screens_unit_reference_and_rule(monkeypatch):
    plan = SB.lead_gate_plan()
    assert (plan["unit"].name, plan["n"], plan["mac_yes"]) == ("1101-a0-e1-a1", 200, 93)
    for name, value in (("KNOWN_ANSWER_MIN_IDENTICAL", 196), ("KNOWN_ANSWER_MAX_DELTA_YES", 3),
                        ("KNOWN_ANSWER_N", 199), ("KNOWN_ANSWERS_SHA256", "0" * 64)):
        with monkeypatch.context() as m:
            m.setattr(granite_pod, name, value)
            with pytest.raises(Refusal, match="rule"):
                SB.lead_gate_plan(lambda: plan)
    other = {**plan, "reference_sha256": "0" * 64}
    with pytest.raises(Refusal, match="1101-a0-e1-a1"):
        SB.lead_gate_plan(lambda: other)


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


@needs_real
def test_refill_report_must_name_the_pinned_refill_tool(tmp_path):
    rows = refill_rows_from_real()
    path, digest = make_refill(tmp_path / "other-tool", 2, rows, script_sha256="0" * 64)
    with pytest.raises(Refusal, match="not the pinned"):
        SB.plan(2, path, digest)
    path, digest = make_refill(tmp_path / "no-tool", 2, rows, script_sha256=None)
    with pytest.raises(Refusal, match="not the pinned"):
        SB.plan(2, path, digest)
    path, digest = make_refill(tmp_path / "pinned", 2, rows)
    assert SB.plan(2, path, digest)["refill"]["script_sha256"] == P.REFILL_TOOL_SHA256 == (
        "165f1a30126e81f8c46285415ed446c5b691d1a05ebdd0dcad2dd5224763ff0c")


@needs_real
def test_engine_identity_is_pinned_and_recorded(tmp_path, monkeypatch):
    code, out = dry(tmp_path, "--limit", "1", tag="sp-dry-engine")
    assert code == 0
    engine = json.loads((out / "bundle-record.json").read_bytes())["engine"]
    assert engine["code_sha256"] == engine["code_sha256_pinned"] == P.ENGINE_CODE_SHA256 == (
        "e49a978c5fa27c3ba4bb1570ac8b24501e09bf8db5c35e31ffba90bf775cdc06")
    assert engine["base_commit"] == "8801456" and isinstance(engine["changed_since_base"], list)
    assert len(engine["files_sha256"]) == 64 and engine["files"] == len(SB.engine_files())
    monkeypatch.setattr(P, "ENGINE_CODE_SHA256", "0" * 64)
    code, out2 = dry(tmp_path, "--limit", "1", tag="sp-dry-engine2")
    assert code == 2 and not (out2 / "bundle.tar.gz").exists()
    with pytest.raises(Refusal, match="code identity"):
        SB.engine_identity(SB.engine_files())
