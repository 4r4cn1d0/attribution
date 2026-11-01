"""LN-15e's fallback report (addendum §27 point 2, §29, §32 point 5): synthetic inputs only; the two real inputs are
only hashed, never parsed here."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from experiments.minimal_safety import common as engine_common
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file
from scripts.stage1 import report_ln15e as rl

WORKSPACE = Path(engine_common.__file__).resolve().parents[2]     # the real repository, also under the mutation runner
REAL_A1 = ".ai/inputs/stage1-commitments-20261016/a1-variants/a1_variants.json"
REAL_DECISION = ".ai/inputs/stage1-post-w1-20261023/block-a/unpulled-outputs-a2.json"
# Hand values: the ledger's FO-04 row names c1fa6615; the brief names e897885c (full hashes typed from shasum -a 256).
A1_PIN = "c1fa6615e724bdfdc9230edc40c93b7e9a3c48b84b37451e22bae1e3dc45945e"
DECISION_PIN = "e897885c9b1aa0be016c1bc3879024ef9c599b7b414910874cb844423fea79f0"

# Synthetic FO-04 figures (hand values with full float digits, all different; V1's a1, e1 and q values differ on
# purpose; the mean identity is 0.0, as in the real file, so a figure that is falsy must still be copied).
SPEARMAN = 0.6180339887498949
JACCARD_Q_E1 = 0.3333333333333333
JACCARD_A1_Q, JACCARD_A1_E1 = 0.5714285714285714, 0.7071067811865476
MEAN_IDENTITY = 0.0
ROWS = 96
V1_A1, V1_E1, V1_Q = 0.14285714285714285, 0.875, 0.0625

# The sections that quote each figure (hand values from REV4 §9.3 item 3, DRAFT rev3 §9.3 item 3, the ledger's FO-04
# row and the first draft's §9.3 item 2, which names ρ and the q–e1 Jaccard without a value).
LEDGER, REV4, DRAFT3, DRAFT1 = ("decision ledger, row FO-04", "REV4 §9.3 item 3", "DRAFT rev3 §9.3 item 3",
                                "first draft §9.3 item 2")
QUOTED = {"spearman_q_e1": [LEDGER, REV4, DRAFT3, DRAFT1], "rows": [REV4, DRAFT3],
          "jaccard_top600_q_e1": [LEDGER, REV4, DRAFT3, DRAFT1], "jaccard_top600_a1_q": [REV4, DRAFT3],
          "jaccard_top600_a1_e1": [REV4, DRAFT3], "v1_adam_against_a1": [LEDGER, REV4, DRAFT3],
          "mean_identity_max_abs_difference": [REV4, DRAFT3]}


def a1_doc() -> dict:
    return {"kind": "stage1 A1 report-only variants", "version": 1, "rows": ROWS, "k": 600,
            "stability": {"spearman_q_e1": SPEARMAN, "jaccard_top_q_e1": JACCARD_Q_E1, "jaccard_top_q_a1": JACCARD_A1_Q,
                          "jaccard_top_e1_a1": JACCARD_A1_E1, "mean_identity_max_abs_difference": MEAN_IDENTITY},
            "adam_preconditioned_v1": {"name": "V1 (synthetic)", "spearman_unit_means_with_a1": 0.25,
                                       "jaccard_top_with": {"a1": V1_A1, "e1": V1_E1, "q": V1_Q}}}


def decision_doc() -> dict:
    return {"host": "a-2", "jobs": [12, 13, 14, 15], "kind": "stage1 unpulled outputs decision",
            "reason": "synthetic", "recorded_by": "the test", "utc": "2026-10-26T00:00:00Z"}


def put(path: Path, doc: dict) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(canonical_json(doc))
    return path


@pytest.fixture
def inputs(tmp_path, monkeypatch):
    """Synthetic inputs, with the module's pins set to their SHA-256 (the real pins are tested on their own)."""
    a1 = put(tmp_path / "in" / "a1_variants.json", a1_doc())
    dec = put(tmp_path / "in" / "unpulled-outputs-a2.json", decision_doc())
    monkeypatch.setattr(rl, "A1_VARIANTS_SHA256", sha256_file(a1))
    monkeypatch.setattr(rl, "DECISION_SHA256", sha256_file(dec))
    reads: list[Path] = []
    real_read = rl.read_input
    monkeypatch.setattr(rl, "read_input", lambda p: reads.append(p) or real_read(p))
    return {"a1": a1, "decision": dec, "out": tmp_path / "out" / "ln15e.json", "reads": reads, "root": tmp_path}


def run(capsys, a1, dec, out, *extra) -> tuple[int, str, str]:
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    code = rl.main(["--a1-variants", str(a1), "--decision", str(dec), "--out", str(out), *extra])
    captured = capsys.readouterr()
    return code, captured.out, captured.err


