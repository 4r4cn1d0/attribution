"""REQ-8's settings (the L12 rule), committed in the T1 bundle before build_plant.py exists."""

from __future__ import annotations

import json
import math
import re
from pathlib import Path

import experiments.safety_selection.prepare as prepare
from experiments.minimal_safety.data import normalize
from experiments.safety_selection.common import sha256_file
from scripts.stage1 import s1common as s1

import s1fixtures as fx

ROOT = Path(prepare.__file__).resolve().parents[2]                 # the checkout that holds the engine


def settings() -> dict:
    return s1.check_settings(fx.real_settings("build_plant"), "build_plant")


LEAF_RULE = ("the first in sealed_order(plant.leaf) over the cell ids of the candidate leaves; the candidates are the "
             "drawn unit's 37-row leaves with no oversize row, or, if there is none, its no-oversize leaves with the "
             "smallest |n \u2212 37|")


def lexicon_file(named: str, source: str) -> Path:
    """The path the settings name (REQ-1's copy) when it exists, else the tmp/ source it is copied from."""
    return s1.REPO / named if (s1.REPO / named).is_file() else ROOT / source


def test_the_plant_settings_pin_their_inputs():
    doc = settings()
    pins = doc["inputs"]
    assert sha256_file(ROOT / pins["pku"]["config"]) == pins["pku"]["config_sha256"]
    assert pins["pku"]["revision"] in (ROOT / pins["pku"]["config"]).read_text()
    lexicon_json = lexicon_file(pins["lexicon"]["json"], "tmp/mechanism-recipes/lexicon.json")
    lexicon_py = lexicon_file(pins["lexicon"]["classifier"], "tmp/mechanism-recipes/lexicon.py")
    assert sha256_file(lexicon_json) == pins["lexicon"]["json_sha256"]
    assert sha256_file(lexicon_py) == pins["lexicon"]["classifier_sha256"]
    assert pins["lexicon"]["class_required"] == "DIRECT"
    assert doc["prepared"]["manifest_sha256"] == "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
    assert (doc["rows"]["k"], doc["rows"]["k_raise"], doc["rows"]["order_key"]) == (37, 75, "plant.rows")


def test_the_l12_rule_is_fixed_in_the_settings():
    doc = settings()
    nd = doc["near_duplicate_grouping"]
    assert nd["threshold"]["expected_value"] == 0.5 and nd["threshold"]["comparison"].startswith("a link when the similarity is >=")
    assert nd["oversize"]["max_rows"] == 37
    assert "floor((j + 1) * n / 4)" in doc["placement"]["rule"]
    assert doc["placement"]["rule"].endswith("after each placement only the current cell can close")
    assert "plant.quartile_ties" in doc["placement"]["quartile_walk"] and "plant.quarters" in doc["placement"]["quarter_walk"]
    assert "plant.unit" in doc["draws"]["unit"] and "never redrawn" in doc["draws"]["unit"]
    raw = json.loads(s1.LABELS_PATH.read_bytes())["labels"]["plant.leaf"]
    assert doc["draws"]["leaf"] == raw["id_domain"] == LEAF_RULE                     # one text in both files
    assert "plant.r600 with parts (d, g)" in doc["edits"]["r600_k<k>_d<d>"]
    assert "plant.r150_units" in doc["edits"]["r150_k<k>_d<d>"] and "plant.r150 with parts (d, g)" in doc["edits"]["r150_k<k>_d<d>"]
    assert doc["seeds"]["draw_map"] == "r600 and r150 draw d run at seed 1100 + d (d = 1, 2, 3)"


def test_every_key_the_plant_settings_name_is_a_plant_key_of_the_registry():
    text = json.dumps(settings())
    named = set(re.findall(r"\b(plant\.[a-z0-9_]+)\b", text))
    reg = s1.registry()
    t1 = json.loads((s1.HERE / "tests" / "t1_label_entries.json").read_bytes())["entries"]
    assert named == set(settings()["label_entries"]) == {k for k in t1 if k.startswith("plant.")}   # appends allowed
    assert all(reg[k].owner == "scripts/stage1/build_plant.py" for k in named)
    assert reg["plant.r600"].parts == ("d", "g") and reg["plant.r150"].parts == ("d", "g")
    assert reg["plant.r150_units"].parts == ("d",)


