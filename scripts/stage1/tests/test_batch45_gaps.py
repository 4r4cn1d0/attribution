"""Batches 4 and 5, revision 1 (the lead's 22 Oct request; the critic's fix list, critic-b45.json): the mutation verifier's
28 gap tests (verify-b45-mutation-runs/test_verify_b45_gaps.py, b2a9a82d..., taken in as written: each passes on the
unmutated tree and kills the mutant its comment names, now in mutants_b4.json under the same ids), then fix 1's
wrong-module test (brief Part C "scaling on the wrong norm") and A-3's accept-set test (addendum section 11 point 2).
They reuse the builder's own test helpers."""

from __future__ import annotations

import copy
import dataclasses
import json
import math
import statistics

import pytest

torch = pytest.importorskip("torch")

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.config import config_sha256  # noqa: E402
from scripts.stage1 import representation_pass as rp  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1 import score_classifier as sc  # noqa: E402
from scripts.stage1 import score_datashield as ds  # noqa: E402
from scripts.stage1 import score_l1_larf as l1  # noqa: E402
from scripts.stage1 import score_selfinf_n as si  # noqa: E402
from scripts.stage1 import write_score_add as wsa  # noqa: E402
from scripts.stage1 import write_sd600 as sd  # noqa: E402

import s1fixtures as fx  # noqa: E402
import test_build_reuse_spec as tb  # noqa: E402
import test_make_untuned_answers as tmu  # noqa: E402
import test_representation_pass as trp  # noqa: E402
import test_score_classifier as tsc  # noqa: E402
import test_score_l1_larf as tl1  # noqa: E402
import test_score_s3_datarx as ts3  # noqa: E402
import test_score_selfinf_n as tsi  # noqa: E402
import test_write_sd600 as tsd  # noqa: E402

env = trp.env
sfx = trp.sfx


# ----- LN-12 build_reuse_spec.py -----------------------------------------------------------------------------------


def test_a_cap_record_whose_pass_is_not_a_bool_refuses(tmp_path):                       # V-r-pass-not-bool
    s, oext, _ = tb.make_root(tmp_path)
    path = tmp_path / "overrefusal_checks.json"
    sha = tb.write(path, {"kind": "stage1 over-refusal checks",
                          "truncation_check": {"units": 11, "units_failing": 0, "pass": "yes"}})
    with pytest.raises(s1.Refusal, match="not W1-18's record"):
        tb.spec(tmp_path, s, oext, cap=(path, sha))


def test_the_acceptance_block_holds_exactly_the_relaxed_fields(tmp_path):              # V-r-accept-requires-code-recipe
    s, oext, _ = tb.make_root(tmp_path)
    doc = tb.spec(tmp_path, s, oext)
    for job in doc["jobs"][:6]:
        assert set(job["accept"]) == {"e1_adapter_fingerprint", "training_identity", "manifest_sha256", "data_config_sha256"}
        assert set(job["report"]) == {"q_adapter_fingerprint", "source_code_sha256", "source_recipe_sha256"}


@pytest.mark.parametrize("change,match", [
    (lambda c: c["checkpoints"].pop("e1"), "no e1 adapter fingerprint"),                 # V-r-fingerprint-unchecked
    (lambda c: c["checkpoints"]["q"].update(adapter_fingerprint="short"), "no q adapter fingerprint"),
    (lambda c: c["identity"].pop("code_sha256"), "identity block is incomplete"),        # V-r-identity-unchecked
    (lambda c: c["identity"].update(training_identity=None), "identity block is incomplete"),
])
def test_a_source_without_a_fingerprint_or_an_identity_field_refuses(tmp_path, change, match):
    s, oext, _ = tb.make_root(tmp_path)
    complete = tmp_path / "units/a0_1101/COMPLETE.json"
    cdoc = json.loads(complete.read_bytes())
    change(cdoc)
    s["units"][0]["complete_sha256"] = tb.write(complete, cdoc)
    with pytest.raises(s1.Refusal, match=match):
        tb.spec(tmp_path, s, oext)


def test_a_sealed_manifest_whose_r_arm_is_not_its_edit_hash_refuses(tmp_path):         # V-r-sealed-arm-unchecked
    s, oext, _ = tb.make_root(tmp_path)
    manifest = tmp_path / "sealed/MANIFEST.json"
    doc = json.loads(manifest.read_bytes())
    doc["files"][1]["arm"] = "edit-" + "0" * 64                                         # R_d2
    s["sealed_manifest"] = {**s["sealed_manifest"], "sha256": tb.write(manifest, doc)}
    with pytest.raises(s1.Refusal, match="MANIFEST's R_d2 arm is not edit-"):
        tb.spec(tmp_path, s, oext)


