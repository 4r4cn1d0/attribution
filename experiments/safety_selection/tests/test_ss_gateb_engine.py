"""Gate B engine X (brief gate-b-engine-kit-reading-20261008, Part A; ENGINEERING FIXTURES on CPU):
A2 the anchor bank and bi-anchored scores; A4 the lock copy, lock record and guard record; A5 the applied rate on every
step; A6 an unknown target; A7 make-job --anchors; A8 recipe S. No text is printed or kept in any error."""

from __future__ import annotations

import hashlib
import json
import os
import random
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import removal_digest as rd  # noqa: E402
import ss_fixtures as fx  # noqa: E402
import test_ss_runner as tr  # noqa: E402

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import loaders as ld  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.__main__ import main as cli  # noqa: E402
from experiments.safety_selection.attribution import ADAM, BI_ANCHORED_SIGN, GRADSIM, SIGN  # noqa: E402
from experiments.safety_selection.common import canonical_json  # noqa: E402
from experiments.safety_selection.config import (LOSS_TOKEN_MEAN, ConfigError, config_sha256,  # noqa: E402
                                                 load_recipe, training_identity, validate_recipe)
from experiments.safety_selection.jobs import (JobError, check_attribution_access, check_identities,  # noqa: E402
                                               read_anchor_bank, validate_job)
from experiments.safety_selection.prepare import load_prepared  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
FIELDS = ("prompt", "response", "prompt_tokens", "target_tokens", "token_sha256")
REC = ROOT / "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"


def anchor_doc(harmful: list[dict], safe: list[dict], model: dict) -> dict:
    return {"kind": "safety-selection anchor bank", "version": 1, "model": model,
            "harmful": [{"anchor_id": f"h-{k}", **{f: r[f] for f in FIELDS}} for k, r in enumerate(harmful)],
            "safe": [{"anchor_id": f"s-{k}", **{f: r[f] for f in FIELDS}} for k, r in enumerate(safe)],
            "counts": {"harmful": len(harmful), "safe": len(safe)}, "provenance": {"fixture": True}}


def write_bank(path: Path, doc: dict) -> str:
    data = canonical_json(doc)
    path.write_bytes(data)
    return hashlib.sha256(data).hexdigest()


def texts_of(doc: dict) -> list[str]:
    return [a[f] for name in ("harmful", "safe") for a in doc[name] for f in ("prompt", "response") if a[f]]


# ----- A2: anchor bank, bi-anchored scores (one module environment: three recipes, each with its own a0) ------------

@pytest.fixture(scope="module")
def a2(tmp_path_factory):
    root = tmp_path_factory.mktemp("gateb-a2")
    prepared_dir, sha = fx.prepare_dir(root / "prepared")
    view = load_prepared(prepared_dir, sha, banks=("dev",))
    base = fx.recipe()
    model = {"repo_id": base["model"]["repo_id"], "revision": base["model"]["revision"]}
    members = {rid for gid in view.groups["dev"] for rid in view.groups["dev"][gid]}
    others = [view.train_rows[rid] for rid in sorted(view.train_rows) if rid not in members][:3] or \
        [view.train_rows[rid] for rid in sorted(view.train_rows)[:3]]
    ref_rows = list(view.query_rows)

    def run(name: str, bank_doc: dict | None) -> SimpleNamespace:
        folder = root / name
        folder.mkdir()
        recipe, anchors = base, None
        if bank_doc is not None:
            anchors = folder / "anchors.json"
            recipe = fx.recipe(**{"attribution.query_bank": f"anchors-{write_bank(anchors, bank_doc)}"})
        e = SimpleNamespace(root=folder, prepared=prepared_dir, sha=sha, recipe=recipe, view=view,
                            session=runner.Session(recipe, fx.fixture_loaders()))
        e.direct = runner.run_one(tr.run_job(e, target_checkpoint="e1", evaluate_bank=None),
                                  prepared_dir=prepared_dir, out_dir=folder / "direct", session=e.session)
        e.to_e3 = runner.run_one(tr.run_job(e, target_checkpoint="e3", evaluate_bank=None,
                                            resume_from=e.direct["run_dir"]),
                                 prepared_dir=prepared_dir, out_dir=folder / "e3", session=e.session)
        job = tr.attr_job(e, query_bank=recipe["attribution"]["query_bank"],
                          **({"anchors": str(anchors)} if anchors else {}))
        e.result = runner.attributes(job, prepared_dir=prepared_dir, out_dir=folder / "attr", session=e.session)
        out = Path(e.result["run_dir"])
        e.rows = {r["row_id"]: r for r in map(json.loads, (out / "rows.jsonl").read_text().splitlines())}
        e.groups = json.loads((out / "groups.json").read_text())
        e.queries = json.loads((out / "queries.json").read_text())
        e.assets = json.loads((out / "assets.json").read_text())
        e.job, e.out = job, out
        return e

    hs_doc = anchor_doc(ref_rows, others, model)
    return SimpleNamespace(ref=run("ref", None), hs=run("hs", hs_doc), sh=run("sh", anchor_doc(others, ref_rows, model)),
                           hs_doc=hs_doc, ref_rows=ref_rows, others=others, model=model, view=view)


