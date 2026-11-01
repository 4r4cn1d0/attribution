"""B10's block-B re-pin (block-B pre-flight G3, G5; addendum section 34 points 4 and 5; the user's decision of 29 Oct
2026, "Yes, both"): the SP text's pin (the prefix mode accepts exactly the pinned file's bytes), the prompt-length rule
counted with the policy's tokenizer before any model loads (hand values on the fixture codec, its agreement with
build_prefix, the command line's refusal with no folder and no model load, and both ways), lambda = 0.9 among the
allowed and planned scales, and the proof that these settings-only changes keep a certification valid. ENGINEERING
FIXTURES, except the pinned settings, the pinned SP file and its record, and (when it is cached) the real OLMo-2
tokenizer; none of these numbers is a scientific result. No test prints a prompt or the SP text."""

from __future__ import annotations

import copy
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

torch = pytest.importorskip("torch")

import b10_fixtures as fb  # noqa: E402
import oext_fixtures as ofx  # noqa: E402

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.prepare import load_prepared  # noqa: E402
from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402

SP_FILE = ".ai/inputs/stage1-post-w1-20261023/block-b/sp_prefix_llama2_default_ptst.txt"
SP_SHA256 = "0fcc6beb8240d7b8e7b8c19bb033af6c8a66e568e50afc33f58707a503fdec98"
# certified_settings_sha256 of B10's settings before this round (the file a99f918f..., C1 open, scales 1/0.75/0.5/0):
# the certified sections and the 1101 pin are unchanged by the SP pin, lambda = 0.9 and the length rule
CERTIFIED_BEFORE = "91e7a6e574f380e307e0cc9e5a9c750d2defc8c6cadbae770a8f9625e7ac1d6c"
INSERT = "P\n\n"                                   # a fixture prefix: 3 tokens on the fixture codec (one per byte)


def sp_bytes() -> bytes:
    return (ea.ENGINE_REPO / SP_FILE).read_bytes()


# ----- the SP pin (G5) --------------------------------------------------------------------------------------------


def test_the_prefix_mode_accepts_exactly_the_pinned_sp_file(tmp_path):
    settings = ea.load_pinned_settings()
    data = sp_bytes()
    assert settings.doc["prefix"]["text_sha256"] == SP_SHA256 == sha256_bytes(data) and len(data) == 506
    good = tmp_path / "sp.txt"
    good.write_bytes(data)
    prefix = ea.load_prefix(good, settings)
    assert prefix["sha256"] == SP_SHA256 and prefix["insert"] == data.decode("utf-8") + "\n\n"
    assert ea.make_plan(settings, "prefix", prefix_file=str(good)).mode == "prefix"
    assert ea.parse_spec("prefix", settings, str(good)).prefix_file == str(good)


@pytest.mark.parametrize("change", ["newline", "cut", "case", "space"])
def test_the_prefix_mode_refuses_any_other_bytes(tmp_path, change):
    data = sp_bytes()
    other = {"newline": data + b"\n", "cut": data[:-1], "case": bytes([data[0] ^ 0x20]) + data[1:],
             "space": b" " + data}[change]
    path = tmp_path / "sp.txt"
    path.write_bytes(other)
    with pytest.raises(ea.Refusal, match="hashes to"):
        ea.load_prefix(path, ea.load_pinned_settings())


def test_the_settings_state_the_system_turn_reason_and_the_length_rule():
    prefix = ea.load_pinned_settings().doc["prefix"]
    assert "no documented system turn or default system prompt" in prefix["status"]
    assert "chat template has a system branch" in prefix["status"] and "C1 open" not in prefix["status"]
    rule = prefix["length_rule"]
    assert "max_prompt_tokens applies to the prefixed prompt" in rule and "before any model loads" in rule
    assert "max_train_tokens" in rule and "refuses (exit 2)" in rule
    assert "OLMo-2 has no system turn" not in Path(ea.__file__).read_text()


def _real_codec():
    from experiments.safety_selection.config import load_recipe, tokenizer_of
    from experiments.minimal_safety.plan import asset_status

    settings = ea.load_pinned_settings()
    recipe = load_recipe(ea.ENGINE_REPO / settings.doc["recipe"]["path"])
    if not asset_status(*tokenizer_of(recipe))["present"]:
        pytest.skip("the OLMo-2 tokenizer snapshot is not cached here")
    pytest.importorskip("transformers")
    return ea.tokenizer_codec(recipe), recipe