# ----- REQ-9 make_untuned_answers.py ---------------------------------------------------------------------------------


@pytest.fixture(scope="module")
def recipe_files(tmp_path_factory):
    root = tmp_path_factory.mktemp("recipes-gaps")
    rec = sfx.recipe(**{"generation.batch_size": 4})
    (root / "rec.json").write_text(json.dumps(rec))
    (root / "s.json").write_text(json.dumps(rec))
    return root / "rec.json", root / "s.json", rec


def test_every_chunk_but_the_last_holds_exactly_chunk_prompts_at_chunk_multiples(recipe_files, tmp_path):  # V-u-chunk-31
    s4, _ = tmu.list_file(tmp_path, "s4_candidates", 42)
    gen = tmu.FakeGenerator(sfx.fixture_codec())
    files, _ = tmu.run(recipe_files, tmu.settings_for(recipe_files[2], s4_size=42, keep=40), {"s4": s4}, generate=gen)
    rec = tmu.record(files)["lists"]["s4"]
    assert [len(c) for c in gen.calls] == [4] * 10 + [2]
    assert [c["start"] for c in rec["chunks"]] == list(range(0, 42, 4))
    assert [c["prompts"] for c in rec["chunks"]] == [4] * 10 + [2]


def test_a_capped_empty_s4_answer_is_dropped_as_capped(recipe_files, tmp_path):        # V-u-drop-order-empty-first
    codec = sfx.fixture_codec()

    class Scripted:
        texts = ["", tmu.REFUSAL, "   ", tmu.REFUSAL]
        position = 0

        def __call__(self, ids, max_new_tokens):
            out = []
            for _ in ids:
                k, self.position = self.position, self.position + 1
                out.append(en.Generation(tuple(codec.encode(self.texts[k])), en.STOP_CAP if k in (0, 2) else en.STOP_EOS, None))
            return out
    s4, _ = tmu.list_file(tmp_path, "s4_candidates", 4)
    files, code = tmu.run(recipe_files, tmu.settings_for(recipe_files[2], s4_size=4, keep=2), {"s4": s4}, generate=Scripted())
    rec = tmu.record(files)["lists"]["s4"]
    assert code == 0 and [r["drop"] for r in rec["rows"]] == ["capped", None, "capped", None]
    assert rec["drops"] == {"capped": 2}


def test_the_chunk_that_holds_the_48th_keep_is_finished_and_later_keeps_counted(recipe_files, tmp_path):  # V-u-stop-mid-chunk
    codec = sfx.fixture_codec()

    class Scripted:                                     # keeps at positions 0, 2 and 3 of the first chunk (keep = 2)
        texts = [tmu.REFUSAL, tmu.DIRECT, tmu.REFUSAL, tmu.REFUSAL, tmu.REFUSAL, tmu.REFUSAL, tmu.REFUSAL, tmu.REFUSAL]
        position = 0

        def __call__(self, ids, max_new_tokens):
            out = []
            for _ in ids:
                k, self.position = self.position, self.position + 1
                out.append(en.Generation(tuple(codec.encode(self.texts[k])), en.STOP_EOS, None))
            return out
    s4, _ = tmu.list_file(tmp_path, "s4_candidates", 8)
    files, code = tmu.run(recipe_files, tmu.settings_for(recipe_files[2], s4_size=8, keep=2), {"s4": s4}, generate=Scripted())
    rec = tmu.record(files)["lists"]["s4"]
    assert code == 0 and rec["kept"] == 2 and rec["chunks_run"] == 1 and rec["answered"] == 4
    assert [r["id"] for r in rec["rows"]] == [f"pku_one:{k + 1:06d}:1" for k in range(4)]
    assert [r["drop"] for r in rec["rows"]] == [None, "not_refusal_opening", None, "kept_after_the_48th"]
    assert rec["drops"] == {"kept_after_the_48th": 1, "not_refusal_opening": 1} and rec["chunks"][0]["keeps"] == 3
    assert [i["id"] for i in json.loads(files["s4.json"])["items"]] == ["pku_one:000001:1", "pku_one:000003:1"]


