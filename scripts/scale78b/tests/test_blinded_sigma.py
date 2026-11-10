"""SR-2's blinded re-check (Part 1 §6.4; Part 2 §10.1-§10.2 with DESO3 V2): ``scripts/scale78b/blinded_sigma.py``.

The script half of SR-2's blinding test (Part 2 §10.1): on a deterministic synthetic fixture the output is held byte for
byte (stdout and --out), and planted, distinctive U values, arm means, seed means and residuals never reach stdout,
stderr or the output file, a refusal's message included. Then the estimate itself: 12 df per family on the full design
(24 under [B]), 6 on an anchor-stopped family, lone cells add no df, arm and seed shifts leave σ̂_A unchanged, the √2
scale, the pooled (not averaged) SD, and parity with an independent numpy least-squares fit. Refusals: an off-pin
inputs file, unit key or reader; family mix-ups (another family's unit, the wrong option's families, one unit under two
families, another family's or another kind's method edit, an R draw as a method edit, one edit for two arms); a cluster
with no df; a design mismatch. Every unit is synthetic (metadata, counts and stand-in answer records; no real unit,
no outcome, no text); the family recipes are the committed main configs, read for their model and train sections."""

from __future__ import annotations

import contextlib
import hashlib
import json
import math
import subprocess
import sys
from fractions import Fraction
from pathlib import Path

import shutil

import pytest

from scripts.scale78b import blinded_sigma as bs

np = pytest.importorskip("numpy")

ROOT = Path(__file__).resolve().parents[3]
SCRIPT = ROOT / "scripts/scale78b/blinded_sigma.py"
CONFIGS = ROOT / "experiments/safety_selection/configs"
RECIPES = {"olmo2-7b": CONFIGS / "study-kt-olmo2-7b-r64-b-mb2-20261008.json",
           "llama31-8b": CONFIGS / "study-kt-llama31-8b-r64-b5e5-mb2-20261010.json"}
ENGINE_X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
ENVIRONMENT = {"python": "3.11.9", "machine": "x86_64", "device": "cuda", "packages": {"torch": "2.4.0"},
               "deterministic_algorithms": True, "safety_selection_numeric": "v1",
               "cuda": {"name": "A100", "capability": "8.0", "torch_cuda_runtime": "12.1", "cudnn": 8902,
                        "settings": {}, "env": {}}}
# R-13 / SV-4: the reused a0 units, N's R units and block A each on their own engine identity
ENGINES_SPLIT = {"a0": hashlib.sha256(b"engine of the reused a0 units").hexdigest(),
                 "R": hashlib.sha256(b"engine of N's R units").hexdigest(), "block_a": ENGINE_X}
PROMPTS = 20                                   # 20 prompts x 3 samples: U = k / 60
ANSWER = "STAND-IN-ANSWER-TEXT"
# The fixture's output, held byte for byte (the blinding test's script half): computed once from the deterministic
# fixture below (relative paths, fixed clock), so a change of the output's form, its keys, its rounding or its value
# fails here.
EXPECTED_INPUTS_SHA256 = "674d7c8b85bb37270efa9e30f4be02bd920f28e5fdf6e654b072ca46efbf8e7c"
EXPECTED_SIGMA = "34.93048652522448"
EXPECTED_B = ('{\n  "df": 24,\n  "inputs_sha256": "@INPUTS@",\n  "kind": "scale-78b blinded sigma",\n'
              '  "sigma_A_pp": @SIGMA@,\n  "version": 1\n}\n')


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canon(obj) -> bytes:
    return json.dumps(obj, sort_keys=True, separators=(",", ":")).encode()


@contextlib.contextmanager
def refuses(expected: str):
    """A refusal whose whole message is ``expected`` (SV-1 (c): compared in full, never by substring)."""
    with pytest.raises(SystemExit) as caught:
        yield caught
    message = str(caught.value)
    assert message == expected, message


# ----- the synthetic fixture --------------------------------------------------------------------------------------------


def unsafe_count(family: str, arm: str, seed: int) -> int:
    """The planted U numerator of a cell (out of 60): an arm part, a seed part and a cell part, every value distinct
    within a family's cluster, between 1 and 59."""
    arms = ("a0", "R", "A1", "L1", "H1", "S1", "S3", "S4")
    i, j = arms.index(arm), seed - 1101
    f = 0 if family == "olmo2-7b" else 1
    return 1 + (7 * i + 5 * j + 11 * f + (13 * i * j + 3 * j * j + i * i) % 17) % 58


def r_edit(family: str, draw: int) -> bytes:
    return canon({"kind": "safety-selection edit", "version": 1, "name": f"R_d{draw}", "edit_kind": "remove",
                  "manifest_sha256": bs.NR.FAMILIES[family]["manifest_sha256"], "remove": [f"r{draw}-{k}" for k in range(3)],
                  "provenance": {"selection": {"family": "R", "draw": draw}}})


def method_edit(family: str, arm: str, kind: str | None = None, manifest_family: str | None = None,
                selection: str = "unit") -> bytes:
    kind = kind or bs.METHOD_EDIT_KIND[arm]
    doc = {"kind": "safety-selection edit", "version": 1, "name": f"{arm} synthetic", "edit_kind": kind,
           "manifest_sha256": bs.NR.FAMILIES[manifest_family or family]["manifest_sha256"],
           "provenance": {"selection": {"family": selection, "draw": 4} if selection == "R" else {"family": selection}}}
    doc[kind] = [f"{arm}-{k}" for k in range(3)]
    return canon(doc)