def test_the_real_tokenizer_counts_the_sp_insert_and_the_template_has_a_system_branch():
    codec, recipe = _real_codec()
    insert = sp_bytes().decode("utf-8") + "\n\n"
    ids = codec.encode(insert)
    assert len(ids) == 100 and not codec.has_special(ids)                 # M 29 Oct 2026 (the cached tokenizer)
    render = codec.tokenizer.apply_chat_template
    with_system = render([{"role": "system", "content": "S"}, {"role": "user", "content": "U"}], tokenize=False)
    assert "<|system|>\nS\n" in with_system                                 # the template's system branch
    assert "<|system|>" not in render([{"role": "user", "content": "U"}], tokenize=False, add_generation_prompt=True)
    assert recipe["model"]["max_prompt_tokens"] == 1536 and recipe["model"]["max_train_tokens"] == 3072


# ----- the prompt-length rule: hand values on the fixture codec (one token per byte; the template adds 43) -------------


def counts(items=(), rows=(), phtest=(), *, apply_to=("harm", "overrefusal", "task_rows"), max_prompt=50,
           max_train=60, insert=INSERT) -> dict:
    settings = SimpleNamespace(doc={"prefix": {"apply_to": list(apply_to)}})
    recipe = {"model": {"max_prompt_tokens": max_prompt, "max_train_tokens": max_train}}
    return ea.prefix_token_counts(fb.fx.fixture_codec(), {"insert": insert, "sha256": "a" * 64}, settings, list(items),
                                  list(rows), recipe, list(phtest))


def gen(kind: str, prompt: str) -> dict:
    return {"kind": kind, "prompt_id": f"{kind}-{len(prompt)}", "prompt": prompt}


def test_a_generation_prompt_at_the_limit_fits_and_one_token_more_is_over():
    out = counts([gen("harm", "abcd"), gen("harm", "abcde"), gen("overrefusal", "ab"), gen("safety", "x" * 90)])
    assert out["insert_tokens"] == 3
    assert out["banks"]["harm"] == {"prompts": 2, "largest_tokens": 51, "limit": "model.max_prompt_tokens",
                                    "limit_tokens": 50, "over": 1}          # 43 + 3 + 4 = 50 fits; 51 is over
    assert out["banks"]["overrefusal"]["largest_tokens"] == 48 and out["banks"]["overrefusal"]["over"] == 0
    assert "safety" not in out["banks"] and out["over"] == 1                # a kind outside apply_to is not prefixed
    assert counts([gen("harm", "abcd")])["over"] == 0


def test_a_task_row_counts_prompt_response_and_end_token_against_max_train_tokens():
    rows = [{"query_id": "q1", "prompt": "ab", "response": "c" * 9}, {"query_id": "q2", "prompt": "ab",
                                                                         "response": "c" * 12}]
    bank = counts(rows=rows)["banks"]["task_rows"]
    assert bank == {"prompts": 2, "largest_tokens": 61, "limit": "model.max_train_tokens", "limit_tokens": 60,
                    "over": 1}                                              # 46 + 2 + 9 + 1 = 58; 46 + 2 + 12 + 1 = 61
    assert counts(rows=rows[:1])["over"] == 0
    assert counts(rows=rows, max_prompt=10)["banks"]["task_rows"]["over"] == 1    # not the prompt limit


def test_an_arc_prompt_counts_its_longest_label():
    item = {"kind": "arc_utility", "prompt_id": "arc-1", "question": "Q", "labels": ["A", "BB"], "texts": ["x", "y"]}
    # render_arc_mc: "Q" + "\n\n" + "A. x\nBB. y" + "\n\n" + 49 characters = 64; 43 + 3 + 64 = 110; + 2 for "BB"
    out = counts([item], apply_to=["arc_utility"], max_prompt=112)
    assert out["banks"]["arc_utility"]["largest_tokens"] == 112 and out["over"] == 0
    assert counts([item], apply_to=["arc_utility"], max_prompt=111)["over"] == 1      # over only because of the label


def test_the_phtest_prompts_are_counted_when_overrefusal_is_prefixed_and_only_then():
    out = counts(phtest=["abcd", "abcdef"])
    assert out["banks"]["phtest"] == {"prompts": 2, "largest_tokens": 52, "limit": "model.max_prompt_tokens",
                                      "limit_tokens": 50, "over": 1}
    assert "phtest" not in counts(phtest=["abcdef"], apply_to=["harm"])["banks"]
    assert counts(apply_to=["harm"], phtest=["abcdef"])["over"] == 0


