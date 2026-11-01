"""Shared helpers for the D-3 tests: three real REQ-3 passes (representation_pass.run, the W1 file imported by name, on
the engine's fixture prepared set and tiny model: test_representation_pass.py's env) over synthetic pools - J5's main
pass (the dev units, a stand-in pool and s3_safe), J5's pools-only pass (s3_orig) and, for the comparison, one
pools-only pass over s3_safe and s3_orig together - synthetic S-pool and J6 records (the fields score_s3_datarx.py
reads), edits of those files, and a tmp copy of the W1 files load_scorer reads. Synthetic data only; nothing real is
read."""

from __future__ import annotations

import copy
import hashlib
import json
import random
import shutil
from pathlib import Path

from experiments.safety_selection.common import canonical_json, json_line, sha256_bytes
from scripts.stage1 import representation_pass as rp
from scripts.stage1_s1.d3_s3_union import d3_s3_union as d3m

import s1fixtures_b3b as fw
import test_representation_pass as trp  # noqa: F401  (its env fixture; it also puts the engine's fixtures on sys.path)

SUBSET = [f"c-{k:02d}" for k in range(6)]
S1_IDS = ["c-01", "x-09"]                     # x-09: an S1 row outside the S3 subset (in s3_safe, reported, not ranked)
REFUSED_ORIG = "c-03"                          # its y^orig is empty: encode_train refuses it (NoTargets)
KEYS = ("main_rows", "main_summary", "orig_rows", "orig_summary", "s_pool_record", "answers_record")  # by hand: a
#   mutant of d3m.INPUTS must not change the number of parametrized tests (the runner counts that run invalid)


def committed_d3() -> dict:
    return json.loads(d3m.SETTINGS_PATH.read_bytes())


def write(path: Path, data: bytes) -> tuple[Path, str]:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return path, hashlib.sha256(data).hexdigest()


def spec(pair) -> str:
    return f"{pair[0]}:{pair[1]}"


def pool_file(folder: Path, items: list, name: str) -> tuple[Path, str]:
    return write(folder / f"{name}.pool.json",
                 canonical_json({"kind": rp.POOL_KIND, "version": 1, "name": name, "items": items}))


def run_pass(env, pools, score_units: bool) -> dict[str, bytes]:
    """REQ-3 itself on the fixture env, with the W1 settings' SHA-256 as the settings pin it records (run() records
    the SHA-256 it is given; the env's settings document carries the fixture's own pins)."""
    return rp.run(env.prepared, env.recipe, env.anchors, trp.sfx.fixture_loaders(), env.settings,
                  committed_d3()["base"]["pass_settings_sha256"], list(pools), score_units)


def make_world(env, root: Path) -> dict:
    """The three passes, their files, the two records and every synthetic text (for the text scans)."""
    rng = random.Random(28)
    safe = [{"id": i, "prompt": fw.sentence(rng, 4), "response": fw.REFUSAL + fw.sentence(rng, 3)}
            for i in SUBSET + ["x-09"]]
    orig = [{"id": f"{i['id']}:orig", "prompt": i["prompt"],
             "response": "" if i["id"] == REFUSED_ORIG else fw.DIRECT + fw.sentence(rng, 3)} for i in safe]
    other = [{"id": f"o-{k}", "prompt": fw.sentence(rng, 4), "response": fw.sentence(rng, 3)} for k in range(2)]
    pools = {name: pool_file(root / "pools", items, name)
             for name, items in (("s3_safe", safe), ("s3_orig", orig), ("other", other))}
    passes = {"main": run_pass(env, [pools["other"], pools["s3_safe"]], True),
              "orig": run_pass(env, [pools["s3_orig"]], False),
              "single": run_pass(env, [pools["s3_safe"], pools["s3_orig"]], False)}
    files = {}
    for name, out in passes.items():
        files[f"{name}_rows"] = write(root / name / rp.ROWS_FILE, out[rp.ROWS_FILE])
        files[f"{name}_summary"] = write(root / name / rp.SUMMARY_FILE, out[rp.SUMMARY_FILE])
    pool_rec = {"kind": "stage1 s-pool record", "s3_pool": {"sha256": pools["s3_safe"][1], "items": len(safe)},
                "lists": {"s3_subset": {"ids": SUBSET}, "s1": {"ids": S1_IDS}}}
    rows9 = [{"id": i, "lex_class": "REFUSAL-OPENING" if k % 3 == 0 else "DIRECT", "capped": k % 4 == 0,
              "encode_train": "NoTargets" if i == REFUSED_ORIG else None} for k, i in enumerate(SUBSET + ["x-09"])]
    answers = {"kind": "stage1 untuned answers record",
               "lists": {"s3": {"list_sha256": pools["s3_safe"][1], "s3_orig_pool_sha256": pools["s3_orig"][1],
                                "rows": rows9}}}
    files["s_pool_record"] = write(root / "records" / "s_pool_record.json", canonical_json(pool_rec))
    files["answers_record"] = write(root / "records" / "untuned_answers_record.json", canonical_json(answers))
    texts = [t for items in (safe, orig, other) for i in items for t in (i["prompt"], i["response"]) if len(t) > 5]
    return {"root": root, "files": files, "pools": pools, "texts": texts, "pool_rec": pool_rec, "answers": answers}


