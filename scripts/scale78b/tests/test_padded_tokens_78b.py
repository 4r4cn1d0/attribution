"""padded_tokens_78b.py on synthetic fixtures only (R3 Track P; GXB R-46, O1; lead rulings P-1, P-2). A fake codec (one
token per word) stands in for the tokenizer; the prepared set is a synthetic engine ``Prepared`` held in memory and the
edits are synthetic engine edit files under pytest's tmp_path. Every fixture text holds a planted sentinel, and the
tests prove that it never reaches stdout, stderr, the record or a message. The real recipes (committed configs) are
read for their hashes and training settings only; no real prepared set, edit file or tokenizer is opened. The expected
values are computed here independently of the tool (the stream's documented order rule, re-written in this file)."""

from __future__ import annotations

import importlib
import json
import random
import sys
from fractions import Fraction
from pathlib import Path
from types import SimpleNamespace

import pytest

from experiments.safety_selection import edits as E
from experiments.safety_selection.common import derive_seed, ids_sha256
from experiments.safety_selection.config import tokenizer_of
from experiments.safety_selection.prepare import Prepared
from scripts.scale78b import encode_count_78b as ec
from scripts.scale78b import padded_tokens_78b as pt

ROOT = Path(__file__).resolve().parents[3]
KIT = ROOT / "runkit" / "stage1-78b"
SENT = "QZXJ-planted-sentinel-padded-5521"
FAMILY = "olmo2-7b"
SEEDS = tuple(range(1101, 1114))                 # R-54: every seed blocks A and B train at


class FakeCodec:
    """ENGINEERING FIXTURE: one id per whitespace word; prompt_ids adds two header ids; the end id closes a row."""

    eos_id = 2

    def __init__(self, fail_on: str | None = None):
        self.fail_on = fail_on

    def encode(self, text):
        if self.fail_on is not None and self.fail_on in text:
            raise ValueError(f"cannot encode {text}")          # a message holding the text read
        return [7 for _ in text.split()]

    def prompt_ids(self, text):
        return [5] + self.encode(text) + [6]

    def has_special(self, ids):
        return False


def ids_of(prompt: str, response: str) -> list[int]:
    c = FakeCodec()
    return c.prompt_ids(prompt) + c.encode(response) + [c.eos_id]


def row(prompt: str, response: str) -> dict:
    ids = ids_of(prompt, response)
    n_prompt = len(FakeCodec().prompt_ids(prompt))
    return {"prompt": prompt, "response": response, "prompt_tokens": n_prompt, "target_tokens": len(ids) - n_prompt,
            "token_sha256": ids_sha256(ids)}


def words(n: int, w: str = "w") -> str:
    return " ".join([w] * n)


def prepared_fixture(n: int = 300, *, equal: bool = False, family: str = FAMILY, manifest: str | None = None,
                     heldout=()) -> Prepared:
    """n synthetic training rows r-0000..; lengths vary with the row (or are all equal)."""
    rows = {}
    for i in range(n):
        p = 1 if equal else (i * 7) % 13
        r = 2 if equal else (i * 5) % 17
        rows[f"r-{i:04d}"] = row(f"{SENT} prompt {words(p)}", f"{SENT} response {words(r, 'v')}")
    return Prepared(Path("fixture"), {"data_config": {}}, manifest or ec.MANIFESTS[family], rows, [],
                    {"heldout": {"g-held": list(heldout)}}, {}, {})


def edit_doc(*, remove=(), add=(), rewrite=(), family: str = FAMILY, manifest: str | None = None, kind=None) -> dict:
    add = [{"row_id": rid, "prompt": p, "response": r} for rid, p, r in add]
    rewrite = [{"row_id": rid, "response": r} for rid, r in rewrite]
    present = [k for k, v in (("remove", remove), ("rewrite", rewrite), ("add", add)) if v]
    return {"kind": E.EDIT_KIND, "version": E.EDIT_VERSION, "name": "fixture edit", "edit_kind": kind or
            (present[0] if len(present) == 1 else "combined"), "manifest_sha256": manifest or ec.MANIFESTS[family],
            "remove": sorted(remove), "rewrite": rewrite, "add": add, "position_rule": E.POSITION_RULE,
            "counts": {"remove": len(remove), "rewrite": len(rewrite), "add": len(add)}, "provenance": {}}


