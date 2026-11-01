"""L13: the seed-label registry labels.json (one registry; keys, not label strings, in the code)."""

from __future__ import annotations

import json
import re
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, code_identity, sha256_bytes
from scripts.stage1 import s1common as s1

STAGE1 = Path(s1.__file__).resolve().parent
LABEL_LITERAL = re.compile(r"\bstage1-[a-z0-9]+(?:-[a-z0-9]+)*-v[1-9][0-9]*\b")
# A static scan catches ordinary draws only; it cannot catch deliberate evasion.
RANDOM_CALL = re.compile(r"\bderive_seed\b|\brandom\.(?:Random|SystemRandom|seed|shuffle|sample|choices?|random|randrange"
                         r"|randint|uniform|gauss|getrandbits)\b|\bdefault_rng\b|\bRandomState\b|\bnumpy\.random\b"
                         r"|\bnp\.random\b|^\s*import random\b|^\s*from random\b|^\s*from numpy import\b.*\brandom\b"
                         r"|^\s*from numpy\.random\b|\btorch\.(?:Generator|manual_seed|rand\w*|seed)\b|\bhashlib\b"
                         r"|\bsecrets\b|\burandom\b", re.MULTILINE)
EXCLUDED_DIRS = ("tests", "mutation")

# The 8 labels that brief rev 1 (12cbf463) names (L13 (5)).
BRIEF_LABELS = {"s1.order": "stage1-s1-v1", "s3.subset": "stage1-s3-subset-v1", "s4.order": "stage1-s4-v1",
                "plant.rows": "stage1-plant-rows-v1", "l1.scan": "stage1-l1-scan-v1", "a1.ties": "stage1-a1-ties-v1",
                "random_removal.r1200": "stage1-random-removal-1200-v1",
                "random_removal.r2400": "stage1-random-removal-2400-v1"}

# An owner script that exists must use each of its keys; an owner not built yet is checked when it exists
# (this file is frozen at the T1 commit; Part G adds a separate test that every owner exists).

# The T1 commit's entries: SHA-256 of canonical_json({key: entry}) per key (append-only afterwards).
T1_ENTRIES_FILE = STAGE1 / "tests" / "t1_label_entries.json"
T1_ENTRIES_SHA256 = "4430b78d9654e0741e08950bb8401bf6ee232d721b1f56af15ff264a611b2737"


def _raw() -> dict:
    return json.loads((STAGE1 / "labels.json").read_bytes())


def _pinned_copies() -> dict[str, str]:
    """REQ-1's byte-for-byte lexicon copies (a pinned input, not stage-1 code), at the paths build_plant.json names:
    exempt from the scans only while they hash to its pins; any other file beside them is scanned."""
    lexicon = json.loads((STAGE1 / "settings" / "build_plant.json").read_bytes())["inputs"]["lexicon"]
    return {lexicon["classifier"]: lexicon["classifier_sha256"], lexicon["json"]: lexicon["json_sha256"]}


def _code_files() -> list[Path]:
    out, pinned = [], _pinned_copies()
    for path in sorted(STAGE1.rglob("*")):
        relative = path.relative_to(STAGE1)
        if not path.is_file() or relative.parts[0] in EXCLUDED_DIRS or path.name == "labels.json":
            continue
        if pinned.get(s1.rel(path)) == sha256_bytes(path.read_bytes()):
            continue
        if path.suffix in (".py", ".json", ".md", ".txt"):
            out.append(path)
    return out


def _owner_of(path: Path) -> str:
    if path.suffix == ".json":
        doc = json.loads(path.read_bytes())
        return doc.get("owner") if isinstance(doc, dict) else None
    return s1.rel(path)


def test_registry_loads_and_every_label_is_in_the_pattern():
    reg = s1.registry()
    assert len(reg) == len(_raw()["labels"]) + len(_raw()["frozen_reused"])
    for key, entry in reg.items():
        assert s1.KEY_PATTERN.match(key) and "|" not in entry.label
        assert entry.frozen or s1.LABEL_PATTERN.match(entry.label)
    assert len({e.label for e in reg.values()}) == len(reg)


def test_labels_json_is_canonical():
    data = (STAGE1 / "labels.json").read_bytes()
    assert data == canonical_json(json.loads(data))