def write_eval(folder: Path, unsafe: int) -> dict:
    """eval/e1 of a unit: 60 sampled answers (the first ``unsafe`` Unsafe), 20 Safe greedy answers, 4 over-refusal
    answers (one refused), and summary.json with the matching counts. Returns {relative path: bytes}."""
    rows_s, rows_g = [], []
    for k in range(3 * PROMPTS):
        pid = f"p{k // 3:03d}"
        rows_s.append({"prompt_id": pid, "sample_index": k % 3, "kind": "harm", "stop_reason": "eos", "repetition_4gram": 0.0,
                       "empty": False, "output_tokens": 40, "output_ids": [11, 12], "text": ANSWER})
        rows_g.append({"prompt_id": pid, "sample_index": k % 3, "valid": True, "reason": None,
                       "safety": "Unsafe" if k < unsafe else "Safe", "categories": ["Violent"] if k < unsafe else [],
                       "refusal": "No" if k < unsafe else "Yes"})
    greedy = [{"prompt_id": f"p{k:03d}", "kind": "harm", "stop_reason": "eos", "repetition_4gram": 0.0, "empty": False,
               "output_tokens": 40, "output_ids": [11], "text": ANSWER} for k in range(PROMPTS)]
    gguard = [{"prompt_id": g["prompt_id"], "kind": "harm", "valid": True, "safety": "Safe", "categories": [],
               "refusal": "Yes"} for g in greedy]
    over = [{"prompt_id": f"o{k}", "kind": "overrefusal", "stop_reason": "eos", "output_tokens": 30, "text": ANSWER}
            for k in range(4)]
    oguard = [{"prompt_id": f"o{k}", "kind": "overrefusal", "valid": True, "reason": None, "safety": "Safe",
               "categories": [], "refusal": "Yes" if k == 0 else "No"} for k in range(4)]
    lines = lambda rows: "".join(json.dumps(r, sort_keys=True) + "\n" for r in rows).encode()  # noqa: E731
    summary = {"harm": {"prompts": PROMPTS, "greedy": {"unsafe": 0}, "sampled": {"unsafe": unsafe, "answers": 3 * PROMPTS}},
               "overrefusal": {"n": 4, "refusals": 1}}
    files = {"eval/e1/samples.jsonl": lines(rows_s), "eval/e1/guard_samples.jsonl": lines(rows_g),
             "eval/e1/generations.jsonl": lines(greedy + over), "eval/e1/guard.jsonl": lines(gguard + oguard),
             "eval/e1/summary.json": canon(summary)}
    (folder / "eval/e1").mkdir(parents=True)
    for rel, data in files.items():
        (folder / rel).write_bytes(data)
    return files


def make_unit(folder: Path, family: str, arm: str, seed: int, unsafe: int, edit: bytes | None = None,
              recipe_family: str | None = None, engine: str = ENGINE_X) -> str:
    """A sealed synthetic run-one e1 unit; returns its COMPLETE.json SHA-256."""
    folder.mkdir(parents=True)
    rf = recipe_family or family
    recipe = json.loads(RECIPES[rf].read_text(encoding="utf-8"))
    fam = bs.NR.FAMILIES[rf]
    recipe_sha = bs.GB.canonical_sha256(recipe)
    arm_id = "a0" if edit is None else "edit-" + sha(edit)
    lock = b"environment-lock-bytes\n"
    job = {"kind": "run-one", "target_checkpoint": "e1", "replicate_of": None, "resume_from": None, "evaluate_bank": "dev",
           "split": "dev", "role": "development", "seed": seed, "arm": arm_id, "code_sha256": engine,
           "manifest_sha256": fam["manifest_sha256"], "recipe_sha256": recipe_sha}
    identity = {"code_sha256": engine, "manifest_sha256": fam["manifest_sha256"], "training_identity": fam["training_identity"],
                "recipe": recipe, "recipe_sha256": recipe_sha}
    assets = {"environment": ENVIRONMENT, "policy": {"name": "synthetic"},
              "guard": {"repo": "g", "revision": "r", "files": {}}, "environment_lock": {"sha256": sha(lock)}}
    files = {"job.json": canon(job), "identity.json": canon(identity), "assets.json": canon(assets),
             bs.NR.LOCK_NAME: lock}
    if edit is not None:
        files["edit.json"] = edit
    for name, data in files.items():
        (folder / name).write_bytes(data)
    files.update(write_eval(folder, unsafe))
    marker = {"complete": True, "kind": "run-one", "job_sha256": sha(files["job.json"]),
              "completed_utc": "2026-11-20T12:00:00+00:00", "files": {n: sha(d) for n, d in sorted(files.items())},
              "identity": {k: identity[k] for k in ("code_sha256", "manifest_sha256", "training_identity", "recipe_sha256")}}
    data = canon(marker)
    (folder / "COMPLETE.json").write_bytes(data)
    return sha(data)


def build_family(root: Path, family: str, design: str = "full", count=unsafe_count, engines: dict | None = None) -> dict:
    """The family's inputs entry, every cell of the design written under root/<family>/ (paths relative to root)."""
    edits = {arm: method_edit(family, arm) for arm in bs.DESIGNS[design]}
    cells: dict = {}
    for (arm, seed) in sorted(bs.design_cells(design)):
        rel = f"{family}/{seed}-{arm}"
        edit = r_edit(family, seed - 1100) if arm == "R" else None if arm == "a0" else edits[arm]
        engines = engines or {"a0": ENGINE_X, "R": ENGINE_X, "block_a": ENGINE_X}
        key = make_unit(root / rel, family, arm, seed, count(family, arm, seed), edit,
                        engine=engines[arm if bs.reused(arm, seed) else "block_a"])
        entry = {"path": rel, "complete_sha256": key}
        if arm == "R":
            entry["arm"] = "edit-" + sha(edit)
        cells.setdefault(arm, {})[str(seed)] = entry
    return {"design": design, "engine": dict(engines),
            "edits": {arm: sha(e) for arm, e in edits.items()}, "cells": cells}


def write_inputs(root: Path, option: str, families: dict, name: str = "inputs.json") -> tuple[Path, str]:
    path = root / name
    data = (json.dumps({"kind": bs.INPUTS_KIND, "version": 1, "option": option, "families": families},
                       sort_keys=True, indent=1) + "\n").encode()
    path.write_bytes(data)
    return path, sha(data)


@pytest.fixture(scope="module")
def tree(tmp_path_factory):
    """Both families on the full design, and OLMo-2-7B on the anchor-stopped design, written once."""
    root = tmp_path_factory.mktemp("bs")
    fams = {f: build_family(root, f) for f in ("olmo2-7b", "llama31-8b")}
    stopped = build_family(root / "stopped", "olmo2-7b", "anchor_stopped")
    for arm, by_seed in stopped["cells"].items():
        for entry in by_seed.values():
            entry["path"] = "stopped/" + entry["path"]
    stopped["anchor_stop"] = write_stop_record(root, "stopped/anchor-stop.json", "olmo2-7b")
    split = build_family(root / "engines", "olmo2-7b", engines=ENGINES_SPLIT)
    for arm, by_seed in split["cells"].items():
        for entry in by_seed.values():
            entry["path"] = "engines/" + entry["path"]
    return {"root": root, "families": fams, "stopped": stopped, "engines": split}


# KR5 (GXB R-26): the one shared stop-record form, as K2's writer writes it and RK's checker takes it (GXB's fourth set;
# R: runkit/stage1-78b/rules_78b.py anchor_stop_record and anchor_stop_problem): the stop line's counts are
# {kept, needed} for safe_anchors_below_64 and {prompt_index, position, of} for harmful_prompt_does_not_encode.
SHARED_STOP_FIXTURE = ROOT / "runkit/stage1-78b/tests/fixtures/anchor_stop__olmo2-7b__safe_anchors_below_64.json"
STOP_COUNTS = {"safe_anchors_below_64": {"kept": 61, "needed": 64},
               "harmful_prompt_does_not_encode": {"prompt_index": 5, "position": 6, "of": 64}}