def write_edit(folder: Path, name: str, doc: dict) -> tuple[Path, str]:
    folder.mkdir(parents=True, exist_ok=True)
    data = E.edit_bytes(doc)
    path = folder / name
    path.write_bytes(data)
    return path, E.sha256_bytes(data)


def added(k: int, n_words: int = 9) -> list[tuple[str, str, str]]:
    return [(f"add-{j:03d}", f"{SENT} added prompt {words(n_words + j % 4)}", f"{SENT} added answer {words(3 + j)}")
            for j in range(k)]


def recipe_tokenizer(family: str) -> dict:
    recipe = ec.load_recipe(family, None)[0]
    repo_id, revision = tokenizer_of(recipe)
    return {"repo_id": repo_id, "revision": revision, "end_of_turn_token": recipe["model"]["end_of_turn_token"]}


def context(codec=None, tokenizer=None, manifest: str | None = None):
    def make(family, prepared):
        return ec.Context(codec or FakeCodec(), tokenizer or recipe_tokenizer(family), manifest or ec.MANIFESTS[family])
    return make


def run(tmp: Path, capsys, prep: Prepared, *args: str, codec=None, tokenizer=None, manifest=None, out_name="rec.json",
        family: str = FAMILY):
    (tmp / "out").mkdir(exist_ok=True)
    out = tmp / "out" / out_name
    argv = ["--family", family, "--prepared", str(tmp / "prepared"), *args, "--out", str(out)]
    code = pt.main(argv, context=context(codec, tokenizer, manifest), loader=lambda path, pin: prep)
    o, e = capsys.readouterr()
    doc = json.loads(out.read_bytes()) if out.exists() else None
    for text in (o, e, out.read_text() if out.exists() else ""):
        assert SENT not in text and "prompt w" not in text and "response v" not in text
    return SimpleNamespace(code=code, out=o, err=e, doc=doc, path=out)


# ----- the independent expectation ---------------------------------------------------------------------------------


def lengths_of(prep: Prepared, doc: dict | None = None) -> dict[str, int]:
    out = {rid: r["prompt_tokens"] + r["target_tokens"] for rid, r in prep.train_rows.items()}
    if doc:
        for item in doc["rewrite"]:
            out[item["row_id"]] = len(ids_of(prep.train_rows[item["row_id"]]["prompt"], item["response"]))
        for item in doc["add"]:
            out[item["row_id"]] = len(ids_of(item["prompt"], item["response"]))
    return out