# ----- the pins ----------------------------------------------------------------------------------------------------


def test_the_pins_are_the_full_hashes_and_the_real_inputs_match_them():
    assert rl.A1_VARIANTS_SHA256 == A1_PIN and A1_PIN.startswith("c1fa6615")
    assert rl.DECISION_SHA256 == DECISION_PIN and DECISION_PIN.startswith("e897885c")
    assert rl.A1_VARIANTS_PATH.relative_to(rl.REPO).as_posix() == REAL_A1
    assert rl.DECISION_PATH.relative_to(rl.REPO).as_posix() == REAL_DECISION
    assert sha256_file(WORKSPACE / REAL_A1) == A1_PIN                      # hashed only
    assert sha256_file(WORKSPACE / REAL_DECISION) == DECISION_PIN


def test_the_real_pins_refuse_synthetic_inputs(tmp_path, capsys):
    a1 = put(tmp_path / "a1_variants.json", a1_doc())
    dec = put(tmp_path / "unpulled-outputs-a2.json", decision_doc())
    code, _, err = run(capsys, a1, dec, tmp_path / "o" / "r.json")
    assert code == 2 and "FO-04's pin is " + A1_PIN in err and not (tmp_path / "o" / "r.json").exists()


# ----- accept: the report --------------------------------------------------------------------------------------------


def test_writes_the_fallback_report(inputs, capsys):
    code, out, err = run(capsys, inputs["a1"], inputs["decision"], inputs["out"])
    assert code == 0 and err == ""
    data = inputs["out"].read_bytes()
    assert data == canonical_json(json.loads(data))
    doc = json.loads(data)
    assert doc["kind"] == "stage1 LN-15e report (fallback)" and doc["version"] == 1
    assert out.splitlines() == [f"wrote {inputs['out']}", f"  {sha256_bytes(data)}  ln15e.json"]
    fb = doc["fallback"]
    assert fb["taken"] is True and fb["host"] == "a-2" and fb["jobs"] == [12, 13, 14, 15]
    assert fb["units_not_retrieved"] == 4
    for words in ("ran on pod a-2 (jobs 12, 13, 14 and 15", "Its 4 units were not retrieved, because of a kit defect",
                  "no top-600 Jaccard and no Kendall τ of a re-score against the sealed A1 set exists",
                  "FO-04's figures are the stated limit."):
        assert words in fb["statement"]
    assert fb["not_available"] == ["the top-600 Jaccard of each re-score against the sealed A1 set",
                                   "the Kendall τ of each re-score against the sealed A1 set"]
    assert doc["inputs"] == {"a1_variants": {"path": str(inputs["a1"]), "sha256": sha256_file(inputs["a1"])},
                             "decision_record": {"path": str(inputs["decision"]),
                                                 "sha256": sha256_file(inputs["decision"])}}
    assert doc["decision_record"] == {"kind": "stage1 unpulled outputs decision", "host": "a-2",
                                      "jobs": [12, 13, 14, 15], "utc": "2026-10-26T00:00:00Z",
                                      "recorded_by": "the test"}
    assert doc["script"] == {"path": "scripts/stage1/report_ln15e.py", "sha256": sha256_file(Path(rl.__file__))}
    assert re.fullmatch(r"2[0-9]{3}-[01][0-9]-[0-3][0-9]T[0-2][0-9]:[0-5][0-9]:[0-5][0-9]Z", doc["utc"])
    assert inputs["reads"] == [inputs["a1"], inputs["decision"]]


def test_the_figures_are_copied_exactly(inputs, capsys):
    assert run(capsys, inputs["a1"], inputs["decision"], inputs["out"])[0] == 0
    data = inputs["out"].read_bytes()
    doc = json.loads(data)
    figures = doc["fo04_figures"]
    expected = {"spearman_q_e1": (SPEARMAN, ["stability", "spearman_q_e1"]),
                "rows": (ROWS, ["rows"]),
                "jaccard_top600_q_e1": (JACCARD_Q_E1, ["stability", "jaccard_top_q_e1"]),
                "jaccard_top600_a1_q": (JACCARD_A1_Q, ["stability", "jaccard_top_q_a1"]),
                "jaccard_top600_a1_e1": (JACCARD_A1_E1, ["stability", "jaccard_top_e1_a1"]),
                "v1_adam_against_a1": (V1_A1, ["adam_preconditioned_v1", "jaccard_top_with", "a1"]),
                "mean_identity_max_abs_difference": (MEAN_IDENTITY, ["stability", "mean_identity_max_abs_difference"])}
    assert sorted(figures) == sorted(expected) == sorted(QUOTED)
    for name, (value, source) in expected.items():
        assert figures[name]["value"] == value and type(figures[name]["value"]) is type(value)
        assert repr(figures[name]["value"]) == repr(value)
        assert figures[name]["source"] == source
        assert f'"value": {value!r}'.encode() in data                       # the same number text as the input
        assert [q["text"] for q in figures[name]["quoted_in"]] == QUOTED[name]
        assert all(isinstance(q["as"], str) and q["as"] for q in figures[name]["quoted_in"])
    assert figures["v1_adam_against_a1"]["value"] not in (V1_E1, V1_Q)
    assert doc["fo04_context"] == {"rows": ROWS, "k": 600}
    assert doc["quoted_in_files"] == {
        LEDGER: "research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md",
        REV4: "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md",
        DRAFT3: "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-DRAFT-rev3.md",
        DRAFT1: "research/experiments/2026-10-17-stage1-preregistration/stage1-preregistration-DRAFT.md"}