def test_harmful_anchors_equal_to_the_ref_rows_give_the_ref_scores_bit_for_bit(a2):
    ref, hs = a2.ref, a2.hs
    assert set(hs.rows) == set(ref.rows)
    for rid, row in ref.rows.items():
        for c, features in row["per_checkpoint"].items():
            assert hs.rows[rid]["per_checkpoint"][c]["harmful"] == features, (rid, c)
    for gid, agg in ref.groups["groups"].items():
        assert hs.groups["groups"][gid]["harmful"] == agg, gid
        assert hs.result["scores"][gid]["harmful"] == ref.result["scores"][gid]


def test_safe_anchors_equal_to_the_ref_rows_give_the_ref_scores_and_swapping_negates_bi_exactly(a2):
    ref, hs, sh = a2.ref, a2.hs, a2.sh
    for rid, row in ref.rows.items():
        for c, features in row["per_checkpoint"].items():
            assert sh.rows[rid]["per_checkpoint"][c]["safe"] == features, (rid, c)
    for gid, agg in ref.groups["groups"].items():
        assert sh.groups["groups"][gid]["safe"] == agg
        for v in (GRADSIM, ADAM):
            bi = hs.groups["groups"][gid]["bi_anchored"][v]
            assert bi == hs.groups["groups"][gid]["harmful"][v] - hs.groups["groups"][gid]["safe"][v]  # one subtraction
            assert sh.groups["groups"][gid]["bi_anchored"][v] == -bi                                     # exactly
            assert bi != 0.0                                                                            # distinct sets
            assert hs.result["scores"][gid]["bi_anchored"][v] == bi


def test_the_anchor_outputs_passes_and_records(a2):
    hs, doc = a2.hs, a2.hs_doc
    n_h, n_s, rows = len(doc["harmful"]), len(doc["safe"]), len(hs.rows)
    checkpoints = hs.recipe["attribution"]["checkpoints"]
    assert hs.result["costs"]["gradient_passes"] == (n_h + n_s + rows) * len(checkpoints)
    assert hs.groups["sign"] == SIGN and hs.groups["bi_anchored_sign"] == BI_ANCHORED_SIGN
    assert "bi_anchored_sign" not in a2.ref.groups                          # "ref" writes only what it wrote before
    bank = hs.recipe["attribution"]["query_bank"]
    assert hs.queries["query_bank"] == bank and hs.queries["query_bank_sha256"] == bank[len("anchors-"):]
    assert hs.queries["counts"] == {"harmful": n_h, "safe": n_s} == hs.result["anchor_counts"]
    for c in checkpoints:
        assert sorted(hs.queries["per_checkpoint"][c]["harmful"]["losses"]) == [a["anchor_id"] for a in doc["harmful"]]
        assert hs.queries["per_checkpoint"][c]["safe"]["n"] == n_s
    assert set(hs.result["scores"][next(iter(hs.result["scores"]))]) == {"harmful", "safe", "bi_anchored"}
    assert hs.assets["environment_lock"] is None and hs.assets["guard"] is None      # cpu; attributes evaluate nothing
    out = (hs.out / "groups.json").read_text() + (hs.out / "queries.json").read_text() + \
        (hs.out / "rows.jsonl").read_text() + json.dumps(hs.result)
    assert not any(t in out for t in texts_of(doc))                         # no anchor text in any output