def expected_total(prep: Prepared, seed: int, doc: dict | None = None) -> tuple[int, int, int]:
    """(padded total over one epoch, rows, steps): the stream module's documented order (seed's data-order shuffle of
    the sorted corpus, removed rows dropped, added rows spread by the position rule), 128-row steps, 2-row
    micro-batches, each padded to its longest row."""
    lengths = lengths_of(prep, doc)
    order = sorted(prep.train_rows)
    random.Random(derive_seed(seed, "data-order", 0)).shuffle(order)
    removed = set(doc["remove"]) if doc else set()
    kept = [r for r in order if r not in removed]
    extra = sorted(item["row_id"] for item in doc["add"]) if doc else []
    if extra:
        random.Random(derive_seed(seed, "added-order", 0)).shuffle(extra)
        seq, start, n, m = [], 0, len(kept), len(extra)
        for j, rid in enumerate(extra):
            cut = (j + 1) * n // (m + 1)
            seq += kept[start:cut] + [rid]
            start = cut
        kept = seq + kept[start:]
    steps = -(-len(kept) // 128)
    total = 0
    for s in range(steps):
        batch = kept[s * 128:(s + 1) * 128]
        for i in range(0, len(batch), 2):
            pair = batch[i:i + 2]
            total += len(pair) * max(lengths[r] for r in pair)
    return total, len(kept), steps


# ----- the record ---------------------------------------------------------------------------------------------------


def test_the_record_is_k2s_form_with_the_largest_value_over_every_block_seed(tmp_path, capsys):
    prep = prepared_fixture()
    rm_doc = edit_doc(remove=[f"r-{i:04d}" for i in range(0, 300, 7)])          # 43 removed: 257 rows, 3 steps
    add_doc = edit_doc(add=added(12))                                            # 312 rows, 3 steps
    rm, rm_sha = write_edit(tmp_path / "edits", "remove.json", rm_doc)
    ad, ad_sha = write_edit(tmp_path / "edits", "add.json", add_doc)
    r = run(tmp_path, capsys, prep, "--edit", f"{rm}:{rm_sha}", "--edit", f"{ad}:{ad_sha}")
    assert r.code == 0, r.err
    doc = r.doc
    assert tuple(doc) == tuple(sorted(pt.KEYS)) and set(doc) == set(pt.KEYS)
    assert (doc["kind"], doc["version"], doc["family"]) == ("stage1-78b padded tokens record", 1, FAMILY)
    assert set(doc["edits"]) == {rm_sha, ad_sha}
    src = doc["source"]
    assert src["seeds"] == list(SEEDS) and "largest over seeds 1101-1113" in src["rule"] and "R-54" in src["rule"]
    assert src["recipe"]["config_sha256"] == ec.RECIPES[FAMILY][1] and src["manifest_sha256"] == ec.MANIFESTS[FAMILY]
    assert (src["recipe"]["micro_batch"], src["recipe"]["grad_accum"], src["recipe"]["target_checkpoint"]) == (2, 64, "e1")
    for sha, d, removed, add_n in ((rm_sha, rm_doc, 43, 0), (ad_sha, add_doc, 0, 12)):
        exp = {s: expected_total(prep, s, d) for s in SEEDS}
        totals = {s: t for s, (t, _, _) in exp.items()}
        rows, steps = exp[1101][1], exp[1101][2]
        detail = src["edits"][sha]
        assert (detail["rows"], detail["steps"], detail["removed"], detail["added"], detail["rewritten"]) == \
            (rows, steps, removed, add_n, 0)
        assert detail["padded_tokens_by_seed"] == {str(s): t for s, t in totals.items()}
        assert doc["edits"][sha] == max(totals.values()) / steps
        assert detail["largest_at_seed"] == min(s for s, t in totals.items() if t == max(totals.values()))
    assert src["edits"][rm_sha]["rows"] == 257 and src["edits"][ad_sha]["rows"] == 312
    assert "wrote rec.json" in r.out


def test_the_value_depends_on_the_seed_and_the_largest_is_taken(tmp_path, capsys):
    """P-1: with rows of unequal length the 2-row pairing depends on the seed's order, so the seven totals differ and
    the value is the largest (not the first seed's, not the smallest)."""
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001", "r-0002"]))
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    d = r.doc["source"]["edits"][sha]
    totals = [d["padded_tokens_by_seed"][str(s)] for s in SEEDS]
    assert d["seed_dependent"] is True and len(set(totals)) > 1
    assert r.doc["edits"][sha] == max(totals) / d["steps"] > min(totals) / d["steps"]
    assert max(totals) != totals[0] or min(totals) != totals[0]
    assert d["padded_tokens_by_seed"][str(d["largest_at_seed"])] == max(totals)


def test_equal_rows_give_a_seed_independent_known_answer(tmp_path, capsys):
    """Hand known answer: 300 rows of 10 tokens each (prompt 5 with its two header ids, response 4, end 1), 40 removed:
    260 rows, ceil(260 / 128) = 3 steps (128, 128, 4), no padding at all: 260 x 10 = 2,600 tokens, 2,600 / 3 per step
    at every seed."""
    prep = prepared_fixture(equal=True)
    assert set(lengths_of(prep).values()) == {10}
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=[f"r-{i:04d}" for i in range(40)]))
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    d = r.doc["source"]["edits"][sha]
    assert (d["rows"], d["steps"]) == (260, 3)
    assert d["padded_tokens_by_seed"] == {str(s): 2600 for s in SEEDS} and d["seed_dependent"] is False
    assert d["largest_at_seed"] == 1101                     # V-3: on a tie, the first seed of the tie
    assert r.doc["edits"][sha] == 2600 / 3