def test_the_quoted_texts_name_each_figure_as_rounded_in_rev4():
    """The 'as' text of each REV4 quote holds the figure as REV4 prints it (hand values from REV4 §9.3 item 3)."""
    printed = {"spearman_q_e1": "0.771", "rows": "4,800", "jaccard_top600_q_e1": "0.434",
               "jaccard_top600_a1_q": "0.630", "jaccard_top600_a1_e1": "0.709", "v1_adam_against_a1": "0.314",
               "mean_identity_max_abs_difference": "exact"}
    quotes = {name: dict(cites) for name, _, cites in rl.FIGURES}
    assert sorted(quotes) == sorted(printed)
    for name, text in printed.items():
        assert text in quotes[name][REV4] and quotes[name][REV4] == quotes[name][DRAFT3]


# ----- refuse: changed inputs ----------------------------------------------------------------------------------------


@pytest.mark.parametrize("which", ["a1", "decision"])
def test_a_changed_input_refuses(inputs, capsys, which):
    path = inputs[which]
    path.write_bytes(path.read_bytes() + b" ")                            # same JSON content, another SHA-256
    code, _, err = run(capsys, inputs["a1"], inputs["decision"], inputs["out"])
    assert code == 2 and err.startswith("REFUSED: ") and not inputs["out"].exists()
    assert ("FO-04's pin" if which == "a1" else "the §29 pin") in err


@pytest.mark.parametrize("change, words", [
    (lambda d: d.update(host="a-3"), "host a-2 and jobs 12-15"),
    (lambda d: d.update(jobs=[12, 13, 14]), "host a-2 and jobs 12-15"),
    (lambda d: d.update(jobs=[12, 13, 14, 15.0]), "host a-2 and jobs 12-15"),
    (lambda d: d.update(kind="stage1 other decision"), "not a stage-1 unpulled outputs decision"),
])
def test_the_decision_must_name_a2_and_jobs_12_to_15(inputs, capsys, monkeypatch, change, words):
    doc = decision_doc()
    change(doc)
    put(inputs["decision"], doc)
    monkeypatch.setattr(rl, "DECISION_SHA256", sha256_file(inputs["decision"]))     # past the pin: the content check
    code, _, err = run(capsys, inputs["a1"], inputs["decision"], inputs["out"])
    assert code == 2 and words in err and not inputs["out"].exists()


@pytest.mark.parametrize("change, words", [
    (lambda d: d["adam_preconditioned_v1"]["jaccard_top_with"].pop("a1"), "adam_preconditioned_v1/jaccard_top_with/a1"),
    (lambda d: d["stability"].update(spearman_q_e1=None), "stability/spearman_q_e1"),
    (lambda d: d["stability"].update(jaccard_top_q_e1=True), "stability/jaccard_top_q_e1"),
    (lambda d: d["stability"].pop("jaccard_top_q_a1"), "stability/jaccard_top_q_a1"),
    (lambda d: d["stability"].pop("jaccard_top_e1_a1"), "stability/jaccard_top_e1_a1"),
    (lambda d: d["stability"].pop("mean_identity_max_abs_difference"), "stability/mean_identity_max_abs_difference"),
    (lambda d: d["stability"].update(mean_identity_max_abs_difference="0.0"), "stability/mean_identity_max_abs"),
    (lambda d: d.pop("rows"), "holds no finite number at rows"),
    (lambda d: d.pop("stability"), "stability/spearman_q_e1"),
    (lambda d: d.update(k=300), "not top-600"),
    (lambda d: d.update(kind="stage1 other"), "not the A1 report-only variants record"),
])
def test_the_a1_record_must_hold_the_figures(inputs, capsys, monkeypatch, change, words):
    doc = a1_doc()
    change(doc)
    put(inputs["a1"], doc)
    monkeypatch.setattr(rl, "A1_VARIANTS_SHA256", sha256_file(inputs["a1"]))
    code, _, err = run(capsys, inputs["a1"], inputs["decision"], inputs["out"])
    assert code == 2 and words in err and not inputs["out"].exists()