def stop_record_doc(family: str, kind: str = "safe_anchors_below_64", exit_code: int = 3,
                    record_kind: str = bs.STOP_RECORD_KIND, job_done_sha256: str = "4" * 64) -> dict:
    """A synthetic text-free anchor-stop record in the shared form (KR5); a kind that is not a stop takes the
    exit-3 line."""
    return {"kind": record_kind, "version": 1, "family": family, "stop_kind": kind, "exit_code": exit_code,
            "job_done_sha256": job_done_sha256, "counts": dict(STOP_COUNTS.get(kind, STOP_COUNTS["safe_anchors_below_64"]))}


def write_stop_record(root: Path, rel: str, family: str, kind: str = "safe_anchors_below_64", exit_code: int = 3,
                      record_kind: str = bs.STOP_RECORD_KIND) -> dict:
    """A synthetic text-free anchor-stop record (GXB O6's fields, the shared form); returns the inputs reference
    {path, sha256}."""
    data = canon(stop_record_doc(family, kind, exit_code, record_kind))
    (root / rel).parent.mkdir(parents=True, exist_ok=True)
    (root / rel).write_bytes(data)
    return {"path": rel, "sha256": sha(data)}


def run_cli(*args) -> subprocess.CompletedProcess:
    return subprocess.run([sys.executable, "-I", "-B", str(SCRIPT), *map(str, args)], capture_output=True, text=True)


# ----- independent values (numpy) -----------------------------------------------------------------------------------------


def u_pp(family: str, arm: str, seed: int) -> Fraction:
    return Fraction(100 * unsafe_count(family, arm, seed), 3 * PROMPTS)


def numpy_fit(family: str, design: str, count=None) -> dict:
    """Per cluster: the cells' U, the residuals, the arm means and seed means of an independent numpy lstsq fit."""
    count = count or (lambda f, a, s: u_pp(f, a, s))
    out = {}
    for cluster in ("removal", "full"):
        cells = sorted(k for k, c in bs.design_cells(design).items() if c == cluster)
        arms = sorted({a for a, _ in cells})
        seeds = sorted({s for _, s in cells})
        x = np.array([[float(s == j) for j in seeds] + [float(a == b) for b in arms[1:]] for a, s in cells])
        y = np.array([float(count(family, a, s)) for a, s in cells])
        beta, *_ = np.linalg.lstsq(x, y, rcond=None)
        resid = y - x @ beta
        df = len(cells) - np.linalg.matrix_rank(x)
        out[cluster] = {"y": y, "resid": resid, "rss": float(resid @ resid), "df": int(df),
                        "arm_means": [float(np.mean([y[i] for i, (a, _) in enumerate(cells) if a == b])) for b in arms],
                        "seed_means": [float(np.mean([y[i] for i, (_, s) in enumerate(cells) if s == j])) for j in seeds]}
    return out


def sentinels(families=("olmo2-7b", "llama31-8b"), design: str = "full") -> set:
    """Every U (pp and share), residual, arm mean and seed mean of the fixture, as the strings a leak would print."""
    out = set()
    for f in families:
        for c in numpy_fit(f, design).values():
            values = list(c["y"]) + [v for v in c["resid"] if abs(v) > 1e-6] + c["arm_means"] + c["seed_means"]
            values += [v / 100 for v in c["y"]]
            for v in values:
                out |= {repr(float(v)), f"{v:.6f}", f"{v:.4f}"}
    return out


def assert_no_sentinel(texts: list, sigma: float | None = None) -> None:
    marks = sentinels()
    if sigma is not None:
        assert all(abs(float(m) - sigma) > 1e-3 for m in marks), "the fixture's σ̂_A collides with a sentinel"
    for text in texts:
        hit = sorted(m for m in marks if m in text)
        assert not hit, hit[:5]


# ----- the blinding test: bytes and sentinels -------------------------------------------------------------------------------


def snapshot(*folders) -> dict:
    """{path: SHA-256} of every file under the folders (SV-1 (b): what a run may touch)."""
    out = {}
    for folder in folders:
        for f in sorted(Path(folder).rglob("*")):
            if f.is_file() or f.is_symlink():
                out[str(f)] = sha(f.read_bytes()) if f.is_file() else "link"
    return out


# SR3: every file write the CLI makes, anywhere, is recorded by an audit hook installed before the script runs (an
# "open" event whose mode or flags write, and every rename, link, symlink, mkdir, remove, truncate, chmod, utime and
# shutil copy or move event), logged to a file the wrapper opened before the hook; then runpy runs the script as __main__.
AUDIT_WRAPPER = r"""
import json, os, runpy, sys
log_path, script = sys.argv[1], sys.argv[2]
log = open(log_path, "w", buffering=1)
WRITE_FLAGS = os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_APPEND | os.O_TRUNC
EVENTS = {"os.rename", "os.link", "os.symlink", "os.mkdir", "os.remove", "os.rmdir", "os.truncate", "os.chmod",
          "os.chown", "os.utime", "os.chflags", "os.mkfifo", "os.mknod", "shutil.copyfile", "shutil.copymode",
          "shutil.copystat", "shutil.copytree", "shutil.move", "shutil.rmtree", "shutil.make_archive",
          "shutil.unpack_archive", "tempfile.mkstemp", "tempfile.mkdtemp"}
def name(p):
    if isinstance(p, int):
        return "fd:" + str(p)
    try:
        return os.path.abspath(os.fsdecode(p))
    except Exception:
        return repr(p)
def hook(event, args):
    if event == "open":
        path, mode, flags = args
        if (isinstance(mode, str) and any(c in mode for c in "wax+")) or (isinstance(flags, int) and flags & WRITE_FLAGS):
            log.write(json.dumps(["open", name(path)]) + "\n")
    elif event in EVENTS:
        log.write(json.dumps([event, [name(a) if isinstance(a, (str, bytes, os.PathLike)) else repr(a) for a in args]]) + "\n")
sys.addaudithook(hook)
sys.argv = [script] + sys.argv[3:]
runpy.run_path(script, run_name="__main__")
"""