@pytest.mark.parametrize("removed,rows,steps", [(44, 256, 2), (43, 257, 3), (172, 128, 1), (171, 129, 2)])
def test_steps_are_ceil_rows_over_128(tmp_path, capsys, removed, rows, steps):
    """GXB O1 at the boundaries: the final, smaller step is counted and steps never cross the epoch."""
    prep = prepared_fixture()
    doc = edit_doc(remove=[f"r-{i:04d}" for i in range(removed)])
    p, sha = write_edit(tmp_path / "edits", "rm.json", doc)
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    d = r.doc["source"]["edits"][sha]
    assert (d["rows"], d["steps"]) == (rows, steps)
    assert d["padded_tokens_by_seed"] == {str(s): expected_total(prep, s, doc)[0] for s in SEEDS}


def test_a_rewrite_and_a_combined_edit_count_the_rewritten_rows(tmp_path, capsys):
    prep = prepared_fixture()
    doc = edit_doc(rewrite=[("r-0005", f"{SENT} a much longer replacement {words(40, 'x')}")],
                   remove=["r-0009"], add=added(2))
    p, sha = write_edit(tmp_path / "edits", "comb.json", doc)
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    assert r.code == 0, r.err
    d = r.doc["source"]["edits"][sha]
    assert (d["removed"], d["added"], d["rewritten"], d["rows"]) == (1, 2, 1, 301)
    assert d["padded_tokens_by_seed"] == {str(s): expected_total(prep, s, doc)[0] for s in SEEDS}


def test_the_kits_reader_takes_the_record(tmp_path, capsys, monkeypatch, kit_modules):
    """plan_tool.padded_tokens (K2's reader, imported read only from runkit/stage1-78b) reads the tool's record at its
    pin and gives each run's value by its edit's SHA-256; the a0 check record is refused there."""
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=[f"r-{i:04d}" for i in range(0, 300, 3)]))
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    assert r.code == 0
    tool = kit_plan_tool(monkeypatch)
    monkeypatch.setattr(tool, "ROOT", tmp_path)
    monkeypatch.setitem(tool.r78.METHOD_EDITS[FAMILY], "A1", {"path": ".ai/inputs/test/a1.json", "sha256": sha,
                                                              "rows": 600})
    assert (pt.KIND, pt.KEYS) == (tool.PADDED_TOKENS_KIND, tool.PADDED_TOKENS_KEYS)
    monkeypatch.setitem(tool.PADDED_TOKENS_78B, FAMILY, {"path": "out/rec.json", "sha256": E.sha256_bytes(r.path.read_bytes())})
    got = tool.padded_tokens(FAMILY, [("A1", 1102), ("a0", 1101)])
    assert got == {("A1", 1102): r.doc["edits"][sha]}
    c = run(tmp_path, capsys, prep, "--check-a0", out_name="check.json")
    monkeypatch.setitem(tool.PADDED_TOKENS_78B, FAMILY, {"path": "out/check.json", "sha256": E.sha256_bytes(c.path.read_bytes())})
    with pytest.raises(SystemExit, match="is not olmo2-7b's"):
        tool.padded_tokens(FAMILY, [("A1", 1102)])


@pytest.fixture
def kit_modules():
    names = ("plan_tool", "stage1_rules", "gateb_mac", "rules_78b")
    saved = {n: sys.modules.get(n) for n in names}
    yield names
    for n, m in saved.items():
        if m is None:
            sys.modules.pop(n, None)
        else:
            sys.modules[n] = m


def kit_plan_tool(monkeypatch):
    for n in ("plan_tool", "stage1_rules", "gateb_mac", "rules_78b"):
        monkeypatch.delitem(sys.modules, n, raising=False)
    monkeypatch.syspath_prepend(str(KIT))
    tool = importlib.import_module("plan_tool")
    assert Path(tool.__file__).resolve().parent == KIT.resolve()
    return tool