def _bank(tmp_path: Path, doc: dict, name: str = "bank.json") -> tuple[Path, str]:
    path = tmp_path / name
    return path, f"anchors-{write_bank(path, doc)}"


def test_the_anchor_file_refusals_carry_no_text(a2, tmp_path):
    recipe = fx.recipe()
    doc = a2.hs_doc
    path, bank = _bank(tmp_path, doc)
    assert read_anchor_bank(path, bank, recipe) == doc
    cases = {
        "hash": (lambda d: d, "0" * 64),
        "kind": (lambda d: {**d, "kind": "x"}, None),
        "model": (lambda d: {**d, "model": {**d["model"], "revision": "1" * 40}}, None),
        "duplicate": (lambda d: {**d, "safe": [{**d["safe"][0], "anchor_id": d["harmful"][0]["anchor_id"]},
                                               *d["safe"][1:]]}, None),
        "counts": (lambda d: {**d, "counts": {"harmful": 1, "safe": 1}}, None),
        "empty": (lambda d: {**d, "safe": [], "counts": {**d["counts"], "safe": 0}}, None),
        "unknown key": (lambda d: {**d, "extra": 1}, None),
        "field": (lambda d: {**d, "harmful": [{**d["harmful"][0], "prompt_tokens": "1"}, *d["harmful"][1:]]}, None),
    }
    for name, (change, forced) in cases.items():
        p, b = _bank(tmp_path, change(json.loads(json.dumps(doc))), f"{name}.json")
        with pytest.raises(JobError) as err:
            read_anchor_bank(p, f"anchors-{forced}" if forced else b, recipe)
        assert not any(t in str(err.value) for t in texts_of(doc)), name
    p = tmp_path / "pretty.json"
    p.write_text(json.dumps(doc))                                       # valid JSON, not canonical
    with pytest.raises(JobError, match="canonical"):
        read_anchor_bank(p, f"anchors-{hashlib.sha256(p.read_bytes()).hexdigest()}", recipe)
    with pytest.raises(JobError):
        read_anchor_bank(path, "ref", recipe)


def test_anchor_jobs_and_banks_are_validated(a2, tmp_path):
    job = a2.hs.job
    assert validate_job(dict(job)) == job
    for bad in ({**job, "anchors": ""}, {k: v for k, v in job.items() if k != "anchors"},
                {**job, "query_bank": "ref"}, {**job, "query_bank": "anchors-xyz"}, {**job, "unknown": 1}):
        with pytest.raises(JobError):
            validate_job(bad)
    ref_job = a2.ref.job
    assert validate_job(dict(ref_job)) == ref_job and "anchors" not in ref_job
    manifest = json.loads((a2.ref.prepared / "manifest.json").read_text())
    with pytest.raises(JobError, match="query bank differs"):          # the job's bank must be the recipe's
        check_identities({**ref_job, "recipe_sha256": config_sha256(a2.hs.recipe)}, manifest, a2.ref.sha,
                         a2.hs.recipe, {"sha256": "0" * 64})
    for bank in ("anchors-" + "A" * 64, "anchors-" + "0" * 63, "anchor-" + "0" * 64, "anchorz-" + "0" * 64, "", "dev"):
        with pytest.raises(ConfigError):
            validate_recipe(fx.recipe(**{"attribution.query_bank": bank}))
    validate_recipe(fx.recipe(**{"attribution.query_bank": "anchors-" + "0" * 64}))


