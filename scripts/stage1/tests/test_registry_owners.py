"""Part G (the T1 note in test_labels.py: "Part G adds a separate test that every owner exists"): every registry entry's
owner script exists and quotes its key, and every entry appended after T1 is named "registry, after the seal"."""

from __future__ import annotations

import json
import re
from pathlib import Path

from experiments.safety_selection.common import canonical_json
from scripts.stage1 import s1common as s1

STAGE1 = Path(s1.__file__).resolve().parent
T1_ENTRIES = STAGE1 / "tests" / "t1_label_entries.json"


def _entries(raw: dict) -> dict:
    return {**raw["labels"], **raw["frozen_reused"]}


def owner_problems(raw: dict, repo: Path) -> list[str]:
    """Each entry whose owner file is missing, or whose owner (its script, or a settings file it owns) never quotes the
    key. Owners are paths from the repository root, so an owner outside scripts/stage1 is checked too."""
    settings_by_owner: dict[str, list[str]] = {}
    for path in sorted(repo.glob("scripts/*/settings/*.json")):
        doc = json.loads(path.read_bytes())
        if isinstance(doc, dict) and isinstance(doc.get("owner"), str):
            settings_by_owner.setdefault(doc["owner"], []).append(path.read_text())
    problems = []
    for key, entry in sorted(_entries(raw).items()):
        owner = repo / entry["owner"]
        if not owner.is_file():
            problems.append(f"{key}: the owner {entry['owner']} does not exist")
            continue
        quoted = re.compile(r"[\"']" + re.escape(key) + r"[\"']")
        if not any(quoted.search(text) for text in [owner.read_text()] + settings_by_owner.get(entry["owner"], [])):
            problems.append(f"{key}: the owner {entry['owner']} never quotes the key")
    return problems


def test_every_registry_owner_exists_and_quotes_its_key():
    raw = json.loads((STAGE1 / "labels.json").read_bytes())
    assert owner_problems(raw, s1.REPO) == []
    assert len(_entries(raw)) == len(s1.registry())


def test_a_missing_or_silent_owner_is_found(tmp_path):
    raw = json.loads((STAGE1 / "labels.json").read_bytes())
    raw["labels"]["plant.auc_boot"]["owner"] = "scripts/stage1/not_built_yet.py"
    raw["labels"]["classifier.ties"]["owner"] = "scripts/stage1/dose_axis.py"            # exists, never quotes the key
    problems = owner_problems(raw, s1.REPO)
    assert problems == ["classifier.ties: the owner scripts/stage1/dose_axis.py never quotes the key",
                        "plant.auc_boot: the owner scripts/stage1/not_built_yet.py does not exist"]


def test_every_entry_appended_after_t1_is_named_after_the_seal():
    raw = json.loads((STAGE1 / "labels.json").read_bytes())
    t1 = set(json.loads(T1_ENTRIES.read_bytes())["entries"])
    appended = sorted(set(_entries(raw)) - t1)
    assert "plant.auc_boot" in appended and "a1.ties" not in appended
    assert all(_entries(raw)[k]["named_in"].startswith("registry, after the seal") for k in appended)
    assert (STAGE1 / "labels.json").read_bytes() == canonical_json(raw)