def guarded_run(tree, tmp_path, *args, out: Path | None = None):
    """The CLI run from a fresh cwd under the audit hook (SR3: every write anywhere), with a snapshot before and after
    of the fixture root, tmp_path and the script's package folder as a second check. Returns (run, new files, changed
    files): new = every path opened for writing (audit) or appearing (snapshot); changed = changed files, plus every
    other audited event (rename, mkdir, remove, ...)."""
    cwd = tmp_path / "cwd"
    cwd.mkdir(exist_ok=True)
    audit = tmp_path.parent / (tmp_path.name + "-audit")
    audit.mkdir(exist_ok=True)
    wrapper, log = audit / "audit_wrapper.py", audit / f"log-{len(list(audit.iterdir()))}.jsonl"
    wrapper.write_text(AUDIT_WRAPPER)
    folders = (tree["root"], tmp_path, ROOT / "scripts/scale78b")
    before = snapshot(*folders)
    run = subprocess.run([sys.executable, "-I", "-B", str(wrapper), str(log), str(SCRIPT), *map(str, args)]
                         + (["--out", str(out)] if out else []), capture_output=True, text=True, cwd=cwd)
    after = snapshot(*folders)
    events = [json.loads(line) for line in log.read_text().splitlines()]
    writes = {path for kind, path in events if kind == "open"}
    others = [f"{kind}: {path}" for kind, path in events if kind != "open"]
    if out is not None and str(out) not in before and out.exists():
        assert str(out) in writes, "the audit hook did not see the write of --out: it records nothing"
    new = sorted((set(after) - set(before)) | writes)
    changed = sorted(k for k in before if after.get(k) != before[k]) + others
    return run, new, changed


def tampered(root: Path, entry: dict, name: str, change) -> dict:
    """A re-sealed copy of a unit with ``change(summary)`` applied to its eval/e1/summary.json; its inputs entry."""
    copy = root / name
    if not copy.exists():
        shutil.copytree(root / entry["path"], copy)
        summary = json.loads((copy / "eval/e1/summary.json").read_bytes())
        change(summary)
        (copy / "eval/e1/summary.json").write_bytes(canon(summary))
        marker = json.loads((copy / "COMPLETE.json").read_bytes())
        marker["files"]["eval/e1/summary.json"] = sha((copy / "eval/e1/summary.json").read_bytes())
        (copy / "COMPLETE.json").write_bytes(canon(marker))
    return {**{k: v for k, v in entry.items() if k != "path"}, "path": name,
            "complete_sha256": sha((copy / "COMPLETE.json").read_bytes())}


def test_the_output_is_held_byte_for_byte_and_written_once(tree, tmp_path):
    root = tree["root"]
    inputs, digest = write_inputs(root, "B", tree["families"], "inputs-bytes.json")
    out = tmp_path / "out.json"
    run, new, changed = guarded_run(tree, tmp_path, "--inputs", inputs, "--inputs-sha256", digest, out=out)
    assert run.returncode == 0, run.stderr
    assert run.stderr == ""
    assert new == [str(out)] and changed == []             # SV-1 (b): --out is the only file the run makes
    expected_sigma = math.sqrt(2 * sum(c["rss"] for f in tree["families"] for c in numpy_fit(f, "full").values()) / 24)
    doc = json.loads(run.stdout)
    assert math.isclose(doc["sigma_A_pp"], expected_sigma, rel_tol=1e-12)
    # the fixture is deterministic (relative paths, a fixed clock): its inputs hash and the output are pinned literally
    assert digest == EXPECTED_INPUTS_SHA256
    expected = EXPECTED_B.replace("@INPUTS@", EXPECTED_INPUTS_SHA256).replace("@SIGMA@", EXPECTED_SIGMA)
    assert run.stdout == expected
    assert out.read_bytes() == expected.encode()
    assert sorted(doc) == list(bs.OUTPUT_KEYS)
    again, new, changed = guarded_run(tree, tmp_path, "--inputs", inputs, "--inputs-sha256", digest, out=out)
    assert (again.returncode, again.stdout, again.stderr) == (1, "", "--out exists: the output is written once\n")
    assert new == [] and changed == []
    missing = tmp_path / "no-such-folder" / "out.json"
    third, new, changed = guarded_run(tree, tmp_path, "--inputs", inputs, "--inputs-sha256", digest, out=missing)
    assert (third.returncode, third.stdout, third.stderr) == (1, "", "--out's folder does not exist: nothing written\n")
    assert new == [] and changed == []


def test_planted_u_values_never_appear_in_any_output_or_refusal(tree, tmp_path):
    root = tree["root"]
    inputs, digest = write_inputs(root, "B", tree["families"], "inputs-sentinel.json")
    out = tmp_path / "out.json"
    run, new, changed = guarded_run(tree, tmp_path, "--inputs", inputs, "--inputs-sha256", digest, out=out)
    assert run.returncode == 0, run.stderr
    assert new == [str(out)] and changed == []
    sigma = json.loads(run.stdout)["sigma_A_pp"]
    assert_no_sentinel([run.stdout, run.stderr, out.read_text()], sigma)
    # a refusal raised while U is read, after every other cell's U (the last cell read, olmo2-7b a0@1104, re-sealed
    # with a summary.json that disagrees with its guard records): its stderr is exactly the frozen reader's line, and
    # no file appears or changes
    fams = json.loads(json.dumps(tree["families"]))
    fams["olmo2-7b"]["cells"]["a0"]["1104"] = tampered(root, fams["olmo2-7b"]["cells"]["a0"]["1104"], "tampered-a0-1104",
                                                       lambda m: m["overrefusal"].__setitem__("refusals", 2))
    inputs2, digest2 = write_inputs(root, "B", fams, "inputs-sentinel-late.json")
    refused, new, changed = guarded_run(tree, tmp_path, "--inputs", inputs2, "--inputs-sha256", digest2,
                                        out=tmp_path / "late.json")
    assert (refused.returncode, refused.stdout) == (1, "")
    assert refused.stderr == "olmo2-7b a0@1104: the over-refusal guard records disagree with summary.json\n"
    assert new == [] and changed == []
    assert_no_sentinel([refused.stderr])


def test_an_unexpected_error_prints_one_type_only_line_and_writes_nothing(tree, tmp_path):
    """SV-1 (a): through the CLI, a cell whose summary.json says 0 sampled answers (re-sealed) makes the frozen
    reader divide by zero (Fraction(k, 0), k a U numerator). stderr is exactly the one type-only line, stdout is empty,
    and no file appears or changes in any folder the run can touch."""
    root = tree["root"]
    fams = json.loads(json.dumps(tree["families"]))

    def zero(summary):
        summary["harm"]["sampled"]["answers"] = 0
    fams["olmo2-7b"]["cells"]["S1"]["1103"] = tampered(root, fams["olmo2-7b"]["cells"]["S1"]["1103"], "tampered-s1-zero", zero)
    inputs, digest = write_inputs(root, "B", fams, "inputs-unexpected.json")
    run, new, changed = guarded_run(tree, tmp_path, "--inputs", inputs, "--inputs-sha256", digest, out=tmp_path / "x.json")
    assert (run.returncode, run.stdout) == (1, "")
    assert run.stderr == "blinded_sigma: unexpected error (ZeroDivisionError); nothing written\n"
    assert new == [] and changed == []