def test_an_anchor_that_does_not_encode_or_audit_refuses_after_the_load_with_ids_only(a2):
    codec, recipe = fx.fixture_codec(), fx.recipe()
    doc = json.loads(json.dumps(a2.hs_doc))
    assert {k: len(v) for k, v in runner.anchor_examples(codec, doc, recipe).items()} == doc["counts"]
    audit = json.loads(json.dumps(doc))
    audit["safe"][1]["token_sha256"] = "0" * 64
    with pytest.raises(JobError, match=r"anchor set safe anchor s-1 \(2 of \d+\) encodes differently"):
        runner.anchor_examples(codec, audit, recipe)
    control = json.loads(json.dumps(doc))
    control["harmful"][0]["response"] = "a <|im_end|> b"
    with pytest.raises(JobError, match=r"anchor set harmful anchor h-0 \(1 of \d+\) does not encode") as err:
        runner.anchor_examples(codec, control, recipe)
    assert "<|im_end|>" not in str(err.value) and not any(t in str(err.value) for t in texts_of(control))


# ----- A4: lock copy, lock record and guard record ---------------------------------------------------------------------

def test_lock_record_reads_the_lock_on_cuda_only(tmp_path):
    assert runner.lock_record("cpu", tmp_path) is None and runner.lock_record("mps", tmp_path) is None
    with pytest.raises(JobError, match="no environment-linux.lock"):
        runner.lock_record("cuda", tmp_path)
    (tmp_path / "environment-linux.lock").write_bytes(b"")
    with pytest.raises(JobError, match="is empty"):
        runner.lock_record("cuda", tmp_path)
    data = b"setuptools==78.1.0\ntorch==2.8.0\n"
    (tmp_path / "environment-linux.lock").write_bytes(data)
    record, raw = runner.lock_record("cuda", tmp_path)
    assert record == {"name": "environment-linux.lock", "sha256": hashlib.sha256(data).hexdigest()} and raw == data


def _global_state() -> tuple:
    return (torch.get_rng_state().clone(), random.getstate(), dict(os.environ),
            torch.are_deterministic_algorithms_enabled())


class _WatchedEnviron(dict):
    """os.environ during the inserted calls: every write is recorded, even one that leaves the value unchanged."""
    def __init__(self, base, writes):
        super().__init__(base)
        self.writes = writes

    def __setitem__(self, key, value):
        self.writes.append(key)
        super().__setitem__(key, value)

    def __delitem__(self, key):
        self.writes.append(key)
        super().__delitem__(key)


def _same(a: tuple, b: tuple) -> bool:
    return torch.equal(a[0], b[0]) and a[1:] == b[1:]


@pytest.fixture
def a4(tmp_path, monkeypatch):
    """A fixture environment whose inserted A4 lines see "cuda" and a lock, with spies on process-global state."""
    lock_dir = tmp_path / "pod"
    lock_dir.mkdir()
    (lock_dir / "environment-linux.lock").write_bytes(b"setuptools==78.1.0\n")
    real_lock, real_merge = runner.lock_record, runner.merge_assets
    calls = []

    def watched(call):
        writes, saved = [], os.environ
        os.environ = _WatchedEnviron(saved, writes)
        try:
            before = _global_state()
            out = call()
            return out, _same(before, _global_state()) and not writes
        finally:
            os.environ = saved

    def lock_spy(device, cwd):
        out, same = watched(lambda: real_lock("cuda", lock_dir))
        calls.append(("lock", same))
        return out

    def merge_spy(run_dir, lock, guard):
        _, same = watched(lambda: real_merge(run_dir, lock, guard))
        calls.append(("merge", same, guard))

    monkeypatch.setattr(runner, "lock_record", lock_spy)
    monkeypatch.setattr(runner, "merge_assets", merge_spy)
    monkeypatch.setattr(ld, "asset_status", lambda repo, rev: {
        "repo_id": repo, "revision": rev, "snapshot": "/local/path", "present": True, "safetensors": ["m.safetensors"],
        "files": [{"file": "config.json", "bytes": 3, "blob": "a" * 40}, {"file": "m.safetensors", "bytes": 9,
                                                                         "blob": "b" * 64}]})
    prepared_dir, sha = fx.prepare_dir(tmp_path / "prepared")
    recipe = fx.recipe()
    e = SimpleNamespace(root=tmp_path, prepared=prepared_dir, sha=sha, recipe=recipe, calls=calls, lock_dir=lock_dir,
                        session=runner.Session(recipe, fx.fixture_loaders()))
    return e


