"""The two Gate C diagnostic scripts (brief gate-b-engine-kit-reading-20261008, A9 with [D8], [D9] A-5; ENGINEERING
FIXTURES on CPU: the tiny policy and the scripted guard). CUDA and the real models are untested here."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import statistics
import sys
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("transformers")
pytest.importorskip("peft")

import ss_fixtures as fx  # noqa: E402

from experiments.safety_selection.common import canonical_json, read_jsonl  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / f"{name}.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


rep, clf = load("gate_c_representation"), load("gate_c_classifier")
FIELDS = ("prompt", "response", "prompt_tokens", "target_tokens", "token_sha256")


@pytest.fixture(scope="module")
def env(tmp_path_factory):
    root = tmp_path_factory.mktemp("gatec")
    prepared_dir, sha = fx.prepare_dir(root / "prepared")
    view = load_prepared(prepared_dir, sha, banks=("dev",))
    base = fx.recipe()
    rows = [view.train_rows[r] for r in sorted(view.train_rows)]
    doc = {"kind": "safety-selection anchor bank", "version": 1,
           "model": {"repo_id": base["model"]["repo_id"], "revision": base["model"]["revision"]},
           "harmful": [{"anchor_id": f"h-{k}", **{f: q[f] for f in FIELDS}} for k, q in enumerate(view.query_rows)],
           "safe": [{"anchor_id": f"s-{k}", **{f: r[f] for f in FIELDS}} for k, r in enumerate(rows[:3])],
           "counts": {"harmful": len(view.query_rows), "safe": 3}, "provenance": {"fixture": True}}
    data = canonical_json(doc)
    anchors = root / "anchors.json"
    anchors.write_bytes(data)
    recipe = root / "recipe.json"
    recipe.write_text(json.dumps(fx.recipe(**{"attribution.query_bank": "anchors-" + hashlib.sha256(data).hexdigest()})))
    groups = sorted(view.groups["dev"])
    texts = [t for name in ("harmful", "safe") for a in doc[name] for t in (a["prompt"], a["response"])] + \
        [t for gid in groups for rid in view.groups["dev"][gid] for t in (view.train_rows[rid]["prompt"],
                                                                         view.train_rows[rid]["response"])]
    return type("Env", (), dict(root=root, prepared=prepared_dir, view=view, anchors=anchors, recipe=recipe,
                                groups=groups, texts=[t for t in texts if len(t) > 3]))


def stable(record: dict) -> dict:
    return {k: v for k, v in record.items() if k != "costs"}


def test_representation_scores_are_deterministic_untuned_and_text_free(env, monkeypatch):
    flags = []
    real = torch.nn.Module.__call__
    a = rep.run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "rep-a", fx.fixture_loaders())
    b = rep.run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "rep-b", fx.fixture_loaders())
    assert stable(a) == stable(b)
    assert set(a["groups"]) == set(env.groups)
    for gid in env.groups:
        g = a["groups"][gid]
        assert g["rows"] == len(env.view.groups["dev"][gid])
        assert math.isclose(g["score"], g["harmful"] - g["safe"], rel_tol=1e-12, abs_tol=1e-15)   # means of a difference
    text = (env.root / "rep-a" / "representation.json").read_text()
    assert not any(t in text for t in env.texts)
    assert a["anchor_file_sha256"] == hashlib.sha256(env.anchors.read_bytes()).hexdigest()
    assert set(a["costs"]) == {"diag_setup", "diag_rows"} and a["costs"]["diag_rows"]["rows"] == \
        sum(g["rows"] for g in a["groups"].values())

    def spy(self, *args, **kwargs):                       # every forward of the policy runs with its adapter disabled
        if kwargs.get("output_hidden_states"):
            flags.append(all(m.disable_adapters for m in self.modules() if hasattr(m, "disable_adapters")))
        return real(self, *args, **kwargs)
    monkeypatch.setattr(torch.nn.Module, "__call__", spy)
    rep.run(env.prepared, env.recipe, env.anchors, env.groups[:1], env.root / "rep-c", fx.fixture_loaders())
    assert flags and all(flags)


def test_the_unit_score_is_the_mean_of_the_row_differences(env, monkeypatch):
    seen = {}
    real = torch.nn.functional.cosine_similarity

    def spy(a, b, dim):
        value = real(a, b, dim=dim)
        seen.setdefault("calls", []).append(float(value))
        return value
    monkeypatch.setattr(torch.nn.functional, "cosine_similarity", spy)
    record = rep.run(env.prepared, env.recipe, env.anchors, env.groups[:1], env.root / "rep-d", fx.fixture_loaders())
    calls = seen["calls"]                                  # per row: harmful then safe
    diffs = [calls[k] - calls[k + 1] for k in range(0, len(calls), 2)]
    assert record["groups"][env.groups[0]]["score"] == math.fsum(diffs) / len(diffs)


def test_a_wrong_anchor_file_refuses_before_any_load(env):
    wrong = env.root / "wrong.json"
    wrong.write_bytes(env.anchors.read_bytes() + b" ")
    for module in (rep, clf):
        with pytest.raises(SystemExit, match="anchor file is refused"):
            module.run(env.prepared, env.recipe, wrong, env.groups, env.root / f"x-{module.KIND[:6]}",
                       fx.fixture_loaders())
    with pytest.raises(SystemExit, match="distinct dev groups"):
        rep.run(env.prepared, env.recipe, env.anchors, ["g-none"], env.root / "x-g", fx.fixture_loaders())


def test_classifier_scores_all_rows_with_the_analytic_se_and_the_uninformative_flag(env):
    a = clf.run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "clf-a", fx.fixture_loaders())
    b = clf.run(env.prepared, env.recipe, env.anchors, env.groups, env.root / "clf-b", fx.fixture_loaders())
    assert stable(a) == stable(b)
    for gid, g in a["groups"].items():
        assert g["rows"] == len(env.view.groups["dev"][gid]) == g["scored"] + g["unscored"]
        assert g["se"] == g["sd"] / math.sqrt(g["scored"])
    means = [g["mean"] for g in a["groups"].values()]
    assert a["uninformative"] == ((max(means) - min(means)) < 2 * max(g["se"] for g in a["groups"].values()))
    assert a["representation_script_sha256"] == hashlib.sha256((ROOT / "scripts/gate_c_representation.py").read_bytes()).hexdigest()
    assert not any(t in (env.root / "clf-a" / "classifier.json").read_text() for t in env.texts)


def test_classifier_unit_statistics_by_hand(env, monkeypatch):
    from experiments.safety_selection import scoring
    gid = env.groups[0]
    members = list(env.view.groups["dev"][gid])
    values = [0.1 * (k + 1) for k in range(len(members))]

    def fake(self, items, check=None, over_limit_unscored=False):
        return [{"item_id": i, "valid": k != 0, "normalized": {"Unsafe": values[k]} if k else None,
                 "guard_input_tokens": 7} for k, (i, _, _) in enumerate(items)]
    monkeypatch.setattr(scoring.GuardScorer, "label_scores", fake)
    g = clf.run(env.prepared, env.recipe, env.anchors, [gid], env.root / "clf-hand", fx.fixture_loaders())["groups"][gid]
    kept = values[1:]                                                       # the first row is unscored, not imputed
    assert (g["scored"], g["unscored"]) == (len(kept), 1)
    assert g["mean"] == math.fsum(kept) / len(kept) and g["sd"] == statistics.stdev(kept)
    assert g["se"] == statistics.stdev(kept) / math.sqrt(len(kept))           # over the scored rows, not all rows


def test_the_vector_is_the_final_layer_at_the_last_response_token():
    """A fake model whose hidden state at position i of layer l is (l, i): the vector must come from the last layer at
    position len - 2 (the token before the end-of-turn id)."""
    class Fake:
        def __call__(self, input_ids, output_hidden_states):
            n = input_ids.shape[1]
            layers = [torch.stack([torch.tensor([float(layer), float(i)]) for i in range(n)])[None] for layer in range(3)]
            return type("Out", (), {"hidden_states": tuple(layers)})
    vector = rep.last_response_vector(Fake(), (5, 6, 7, 8, 9), "cpu")
    assert vector.dtype == torch.float64 and vector.tolist() == [2.0, 3.0]


def test_each_cost_phase_starts_with_a_peak_memory_reset(env, monkeypatch):
    """Review fix 3 with [D14] A: both scripts reset the cuda peak at the start of the setup phase and of the rows
    phase. One ordered event list per run records each reset (with its device), the policy or guard load (entered and
    returned), the rows work (consecutive rows calls are one event) and each peak read; per phase the order must be
    reset, then the load (setup) or the rows work (rows), then the peak. On CPU the reset is a no-op; a fake cuda counts
    the real reset path. CUDA itself is untested."""
    import dataclasses

    from experiments.safety_selection import scoring

    resets = []
    monkeypatch.setattr(torch.cuda, "reset_peak_memory_stats", lambda *a, **k: resets.append("cuda"))
    rep._reset_peak("cpu")
    assert resets == []
    rep._reset_peak("cuda")
    assert resets == ["cuda"]
    real_vector, real_scores = rep.last_response_vector, scoring.GuardScorer.label_scores
    for module, name, kind in ((rep, "rep-order", "policy"), (clf, "clf-order", "guard")):
        events = []

        def note(event, events=events):
            if not (event == "rows" and events and events[-1] == "rows"):
                events.append(event)
        real_peak, loaders = module._peak, fx.fixture_loaders()
        real_load = getattr(loaders, kind)

        def load(*args, real_load=real_load, note=note):
            note("load")
            loaded = real_load(*args)
            note("loaded")
            return loaded

        def vector(*args, note=note):
            note("rows")
            return real_vector(*args)

        def scores(self, *args, note=note, **kwargs):
            note("rows")
            return real_scores(self, *args, **kwargs)
        monkeypatch.setattr(module, "_reset_peak", lambda device, note=note: note(f"reset:{device}"))
        monkeypatch.setattr(module, "_peak", lambda device, note=note, real_peak=real_peak: (note("peak"),
                                                                                             real_peak(device))[1])
        monkeypatch.setattr(rep, "last_response_vector", vector)
        monkeypatch.setattr(scoring.GuardScorer, "label_scores", scores)
        module.run(env.prepared, env.recipe, env.anchors, env.groups[:1], env.root / name,
                   dataclasses.replace(loaders, **{kind: load}))
        assert events == ["reset:cpu", "load", "loaded", "peak",                  # setup
                          "reset:cpu", "rows", "peak"], (name, events)            # rows


def test_the_setup_peak_includes_the_load_stage_ledger_peak(env, monkeypatch):
    """[D14] A: the ledger's memory probe resets the cuda peak when the load stage ends, so the setup phase reports the
    larger of the script's own peak and the load stage's ledger CUDA peak; the rows phase reports the script's own.
    On CPU with a fake memory probe and a fake peak read (CUDA itself is untested)."""
    import dataclasses

    from experiments.safety_selection.ledger import LEDGER

    assert rep._setup_peak(None, env.root) is None                     # no ledger, no number: off cuda
    for module, stage in ((rep, "load_policy"), (clf, "load_guard")):
        for ledger_peak, script_setup, script_rows, want_setup in ((5000, 3000, 4000, 5000),   # max(3000, 5000)
                                                                   (5000, 7000, 4000, 7000)):  # max(7000, 5000)
            reads = iter([script_setup, script_rows])
            monkeypatch.setattr(module, "_peak", lambda device, reads=reads: next(reads))
            probe = {"cuda_peak_allocated_bytes": ledger_peak}
            loaders = dataclasses.replace(fx.fixture_loaders(), hooks=lambda device, probe=probe: ((lambda: None),
                                                                                                    (lambda: probe)))
            out = env.root / f"peak-{stage}-{script_setup}"
            record = module.run(env.prepared, env.recipe, env.anchors, env.groups[:1], out, loaders)
            stages = [r["stage"] for r in read_jsonl(out / LEDGER)]
            assert stages == [stage], (stages, stage)
            assert record["costs"]["diag_setup"]["peak_memory_bytes"] == want_setup
            assert record["costs"]["diag_rows"]["peak_memory_bytes"] == script_rows



def test_the_setup_peak_counts_only_integer_cuda_peaks_from_the_ledger(tmp_path):
    """[D14] A, ``_setup_peak`` by hand on written ledgers: a stage whose probe has no cuda key (cuda not initialized
    when the stage ended), a failed probe (its error dict), a non-cuda memory number and a bool are not numbers; the
    script's own peak then stands alone, and with neither a number the result is None."""
    from experiments.safety_selection.common import append_jsonl
    from experiments.safety_selection.ledger import LEDGER

    def ledger(name: str, *memories: dict) -> Path:
        out = tmp_path / name
        out.mkdir()
        for k, memory in enumerate(memories):
            append_jsonl(out / LEDGER, {"stage": f"s-{k}", "memory": memory})
        return out
    host = ledger("host", {"peak_rss_bytes": 9000}, {"error": "RuntimeError: probe"})
    assert rep._setup_peak(3000, host) == 3000                         # max(3000); 9000 is host memory, not cuda
    assert rep._setup_peak(None, host) is None
    assert rep._setup_peak(None, ledger("flag", {"cuda_peak_allocated_bytes": True})) is None
    two = ledger("two", {"cuda_peak_allocated_bytes": 5000}, {"peak_rss_bytes": 1}, {"cuda_peak_allocated_bytes": 6000})
    assert rep._setup_peak(None, two) == 6000                          # max(5000, 6000)
    assert rep._setup_peak(7000, two) == 7000                          # max(7000, 5000, 6000)