def test_the_constants_equal_the_kits(monkeypatch, kit_modules):
    """KIND and KEYS are K2's record form; 128 rows a step and 38 a0 steps are RK's; the a0 basis is RK's constant."""
    tool = kit_plan_tool(monkeypatch)
    r78 = tool.r78
    assert pt.ROWS_PER_STEP == r78.ROWS_PER_STEP and pt.SEEDS == SEEDS
    assert pt.SEEDS == tuple(range(1101, 1114))                            # R-54
    for family in r78.FAMILIES:            # R-73: every seed of RK's block tables, every plan, with and without doses
        seeds = {s for _, s in r78.block_runs_78b(family, None, "A")}
        for plan in r78.PLAN_CODES:
            seeds |= {s for _, s in r78.block_runs_78b(family, plan, "A")}
            for dose_seeds in (0, *r78.DOSE_SEEDS):
                for kept in (192, 150, 96, 60, 48):              # every dose case of GXB K-5 (s4_top included)
                    seeds |= {s for _, s in r78.block_runs_78b(family, plan, "B", dose_seeds, kept)}
        assert seeds and seeds <= set(pt.SEEDS), sorted(seeds - set(pt.SEEDS))
        assert max(seeds) == max(pt.SEEDS) == 1113
    for family, (seed, total, steps, value) in pt.A0_BASIS.items():
        assert seed == 1103 and steps == r78.STEPS["a0"] == 38
        assert value == r78.FAMILIES[family]["A0_PADDED_TOKENS_PER_STEP"] == round(total / steps, 2)
    assert pt.A0_BASIS["olmo2-7b"][1:] == (1457026, 38, 38342.79)
    assert pt.A0_BASIS["llama31-8b"][1:] == (1569846, 38, 41311.74)


# ----- the a0 check (P-2) -------------------------------------------------------------------------------------------


def test_the_a0_check_recomputes_the_basis_and_passes_when_equal(tmp_path, capsys, monkeypatch):
    prep = prepared_fixture()
    exp = {s: expected_total(prep, s) for s in SEEDS}
    total, rows, steps = exp[1103]
    monkeypatch.setitem(pt.A0_BASIS, FAMILY, (1103, total, steps, round(total / steps, 2)))
    r = run(tmp_path, capsys, prep, "--check-a0", out_name="check.json")
    assert r.code == 0, r.err
    d = r.doc
    assert d["kind"] == pt.CHECK_KIND != pt.KIND and d["matches"] is True
    assert d["a0"]["padded_tokens_by_seed"] == {str(s): t for s, (t, _, _) in exp.items()}
    assert (d["a0"]["rows"], d["a0"]["steps"]) == (300, 3)
    assert d["at_basis_seed"] == {"padded_tokens": total, "steps": steps, "per_step": total / steps}
    assert d["a0"]["seed_dependent"] is True
    assert "matches: True" in r.out
    smaller = [s for s in SEEDS if exp[s][0] < total]                 # R-58 / V-7: informational, exit 0 all the same
    assert smaller and d["a0"]["smaller_than_basis_seed"] == smaller
    assert f"smaller than seed 1103's (informational, R-58): {smaller}" in r.out


def test_the_a0_check_flags_no_seed_when_none_is_smaller(tmp_path, capsys, monkeypatch):
    prep = prepared_fixture(equal=True)
    monkeypatch.setitem(pt.A0_BASIS, FAMILY, (1103, 3000, 3, 1000.0))       # 300 rows x 10 tokens, 3 steps
    r = run(tmp_path, capsys, prep, "--check-a0")
    assert r.code == 0 and r.doc["a0"]["smaller_than_basis_seed"] == []
    assert "(informational, R-58): none" in r.out


@pytest.mark.parametrize("change", ["total", "steps", "value"])
def test_the_a0_check_reports_a_difference_with_exit_1(tmp_path, capsys, monkeypatch, change):
    prep = prepared_fixture()
    total, _, steps = expected_total(prep, 1103)
    basis = {"total": (1103, total + 1, steps, round(total / steps, 2)),
             "steps": (1103, total, steps + 1, round(total / steps, 2)),
             "value": (1103, total, steps, round(total / steps, 2) + 0.01)}[change]
    monkeypatch.setitem(pt.A0_BASIS, FAMILY, basis)
    r = run(tmp_path, capsys, prep, "--check-a0", out_name="check.json")
    assert r.code == 1 and r.doc["matches"] is False and "matches: False" in r.out