# ----- refuse: unit and rescore/ paths (before any file is read) -------------------------------------------------------


def _valid_copy(inputs, monkeypatch, folder: Path) -> Path:
    """A copy of the synthetic a1 input inside folder, with the pin set to it: only the path rule can refuse it."""
    path = put(folder / "a1_variants.json", a1_doc())
    monkeypatch.setattr(rl, "A1_VARIANTS_SHA256", sha256_file(path))
    return path


@pytest.mark.parametrize("folder", ["rescore", "ReScore", "1102-attributes-a1", "round1", "cert", "eval", "judges",
                                    "judges-pending", "hidden", "judge-pod-1"])
def test_a_unit_or_rescore_input_refuses(inputs, capsys, monkeypatch, folder):
    a1 = _valid_copy(inputs, monkeypatch, inputs["root"] / "kit" / folder)
    code, _, err = run(capsys, a1, inputs["decision"], inputs["out"])
    assert code == 2 and "names a unit or a rescore/ path" in err
    assert inputs["reads"] == [] and not inputs["out"].exists()


def test_a_unit_folder_with_a_completion_marker_refuses(inputs, capsys, monkeypatch):
    unit = inputs["root"] / "kit" / "u7"
    a1 = _valid_copy(inputs, monkeypatch, unit / "sub")
    (unit / "COMPLETE.json").write_bytes(b"{}\n")                         # synthetic marker, never read
    code, _, err = run(capsys, a1, inputs["decision"], inputs["out"])
    assert code == 2 and "--a1-variants names a unit or a rescore/ path" in err
    assert inputs["reads"] == [] and not inputs["out"].exists()


def test_a_link_into_rescore_refuses(inputs, capsys, monkeypatch):
    target = _valid_copy(inputs, monkeypatch, inputs["root"] / "kit" / "rescore")
    link = inputs["root"] / "plain.json"
    link.symlink_to(target)
    code, _, err = run(capsys, link, inputs["decision"], inputs["out"])
    assert code == 2 and "--a1-variants names a unit or a rescore/ path" in err and inputs["reads"] == []


@pytest.mark.parametrize("argv", [
    lambda i: ["--out", str(i["root"] / "rescore" / "r.json")],
    lambda i: [f"--decision={i['root'] / '1103-attributes-a2' / 'd.json'}", "--out", str(i["out"])],
    lambda i: ["--out", str(i["out"]), "--unit", str(i["root"] / "rescore")],
    lambda i: ["--out", str(i["out"]), "--unit", str(i["root"] / "u")],
    lambda i: ["--out", str(i["out"]), str(i["root"] / "COMPLETE.json")],
])
def test_unit_arguments_refuse(inputs, capsys, argv):
    code = rl.main(argv(inputs))
    err = capsys.readouterr().err
    assert code == 2 and err.startswith("REFUSED: ") and inputs["reads"] == [] and not inputs["out"].exists()


# ----- refuse: never overwrite; the out rules ---------------------------------------------------------------------------


def test_never_overwrites(inputs, capsys):
    inputs["out"].parent.mkdir(parents=True)
    inputs["out"].write_bytes(b"an earlier report\n")
    code, _, err = run(capsys, inputs["a1"], inputs["decision"], inputs["out"])
    assert code == 2 and "never overwritten" in err and inputs["out"].read_bytes() == b"an earlier report\n"
    fresh = inputs["root"] / "out" / "fresh.json"
    assert run(capsys, inputs["a1"], inputs["decision"], fresh)[0] == 0
    first = fresh.read_bytes()
    code, _, err = run(capsys, inputs["a1"], inputs["decision"], fresh)
    assert code == 2 and "never overwritten" in err and fresh.read_bytes() == first


def test_write_new_is_exclusive(tmp_path):
    out = tmp_path / "r.json"
    assert rl.write_new(out, b"{}\n") == sha256_bytes(b"{}\n")
    with pytest.raises(rl.s1.Refusal, match="never overwritten"):
        rl.write_new(out, b"[]\n")
    assert out.read_bytes() == b"{}\n"


@pytest.mark.parametrize("make_out, words", [
    (lambda i: rl.W1_FOLDER / "ln15e" / "r.json", "W1 commitments folder"),
    (lambda i: i["root"] / "absent" / "r.json", "folder does not exist"),
    (lambda i: i["root"] / "r.txt", "is not a .json file"),
])
def test_the_out_rules(inputs, capsys, make_out, words):
    out = make_out(inputs)
    code = rl.main(["--a1-variants", str(inputs["a1"]), "--decision", str(inputs["decision"]), "--out", str(out)])
    err = capsys.readouterr().err
    assert code == 2 and words in err and not out.exists() and inputs["reads"] == []