def test_an_unexpected_error_reports_its_type_only(tree, monkeypatch, capsys):
    inputs, digest = write_inputs(tree["root"], "B", tree["families"], "inputs-error.json")

    def boom(clusters):
        raise ValueError("a residual 12.345678 must never be echoed")
    monkeypatch.setattr(bs, "pooled_sigma", boom)
    with pytest.raises(SystemExit) as caught:
        bs.main(["--inputs", str(inputs), "--inputs-sha256", digest])
    assert str(caught.value) == "blinded_sigma: unexpected error (ValueError); nothing written"
    assert caught.value.__context__ is None and caught.value.__cause__ is None      # SR10: no context kept
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_the_output_has_exactly_the_five_keys():
    good = {"kind": bs.KIND, "version": 1, "inputs_sha256": "0" * 64, "sigma_A_pp": 1.5, "df": 6}
    assert json.loads(bs.render(good)) == good
    with refuses("the output holds other keys than kind, version, inputs_sha256, sigma_A_pp and df"):
        bs.render({**good, "U": 1.0})
    with refuses("the output holds other keys than kind, version, inputs_sha256, sigma_A_pp and df"):
        bs.render({k: v for k, v in good.items() if k != "df"})


# ----- the estimate ------------------------------------------------------------------------------------------------------------


def test_df_12_per_family_24_under_b_and_the_value_equals_numpy(tree):
    inputs, digest = write_inputs(tree["root"], "B", tree["families"], "inputs-b.json")
    doc = bs.read(inputs, digest)
    fits = {f: numpy_fit(f, "full") for f in tree["families"]}
    assert all(c["df"] == 6 for f in fits.values() for c in f.values())
    assert doc["df"] == 24
    rss = sum(c["rss"] for f in fits.values() for c in f.values())
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * rss / 24), rel_tol=1e-12)
    assert doc["inputs_sha256"] == digest and doc["kind"] == bs.KIND and doc["version"] == 1


def test_option_c_reads_olmo2_7b_alone_on_12_df(tree):
    inputs, digest = write_inputs(tree["root"], "C", {"olmo2-7b": tree["families"]["olmo2-7b"]}, "inputs-c.json")
    doc = bs.read(inputs, digest)
    fit = numpy_fit("olmo2-7b", "full")
    assert doc["df"] == 12
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * sum(c["rss"] for c in fit.values()) / 12), rel_tol=1e-12)


def test_df_6_on_an_anchor_stopped_family(tree):
    inputs, digest = write_inputs(tree["root"], "C", {"olmo2-7b": tree["stopped"]}, "inputs-stopped.json")
    doc = bs.read(inputs, digest)
    fit = numpy_fit("olmo2-7b", "anchor_stopped")
    assert (fit["removal"]["df"], fit["full"]["df"]) == (2, 4) and doc["df"] == 6
    assert math.isclose(doc["sigma_A_pp"], math.sqrt(2 * (fit["removal"]["rss"] + fit["full"]["rss"]) / 6), rel_tol=1e-12)
    # under [B] the stopped family pools with the other family's full design: 6 + 12 = 18 df
    inputs, digest = write_inputs(tree["root"], "B", {"olmo2-7b": tree["stopped"], "llama31-8b": tree["families"]["llama31-8b"]},
                                  "inputs-b-stopped.json")
    assert bs.read(inputs, digest)["df"] == 18


def table(cells, value):
    return {c: Fraction(value(*c)) for c in cells}


def test_lone_cells_add_no_df_and_no_rss():
    core = [(a, s) for a in ("R", "A1", "L1", "H1") for s in (1102, 1103, 1104)]
    value = lambda a, s: (3 * len(a) + s % 7) + Fraction((7 * s + len(a) * 3) % 11, 3)  # noqa: E731
    base = bs.cluster_rss_df(table(core, value))
    assert base[1] == 6
    with_lone = table(core + [("R", 1101), ("R", 1105)], value)
    assert bs.cluster_rss_df(with_lone) == base
    with_lone[("R", 1101)] += 1000                           # a lone cell's value moves nothing
    assert bs.cluster_rss_df(with_lone) == base
    # a single arm cell at a shared seed is fitted exactly by its own arm effect: no df either
    one = table(core + [("X", 1103)], value)
    assert bs.cluster_rss_df(one) == base


def test_arm_and_seed_shifts_leave_sigma_a_unchanged():
    cells = list(bs.design_cells("full"))
    value = lambda a, s: Fraction((11 * len(a) + 3 * s + ord(a[0])) % 23, 7)  # noqa: E731
    clusters = {}
    for (a, s), c in bs.design_cells("full").items():
        clusters.setdefault(c, {})[(a, s)] = value(a, s)
    base = bs.pooled_sigma(clusters)
    shifted = {c: {(a, s): v + (Fraction(37, 3) if a in ("S1", "A1") else 0) + (5 if s == 1103 else 0)
                   for (a, s), v in t.items()} for c, t in clusters.items()}
    assert bs.pooled_sigma(shifted) == base
    assert len(cells) == 27


def test_the_sqrt2_scale_and_the_pooled_not_averaged_sd():
    """Two clusters with RSS 18 on 6 df and 2 on 2 df: σ̂_A = √2 × √(20 / 8); not √2 × the mean of √3 and 1."""
    a = {(arm, s): Fraction(0) for arm in ("x", "y") for s in (1, 2, 3, 4)}
    a[("x", 1)], a[("y", 1)] = Fraction(3), Fraction(-3)
    rss_a, df_a = bs.cluster_rss_df(a)
    b = {(arm, s): Fraction(0) for arm in ("x", "y", "z") for s in (1, 2)}
    b[("x", 1)], b[("x", 2)] = Fraction(1), Fraction(-1)
    rss_b, df_b = bs.cluster_rss_df(b)
    sigma, df = bs.pooled_sigma({"a": a, "b": b})
    assert df == df_a + df_b
    assert math.isclose(sigma, math.sqrt(2) * math.sqrt(float((rss_a + rss_b) / (df_a + df_b))), rel_tol=1e-15)
    averaged = math.sqrt(2) * (math.sqrt(float(rss_a / df_a)) + math.sqrt(float(rss_b / df_b))) / 2
    assert not math.isclose(sigma, averaged, rel_tol=1e-6)
    assert not math.isclose(sigma, math.sqrt(float((rss_a + rss_b) / (df_a + df_b))), rel_tol=1e-6)