def test_the_lock_is_recorded_copied_and_sealed_and_the_guard_pinned_without_global_writes(a4):
    retrain = runner.run_one(tr.run_job(a4, target_checkpoint="q", evaluate_bank=None), prepared_dir=a4.prepared,
                             out_dir=a4.root / "retrain", session=a4.session)
    evaluated = runner.run_one(tr.run_job(a4, target_checkpoint="q", evaluate_bank="dev", seed=1102),
                               prepared_dir=a4.prepared, out_dir=a4.root / "evaluated", session=a4.session)
    state = runner.eval_state(tr.eval_job(a4, evaluated, "q"), prepared_dir=a4.prepared, out_dir=a4.root / "state",
                              session=a4.session)
    lock = (a4.lock_dir / "environment-linux.lock").read_bytes()
    record = {"name": "environment-linux.lock", "sha256": hashlib.sha256(lock).hexdigest()}
    pin = {"repo_id": a4.recipe["guard"]["repo_id"], "revision": a4.recipe["guard"]["revision"], "present": True,
           "files": [{"file": "config.json", "blob": "a" * 40}, {"file": "m.safetensors", "blob": "b" * 64}]}
    for result, guard in ((retrain, None), (evaluated, pin), (state, pin)):
        unit = Path(result["run_dir"])
        assets = json.loads((unit / "assets.json").read_text())
        assert assets["environment_lock"] == record and assets["guard"] == guard
        assert (unit / "environment-linux.lock").read_bytes() == lock
        assert json.loads((unit / "COMPLETE.json").read_text())["files"]["environment-linux.lock"] == record["sha256"]
        assert "policy" in assets and "environment" in assets                       # the existing record is kept
    assert [c[0] for c in a4.calls] == ["lock", "merge"] * 3
    assert all(c[1] for c in a4.calls)                     # torch and Python RNG, os.environ keys, determinism: unchanged
    assert [c[2] for c in a4.calls if c[0] == "merge"] == [None, pin, pin]


def test_a_missing_lock_on_cuda_refuses_before_the_policy_loads(tmp_path, monkeypatch):
    loads = []
    monkeypatch.setattr(runner, "lock_record", lambda device, cwd, real=runner.lock_record: real("cuda", tmp_path))
    prepared_dir, sha = fx.prepare_dir(tmp_path / "prepared")
    recipe = fx.recipe()
    e = SimpleNamespace(root=tmp_path, prepared=prepared_dir, sha=sha, recipe=recipe,
                        session=runner.Session(recipe, fx.fixture_loaders(on_policy_load=lambda: loads.append(1))))
    with pytest.raises(JobError, match="no environment-linux.lock"):
        runner.run_one(tr.run_job(e, target_checkpoint="q", evaluate_bank=None), prepared_dir=prepared_dir,
                       out_dir=tmp_path / "out", session=e.session)
    assert loads == []
    folder = tmp_path / "out"
    assert (folder / "error.txt").exists() and not (folder / "COMPLETE.json").exists()      # a preserved failure


def test_session_construction_never_reads_the_lock(monkeypatch):
    monkeypatch.setattr(runner, "lock_record", lambda *a: pytest.fail("Session read the lock"))
    runner.Session(fx.recipe(), fx.fixture_loaders())


# ----- A5: the applied rate on every step --------------------------------------------------------------------------------

