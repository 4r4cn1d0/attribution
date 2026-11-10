"""R2 Track R re-verifier's probes (scratch only; ENGINEERING FIXTURES)."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import refs_fixtures as rf  # noqa: E402

from scripts.scale78b import make_refs_settings_78b as mk  # noqa: E402
from scripts.scale78b import refs_78b as rw  # noqa: E402

ONE_B = re.compile(r"K\s*=\s*39|K=39|Gate A|optional certification reference|K = 24|12 of 112")


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    return rf.ea_world(tmp_path_factory.mktemp("rrv"))


def test_A_terms_beside_a_pre_existing_output_that_b10_refused(world, tmp_path):
    out = tmp_path / "regen"
    out.mkdir()
    (out / "something.txt").write_bytes(b"made earlier, not by this command")
    code, _, err = rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", out])
    terms = tmp_path / ("regen" + rw.TERMS_SUFFIX)
    doc = json.loads(terms.read_bytes()) if terms.exists() else None
    print("A", code, terms.exists(), doc and (doc["command"], doc["exit"], doc["output"]))
    assert code == 2 and terms.exists()          # a record beside an output this command did not write


def test_B_lambda_zero_runs_through_the_wrapper_and_its_terms_say_none_runs(world, tmp_path):
    regen = tmp_path / "regen"
    assert rf.wrapped(world, ["regenerate", *rf.common(world), "--seed", rf.SEED, "--out", regen])[0] == 0
    out = tmp_path / "s0"
    code, _, err = rf.wrapped(world, ["evaluate", *rf.common(world), "--source-run", regen / "run", "--out", out,
                                      "--mode", "scale", "--lambda", "0", *fb.cert_args(world.cert)])
    terms = json.loads((tmp_path / ("s0" + rw.TERMS_SUFFIX)).read_bytes()) if code == 0 else {}
    job = json.loads((out / "job.json").read_bytes()) if code == 0 else {}
    print("B", code, job.get("mode"), job.get("adapter_scale"), "no lambda = 0 B10 unit runs" in terms.get("terms", {}).get("lambda = 0", ""))
    assert code == 0 and job["adapter_scale"] == 0.0


def test_C_b11_records_with_the_derived_7_8b_prose(tmp_path):
    """The derived 7-8B B11 prose (Llama 1105) in the tiny fixture's settings: check, vcheck and transform records hold
    no 1B term and carry the 7-8B measure text."""
    import b11_fixtures as fx11
    t = fx11.build_tiny(tmp_path / "tiny")
    derived = json.loads((mk.SETTINGS_DIR / "safe_lora__llama31-8b__1105.json").read_bytes())
    doc = copy.deepcopy(t.doc)
    doc["adapter"]["accepted"] = {str(rf.SEED): {"fingerprint": t.fingerprint}}
    doc["v_diagnostic"] = {**doc["v_diagnostic"], **{k: derived["v_diagnostic"][k] for k in
                                                       ("measure", "v_prime", "rule", "when", "outcomes")}}
    for p in ("default", "conditional", "certify"):
        doc["transform"]["points"][p]["status"] = derived["transform"]["points"][p]["status"]
    refs = rf.Refs(tmp_path / "fam")
    refs.manifest = "a" * 64
    rf.o78.oext_inputs(tmp_path / "oext", refs, branch="pending_w1_18")
    refs.put("safe_lora", doc)
    refs.put("eval_adapter", b"{}")
    blob = []
    for command, extra in (("check", ()), ("vcheck", ()), ("transform", ("--point", "default")),
                           ("transform", ("--point", "certify"))):
        out = tmp_path / f"{command}-{len(blob)}"
        code, o, err = rf.call(rw.main, ["safe_lora", *refs.refs_leading(), command, "--adapter", str(t.adapter_file),
                                         "--seed", str(rf.SEED), "--aligned", str(t.aligned), "--base", str(t.base),
                                         "--out", str(out), *extra])
        assert code == 0, err[-300:]
        blob += [p.read_text("utf-8") for p in out.rglob("*.json")] + [o]
    text = "\n".join(blob)
    hits = sorted(set(ONE_B.findall(text)))
    print("C", len(blob), "1B hits:", hits, "K = 78 of 224 in records:", "K = 78 of 224" in text)
    assert not hits and "K = 78 of 224" in text


def test_D_b10_records_with_the_derived_prose(world, tmp_path):
    """The derived 7-8B B10 prose (Llama 1105's certification, exit, outputs, regeneration, oext texts) in the fixture
    settings: a gated run's files (the compare report included) hold no 1B term."""
    derived = json.loads((mk.SETTINGS_DIR / "eval_adapter__llama31-8b__1105.json").read_bytes())
    refs = world.refs
    changes = {"certification__gate": derived["certification"]["gate"],
               "certification__failure_action": derived["certification"]["failure_action"],
               "certification__reference_rule": derived["certification"]["reference_rule"],
               "regeneration__rule": derived["regeneration"]["rule"], "oext__rule": derived["oext"]["rule"],
               "untuned_unit__role": derived["untuned_unit"]["role"]}
    doc = rf.ea_doc(world, refs, **changes)
    refs.put("eval_adapter", doc)
    try:
        code, o, err = rf.wrapped(world, ["run", *rf.common(world), "--seed", rf.SEED, "--regen-out", tmp_path / "r",
                                          "--eval-root", tmp_path / "e", "--evaluations", "certify",
                                          "--gate-reference-eval", fb.eval_dir(world.unit)])
    finally:
        refs.put("eval_adapter", world.doc)
    assert code == 0, err[-300:]
    files = [p for p in tmp_path.rglob("*") if p.is_file() and p.suffix in (".json", ".jsonl", ".txt")]
    text = "\n".join(p.read_text("utf-8", "replace") for p in files if not p.name.endswith(rw.TERMS_SUFFIX)) + o
    hits = sorted(set(ONE_B.findall(text)))
    print("D", len(files), "1B hits (outside the terms records):", hits)
    assert not hits