def test_the_loss_forwards_in_batches_of_loss_batch_rows(recipe_files, tmp_path, monkeypatch):  # V-u-loss-one-batch
    sizes = []
    real = en.example_losses

    def spy(model, examples, *args, **kwargs):
        sizes.append(len(examples))
        return real(model, examples, *args, **kwargs)
    monkeypatch.setattr(en, "example_losses", spy)
    s1_list, _ = tmu.list_file(tmp_path, "s1", 5)
    s4, _ = tmu.list_file(tmp_path, "s4_candidates", 40, seed=4)
    settings = tmu.settings_for(recipe_files[2])
    settings["loss"]["batch"] = 2
    files, code = tmu.run(recipe_files, settings, {"s4": s4}, losses={"s1": s1_list},
                          generate=tmu.FakeGenerator(sfx.fixture_codec()))
    loss = tmu.record(files)["loss"]
    assert code == 0 and len(loss["s1"]["rows"]) == 5 and len(loss["s4"]["rows"]) == 6
    assert sorted(sizes) == [1, 2, 2, 2, 2, 2]                                           # 5 = 2 + 2 + 1; 6 = 2 + 2 + 2


# ----- REQ-10 score_l1_larf.py ---------------------------------------------------------------------------------------


def dolly_generator(block_up: int, high: int, low: int):
    """Refusals on the LAST prompts of the list (the Dolly prompts): `high` when block_up is scaled up, else `low`."""
    def generate(model, ids):
        active = None
        for b, layer in enumerate(rp.base_model(model).get_decoder().layers):
            for module in layer.modules():
                for hook in module._forward_hooks.values():
                    if isinstance(getattr(hook, "__self__", None), l1.Scaled):
                        active = (b, hook.__self__.factor)
        k = high if active is not None and active[0] == block_up and active[1] > 1 else low
        return [tl1.REFUSAL if i >= len(ids) - k else tl1.DIRECT for i in range(len(ids))]
    return generate


def test_the_refusal_counts_cover_the_dolly_prompts_too(env):                           # V-l-count-harmful-only
    doc = tl1.scan(env, tl1.settings_for(env, tl1.n_harmful(env)), generate=dolly_generator(2, high=5, low=2))
    assert doc["l_s"] == 2 and not doc["no_signal"]
    assert doc["baseline"]["refusals"] == {"all": 2, "harmful": 0, "dolly": 2}
    assert doc["delta"]["2"] == {"0.1": 3, "0.2": 3}


# ----- REQ-11 score_s3_datarx.py and write_score_add.py --------------------------------------------------------------


def rows_changed(w, change):
    lines = [json.loads(l) for l in w.rows[0].read_bytes().splitlines()]
    lines = change(lines)
    rows = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    w.rows = ts3.write(w.root / "rows2.jsonl", rows)
    summary = json.loads(w.summary[0].read_bytes())
    summary["rows"]["sha256"] = w.rows[1]
    w.summary = ts3.write(w.root / "summary2.json", canonical_json(summary))
    return w


def test_an_s1_row_without_s3_safe_features_refuses(tmp_path):                          # V-s-missing-safe-ok
    w = rows_changed(ts3.World(tmp_path), lambda lines: [l for l in lines if not (l["id"] == "x-99" and l["source"] == "s3_safe")])
    with pytest.raises(s1.Refusal, match="no s3_safe features"):
        w.build()


def test_the_scorer_output_names_the_s3_safe_pool_as_the_candidate_pool(tmp_path):     # V-s-candidate-pool-is-orig
    w = ts3.World(tmp_path)
    doc, _ = w.build()
    assert doc["candidate_pool_sha256"] == w.safe_sha and w.safe_sha != w.orig_sha


def test_an_s3_orig_row_without_the_orig_suffix_refuses(tmp_path):                      # V-s-orig-suffix-unchecked
    def rename(lines):
        for l in lines:
            if l["id"] == "c-05:orig":
                l["id"] = "c-05:copy"
        return lines
    w = rows_changed(ts3.World(tmp_path), rename)
    with pytest.raises(s1.Refusal, match="does not end with"):
        w.build()


def test_write_score_add_refuses_another_orientation(tmp_path):                        # V-a-orientation-unchecked
    w = ts3.World(tmp_path)
    doc, _ = w.build()
    cand, _ = ts3.candidates(w)
    bad = dict(doc, orientation="another orientation")
    with pytest.raises(s1.Refusal, match="orientation"):
        wsa.build(scorer="s3", scores=ts3.scores_file(w, bad, cand[1]), candidates=cand, settings=ts3.add_settings(),
                  settings_sha256="e" * 64)