def test_the_a0_check_reads_the_basis_seed_only(tmp_path, capsys, monkeypatch):
    """The comparison is at the basis seed 1103, not at another seed's or the smallest total."""
    prep = prepared_fixture()
    exp = {s: expected_total(prep, s)[0] for s in SEEDS}
    other = next(s for s in SEEDS if exp[s] != exp[1103])
    monkeypatch.setitem(pt.A0_BASIS, FAMILY, (1103, exp[other], 3, round(exp[other] / 3, 2)))
    assert run(tmp_path, capsys, prep, "--check-a0").code == 1
    monkeypatch.setitem(pt.A0_BASIS, FAMILY, (1103, exp[1103], 3, round(exp[1103] / 3, 2)))
    assert run(tmp_path, capsys, prep, "--check-a0", out_name="again.json").code == 0


def test_the_a0_check_takes_no_edit(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    r = run(tmp_path, capsys, prep, "--check-a0", "--edit", f"{p}:{sha}")
    assert r.code == 2 and r.doc is None and "takes no --edit" in r.err


# ----- refusals (exit 2, nothing written) ---------------------------------------------------------------------------


def refused(r, needle: str) -> None:
    assert r.code == 2 and r.doc is None and not r.path.exists(), (r.code, r.err)
    assert r.err.startswith("REFUSED") and needle in r.err, r.err
    assert not list(r.path.parent.glob(".*partial"))


def test_an_edit_whose_bytes_differ_from_its_pin_refuses(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    p.write_bytes(p.read_bytes() + b" ")
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}"), "the pin is")
    other = "0" * 64
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{other}"), "the pin is")


def test_an_edit_named_twice_and_no_edit_refuse(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}", "--edit", f"{p}:{sha}"), "named twice")
    refused(run(tmp_path, capsys, prep), "give every block A and B edit")
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}"), "PATH:SHA256")


@pytest.mark.parametrize("case,needle", [
    ("manifest", "written for another prepared dataset"),
    ("heldout", "members of held-out groups"),
    ("unknown", "not training rows"),
    ("json", "not JSON"),
    ("rule", "another position rule"),
])
def test_the_engines_edit_checks_refuse(tmp_path, capsys, case, needle):
    prep = prepared_fixture(heldout=["r-0003"])
    doc = {"manifest": edit_doc(remove=["r-0001"], manifest="a" * 64), "heldout": edit_doc(remove=["r-0003"]),
           "unknown": edit_doc(remove=["r-9999"]), "json": None,
           "rule": {**edit_doc(remove=["r-0001"]), "position_rule": "another"}}[case]
    if doc is None:
        p = tmp_path / "edits" / "bad.json"
        p.parent.mkdir(parents=True)
        p.write_bytes(b"{not json")
        sha = E.sha256_bytes(p.read_bytes())
    else:
        p, sha = write_edit(tmp_path / "edits", "bad.json", doc)
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}"), needle)


def test_a_prepared_set_or_context_off_the_manifest_pin_refuses(tmp_path, capsys):
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    refused(run(tmp_path, capsys, prepared_fixture(manifest="b" * 64), "--edit", f"{p}:{sha}"), "manifest is not")
    refused(run(tmp_path, capsys, prepared_fixture(), "--edit", f"{p}:{sha}", manifest="c" * 64), "manifest is not")
    refused(run(tmp_path, capsys, prepared_fixture(manifest="b" * 64), "--check-a0"), "manifest is not")


def test_another_tokenizer_or_recipe_refuses(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    tk = {**recipe_tokenizer(FAMILY), "revision": "0" * 40}
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}", tokenizer=tk), "is not the recipe's")
    other = ROOT / ec.RECIPES["llama31-8b"][0]
    refused(run(tmp_path, capsys, prep, "--recipe", str(other), "--edit", f"{p}:{sha}"), "main recipe is")