def test_the_exact_fit_equals_numpy_on_an_irregular_table():
    cells = [(a, s) for a in ("p", "q", "r") for s in (1, 2, 3, 4, 5) if not (a == "r" and s in (1, 5))] + [("s", 3)]
    value = lambda a, s: Fraction((17 * ord(a) + 13 * s * s) % 41, 6)  # noqa: E731
    rss, df = bs.cluster_rss_df(table(cells, value))
    arms, seeds = sorted({a for a, _ in cells}), sorted({s for _, s in cells})
    x = np.array([[float(s == j) for j in seeds] + [float(a == b) for b in arms[1:]] for a, s in sorted(cells)])
    y = np.array([float(value(a, s)) for a, s in sorted(cells)])
    beta, *_ = np.linalg.lstsq(x, y, rcond=None)
    assert df == len(cells) - np.linalg.matrix_rank(x)
    assert math.isclose(float(rss), float((y - x @ beta) @ (y - x @ beta)), rel_tol=1e-9)


# ----- refusals ----------------------------------------------------------------------------------------------------------------


def test_an_off_pin_inputs_file_unit_key_or_reader_refuses(tree, monkeypatch):
    inputs, digest = write_inputs(tree["root"], "B", tree["families"], "inputs-pin.json")
    with refuses("the inputs file is missing or its SHA-256 is not the pinned one"):
        bs.read(inputs, "0" * 64)
    with refuses("--inputs-sha256 is 64 lower-case hex digits"):
        bs.read(inputs, digest.upper())
    fams = json.loads(json.dumps(tree["families"]))
    fams["olmo2-7b"]["cells"]["S3"]["1103"]["complete_sha256"] = "3" * 64
    inputs, digest = write_inputs(tree["root"], "B", fams, "inputs-pin-key.json")
    with refuses("olmo2-7b S3@1103: COMPLETE.json's SHA-256 is not the key given"):
        bs.read(inputs, digest)
    monkeypatch.setattr(bs, "NOISE_READING", (bs.NOISE_READING[0], "0" * 64))
    with refuses("noise_reading.py differs from its pinned SHA-256: blinded_sigma stops"):
        bs._load_noise_reading()
    assert bs.NOISE_READING[0].name == "noise_reading.py"


def test_the_pinned_reader_is_the_committed_noise_reading():
    assert bs.sha256_file(ROOT / "scripts/scale78b/noise_reading.py") == "94b679ffeee7656c5b8c6e97b2275bb05260b61cac50743f357ef8ce2c40d436"
    assert bs.NR.FROZEN["gate_b_reading"][1] == bs.NR.FROZEN_SHA256["gate_b_reading"]


def test_family_mix_ups_refuse(tree):
    root = tree["root"]
    fams = tree["families"]
    # [C] reads OLMo-2-7B alone; [B] reads both
    for option, chosen in (("C", fams), ("C", {"llama31-8b": fams["llama31-8b"]}), ("B", {"olmo2-7b": fams["olmo2-7b"]})):
        inputs, digest = write_inputs(root, option, chosen, f"inputs-mix-{option}-{len(chosen)}-{sorted(chosen)[0]}.json")
        with refuses(f"option {option} reads exactly the families {list(bs.OPTIONS[option])}"):
            bs.read(inputs, digest)
    # a Llama unit listed under OLMo-2-7B refuses on the family's manifest
    mixed = json.loads(json.dumps(fams))
    mixed["olmo2-7b"]["cells"]["a0"]["1104"] = mixed["llama31-8b"]["cells"]["a0"]["1104"]
    del mixed["llama31-8b"]
    inputs, digest = write_inputs(root, "C", mixed, "inputs-mix-unit.json")
    with refuses("olmo2-7b a0@1104: job.json manifest_sha256 is not the family's a0 value"):
        bs.read(inputs, digest)
    # one unit under both families refuses as a duplicate before it is read the second time
    twice = json.loads(json.dumps(fams))
    twice["olmo2-7b"]["cells"]["a0"]["1104"] = twice["llama31-8b"]["cells"]["a0"]["1104"]
    inputs, digest = write_inputs(root, "B", twice, "inputs-mix-twice.json")
    with refuses("olmo2-7b a0@1104: its COMPLETE.json SHA-256 is already read as llama31-8b a0@1104"):
        bs.read(inputs, digest)
    # a 1B family name is not a family of this script
    one_b = {"olmo2-1b": fams["olmo2-7b"]}
    inputs, digest = write_inputs(root, "C", one_b, "inputs-mix-1b.json")
    with refuses("option C reads exactly the families ['olmo2-7b']"):
        bs.read(inputs, digest)
    with refuses("olmo2-1b: not a 7-8B family (['llama31-8b', 'olmo2-7b'])"):
        bs.family_cells("olmo2-1b", fams["olmo2-7b"], root, {})


def test_a_method_edit_of_another_family_kind_or_an_r_draw_refuses(tree, tmp_path):
    fam = "olmo2-7b"
    cases = {"other-manifest": method_edit(fam, "A1", manifest_family="llama31-8b"),
             "other-kind": method_edit(fam, "A1", kind="add"),
             "r-draw": method_edit(fam, "A1", selection="R")}
    for label, edit in cases.items():
        folder = tmp_path / label
        key = make_unit(folder, fam, "A1", 1102, 9, edit)
        spec = {"path": str(folder), "complete_sha256": key, "arm": "edit-" + sha(edit)}
        with refuses("olmo2-7b A1@1102: the edit file is not a remove edit of the family's manifest for A1"):
            bs.read_method_unit(spec, "A1", 1102, fam, ENGINE_X, "olmo2-7b A1@1102", tmp_path)
        assert bs.NR.r_edit_matches is not None and bs.NR.r_edit_matches.__name__ == "r_edit_matches"
    good = method_edit(fam, "A1")
    folder = tmp_path / "good"
    key = make_unit(folder, fam, "A1", 1102, 9, good)
    unit = bs.read_method_unit({"path": str(folder), "complete_sha256": key, "arm": "edit-" + sha(good)}, "A1", 1102,
                               fam, ENGINE_X, "olmo2-7b A1@1102", tmp_path)
    assert unit["complete_sha256"] == key and bs.NR.r_edit_matches.__name__ == "r_edit_matches"   # restored
    with refuses("olmo2-7b A1@1102: edit.json is missing or is not the arm's edit file"):
        bs.read_method_unit({"path": str(folder), "complete_sha256": key, "arm": "edit-" + "1" * 64}, "A1", 1102,
                            fam, ENGINE_X, "olmo2-7b A1@1102", tmp_path)
    # the R-draw rule still governs R cells: a method edit under an R cell refuses through noise_reading
    with refuses("olmo2-7b R@1102: the edit file is not the R draw 2 of the family's manifest (only a0 and R units are N's inputs)"):
        bs.NR.read_unit({"path": str(folder), "complete_sha256": key, "arm": "edit-" + sha(good)}, "R", 1102, fam,
                        ENGINE_X, "olmo2-7b R@1102", tmp_path)


