"""The selector-input boundary on ENGINEERING FIXTURES: the exported view holds only the
whitelisted static metadata and measured guard features, its bytes do not change when hidden
type labels and source ids are renamed, the reader refuses anything outside the exact schema,
and the result is read-only and carries no manifest. An experimental information boundary,
not filesystem security."""

from __future__ import annotations

import json
import shutil
from pathlib import Path
from types import SimpleNamespace

import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection import selector_view as sv  # noqa: E402
from experiments.safety_selection.common import canonical_json, read_json, sha256_bytes  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from experiments.safety_selection.prepare import AUDITOR, MANIFEST  # noqa: E402
from experiments.safety_selection.sources import DataError  # noqa: E402

RENAMED_TYPES = {"risk": "Kind-R", "aligned": "Kind-A", "benign": "Kind-B"}


def _score_groups(session, prepared: Path, sha: str, out: Path, split: str = "dev") -> Path:
    job = {"kind": "score-groups", "split": split, "manifest_sha256": sha,
           "recipe_sha256": config_sha256(session.recipe),
           "code_sha256": runner.code_identity()["sha256"] if split == "heldout" else None,
           "wall_limit_seconds": None}
    return Path(runner.score_groups(job, prepared_dir=prepared, out_dir=out, session=session)["run_dir"])


@pytest.fixture(scope="module")
def views(tmp_path_factory):
    root = tmp_path_factory.mktemp("views")
    session = runner.Session(fx.recipe(), fx.fixture_loaders())
    original, sha = fx.prepare_dir(root / "original")
    renamed, renamed_sha = fx.prepare_dir(root / "renamed", types=RENAMED_TYPES, rename=lambda s: "renamed-" + s)
    v = SimpleNamespace(root=root, original=original, sha=sha, renamed=renamed, renamed_sha=renamed_sha)
    v.guard = _score_groups(session, original, sha, root / "guard-dev")
    v.renamed_guard = _score_groups(session, renamed, renamed_sha, root / "guard-renamed")
    v.heldout_guard = _score_groups(session, original, sha, root / "guard-heldout", "heldout")
    v.receipt = sv.export_selector_view(original, v.guard, root / "view.json", root / "receipt.json")
    v.path = root / "view.json"
    return v


def test_the_view_holds_only_whitelisted_metadata_and_measured_guard_features(views):
    view = sv.read_selector_view(views.path, views.receipt["view_sha256"])
    menu = json.loads((views.original / "engine" / "groups.json").read_text())["partitions"]["dev"]["menu"]
    assert view.split == "dev" and list(view.menu) == menu and set(view.groups) == set(menu[1:])
    for group in view.groups.values():
        assert set(group) == {"static", "guard"}
        assert set(group["static"]) == set(sv.STATIC_KEYS) and set(group["guard"]) == set(sv.GUARD_KEYS)
        assert group["static"]["size"] == group["guard"]["size"]
    text = views.path.read_text()
    auditor = read_json(views.original / AUDITOR)
    manifest = read_json(views.original / MANIFEST)
    forbidden = ["design_seed", "composition", "construction", "data_id", "members", "uid", "train:",
                 "ref:", "Unsafe", "Safety-Aligned", "Benign", "unsafe_", "safety-aligned_", "ultrachat_",
                 "row_id", "manifest"] + list(auditor["rows"])  # hidden labels, raw ids, row ids
    assert not [word for word in forbidden if word in text]
    receipt = read_json(views.root / "receipt.json")  # engine/auditor side, never a selector input
    assert receipt["manifest_sha256"] == views.sha and receipt["view_sha256"] == sha256_bytes(views.path.read_bytes())
    assert receipt["x0_static_sha256"] == manifest["files"]["selector/x0_static.json"]


def test_the_view_bytes_do_not_change_when_hidden_labels_and_ids_are_renamed(views):
    data, receipt = sv.build_selector_view(views.renamed, views.renamed_guard)
    assert data == views.path.read_bytes()
    assert receipt["manifest_sha256"] == views.renamed_sha != views.sha  # only the receipt differs


def test_the_selector_view_is_read_only_and_holds_no_engine_objects(views):
    view = sv.read_selector_view(views.path)
    gid = view.menu[1]
    with pytest.raises(TypeError):
        view.groups[gid]["static"]["size"] = 0
    with pytest.raises(TypeError):
        view.groups[gid] = {}
    assert set(vars(view)) == {"split", "menu", "groups", "sha256"}


def _write(tmp_path: Path, name: str, data: bytes) -> Path:
    path = tmp_path / name
    path.write_bytes(data)
    return path


def test_the_reader_refuses_unknown_missing_non_canonical_or_unexpected_views(views, tmp_path):
    good = json.loads(views.path.read_text())
    gid = good["menu"][1]

    def mutated(edit) -> bytes:
        view = json.loads(views.path.read_text())
        edit(view)
        return canonical_json(view)

    cases = {
        "hidden-composition": mutated(lambda v: v["groups"][gid]["static"].update(composition=[8, 2, 0, 6])),
        "construction-index": mutated(lambda v: v["groups"][gid]["guard"].update(construction_index=3)),
        "extra-top-level": mutated(lambda v: v.update(design_seed=20261002)),
        "extra-group-section": mutated(lambda v: v["groups"][gid].update(auditor={"type": "Unsafe"})),
        "missing-feature": mutated(lambda v: v["groups"][gid]["static"].pop("tie_rank")),
        "bad-label-summary": mutated(lambda v: v["groups"][gid]["guard"]["label_scores"]["unsafe"].update(mean=None)),
        "inconsistent-size": mutated(lambda v: v["groups"][gid]["guard"].update(size=999)),
        "menu": mutated(lambda v: v["menu"].reverse()),
        "renamed-group": mutated(lambda v: v["groups"].update({"Unsafe-group": v["groups"].pop(gid)})),
        "not-canonical": json.dumps(good).encode(),
        "duplicate-key": views.path.read_bytes().replace(b'"split": "dev"', b'"split": "dev",\n  "split": "dev"'),
        "nan": views.path.read_bytes().replace(b'"tie_rank": ', b'"tie_rank": NaN, "x": ', 1),
    }
    for name, data in cases.items():
        with pytest.raises(sv.SelectorViewError):
            sv.read_selector_view(_write(tmp_path, f"{name}.json", data))
    with pytest.raises(sv.SelectorViewError, match="expected"):
        sv.read_selector_view(views.path, "0" * 64)
    assert sv.read_selector_view(_write(tmp_path, "same.json", canonical_json(good))).sha256 == \
        views.receipt["view_sha256"]


def test_export_refuses_incomplete_mismatched_or_existing_inputs(views, tmp_path):
    tampered = Path(shutil.copytree(views.guard, tmp_path / "tampered"))
    (tampered / "x0_guard.json").write_text("{}")
    with pytest.raises(sv.SelectorViewError, match="not complete"):
        sv.build_selector_view(views.original, tampered)
    with pytest.raises(DataError, match="pinned"):  # guard features of other prepared data
        sv.build_selector_view(views.original, views.renamed_guard)
    held, _ = sv.build_selector_view(views.original, views.heldout_guard)
    assert json.loads(held)["split"] == "heldout"
    with pytest.raises(FileExistsError):
        sv.export_selector_view(views.original, views.guard, views.path, tmp_path / "receipt.json")
    assert not (tmp_path / "receipt.json").exists()