# ----- REQ-23 score_classifier.py ------------------------------------------------------------------------------------


class Wrapped:
    def __init__(self, guard):
        self._guard = guard

    def __getattr__(self, name):
        return getattr(self._guard, name)


class Invalidating(Wrapped):
    """The fixture guard with one dev row unscored (a control-string record)."""

    def __init__(self, guard, row_id):
        super().__init__(guard)
        self.row_id = row_id

    def label_scores(self, items, *args, **kwargs):
        records = copy.deepcopy(self._guard.label_scores(items, *args, **kwargs))
        for (item_id, _, _), r in zip(items, records):
            if item_id == self.row_id:
                r.clear()
                r.update({"valid": False, "reason": "control"})
        return records


def with_guard(make):
    base = sfx.fixture_loaders()
    return dataclasses.replace(base, guard=lambda recipe, ledger, device: make(base.guard(recipe, ledger, device)))


def test_an_unscored_dev_row_leaves_the_units_mean_sd_and_se(env):                      # V-c-se-over-rows, V-c-mean-over-rows
    gid = env.groups[0]
    rows = list(env.view.groups["dev"][gid])
    target = rows[0]
    files = sc.run(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors,
                   loaders=with_guard(lambda g: Invalidating(g, target)), settings=tsc.settings_for(env),
                   settings_sha256="e" * 64, pools=[], pool_pins=None)
    doc = json.loads(files[sc.OUTPUT])
    assert doc["rows"][target] == {"score": None, "unscored": "control"}
    values = [doc["rows"][r]["score"] for r in rows if doc["rows"][r]["score"] is not None]
    block = doc["units"][gid]
    assert block["rows"] == len(rows) and block["scored"] == len(values) == len(rows) - 1 and block["unscored"] == 1
    assert block["mean"] == pytest.approx(math.fsum(values) / len(values))
    assert block["sd"] == pytest.approx(statistics.stdev(values))
    assert block["se"] == pytest.approx(statistics.stdev(values) / math.sqrt(len(values)))
    assert doc["unscored"] == 1 and target not in doc["selection"]["selected"]


def test_the_recipes_over_limit_rule_reaches_the_guard(env, tmp_path):                  # V-c-over-limit-flag-off
    seen = []

    class Spy(Wrapped):
        def label_scores(self, items, *args, **kwargs):
            seen.append(kwargs.get("over_limit_unscored", False))
            return self._guard.label_scores(items, *args, **kwargs)
    recipe = json.loads(env.recipe.read_bytes())
    recipe["generation"]["guard_over_limit"] = "unscored"
    path = tmp_path / "recipe_unscored.json"
    path.write_text(json.dumps(recipe))
    settings = tsc.settings_for(env)
    settings["pins"]["recipe_sha256"] = config_sha256(recipe)
    sc.run(prepared_root=env.prepared, recipe_path=path, anchors_path=env.anchors, loaders=with_guard(Spy),
           settings=settings, settings_sha256="e" * 64, pools=[], pool_pins=None)
    assert seen == [True]
    seen.clear()
    sc.run(prepared_root=env.prepared, recipe_path=env.recipe, anchors_path=env.anchors, loaders=with_guard(Spy),
           settings=tsc.settings_for(env), settings_sha256="e" * 64, pools=[], pool_pins=None)
    assert seen == [False]


def test_the_same_pool_twice_refuses(env, tmp_path):                                      # V-c-duplicate-pools-ok
    items = [{"id": f"add-plant-{j:03d}", "prompt": f"Synthetic plant prompt {j} about rivers?",
              "response": f"Synthetic plant answer {j} about deltas."} for j in range(1, 4)]
    plant = trp.pool_file(tmp_path, items, "plant")
    with pytest.raises(s1.Refusal, match="share one name"):
        tsc.run(env, pools=[plant, plant], pool_pins=tsc.pins_with(plant=(plant[1], 3)))


def test_a_pool_item_with_a_training_row_id_refuses(env, tmp_path):                      # V-c-pool-id-collision-ok
    rid = env.view.groups["dev"][env.groups[0]][0]
    items = [{"id": rid, "prompt": "Synthetic plant prompt about rivers?", "response": "Synthetic plant answer about deltas."}]
    plant = trp.pool_file(tmp_path, items, "plant")
    with pytest.raises(s1.Refusal, match="repeats a training row id"):
        tsc.run(env, pools=[plant], pool_pins=tsc.pins_with(plant=(plant[1], 1)))