def _run_to_q(tmp_path: Path, recipe: dict, monkeypatch) -> tuple[list[dict], list[float]]:
    applied = []
    real = en.train_step

    def spy(model, named, optimizer, *a, **k):
        applied.append(optimizer.param_groups[0]["lr"])
        return real(model, named, optimizer, *a, **k)
    monkeypatch.setattr(en, "train_step", spy)
    prepared_dir, sha = fx.prepare_dir(tmp_path / "prepared")
    e = SimpleNamespace(root=tmp_path, prepared=prepared_dir, sha=sha, recipe=recipe,
                        session=runner.Session(recipe, fx.fixture_loaders()))
    run = runner.run_one(tr.run_job(e, target_checkpoint="q", evaluate_bank=None), prepared_dir=prepared_dir,
                         out_dir=tmp_path / "out", session=e.session)
    steps = [json.loads(line) for line in (Path(run["run_dir"]) / "steps.jsonl").read_text().splitlines()]
    return steps, applied


def test_every_step_logs_the_rate_its_update_ran_at(tmp_path, monkeypatch):
    real = en.make_optimizer

    def doubled(named, train):
        optimizer = real(named, train)
        for group in optimizer.param_groups:
            group["lr"] = 2 * train["lr"]
        return optimizer
    monkeypatch.setattr(en, "make_optimizer", doubled)
    recipe = fx.recipe()
    steps, applied = _run_to_q(tmp_path / "constant", recipe, monkeypatch)
    assert [s["lr"] for s in steps] == applied == [2 * recipe["train"]["lr"]] * len(steps) and steps
    warm = fx.recipe(**{"train.lr_schedule": "warmup_cosine", "train.warmup_steps": 2, "train.schedule_until": "e1"})
    steps, applied = _run_to_q(tmp_path / "warmup", warm, monkeypatch)
    assert [s["lr"] for s in steps] == applied and applied[0] == 0.0 and len(set(applied)) > 1


def test_the_digest_drops_lr_only_when_constant_and_equal_to_the_recipe_rate():
    step = {"step": 1, "lr": 0.01, "loss": 1.0}
    assert rd.drop_constant_lr(step, {"lr": 0.01, "lr_schedule": "constant"}) == {"step": 1, "loss": 1.0}
    assert rd.drop_constant_lr(step, {"lr": 0.01}) == {"step": 1, "loss": 1.0}                     # constant by default
    assert rd.drop_constant_lr(step, {"lr": 0.02, "lr_schedule": "constant"}) == step
    assert rd.drop_constant_lr(step, {"lr": 0.01, "lr_schedule": "warmup_cosine"}) == step
    assert rd.drop_constant_lr({"step": 1}, {"lr": 0.01}) == {"step": 1}


# ----- A6: an unknown target ------------------------------------------------------------------------------------------------

def test_a_warmup_recipe_with_an_unknown_target_refuses_with_a_job_error():
    warm = fx.recipe(**{"train.lr_schedule": "warmup_cosine", "train.warmup_steps": 2, "train.schedule_until": "e1"})
    manifest = {"data_config": {"tokenizer": {"repo_id": warm["model"]["repo_id"], "revision": warm["model"]["revision"],
                                              "end_of_turn_token": warm["model"]["end_of_turn_token"]}}}
    job = {"kind": "run-one", "manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(warm), "code_sha256": None,
           "target_checkpoint": "e9"}
    with pytest.raises(JobError, match="'e9' is not a checkpoint"):
        check_identities(job, manifest, "0" * 64, warm, {"sha256": "0" * 64})


# ----- A7: make-job --anchors --------------------------------------------------------------------------------------------