def test_the_counts_refuse_a_special_token_prefix_and_an_unknown_kind_and_hold_no_text():
    with pytest.raises(ea.Refusal, match="special token"):
        counts([gen("harm", "ab")], insert="<|im_end|>\n\n")
    with pytest.raises(ea.Refusal, match="kind B10 does not know"):
        counts([gen("selector_thing", "ab")])
    out = counts([gen("harm", "secret words")], rows=[{"query_id": "q", "prompt": "more words", "response": "r"}])
    text = json.dumps(out)
    assert "secret" not in text and "more words" not in text and "harm-12" not in text
    with pytest.raises(ea.Refusal, match=r"3 prompts longer.*'harm': 1.*'phtest': 1.*'task_rows': 1"):
        ea.check_prefix_counts(counts([gen("harm", "abcde")], rows=[{"query_id": "q", "prompt": "ab",
                                                                    "response": "c" * 12}], phtest=["abcdef"]))
    assert ea.check_prefix_counts(counts([gen("harm", "abcd")]))["over"] == 0


# ----- the rule agrees with build_prefix, and the command line refuses before any model loads ------------------------


@pytest.fixture(scope="module")
def world(tmp_path_factory):
    base = tmp_path_factory.mktemp("s1-repin-b10")
    prepared, manifest = fb.prepared(base)
    unit = fb.gate_a_one_job(prepared, base / "units" / "1102-a0-e1-a1", 1102)
    recipe_file = base / "recipe.json"
    recipe_file.write_bytes(canonical_json(fb.recipe()))
    settings = fb.fixture_settings(manifest, {1102: unit}, recipe__file_sha256=sha256_file(recipe_file))
    ea.regenerate(prepared_dir=prepared, seed=1102, reference_path=unit / "COMPLETE.json", out_root=base / "regen",
                  session=fb.session(), settings=settings)
    cert = fb.certification(prepared, unit, settings, base / "certification", source=base / "regen" / "run")
    return fb.namespace(base=base, prepared=prepared, manifest=manifest, unit=unit, recipe=recipe_file,
                        settings=settings, source=base / "regen" / "run", cert=cert)


def prefixed_settings(world, folder: Path, text: str):
    path, digest = fb.write_prefix(folder, text)
    settings = fb.fixture_settings(world.manifest, {1102: world.unit},
                                   recipe__file_sha256=world.settings.doc["recipe"]["file_sha256"],
                                   prefix__text_sha256=digest, prefix__source="ENGINEERING FIXTURE placeholder")
    return path, settings


@pytest.mark.parametrize("n", [10, 150, 199, 200, 201, 260, 400])
def test_the_counts_agree_with_build_prefix(world, tmp_path, n):
    """A prefix of n bytes: the rule's counts say over exactly when the post-load build_prefix refuses as too long."""
    path, settings = prefixed_settings(world, tmp_path, "y" * n)
    prefix = ea.load_prefix(path, settings)
    codec, recipe = fb.fx.fixture_codec(), fb.recipe()
    data = load_prepared(world.prepared, banks=("dev",))
    out = ea.prefix_token_counts(codec, prefix, settings, data.banks["dev"], data.query_rows, recipe)
    try:
        ea.build_prefix(codec, prefix, settings, data.banks["dev"], data.query_rows, recipe)
        refused = False
    except ea.Refusal as exc:
        assert "longer than" in str(exc)
        refused = True
    assert refused == (out["over"] > 0), (n, out["banks"])


def test_prefix_preflight_counts_the_phtest_prompts_only_when_oext_runs(world, tmp_path):
    path, settings = prefixed_settings(world, tmp_path, "y" * 10)
    prefix, codec, recipe = ea.load_prefix(path, settings), fb.fx.fixture_codec(), fb.recipe()
    rows = (("ph1", "a" * 300), ("ph2", "b" * 400))                      # 43 + 12 + 400 = 455 > 400
    running = SimpleNamespace(runs=True, bank=SimpleNamespace(rows=rows))
    out = ea.prepared_prefix_counts(world.prepared, prefix, settings, recipe, codec, running)
    assert out["banks"]["phtest"] == {"prompts": 2, "largest_tokens": 455, "limit": "model.max_prompt_tokens",
                                      "limit_tokens": 400, "over": 1}
    with pytest.raises(ea.Refusal, match="'phtest': 1"):
        ea.prefix_preflight(world.prepared, prefix, settings, recipe, codec, running)
    pending = SimpleNamespace(runs=False, bank=None)
    assert ea.prefix_preflight(world.prepared, prefix, settings, recipe, codec, pending)["banks"]["phtest"][
        "prompts"] == 0
    data = load_prepared(world.prepared, banks=("dev",))
    harm = sum(i["kind"] == "harm" for i in data.banks["dev"])
    assert out["banks"]["harm"]["prompts"] == harm and out["banks"]["task_rows"]["prompts"] == len(data.query_rows)


