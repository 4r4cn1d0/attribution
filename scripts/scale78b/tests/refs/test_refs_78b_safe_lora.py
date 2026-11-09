"""refs_78b.py safe_lora on ENGINEERING FIXTURES (b11_fixtures' tiny OLMo-2 pair and adapter): the wrapper runs the
unchanged B11 script with a family's per-seed settings file and writes the 1B script's files (parity with the 1B main
run as the 1B tests run it, its two settings globals set to the same file); the record names the module that ran and
the family file's SHA-256, which B10's Safe LoRA pin takes; the globals are restored; refusals exit 2 and write
nothing. None of these numbers is a scientific result."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import b11_fixtures as fx11  # noqa: E402
import refs_fixtures as rf  # noqa: E402

from experiments.safety_selection.common import sha256_file  # noqa: E402
from scripts.scale78b import refs_78b as rw  # noqa: E402
from scripts.stage1_s1 import safe_lora as sl  # noqa: E402

SEED = str(rf.SEED)


@pytest.fixture(scope="module")
def tiny(tmp_path_factory):
    """The tiny pair and adapter, with the settings refit to seed 1102 (the reference seed) in a family folder."""
    base = tmp_path_factory.mktemp("refs-sl")
    t = fx11.build_tiny(base / "tiny")
    doc = copy.deepcopy(t.doc)
    doc["adapter"]["accepted"] = {SEED: {"fingerprint": t.fingerprint}}
    refs = rf.Refs(base / "fam")
    refs.manifest = "a" * 64
    rf.o78.oext_inputs(base / "oext", refs, branch="pending_w1_18")
    refs.put("safe_lora", doc)
    refs.put("eval_adapter", b"{}")
    return rf.SimpleNamespace(t=t, doc=doc, refs=refs, base=base)


def argv(tiny, command: str, out: Path, *extra) -> list[str]:
    return [command, "--adapter", str(tiny.t.adapter_file), "--seed", SEED, "--aligned", str(tiny.t.aligned),
            "--base", str(tiny.t.base), "--out", str(out), *extra]


def wrapped(tiny, args):
    return rf.call(rw.main, ["safe_lora", *tiny.refs.refs_leading(), *args])


def direct(tiny, args):
    path, digest = tiny.refs.files["safe_lora"]
    with rf.ox.patched([(sl, "SETTINGS_PATH", path), (sl, "SETTINGS_SHA256", digest)]):
        return rf.call(sl.main, args)


@pytest.mark.parametrize("command, extra", [("transform", ("--point", "default")), ("transform", ("--point", "certify")),
                                            ("check", ()), ("vcheck", ())])
def test_parity_with_the_1b_main(tiny, tmp_path, command, extra):
    out = tmp_path / "out"
    c1, o1, e1 = direct(tiny, argv(tiny, command, out, *extra))
    assert c1 == 0, e1[-300:]
    out.rename(tmp_path / "direct")
    c2, o2, e2 = wrapped(tiny, argv(tiny, command, out, *extra))
    assert c2 == 0, e2[-300:]
    timing = tiny.doc["outputs"]["timing"]
    cmp = rf.compare(tmp_path / "direct", out, {n for n in rf.o78.tree(out) if n != timing})
    assert cmp[timing] in ("bytes", "parsed"), cmp
    p1, p2 = json.loads(o1), json.loads(o2)
    assert {k: v for k, v in p1["written"].items() if k != timing} == \
        {k: v for k, v in p2["written"].items() if k != timing}
    assert json.loads(e2.splitlines()[0])["settings"] == {"safe_lora": tiny.refs.files["safe_lora"][1]}


def test_the_record_names_the_module_that_ran_and_the_family_file(tiny, tmp_path):
    out = tmp_path / "t"
    assert wrapped(tiny, argv(tiny, "transform", out, "--point", "default"))[0] == 0
    record = json.loads((out / tiny.doc["outputs"]["record"]).read_bytes())
    assert record["provenance"]["script"] == "scripts/stage1_s1/safe_lora.py"
    assert record["provenance"]["script_sha256"] == rw.CODE[rw.SL] == sha256_file(Path(sl.__file__).resolve())
    assert record["provenance"]["settings_sha256"] == tiny.refs.files["safe_lora"][1]
    assert sl.SETTINGS_SHA256 not in json.dumps(record)                 # the 1B settings are never named
    entry = rf.sl_entry(tiny.refs)                                        # B10's pin takes this record's settings
    assert entry["settings"]["sha256"] == record["provenance"]["settings_sha256"]
    assert entry["module_sha256"] == record["provenance"]["script_sha256"]


def test_the_globals_are_restored(tiny, tmp_path):
    before = rf.globals_now()
    assert wrapped(tiny, argv(tiny, "check", tmp_path / "a"))[0] == 0
    assert rf.globals_now() == before
    assert wrapped(tiny, argv(tiny, "check", tmp_path / "a"))[0] == 2      # never overwrites (the 1B refusal)
    assert rf.globals_now() == before
    with pytest.raises(SystemExit):
        rw.main(["safe_lora", *tiny.refs.refs_leading(), "transform", "--seed", SEED])
    assert rf.globals_now() == before


@pytest.mark.parametrize("args_of, needle", [
    (lambda t, o: [a if a != SEED else "1103" for a in argv(t, "check", o)], "is not this index's reference seed"),
    (lambda t, o: argv(t, "transform", o, "--poin", "default"), "--poin is not a full flag name"),
    (lambda t, o: argv(t, "check", o, "--point", "default"), "--point is not a full flag name of safe_lora check"),
    (lambda t, o: ["merge", "--out", str(o)], "takes the 1B command"),
    (lambda t, o: argv(t, "transform", o, "--point", "conditional"), "the Safe LoRA point 'conditional' is not run"),
    (lambda t, o: argv(t, "transform", o, "--point=conditional"), "the Safe LoRA point 'conditional' is not run"),
    (lambda t, o: argv(t, "transform", o, "--point", "k12"), "the Safe LoRA point 'k12' is not run"),
])
def test_a_refused_command_exits_2_and_writes_nothing(tiny, tmp_path, args_of, needle):
    out = tmp_path / "x"
    code, _, err = wrapped(tiny, args_of(tiny, out))
    assert code == 2 and needle in err and not out.exists(), err[-300:]


def test_a_waiting_pin_refuses_with_its_event(tiny, tmp_path):
    tiny.refs.waits = [{"pin": "HUB_READ", "event": "the fixture's Hub event", "where": ["families.x.models"],
                        "roles": ["safe_lora"], "fields": {"safe_lora": []}}]
    try:
        code, _, err = wrapped(tiny, argv(tiny, "check", tmp_path / "x"))
    finally:
        tiny.refs.waits = []
    assert code == 2 and "the pin HUB_READ is null" in err and "Hub event" in err and not (tmp_path / "x").exists()


def test_a_changed_run_file_refuses(tiny, tmp_path, monkeypatch):
    monkeypatch.setitem(rw.CODE, rw.SL, "0" * 64)
    code, _, err = wrapped(tiny, argv(tiny, "check", tmp_path / "x"))
    assert code == 2 and "the run files stay byte for byte" in err and not (tmp_path / "x").exists()


def test_a_settings_file_off_the_index_refuses(tiny, tmp_path):
    path, digest = tiny.refs.files["safe_lora"]
    leading = tiny.refs.refs_leading(files={**{r: {"file": p.name, "sha256": h}
                                               for r, (p, h) in tiny.refs.files.items() if r in rf.mk.ROLES},
                                            "safe_lora": {"file": path.name, "sha256": "2" * 64}})
    code, _, err = rf.call(rw.main, ["safe_lora", *leading, *argv(tiny, "check", tmp_path / "x")])
    assert code == 2 and "the index pins 2222" in err and not (tmp_path / "x").exists()


def test_the_flag_tables_are_the_1b_parsers():
    """EA_FLAGS and SL_FLAGS hold every option the 1B parsers define, per command, and nothing else."""
    import argparse

    from scripts.stage1_s1 import eval_adapter as ea

    sub = next(a for a in ea._parser()._actions if isinstance(a, argparse._SubParsersAction))
    got = {name: frozenset(o for act in p._actions for o in act.option_strings if o.startswith("--") and o != "--help")
           for name, p in sub.choices.items()}
    assert got == rw.EA_FLAGS
    seen = {}
    real = argparse.ArgumentParser.parse_args

    def capture(self, args=None, namespace=None):
        sub = next(a for a in self._actions if isinstance(a, argparse._SubParsersAction))
        seen.update({name: frozenset(o for act in p._actions for o in act.option_strings
                                     if o.startswith("--") and o != "--help") for name, p in sub.choices.items()})
        raise SystemExit(0)
    argparse.ArgumentParser.parse_args = capture
    try:
        with pytest.raises(SystemExit):
            sl.main(["check"])
    finally:
        argparse.ArgumentParser.parse_args = real
    assert seen == rw.SL_FLAGS



def test_the_records_parameter_texts_come_from_the_settings(tiny, tmp_path):
    """GXB R-38's premise, measured: every prose text in B11's records (the V/V' measure and rules, each point's
    status, the outcomes) is copied from the settings, and the code writes no K of its own. With every settings prose
    field replaced by a marker, no record of check, vcheck or transform names "K = 39", "39 of 112" or "Gate A"."""
    doc = copy.deepcopy(tiny.doc)
    for key in ("measure", "v_prime", "rule", "when"):
        doc["v_diagnostic"][key] = f"R2 MARKER v_diagnostic.{key}"
    doc["v_diagnostic"]["outcomes"] = {"changes": "R2 MARKER changes", "same": "R2 MARKER same"}
    for point in ("default", "conditional", "certify"):
        doc["transform"]["points"][point]["status"] = f"R2 MARKER {point}"
    refs = rf.Refs(tmp_path / "fam")
    refs.manifest = "a" * 64
    rf.o78.oext_inputs(tmp_path / "oext", refs, branch="pending_w1_18")
    refs.put("safe_lora", doc)
    refs.put("eval_adapter", b"{}")
    texts = []
    for command, extra in (("check", ()), ("vcheck", ()), ("transform", ("--point", "default"))):
        out = tmp_path / command
        code, _, err = rf.call(rw.main, ["safe_lora", *refs.refs_leading(), *argv(tiny, command, out, *extra)])
        assert code == 0, err[-300:]
        texts += [p.read_text("utf-8") for p in out.glob("*.json")]
    blob = "\n".join(texts)
    assert "R2 MARKER v_diagnostic.measure" in blob and "R2 MARKER default" in blob
    assert not any(t in blob for t in ("K = 39", "K=39", "39 of 112", "Gate A"))