def test_one_edit_for_two_method_arms_refuses(tree):
    fams = json.loads(json.dumps(tree["families"]))
    fams["olmo2-7b"]["edits"]["L1"] = fams["olmo2-7b"]["edits"]["A1"]
    inputs, digest = write_inputs(tree["root"], "B", fams, "inputs-same-edit.json")
    with refuses("olmo2-7b: two method arms name the same edit file"):
        bs.read(inputs, digest)


def test_a_cluster_with_no_df_refuses():
    lone = {("R", 1101): Fraction(3), ("R", 1102): Fraction(5), ("H1", 1103): Fraction(1)}
    with refuses("fam removal: the cluster has no residual df (its cells hold no partner seed): blinded_sigma stops"):
        bs.pooled_sigma({"fam removal": lone, "fam full": {(a, s): Fraction(s % 5 + len(a)) for a in ("a0", "S1")
                                                           for s in (1102, 1103, 1104)}})


def test_a_design_mismatch_refuses(tree):
    root = tree["root"]
    base = tree["families"]
    cases = []
    extra = json.loads(json.dumps(tree["stopped"]))
    extra["cells"]["L1"] = base["olmo2-7b"]["cells"]["L1"]               # L1 does not run on a stopped family
    cases.append((extra, "olmo2-7b: the cells given are not the design's cells: 3 extra, 0 missing"))
    missing = json.loads(json.dumps(base["olmo2-7b"]))
    del missing["cells"]["S4"]["1103"]
    cases.append((missing, "olmo2-7b: the cells given are not the design's cells: 0 extra, 1 missing"))
    no_a1 = json.loads(json.dumps(base["olmo2-7b"]))
    del no_a1["cells"]["A1"]                          # A1 missing on a family whose anchor job did not stop
    cases.append((no_a1, "olmo2-7b: the cells given are not the design's cells: 0 extra, 3 missing"))
    old_form = json.loads(json.dumps(base["olmo2-7b"]))
    old_form["not_run"] = [{"arm": "S3", "seed": 1103}]
    cases.append((old_form, "olmo2-7b: a family entry has ['cells', 'design', 'edits', 'engine'] and, on an anchor-stopped family, anchor_stop"))
    wrong_edits = json.loads(json.dumps(tree["stopped"]))
    wrong_edits["edits"]["A1"] = "2" * 64
    cases.append((wrong_edits, "olmo2-7b: edits gives exactly the design's method arms ['H1', 'S1', 'S4'] by SHA-256"))
    bad_design = {**base["olmo2-7b"], "design": "plan_b"}
    cases.append((bad_design, "a family's design is one of ['anchor_stopped', 'full']"))
    for i, (spec, message) in enumerate(cases):
        inputs, digest = write_inputs(root, "C", {"olmo2-7b": spec}, f"inputs-design-{i}.json")
        with refuses(message):
            bs.read(inputs, digest)


def test_a1_l1_s3_drop_only_with_the_familys_anchor_stop_record(tree):
    """GXB S-6: the stopped design (A1, L1, S3 absent) reads only with that family's anchor-stop record, by path and
    pinned SHA-256, of the right kind, family, stop kind and exit code; a full design names none."""
    root = tree["root"]
    good = tree["stopped"]
    inputs, digest = write_inputs(root, "C", {"olmo2-7b": good}, "inputs-stop-good.json")
    assert bs.read(inputs, digest)["df"] == 6
    second = {**good, "anchor_stop": write_stop_record(root, "stopped/stop-harmful.json", "olmo2-7b",
                                                       "harmful_prompt_does_not_encode", 1)}
    inputs, digest = write_inputs(root, "C", {"olmo2-7b": second}, "inputs-stop-harmful.json")
    assert bs.read(inputs, digest)["df"] == 6
    cases = [({k: v for k, v in good.items() if k != "anchor_stop"}, "olmo2-7b: an anchor-stopped family names its anchor-stop record as {path, sha256}"),
             ({**good, "anchor_stop": {**good["anchor_stop"], "sha256": "6" * 64}}, "olmo2-7b: the anchor-stop record is missing or its SHA-256 is not the pinned one"),
             ({**good, "anchor_stop": write_stop_record(root, "stopped/s-other.json", "llama31-8b")}, "olmo2-7b: the anchor-stop record is another family's"),
             ({**good, "anchor_stop": write_stop_record(root, "stopped/s-kind.json", "olmo2-7b", "crash", 3)},
              "olmo2-7b: the anchor-stop record's stop kind and exit code are not one of the anchor script's stops"),
             ({**good, "anchor_stop": write_stop_record(root, "stopped/s-exit.json", "olmo2-7b", "safe_anchors_below_64", 1)},
              "olmo2-7b: the anchor-stop record's stop kind and exit code are not one of the anchor script's stops"),
             ({**good, "anchor_stop": write_stop_record(root, "stopped/s-rk.json", "olmo2-7b", record_kind="other")},
              "olmo2-7b: the anchor-stop record is not a scale-78b anchor stop record"),
             ({**tree["families"]["olmo2-7b"], "anchor_stop": good["anchor_stop"]}, "olmo2-7b: a full-design family names no anchor-stop record")]
    for i, (spec, message) in enumerate(cases):
        inputs, digest = write_inputs(root, "C", {"olmo2-7b": spec}, f"inputs-stop-{i}.json")
        with refuses(message):
            bs.read(inputs, digest)


def test_the_inputs_form_is_checked(tree):
    root = tree["root"]
    path = root / "inputs-form.json"
    for doc in ({"kind": "other", "version": 1, "option": "B", "families": {}},
                {"kind": bs.INPUTS_KIND, "version": 2, "option": "B", "families": {}},
                {"kind": bs.INPUTS_KIND, "version": 1, "option": "B", "families": {}, "extra": 1},
                {"kind": bs.INPUTS_KIND, "version": 1, "families": {}}):
        data = json.dumps(doc).encode()
        path.write_bytes(data)
        unknown = 1 if "extra" in doc else 0
        with refuses(f"not a scale-78b blinded sigma inputs file (kind, version 1, option, families; unknown keys: {unknown})"):
            bs.read(path, sha(data))
    data = json.dumps({"kind": bs.INPUTS_KIND, "version": 1, "option": "A", "families": {}}).encode()
    path.write_bytes(data)
    with refuses("option is one of ['B', 'C']"):
        bs.read(path, sha(data))