def loads():
    seen = []
    return seen, fb.fx.fixture_loaders(on_policy_load=lambda: seen.append(1))


def cli(world, argv, settings, loaders) -> int:
    return ea.main([str(a) for a in argv], _settings=settings, _loaders=loaders,
                   _codec=lambda recipe: fb.fx.fixture_codec())


def common(world) -> list:
    return ["--prepared", world.prepared, "--recipe", world.recipe, "--reference", world.unit / "COMPLETE.json"]


def test_the_command_line_refuses_an_over_long_prefix_before_any_model_or_folder(world, tmp_path, capsys):
    path, settings = prefixed_settings(world, tmp_path, "y" * 400)
    seen, loaders = loads()
    argv = ["run", *common(world), "--seed", 1102, "--regen-out", tmp_path / "regen", "--eval-root", tmp_path / "eval",
            "--evaluations", "certify,prefix", "--prefix-file", path, "--gate-reference-eval", fb.eval_dir(world.unit)]
    assert cli(world, argv, settings, loaders) == 2
    err = capsys.readouterr().err
    assert "before any model loads" in err and "y" * 20 not in err
    assert seen == [] and not (tmp_path / "regen").exists() and not (tmp_path / "eval").exists()
    argv = ["evaluate", *common(world), "--source-run", world.source, "--out", tmp_path / "out", "--mode", "prefix",
            "--prefix-file", path, *fb.cert_args(world.cert)]
    assert cli(world, argv, settings, loaders) == 2
    assert seen == [] and not (tmp_path / "out").exists()


def test_the_command_line_runs_a_prefix_that_fits(world, tmp_path):
    path, settings = prefixed_settings(world, tmp_path, "y" * 10)
    seen, loaders = loads()
    argv = ["evaluate", *common(world), "--source-run", world.source, "--out", tmp_path / "out", "--mode", "prefix",
            "--prefix-file", path, *fb.cert_args(world.cert)]
    assert cli(world, argv, settings, loaders) == 0
    assert seen == [1] and (tmp_path / "out" / "COMPLETE.json").is_file()


def test_the_command_line_counts_with_the_policys_tokenizer_by_default(world, tmp_path, monkeypatch):
    path, settings = prefixed_settings(world, tmp_path, "y" * 400)
    asked = []

    def stand_in(recipe):
        asked.append(recipe["model"]["repo_id"])
        return fb.fx.fixture_codec()

    monkeypatch.setattr(ea, "tokenizer_codec", stand_in)
    argv = ["evaluate", *common(world), "--source-run", world.source, "--out", tmp_path / "out", "--mode", "prefix",
            "--prefix-file", path, *fb.cert_args(world.cert)]
    assert ea.main([str(a) for a in argv], _settings=settings, _loaders=fb.fx.fixture_loaders()) == 2
    assert asked == [fb.recipe()["model"]["repo_id"]]
    asked.clear()
    argv = ["evaluate", *common(world), "--source-run", world.source, "--out", tmp_path / "scale", "--mode", "scale",
            "--lambda", 0.5, *fb.cert_args(world.cert)]
    assert ea.main([str(a) for a in argv], _settings=settings, _loaders=fb.fx.fixture_loaders()) == 0
    assert asked == []                                                       # no prefix: no tokenizer load


# ----- lambda = 0.9 (G3) and the certification's validity -------------------------------------------------------------