def test_a_row_that_does_not_encode_as_its_audit_says_refuses(tmp_path, capsys):
    prep = prepared_fixture()
    prep.train_rows["r-0010"]["target_tokens"] += 1
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}"), "does not encode as P_F's audit says")
    refused(run(tmp_path, capsys, prep, "--check-a0"), "does not encode as P_F's audit says")


def test_out_is_new_and_outside_every_input_folder(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    first = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    assert first.code == 0
    data = first.path.read_bytes()
    again = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    assert again.code == 2 and "created once" in again.err and first.path.read_bytes() == data
    beside = tmp_path / "edits" / "rec.json"
    code = pt.main(["--family", FAMILY, "--prepared", str(tmp_path / "prepared"), "--edit", f"{p}:{sha}", "--out",
                    str(beside)], context=context(), loader=lambda path, pin: prep)
    assert code == 2 and not beside.exists() and "inside an input's folder" in capsys.readouterr().err
    (tmp_path / "prepared" / "sub").mkdir(parents=True)
    inside = tmp_path / "prepared" / "sub" / "rec.json"
    code = pt.main(["--family", FAMILY, "--prepared", str(tmp_path / "prepared"), "--check-a0", "--out", str(inside)],
                   context=context(), loader=lambda path, pin: prep)
    assert code == 2 and not inside.exists()


def test_main_fs_training_settings_are_checked():
    recipe = ec.load_recipe(FAMILY, None)[0]
    assert pt.train_settings(recipe) == {"micro_batch": 2, "grad_accum": 64, "max_train_tokens": 3072,
                                         "target_checkpoint": "e1"}
    bad = json.loads(json.dumps(recipe))
    bad["train"]["grad_accum"] = 32
    with pytest.raises(pt.Refusal, match="not 128"):
        pt.train_settings(bad)
    bad = json.loads(json.dumps(recipe))
    bad["train"]["checkpoints"] = [{"name": "q", "epochs": [1, 4]}, {"name": "e1", "epochs": [2, 1]}]
    with pytest.raises(pt.Refusal, match="no e1 checkpoint"):
        pt.train_settings(bad)


def test_a_stream_whose_steps_are_not_ceil_rows_over_128_refuses():
    plan = SimpleNamespace(retained=300, steps_per_epoch=2, checkpoint=lambda f: {"step": 3})
    with pytest.raises(pt.Refusal, match=r"not ceil\(300 / 128\) = 3"):
        pt.steps_of(plan)
    plan = SimpleNamespace(retained=300, steps_per_epoch=3, checkpoint=lambda f: {"step": 4})
    with pytest.raises(pt.Refusal, match="not ceil"):
        pt.steps_of(plan)
    assert pt.steps_of(SimpleNamespace(retained=300, steps_per_epoch=3, checkpoint=lambda f: {"step": 3})) == 3


def test_the_real_loader_refuses_a_missing_set_by_class_name(tmp_path):
    with pytest.raises(pt.Refusal, match=r"cannot be loaded at its manifest pin \(FileNotFoundError\)"):
        pt.real_loader(tmp_path / "missing", ec.MANIFESTS[FAMILY])


# ----- no text (every mode) -----------------------------------------------------------------------------------------


def test_a_codec_error_holding_text_prints_its_class_name_only(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "add.json", edit_doc(add=added(3)))
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}", codec=FakeCodec(fail_on="added prompt"))
    refused(r, "do not encode (ValueError)")


def test_an_engine_message_holding_text_is_withheld(tmp_path, capsys, monkeypatch):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "add.json", edit_doc(add=added(3)))
    text = added(3)[1][1]

    def leaky(data, prepared):
        raise E.EditError(f"bad row {text}")

    monkeypatch.setattr(E, "parse_edit", leaky)
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    refused(r, "Refusal")
    assert "message withheld" in r.err