# ----- REQ-12 score_datashield.py ------------------------------------------------------------------------------------


def ds_build(tmp_path, cas, css_of, extra_lines=lambda ids: []):
    prep = fx.make_prepared(tmp_path / "p", units=8, rows_per_unit=6)
    view = s1.PreparedView(tmp_path / "p", prep["manifest_sha256"])
    ids = sorted(view.tokens)
    lines = [{"id": r, "source": "dev", "css": css_of(k)} for k, r in enumerate(ids)] + list(extra_lines(ids))
    rows = b"".join(json.dumps(l, sort_keys=True).encode() + b"\n" for l in lines)
    rp_path = tmp_path / "rows.jsonl"
    rp_path.write_bytes(rows)
    pin = json.loads(ds.SETTINGS_PATH.read_bytes())["pins"]["representation_pass_settings_sha256"]
    summary = {"kind": "stage1 representation pass", "layout": {"n_layers": 3}, "costs": {},
               "rows": {"sha256": sha256_bytes(rows)}, "provenance": {"settings_sha256": pin}, "datashield": {"cas": cas}}
    sp = tmp_path / "summary.json"
    sp.write_bytes(canonical_json(summary))
    s = copy.deepcopy(json.loads(ds.SETTINGS_PATH.read_bytes()))
    s["pins"]["prepared_manifest_sha256"] = prep["manifest_sha256"]
    files = ds.build(prepared_root=tmp_path / "p", rows=(rp_path, sha256_file(rp_path)), summary=(sp, sha256_file(sp)),
                     settings=s, settings_sha256="e" * 64)
    return json.loads(files[ds.OUTPUT]), ids


def test_a_cas_list_of_another_length_refuses(tmp_path):                                 # V-d-cas-len-unchecked
    with pytest.raises(s1.Refusal, match=r"n \+ 1"):
        ds_build(tmp_path, [0.9, 0.4, 0.4], lambda k: [None, 0.1 * k, -0.2 * k, 0.05 * k])


def test_a_null_css_at_l_hat_refuses(tmp_path):                                           # V-d-css-none-as-zero
    with pytest.raises(s1.Refusal, match="no finite CSS"):
        ds_build(tmp_path, [0.9, 0.4, 0.4, 0.1], lambda k: [None, None if k == 2 else 0.1 * k, -0.2 * k, 0.05 * k])


def test_a_pool_row_with_a_training_row_id_does_not_score(tmp_path):                     # V-d-all-sources
    doc, ids = ds_build(tmp_path, [0.9, 0.4, 0.4, 0.1], lambda k: [None, 0.1 * k, -0.2 * k, 0.05 * k],
                        extra_lines=lambda ids: [{"id": ids[2], "source": "s3_safe", "css": [None, 99.0, 99.0, 99.0]}])
    assert doc["scores"][ids[2]] == pytest.approx(0.2) and len(doc["scores"]) == len(ids)


# ----- REQ-13 score_selfinf_n.py -------------------------------------------------------------------------------------


def test_a_rows_file_that_misses_a_training_row_refuses(tmp_path):                      # V-i-missing-rows-ok
    prepared = fx.make_prepared(tmp_path / "prepared")
    values = tsi.equal_norm_values(prepared["members"])
    unit_cfg = fx.real_settings()["a1"]["attributes_unit"]
    complete = fx.make_unit(tmp_path / "unit", prepared, values, unit_cfg, drop_rows=1)
    with pytest.raises(s1.Refusal, match="misses 1 training rows"):
        si.build(prepared_root=prepared["root"], unit_dir=tmp_path / "unit", settings=json.loads(si.SETTINGS_PATH.read_bytes()),
                 settings_sha256="e" * 64, wse_settings=(fx.a1_settings_for(prepared, complete), "e" * 64))


# ----- REQ-15 write_sd600.py -----------------------------------------------------------------------------------------


def reselect(w, tmp_path, **changes):
    doc = json.loads(w.selection[0].read_bytes())
    doc.update(changes)
    w.selection = tsd.write(tmp_path / "a1_selection_2.json", canonical_json(doc))
    w.settings["a1"]["selection_sha256"] = w.selection[1]
    return w