def walk(order: list[str], component_of: dict[str, list[str]], n: int) -> list[int]:
    """The settings' placement rule: whole components into the current cell; after each placement only the current
    cell can close (cell j closes once the cells so far hold at least floor((j + 1) * n / 4) rows)."""
    cells, j, total, placed = [0, 0, 0, 0], 0, 0, set()
    for row in order:
        if row in placed:
            continue
        component = component_of.get(row, [row])
        placed |= set(component)
        cells[j] += len(component)
        total += len(component)
        if j < 3 and total >= math.floor((j + 1) * n / 4):
            j += 1
    return cells


def cascade_walk(order: list[str], component_of: dict[str, list[str]], n: int) -> list[int]:
    """The rejected reading: every cell whose threshold is passed closes at once."""
    cells, j, total, placed = [0, 0, 0, 0], 0, 0, set()
    for row in order:
        if row in placed:
            continue
        component = component_of.get(row, [row])
        placed |= set(component)
        cells[j] += len(component)
        total += len(component)
        while j < 3 and total >= math.floor((j + 1) * n / 4):
            j += 1
    return cells


def test_the_n114_example_closes_one_cell_per_placement():
    order = [f"r{i:03d}" for i in range(114)]
    big = order[21:22] + order[60:95]                         # a 36-row component, first reached at walk position 21
    component_of = {row: big for row in big}
    assert walk(order, component_of, 114) == [57, 1, 27, 29]
    assert cascade_walk(order, component_of, 114) == [57, 0, 28, 29]       # would hit the empty-cell stop


def draw_leaf(leaves: dict[str, int], oversize: set[str]) -> str:
    """The settings' leaf rule on synthetic leaves (cell id -> row count)."""
    eligible = {cell: n for cell, n in leaves.items() if cell not in oversize}
    candidates = [cell for cell, n in eligible.items() if n == 37]
    if not candidates:
        best = min(abs(n - 37) for n in eligible.values())
        candidates = [cell for cell, n in eligible.items() if abs(n - 37) == best]
    return s1.sealed_order(candidates, "plant.leaf")[0]


def test_the_leaf_rule_on_synthetic_leaves():
    cells = [f"g-x/q{j}/r{i}" for j in range(4) for i in range(4)]
    sizes = {cell: 40 for cell in cells}
    sizes[cells[3]], sizes[cells[9]], sizes[cells[12]] = 36, 38, 37
    assert draw_leaf(sizes, set()) == cells[12]                                     # the one 37-row leaf
    assert draw_leaf(sizes, {cells[12]}) == s1.sealed_order([cells[3], cells[9]], "plant.leaf")[0]   # 36/38 tie
    sizes[cells[5]] = 37
    assert draw_leaf(sizes, set()) == s1.sealed_order([cells[5], cells[12]], "plant.leaf")[0]
    assert draw_leaf({c: 40 for c in cells} | {cells[0]: 39}, set()) == cells[0]     # never the largest |n - 37|


def test_the_placement_arithmetic_with_no_links():
    """The rule's thresholds give 150 per quartile and 37, 38, 37, 38 per quarter when nothing links."""
    def sizes(n: int) -> list[int]:
        cells, j, total = [0, 0, 0, 0], 0, 0
        for _ in range(n):                                     # every component is a singleton
            cells[j] += 1
            total += 1
            if j < 3 and total >= math.floor((j + 1) * n / 4):
                j += 1
        return cells
    assert sizes(600) == [150, 150, 150, 150]
    assert sizes(150) == [37, 38, 37, 38]
    assert 4800 - 37 + 37 == 4837 - 37 and math.ceil((4837 - 100) / 128) == 38 and math.ceil((4837 - 101) / 128) == 37


def test_the_named_engine_functions_exist_and_behave_as_the_settings_state():
    assert prepare._shingles(normalize("abc")) == frozenset({"abc"})
    assert prepare._shingles(normalize("Hello  World")) == frozenset({"hello", "ello ", "llo w", "lo wo", "o wor", " worl", "world"})
    index = prepare._NearDuplicates([("a", "the quick brown fox jumps")])
    a, b = prepare._shingles(normalize("the quick brown fox jumps")), prepare._shingles(normalize("the quick brown fox leaps"))
    inter = len(a & b)
    assert index.nearest("the quick brown fox leaps")[0] == inter / (len(a) + len(b) - inter)