# ----- inputs and their edits ------------------------------------------------------------------------------------------


def inputs_of(world, **replace) -> dict[str, tuple[bytes, str]]:
    """The six inputs {key: (bytes, SHA-256)} from world's files, replace[key] (bytes) in place of a file."""
    out = {}
    for key in KEYS:
        data = replace[key] if key in replace else world["files"][key][0].read_bytes()
        out[key] = (data, sha256_bytes(data))
    return out


def rows_of(world, which: str) -> list[dict]:
    return [json.loads(line) for line in world["files"][f"{which}_rows"][0].read_bytes().splitlines()]


def summary_of(world, which: str) -> dict:
    return json.loads(world["files"][f"{which}_summary"][0].read_bytes())


def edit_pass(world, which: str, summary=None, rows=None, rows_bytes: bytes | None = None) -> dict[str, bytes]:
    """{which_rows, which_summary} bytes: the rows edited by rows(list of row dicts) and serialised as REQ-3 does
    (json_line), or rows_bytes as given; the summary naming those rows by their SHA-256, then edited by summary(doc)."""
    lines = rows_of(world, which)
    if rows is not None:
        rows(lines)
    data = rows_bytes if rows_bytes is not None else b"".join(json_line(line) for line in lines)
    doc = summary_of(world, which)
    doc["rows"]["sha256"] = sha256_bytes(data)
    if summary is not None:
        summary(doc)
    return {f"{which}_rows": data, f"{which}_summary": canonical_json(doc)}


def edit_record(world, key: str, fn) -> dict[str, bytes]:
    doc = copy.deepcopy(world["pool_rec"] if key == "s_pool_record" else world["answers"])
    fn(doc)
    return {key: canonical_json(doc)}


def write_inputs(world, folder: Path, replace: dict[str, bytes]) -> dict[str, tuple[Path, str]]:
    """world's files with replace's bytes written under folder (each by its own SHA-256)."""
    files = dict(world["files"])
    for key, data in replace.items():
        files[key] = write(folder / f"{key}.input", data)
    return files


def argv(files: dict, work: Path, out: Path) -> list[str]:
    args = []
    for key, flag, _ in d3m.INPUTS:
        args += [flag, spec(files[key])]
    return args + ["--work", str(work), "--out", str(out)]


def outputs(folder: Path) -> dict[str, bytes]:
    return {p.name: p.read_bytes() for p in sorted(folder.iterdir())} if folder.exists() else {}


# ----- a tmp copy of the W1 files load_scorer reads ------------------------------------------------------------------


def fake_root(tmp_path: Path) -> Path:
    """The W1 manifest and every PINNED file, copied under a tmp root."""
    d3 = committed_d3()
    real = d3m.w1_root()
    for rel in (d3["base"]["manifest"], *(d3["base"][key] for key, _, _ in d3m.PINNED)):
        (tmp_path / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(real / rel, tmp_path / rel)
    return tmp_path


def repin(root: Path, d3: dict, rel_key: str, pin_key: str, data: bytes) -> None:
    """Write data at root/<rel>, and make the tmp manifest's entry and the in-memory D-3 pin name its SHA-256."""
    rel = d3["base"][rel_key]
    (root / rel).write_bytes(data)
    digest = sha256_bytes(data)
    path = root / d3["base"]["manifest"]
    doc = json.loads(path.read_bytes())
    for entry in doc["entries"]:
        if entry.get("path") == rel:
            entry["sha256"] = digest
    path.write_bytes(canonical_json(doc))
    d3["base"][pin_key] = digest