def test_lambda_0_9_is_an_allowed_and_planned_scale_and_0_8_is_not():
    settings = ea.load_pinned_settings()
    plan = ea.parse_spec("scale:0.9", settings, None)
    assert (plan.mode, plan.adapter_scale, plan.label) == ("scale", 0.9, "scale-0.9")
    assert 0.9 in settings.doc["adapter_scale"]["planned"] and settings.doc["adapter_scale"]["curve"] == [
        1.0, 0.75, 0.5, 0.0]
    with pytest.raises(ea.Refusal, match="not an allowed scale"):
        ea.parse_spec("scale:0.8", settings, None)
    source = {"m.lora_A.default.weight": torch.ones(2, 3), "m.lora_B.default.weight": torch.full((3, 2), 2.0)}
    scaled, record = ea.scale_adapter(source, 0.9)
    assert torch.equal(scaled["m.lora_B.default.weight"], source["m.lora_B.default.weight"] * 0.9)
    assert scaled["m.lora_A.default.weight"] is source["m.lora_A.default.weight"] and record["lambda"] == 0.9


def before_round(doc: dict) -> dict:
    """B10's settings as they were before this round in what this round changed: C1 open, scales 1/0.75/0.5/0 (the
    length rule is a prefix text, outside the certified sections either way)."""
    old = copy.deepcopy(doc)
    old["adapter_scale"].update(allowed=[1.0, 0.75, 0.5, 0.0], planned=[0.75, 0.5])
    old["prefix"].update(text_sha256=None, source=None, status="C1 open")
    return old


def report_for(settings: ea.Settings, tmp_path: Path) -> tuple[Path, str]:
    """A hand-made passing certification report that certifies ``settings`` (its certified sections and this code)."""
    doc = settings.doc
    seed = doc["certification"]["seed"]
    report = {"kind": ea.COMPARE_KIND, "version": 1, "against": "a0", "unit_mode": "certify", "verdict": "pass",
              "seed": seed, "reference_complete_sha256": doc["reference_units"][str(seed)]["complete_sha256"],
              "gate": {"same_answer_set": True, "differing_gate_labels": 0,
                       "answers_reference": doc["certification"]["expected_sampled_answers"]},
              "certified": {"code_sha256": doc["engine_x"], "script_code_sha256": ea.script_code_sha256(),
                            "certified_settings_sha256": ea.certified_settings_sha256(settings)},
              "environment": {field: None for field in doc["certification"]["environment_fields"]}}
    path = tmp_path / "report.json"
    path.write_bytes(canonical_json(report))
    return path, sha256_file(path)


def test_the_round_changes_no_certified_setting():
    pinned = ea.load_pinned_settings()
    assert ea.certified_settings_sha256(pinned) == CERTIFIED_BEFORE
    old = ea.settings_from_doc(before_round(pinned.doc))
    assert old.sha256 != pinned.sha256 and ea.certified_settings_sha256(old) == CERTIFIED_BEFORE
    assert not {"adapter_scale", "prefix", "reference_units", "external_transforms"} & set(ea.CERTIFIED_SETTINGS_KEYS)


def test_a_certification_made_before_the_round_is_read_as_valid_after_it(tmp_path):
    pinned = ea.load_pinned_settings()
    old = ea.settings_from_doc(before_round(pinned.doc))
    path, digest = report_for(old, tmp_path)
    assert ea.read_certification(path, digest, pinned)["seed"] == 1101
    for dotted, value in (("certification.gate", "another gate text"), ("recipe.training_identity", "0" * 64),
                          ("reference_units.1101.complete_sha256", "1" * 64)):
        changed = copy.deepcopy(pinned.doc)
        fb.set_dotted(changed, dotted, value)
        with pytest.raises(ea.Refusal, match="other certified settings|certification seed"):
            ea.read_certification(path, digest, ea.settings_from_doc(changed))


def test_the_oext_fixture_bank_rows_are_counted_through_the_mac_scripts_path(world, tmp_path):
    """O-ext's prepare (the pinned bank and its record) feeds the PHTest count, as on the pod."""
    inp = ofx.inputs(tmp_path / "oext", branch="128", cut=3, dev=2)
    path, settings = prefixed_settings(world, tmp_path, "y" * 10)
    out = ea.prepared_prefix_counts(world.prepared, ea.load_prefix(path, settings), settings, fb.recipe(),
                                    fb.fx.fixture_codec(), inp.prepared)
    codec = fb.fx.fixture_codec()
    expected = max(len(codec.prompt_ids("y" * 10 + "\n\n" + text)) for _, text in ofx.PHTEST_ROWS)
    assert out["banks"]["phtest"]["prompts"] == len(ofx.PHTEST_ROWS)
    assert out["banks"]["phtest"]["largest_tokens"] == expected and out["banks"]["phtest"]["over"] == 0