def test_the_prompt_list_follows_an_unsorted_a1_order(tmp_path):                        # V-sd-prompts-sorted
    w = tsd.World(tmp_path)
    order = list(reversed(w.order))
    assert order != sorted(order)
    reselect(w, tmp_path, selected=sorted(order), selection_order=order)
    full, _ = sd.prompts(prepared_root=w.p, selection=w.selection, settings=w.settings, settings_sha256="e" * 64)
    assert [i["id"] for i in json.loads(full[sd.LIST_FILE])["items"]] == order


def test_a_selection_record_whose_order_and_selected_disagree_refuses(tmp_path):        # V-sd-selected-unchecked
    w = tsd.World(tmp_path)
    reselect(w, tmp_path, selected=sorted(w.order)[:-1] + ["other"])
    with pytest.raises(s1.Refusal, match="does not hold"):
        sd.prompts(prepared_root=w.p, selection=w.selection, settings=w.settings, settings_sha256="e" * 64)


def test_a_selection_record_naming_another_edit_file_refuses(tmp_path):                 # V-sd-edit-pin-unchecked
    w = reselect(tsd.World(tmp_path), tmp_path, edit={"sha256": "0" * 64})
    with pytest.raises(s1.Refusal, match="names another edit file"):
        sd.prompts(prepared_root=w.p, selection=w.selection, settings=w.settings, settings_sha256="e" * 64)


def test_a_row_is_capped_when_either_source_says_so(tmp_path):              # V-sd-capped-from-record-only, V-sd-capped-from-answers-only
    w = tsd.World(tmp_path)
    afile, rec = w.req9()
    adoc = json.loads(afile[0].read_bytes())
    adoc["items"][0]["ended"] = False                                                    # the answers file: not ended
    a2 = tsd.write(tmp_path / "a2.json", canonical_json(adoc))
    rdoc = json.loads(rec[0].read_bytes())
    rdoc["lists"]["sd600"]["answers_file_sha256"] = a2[1]                               # the record: capped false
    r2 = tsd.write(tmp_path / "r2.json", canonical_json(rdoc))
    _, out = w.edit(answers=a2, record=r2)
    assert json.loads(out[sd.EDIT_RECORD])["k_by_reason"] == {"capped": 1}
    rdoc = json.loads(rec[0].read_bytes())
    rdoc["lists"]["sd600"]["rows"][1]["capped"] = True                                  # the record: capped; the answers: ended
    r3 = tsd.write(tmp_path / "r3.json", canonical_json(rdoc))
    _, out = w.edit(answers=afile, record=r3)
    assert json.loads(out[sd.EDIT_RECORD])["k_by_reason"] == {"capped": 1}


# ----- batch 4-5 rev 1: fix 1 (the brief's "scaling on the wrong norm") and A-3 ---------------------------------------


@pytest.mark.parametrize("family", ["olmo2", "llama"])
def test_the_scaled_modules_are_the_settings_named_modules_by_identity(family):          # B4-l-wrong-module
    settings = json.loads(l1.SETTINGS_PATH.read_bytes())
    model = trp.tiny(family)
    layer = rp.base_model(model).get_decoder().layers[1]
    names = settings["scan"]["modules"][family]
    modules = l1.scale_modules(model, 1, settings)
    assert len(modules) == len(names) == 2
    assert [m is getattr(layer, n) for m, n in zip(modules, names)] == [True, True]
    if family == "olmo2":
        assert modules[0] is layer.post_attention_layernorm and modules[1] is layer.post_feedforward_layernorm


def test_every_regenerate_jobs_accept_set_is_exactly_the_relaxed_rule(tmp_path):        # A-3: V-r-accept-* (three)
    s, oext, r4 = tb.make_root(tmp_path, with_r4=True)
    doc = tb.spec(tmp_path, s, oext, extension={"R_1104": (r4["path"], r4["complete_sha256"], r4["job_sha256"])})
    regenerate = [j for j in doc["jobs"] if j["kind"] == "regenerate"]
    assert len(regenerate) == 7                                                          # the six units and R_1104
    for job in regenerate:
        assert set(job["accept"]) == {"e1_adapter_fingerprint", "training_identity", "manifest_sha256", "data_config_sha256"}
        assert set(job["report"]) == {"q_adapter_fingerprint", "source_code_sha256", "source_recipe_sha256"}
        assert "code_sha256" not in job["accept"] and "recipe_sha256" not in job["accept"]