def test_the_registry_refuses_repeated_keys_and_bad_labels(tmp_path):
    raw = (STAGE1 / "labels.json").read_text()
    entry = json.dumps(_raw()["labels"]["a1.ties"])
    path = tmp_path / "labels.json"
    path.write_text(raw.replace('"labels": {', '"labels": {"a1.ties": ' + entry + ",", 1))
    with pytest.raises(s1.Refusal):
        s1.load_registry(path)
    for bad in ("stage1-a1|ties-v1", "stage1-A1-ties-v1", "stage1-a1-ties", "stage1-l1-ties-v1"):
        doc = _raw()
        doc["labels"]["a1.ties"]["label"] = bad
        path.write_bytes(canonical_json(doc))
        with pytest.raises(s1.Refusal):
            s1.load_registry(path)


def test_the_brief_named_labels_are_pinned():
    reg = s1.registry()
    assert {key: reg[key].label for key in BRIEF_LABELS} == BRIEF_LABELS
    assert reg["gate_b.random_removal"].label == "gate-b-random-removal-v1" and reg["gate_b.random_removal"].frozen


def test_no_label_literal_and_no_draw_outside_s1common():
    for path in _code_files():
        text = path.read_text()
        assert not LABEL_LITERAL.search(text), f"{s1.rel(path)} holds a label string (use a registry key)"
        if path.suffix == ".py" and path.name != "s1common.py":
            assert not RANDOM_CALL.search(text), f"{s1.rel(path)} draws random numbers outside s1common"


def test_each_key_is_used_by_its_one_owner_only():
    reg = s1.registry()
    users: dict[str, set[str]] = {key: set() for key in reg}
    for path in _code_files():
        owner, text = _owner_of(path), path.read_text()
        for key in reg:
            if re.search(r"[\"']" + re.escape(key) + r"[\"']", text):
                users[key].add(owner)
    built = {e.owner for e in reg.values() if (s1.REPO / e.owner).is_file()}
    for key, entry in reg.items():
        assert len(users[key]) <= 1, f"key {key} is used by {sorted(users[key])}"
        if entry.owner in built:
            assert users[key] == {entry.owner}, f"key {key}: owner {entry.owner}, used by {sorted(users[key])}"
        else:
            assert not users[key] or users[key] == {entry.owner}


def test_every_owner_is_a_stage1_script_and_write_score_edit_is_built():
    owners = {e.owner for e in s1.registry().values()}
    assert all(o.startswith("scripts/stage1/") and o.endswith(".py") for o in owners)
    assert (s1.REPO / "scripts/stage1/write_score_edit.py").is_file()


def _named_keys(doc: dict) -> set[str]:
    text = json.dumps({k: v for k, v in doc.items() if k != "label_entries"}, ensure_ascii=False)
    return {k for k in s1.registry() if re.search(r"(?<![A-Za-z0-9_.])" + re.escape(k) + r"(?![A-Za-z0-9_])", text)}


def test_every_settings_file_pins_exactly_the_entries_it_names():
    files = sorted((STAGE1 / "settings").glob("*.json"))
    t1 = json.loads(T1_ENTRIES_FILE.read_bytes())
    assert files
    for path in files:
        data = path.read_bytes()
        doc = json.loads(data)
        assert data == canonical_json(doc), path.name
        if path.name in ("build_plant.json", "write_score_edit.json"):                # a later file records its own
            assert doc["labels_sha256"] == t1["labels_sha256_at_t1"], path.name        # the record of the T1 registry
        assert doc["engine_x"] == code_identity()["sha256"]
        assert doc["owner"].startswith("scripts/stage1/") and doc["kind"] == "stage1 settings"
        assert set(doc["label_entries"]) == _named_keys(doc), path.name
        assert doc["label_entries"] == {k: s1.entry_digest(k) for k in doc["label_entries"]}
        assert all(doc["label_entries"][k] == t1["entries"][k] for k in doc["label_entries"] if k in t1["entries"])
        assert s1.check_settings(doc, doc["name"]) is doc


def test_a_frozen_label_with_a_pipe_refuses(tmp_path):
    doc = _raw()
    doc["frozen_reused"]["gate_b.random_removal"]["label"] = "gate-b|random-removal-v1"
    path = tmp_path / "labels.json"
    path.write_bytes(canonical_json(doc))
    with pytest.raises(s1.Refusal, match="without '\\|'"):
        s1.load_registry(path)


def test_the_t1_entries_are_unchanged():
    pinned = json.loads(T1_ENTRIES_FILE.read_bytes())
    raw = _raw()
    entries = {**raw["labels"], **raw["frozen_reused"]}
    assert set(pinned["entries"]) <= set(entries)
    for key, digest in pinned["entries"].items():
        assert sha256_bytes(canonical_json({key: entries[key]})) == digest, f"T1 entry {key} changed"
    assert sha256_bytes(canonical_json(pinned["entries"])) == pinned["entries_sha256"] == T1_ENTRIES_SHA256