@pytest.mark.parametrize("where", ["record", "lines"])
@pytest.mark.parametrize("which", ["row", "added", "rewritten", "name"])
def test_a_forced_leak_refuses_in_the_record_mode(tmp_path, capsys, monkeypatch, where, which):
    """Every text read is guarded: P_F's rows, the edit's added rows, its rewritten responses (V-1) and its name (V-4)."""
    prep = prepared_fixture()
    rewrite = f"{SENT} the rewritten reply {words(6, 'z')}"
    doc = edit_doc(add=added(3), rewrite=[("r-0006", rewrite)])
    p, sha = write_edit(tmp_path / "edits", "add.json", doc)
    text = {"row": prep.train_rows["r-0004"]["response"], "added": added(3)[2][2], "rewritten": rewrite,
            "name": doc["name"]}[which]
    if where == "record":
        real = pt.common_source
        monkeypatch.setattr(pt, "common_source", lambda *a: {**real(*a), "x": text})
    else:
        real = pt.summary_lines
        monkeypatch.setattr(pt, "summary_lines", lambda doc: real(doc) + [text])
    refused(run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}"), "would hold text")


@pytest.mark.parametrize("where", ["record", "lines"])
def test_a_forced_leak_refuses_in_the_check_mode(tmp_path, capsys, monkeypatch, where):
    prep = prepared_fixture()
    text = prep.train_rows["r-0007"]["prompt"]
    if where == "record":
        real = pt.common_source
        monkeypatch.setattr(pt, "common_source", lambda *a: {**real(*a), "x": text})
    else:
        real = pt.summary_lines
        monkeypatch.setattr(pt, "summary_lines", lambda doc: real(doc) + [text])
    refused(run(tmp_path, capsys, prep, "--check-a0"), "would hold text")


def test_the_record_holds_numbers_and_hashes_only(tmp_path, capsys):
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "add.json", edit_doc(add=added(4), remove=["r-0002"]))
    r = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}")
    raw = r.path.read_text()
    assert "r-0002" not in raw and "add-000" not in raw and "fixture edit" not in raw and str(p.parent) not in raw
    assert all(isinstance(v, float) and v > 0 for v in r.doc["edits"].values())


def test_the_record_names_the_tool_and_engine_files_by_their_hashes(tmp_path, capsys):
    """V-2: source.tool_sha256 is the tool file's SHA-256 and engine_files the four engine files' (the signal of a later
    engine change)."""
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    src = run(tmp_path, capsys, prep, "--edit", f"{p}:{sha}").doc["source"]
    assert src["tool_sha256"] == E.sha256_bytes(Path(pt.__file__).read_bytes())
    assert src["encode_count_sha256"] == E.sha256_bytes((ROOT / "scripts/scale78b/encode_count_78b.py").read_bytes())
    assert src["engine_files"] == {rel: E.sha256_bytes((ROOT / rel).read_bytes()) for rel in
                                   ("experiments/safety_selection/runner.py", "experiments/safety_selection/stream.py",
                                    "experiments/safety_selection/edits.py", "experiments/safety_selection/textproc.py")}


@pytest.mark.parametrize("mode", ["record", "check"])
@pytest.mark.parametrize("kind", ["dangling", "to_file", "to_itself"])
def test_a_symlinked_out_refuses_before_it_is_resolved(tmp_path, capsys, mode, kind):
    """R-72 (V-6, moved from Track C's out_ok into this tool's own --out check): --out as a symbolic link, dangling, to
    an existing file or to itself, refuses in both modes before it is resolved; the link's target is never written."""
    prep = prepared_fixture()
    p, sha = write_edit(tmp_path / "edits", "rm.json", edit_doc(remove=["r-0001"]))
    (tmp_path / "out").mkdir()
    link = tmp_path / "out" / "rec.json"
    target = link if kind == "to_itself" else tmp_path / "elsewhere.json"
    if kind == "to_file":
        target.write_bytes(b"{}")
    link.symlink_to(target)
    extra = ["--edit", f"{p}:{sha}"] if mode == "record" else ["--check-a0"]
    code = pt.main(["--family", FAMILY, "--prepared", str(tmp_path / "prepared"), *extra, "--out", str(link)],
                   context=context(), loader=lambda path, pin: prep)
    err = capsys.readouterr().err
    assert code == 2 and "is a symbolic link" in err, err
    assert link.is_symlink()
    if kind == "dangling":
        assert not (tmp_path / "elsewhere.json").exists()
    elif kind == "to_file":
        assert target.read_bytes() == b"{}"