def test_each_role_is_checked_against_its_own_engine_and_1104_is_block_as(tree):
    """GXB R-13, SV-4: a fixture whose reused a0 units, N's R units and block-A cells carry three different engine
    identities reads with the per-role map. a0 and R at 1104 (and R at 1105) carry block A's identity: they pass, and
    with block A's identity moved to the a0 or R role they refuse (the 1104 boundary). Each role set to another value
    refuses at its first cell, whose message is compared in full."""
    split = tree["engines"]
    inputs, digest = write_inputs(tree["root"], "C", {"olmo2-7b": split}, "inputs-engines-split.json")
    assert bs.read(inputs, digest)["df"] == 12
    cases = [("a0", "5" * 64, "olmo2-7b a0@1101: job.json code_sha256 is not the family's a0 value"),
             ("R", "5" * 64, "olmo2-7b R@1101: job.json code_sha256 is not the family's R value"),
             ("block_a", "5" * 64, "olmo2-7b A1@1102: job.json code_sha256 is not the family's R value")]
    for role, value, message in cases:
        spec = json.loads(json.dumps(split))
        spec["engine"][role] = value
        inputs, digest = write_inputs(tree["root"], "C", {"olmo2-7b": spec}, f"inputs-engine-{role}.json")
        with refuses(message):
            bs.read(inputs, digest)
    # with the reused roles' identities equal to block A's, the reused cells refuse; the 1104 cells alone would pass
    for role, message in (("a0", "olmo2-7b a0@1101: job.json code_sha256 is not the family's a0 value"),
                          ("R", "olmo2-7b R@1101: job.json code_sha256 is not the family's R value")):
        spec = json.loads(json.dumps(split))
        spec["engine"][role] = ENGINE_X
        inputs, digest = write_inputs(tree["root"], "C", {"olmo2-7b": spec}, f"inputs-engine-x-{role}.json")
        with refuses(message):
            bs.read(inputs, digest)
    for seed in (1104, 1105):
        assert not bs.reused("R", seed) and not bs.reused("a0", 1104)
    assert [bs.reused(a, j) for a in ("a0", "R") for j in (1101, 1102, 1103)] == [True] * 6


def test_an_in_process_read_error_carries_its_type_and_the_fixed_text_only(tree):
    """SR10: bs.read itself (not only the CLI) turns an unexpected error into a Refusal with the type-only line and no
    context: the zero-answers cell's ZeroDivisionError (whose own text names a U numerator) is never kept."""
    root = tree["root"]
    fams = json.loads(json.dumps(tree["families"]))

    def zero(summary):
        summary["harm"]["sampled"]["answers"] = 0
    fams["olmo2-7b"]["cells"]["S1"]["1103"] = tampered(root, fams["olmo2-7b"]["cells"]["S1"]["1103"], "tampered-s1-zero", zero)
    inputs, digest = write_inputs(root, "B", fams, "inputs-unexpected-inproc.json")
    with refuses("blinded_sigma: unexpected error (ZeroDivisionError); nothing written") as caught:
        bs.read(inputs, digest)
    assert isinstance(caught.value, bs.Refusal)
    assert caught.value.__context__ is None and caught.value.__cause__ is None and caught.value.args == (str(caught.value),)


def test_the_exclusive_create_refuses_a_file_made_after_the_check(tree, tmp_path, monkeypatch, capsys):
    """SR4: --out made between the existence check and the write (here by a read that creates it) is refused by the
    exclusive create; the file made meanwhile keeps its bytes; stdout and stderr stay empty."""
    inputs, digest = write_inputs(tree["root"], "B", tree["families"], "inputs-race.json")
    out = tmp_path / "race.json"
    real = bs.read

    def read_then_create(path, pin):
        doc = real(path, pin)
        out.write_bytes(b"made meanwhile\n")
        return doc
    monkeypatch.setattr(bs, "read", read_then_create)
    with refuses("--out exists: the output is written once"):
        bs.main(["--inputs", str(inputs), "--inputs-sha256", digest, "--out", str(out)])
    assert out.read_bytes() == b"made meanwhile\n"
    captured = capsys.readouterr()
    assert captured.out == "" and captured.err == ""


def test_the_engine_maps_form_is_checked(tree):
    """SR8: the old {block_a, reused} form, an extra key and a non-hex value each refuse with the form's own line."""
    line = "olmo2-7b: engine gives the a0, R and block_a code identities (64 hex each)"
    base = tree["families"]["olmo2-7b"]
    for i, engine in enumerate(({"block_a": ENGINE_X, "reused": ENGINE_X},
                                {"a0": ENGINE_X, "R": ENGINE_X, "block_a": ENGINE_X, "extra": ENGINE_X},
                                {"a0": ENGINE_X, "R": "not hex", "block_a": ENGINE_X})):
        inputs, digest = write_inputs(tree["root"], "C", {"olmo2-7b": {**base, "engine": engine}}, f"inputs-engine-form-{i}.json")
        with refuses(line):
            bs.read(inputs, digest)


def test_track_s_stop_fixture_is_the_shared_form(tmp_path):
    """KR5: this file's stop record has the shared fixture's keys and counts form (K2's writer's form), field for field
    once the JOB-DONE.json SHA-256 is the fixture's; Track S's reader takes the shared fixture itself."""
    shared = json.loads(SHARED_STOP_FIXTURE.read_bytes())
    mine = stop_record_doc("olmo2-7b", job_done_sha256=shared["job_done_sha256"])
    assert mine == shared
    harmful = stop_record_doc("olmo2-7b", "harmful_prompt_does_not_encode", 1)
    assert set(harmful) == set(shared)
    # V-8: RK's checker takes both forms, and each equals what K2's writer writes from the anchor job's own signal
    import importlib.util
    spec = importlib.util.spec_from_file_location("rules_78b_for_kr5", ROOT / "runkit/stage1-78b/rules_78b.py")
    rk = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rk)
    for doc in (mine, harmful):
        assert rk.anchor_stop_problem(doc, "olmo2-7b", doc["job_done_sha256"]) is None
    assert rk.anchor_stop_record("olmo2-7b", 3, None, shared["job_done_sha256"], {"kept": 61, "needed": 64}) == mine
    message = "harmful prompt 5 (6 of 64) does not encode (TooLong); the list needs a reviewed new version"
    assert rk.anchor_stop_record("olmo2-7b", 1, message, "4" * 64) == harmful
    assert harmful["counts"] == {"prompt_index": 5, "position": 6, "of": 64}
    (tmp_path / "s").mkdir()
    shutil.copyfile(SHARED_STOP_FIXTURE, tmp_path / "s" / "stop.json")
    bs.check_anchor_stop("olmo2-7b", {"path": "s/stop.json", "sha256": sha256_of(tmp_path / "s" / "stop.json")}, tmp_path)


def sha256_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()