def test_make_job_takes_the_recipes_bank_and_checks_the_anchor_file(a2, tmp_path, capsys):
    recipe_path = tmp_path / "recipe.json"
    recipe_path.write_text(json.dumps(a2.hs.recipe))
    anchors = a2.hs.job["anchors"]
    base = ["make-job", "attributes", "--prepared", str(a2.hs.prepared), "--recipe", str(recipe_path), "--split", "dev",
            "--seed", "1101", "--role", "development", "--groups", ",".join(sorted(a2.view.groups["dev"])),
            "--a0-state", "q=x", "--a0-state", "e1=x", "--a0-state", "e3=x", "--pin-code"]
    assert cli([*base, "--anchors", anchors, "--out", str(tmp_path / "job.json")]) == 0
    job = json.loads((tmp_path / "job.json").read_text())
    assert job["query_bank"] == a2.hs.recipe["attribution"]["query_bank"] and job["anchors"] == anchors
    assert job["code_sha256"] is not None
    wrong = tmp_path / "wrong.json"
    wrong.write_bytes(Path(anchors).read_bytes() + b" ")
    assert cli([*base, "--anchors", str(wrong), "--out", str(tmp_path / "j2.json")]) != 0      # the hash differs
    assert cli([*base, "--out", str(tmp_path / "j3.json")]) != 0                                # no anchors
    ref_path = tmp_path / "ref.json"
    ref_path.write_text(json.dumps(a2.ref.recipe))
    ref = [a if a != str(recipe_path) else str(ref_path) for a in base]
    assert cli([*ref, "--anchors", anchors, "--out", str(tmp_path / "j4.json")]) != 0         # ref takes no anchors
    assert cli([*ref, "--out", str(tmp_path / "j5.json")]) == 0
    assert json.loads((tmp_path / "j5.json").read_text())["query_bank"] == "ref"
    printed = capsys.readouterr()
    assert not any(t in printed.out + printed.err for t in texts_of(a2.hs_doc))


# ----- A8: recipe S ----------------------------------------------------------------------------------------------------------

def test_recipe_s_has_recs_training_identity_and_evaluation_config(tmp_path):
    out = tmp_path / "S.json"
    done = subprocess.run([sys.executable, "-B", str(ROOT / "scripts/make_gateb_recipe.py"), "--anchors-sha256",
                           "ab" * 32, "--out", str(out)], capture_output=True, text=True, cwd=ROOT,
                          env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0, done.stderr
    s, rec = load_recipe(out), load_recipe(REC)
    assert training_identity(s) == training_identity(rec) == \
        "f46279e5830f477742189ef03c03ffc0ec86107ae060bb5ef9034ba47acabfac"
    printed = json.loads(done.stdout)
    assert printed == {"recipe_sha256": config_sha256(s), "training_identity": training_identity(s),
                       "rec_sha256": config_sha256(rec)}
    assert s["attribution"]["checkpoints"] == ["q", "e1"] and s["attribution"]["query_bank"] == "anchors-" + "ab" * 32
    changed = {k for k in set(s) | set(rec) if s.get(k) != rec.get(k)}
    assert changed == {"name", "purpose", "attribution"}
    assert {k for k in s["attribution"] if s["attribution"][k] != rec["attribution"][k]} == {"checkpoints", "query_bank"}
    import importlib.util
    spec = importlib.util.spec_from_file_location("fpr_s", ROOT / "scripts/family_probe_reading.py")
    fpr = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(fpr)
    assert fpr.eval_config(s) == fpr.eval_config(rec)
    data_config = json.loads((ROOT / "experiments/safety_selection/configs/study-kt-data-dolly-olmo2.json").read_text())
    job = {"role": "development", "split": "dev", "seed": 1101, "a0_states": {"q": "x", "e1": "x"}}
    check_attribution_access(job, data_config, s)
    with pytest.raises(JobError, match="a0_states must name exactly"):
        check_attribution_access({**job, "a0_states": {"q": "x", "e1": "x", "e3": "x"}}, data_config, s)
    assert subprocess.run([sys.executable, "-B", str(ROOT / "scripts/make_gateb_recipe.py"), "--anchors-sha256",
                           "AB" * 32, "--out", str(tmp_path / "bad.json")], capture_output=True, cwd=ROOT).returncode
    assert subprocess.run([sys.executable, "-B", str(ROOT / "scripts/make_gateb_recipe.py"), "--anchors-sha256",
                           "ab" * 32, "--out", str(out)], capture_output=True, cwd=ROOT).returncode   # written once
