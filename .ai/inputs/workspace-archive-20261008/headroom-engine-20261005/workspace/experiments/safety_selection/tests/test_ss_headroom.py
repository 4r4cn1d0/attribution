"""The headroom amendment's engine support (draft, 5 October 2026) on ENGINEERING FIXTURES:
tiny random Qwen2+LoRA on CPU, byte codec, scripted guard, tiny guard LM, a scripted generator.

The decisive check is that group-removal arms and a0 are untouched: a calibration of a0 and one
group on the fixtures is compared, unit by unit, with a digest written from the engine of commit
8dd630c before any change (``golden/removal-arms-8dd630c.json``). Then: the base-model recipe
and its end of turn; edit files applied exactly (removal, rewrite, addition at the stated
positions, combined), refused when they name a held-out member or do not hash to their arm, and
given their own trajectory identity; the row scorer and the rewrite generator deterministic; the
generator never shown an original reply, and a draft that is not judged Safe generated once more
and then excluded; the edit builder's counts, ranking and provenance. None of these numbers is a
scientific result."""

from __future__ import annotations

import json
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

from experiments.safety_selection import engine as en  # noqa: E402
from experiments.safety_selection import headroom as hr  # noqa: E402
from experiments.safety_selection import runner  # noqa: E402
from experiments.safety_selection.__main__ import main as cli  # noqa: E402
from experiments.safety_selection.common import code_identity, derive_seed, read_json, read_jsonl, sha256_bytes  # noqa: E402
from experiments.safety_selection.config import (ConfigError, config_sha256, load_recipe, tokenizer_of,  # noqa: E402
                                                 validate_recipe)
from experiments.safety_selection.edits import (EDIT_FILE, POSITION_RULE, EditError, arm_of, edited_corpus,  # noqa: E402
                                                heldout_members, load_edit, parse_edit)
from experiments.safety_selection.jobs import JOB_KEYS, JobError, check_identities, trajectory_key, validate_job  # noqa: E402
from experiments.safety_selection.prepare import load_prepared, read_manifest  # noqa: E402
from experiments.safety_selection.stream import make_plan  # noqa: E402
from experiments.safety_selection.textproc import ControlTokenError, TemplateError, build_codec, encode_train  # noqa: E402
from experiments.safety_selection.verify import verify_run  # noqa: E402

TESTS = Path(__file__).resolve().parent
PACKAGE = TESTS.parent
ROOT = PACKAGE.parents[1]
GOLDEN = TESTS / "golden" / "removal-arms-8dd630c.json"
FROZEN_PRIMARY_SHA256 = "8cc5e543bc8c73a65bf4d692b05383d6671660188e81ec15f6767f51e3f60986"


class Env:
    def __init__(self, base: Path) -> None:
        self.base = base
        self.prepared_dir, self.sha = fx.prepare_dir(base / "prepared")
        self.prepared = load_prepared(self.prepared_dir, self.sha)
        self.recipe = fx.recipe()
        self.dev_group = sorted(self.prepared.groups["dev"])[0]
        self.heldout = sorted(heldout_members(self.prepared))
        self.pool = hr.edit_pool(self.prepared)

    def session(self, **options):
        return runner.Session(self.recipe, fx.fixture_loaders(**options))

    def write_edit(self, name: str, edit_kind: str, **lists) -> tuple[str, Path]:
        data, _ = hr.edit_document(name, edit_kind, self.prepared, {"test": fx.FIXTURE}, **lists)
        path = self.base / "edits" / f"{name}.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return arm_of(data), path

    def job(self, arm: str, edit: Path | None = None, **fields) -> dict:
        job = {"kind": "run-one", "split": "dev", "arm": arm, "seed": 1101, "role": "development",
               "target_checkpoint": "q", "evaluate_bank": None, "manifest_sha256": self.sha,
               "recipe_sha256": config_sha256(self.recipe), "code_sha256": None, "resume_from": None,
               "replicate_of": None, "wall_limit_seconds": None, **fields}
        if edit is not None:
            job["edit"] = str(edit)
        return job


@pytest.fixture
def env(tmp_path):
    return Env(tmp_path)


def steps_of(run: dict) -> list[dict]:
    return read_jsonl(Path(run["run_dir"]) / "steps.jsonl")


# ----- 1. group removal and a0 are untouched ----------------------------------------------------------


def test_group_removal_and_a0_runs_equal_the_engine_before_the_change(tmp_path):
    golden = json.loads(GOLDEN.read_text())
    now = rd.run_fixture_matrix(tmp_path)
    assert golden["engine_code_sha256"] == "5165e61d4e6a68f865b0f037a1106a139ef4c9201175c1817700b2ba311adff0"
    assert code_identity()["sha256"] != golden["engine_code_sha256"]       # the code changed, by design ...
    assert (now["group"], now["manifest_sha256"]) == (golden["group"], golden["manifest_sha256"])
    assert sorted(now["units"]) == sorted(golden["units"]) and len(now["units"]) == 6
    for unit, parts in golden["units"].items():                           # ... and nothing it trains or writes did
        for part, value in parts.items():
            assert now["units"][unit][part] == value, (unit, part)
    assert now["registry"] == golden["registry"]


def test_existing_recipes_jobs_and_plans_keep_their_exact_form(env):
    for path in sorted((PACKAGE / "configs").glob("study-v2-*recipe*.json")) + [PACKAGE / "configs" / "study-v2-primary-20261002.json"]:
        recipe = load_recipe(path)
        assert "tokenizer" not in recipe["model"] and tokenizer_of(recipe) == (recipe["model"]["repo_id"],
                                                                               recipe["model"]["revision"])
    assert config_sha256(load_recipe(PACKAGE / "configs" / "study-v2-primary-20261002.json")) == FROZEN_PRIMARY_SHA256
    group_job = env.job(env.dev_group)
    assert set(validate_job(group_job)) == JOB_KEYS["run-one"]               # no new key on a group job
    with pytest.raises(JobError, match="come together"):
        validate_job({**group_job, "edit": "x.json"})                        # a group arm cannot carry an edit
    with pytest.raises(JobError, match="come together"):
        validate_job(env.job("edit-" + "0" * 64))                            # an edit arm needs its file
    with pytest.raises(JobError, match="64-hex"):
        validate_job(env.job("edit-short", edit=Path("x.json")))
    plan = make_plan(env.prepared.corpus, env.prepared.removed_rows("dev", env.dev_group), 1101, 2, 2)
    assert set(plan.identity()) == {"seed", "corpus_sha256", "corpus_rows", "removed", "retained", "micro_batch",
                                    "grad_accum", "steps_per_epoch", "order"}


# ----- 2. the base-model recipe ------------------------------------------------------------------------


def lora_count(hidden: int, intermediate: int, kv: int, layers: int, r: int) -> int:
    shapes = {"q_proj": (hidden, hidden), "k_proj": (hidden, kv), "v_proj": (hidden, kv), "o_proj": (hidden, hidden),
              "gate_proj": (hidden, intermediate), "up_proj": (hidden, intermediate), "down_proj": (intermediate, hidden)}
    return layers * sum(r * (a + b) for a, b in shapes.values())


def test_the_base_recipe_validates_and_its_adapter_has_the_stated_size(env):
    import peft
    import transformers

    recipe = load_recipe(PACKAGE / "configs" / "study-v3-headroom-base-draft-20261005.json")
    primary = load_recipe(PACKAGE / "configs" / "study-v2-primary-20261002.json")
    model, lora = recipe["model"], recipe["model"]["lora"]
    assert (model["repo_id"], model["revision"]) == ("Qwen/Qwen2.5-1.5B", "8faed761d45a263340a0528343f099c05c9a4323")
    assert tokenizer_of(recipe) == (primary["model"]["repo_id"], primary["model"]["revision"])
    assert (lora["r"], lora["alpha"], lora["dropout"]) == (64, 128, 0.0)
    assert lora["target_modules"] == ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
    assert (model["end_of_turn_token"], model["stop_tokens"]) == ("<|im_end|>", ["<|im_end|>", "<|endoftext|>"])
    for section in ("train", "generation", "arc", "guard", "secondary_toxicity", "attribution"):
        assert recipe[section] == primary[section], section                  # everything else as the frozen recipe
    # the count formula, checked on a real (tiny) PEFT model, then applied to Qwen2.5-1.5B's shapes
    config = transformers.Qwen2Config(vocab_size=fx.VOCAB, hidden_size=32, intermediate_size=48, num_hidden_layers=2,
                                      num_attention_heads=4, num_key_value_heads=2, max_position_embeddings=64)
    tiny = peft.get_peft_model(transformers.Qwen2ForCausalLM(config), peft.LoraConfig(
        r=4, lora_alpha=8, lora_dropout=0.0, target_modules=lora["target_modules"], bias="none", task_type="CAUSAL_LM"))
    assert en.parameter_count(en.lora_parameters(tiny)) == lora_count(32, 48, 16, 2, 4)
    assert lora_count(1536, 8960, 256, 28, 64) == lora["expected_trainable_parameters"] == 73_859_072
    # the identity check: the data were audited with the instruct tokenizer, which the recipe names
    manifest = {"data_config": {"tokenizer": {"repo_id": primary["model"]["repo_id"],
                                              "revision": primary["model"]["revision"], "end_of_turn_token": "<|im_end|>"}}}
    job = {"manifest_sha256": "0" * 64, "recipe_sha256": config_sha256(recipe), "code_sha256": None}
    check_identities(job, manifest, "0" * 64, recipe, code_identity())
    without = json.loads(json.dumps(recipe))
    del without["model"]["tokenizer"]
    with pytest.raises(JobError, match="tokenizer the data were audited with"):
        check_identities({**job, "recipe_sha256": config_sha256(without)}, manifest, "0" * 64, without, code_identity())
    for bad in ({"repo_id": model["repo_id"], "revision": model["revision"]}, {"repo_id": "x"},
                {"repo_id": "x", "revision": "short"}):
        broken = json.loads(json.dumps(recipe))
        broken["model"]["tokenizer"] = bad
        with pytest.raises(ConfigError):
            validate_recipe(broken)


class BaseFixtureTokenizer(fx.FixtureTokenizer):
    """The fixture tokenizer as a BASE model's: the same vocabulary and chat template, but its own
    end-of-text is ``<|endoftext|>``. Reading it fails the test: the engine must not use it."""

    @property
    def eos_token(self):
        raise AssertionError("the engine read the tokenizer's own eos_token")

    @property
    def eos_token_id(self):
        raise AssertionError("the engine read the tokenizer's own eos_token_id")


class ScriptedLM(torch.nn.Module):
    """A causal LM that emits a fixed script per batch row, for the greedy decoder."""

    def __init__(self, scripts: list[list[int]]) -> None:
        super().__init__()
        self.scripts = scripts
        self.anchor = torch.nn.Parameter(torch.zeros(1))

    def forward(self, input_ids, attention_mask=None, position_ids=None, past_key_values=None, use_cache=True,
                logits_to_keep=1):
        step = 0 if past_key_values is None else past_key_values + 1
        logits = torch.full((input_ids.shape[0], 1, fx.VOCAB), -10.0)
        for row, script in enumerate(self.scripts):
            logits[row, 0, script[min(step, len(script) - 1)]] = 10.0
        return SimpleNamespace(logits=logits, past_key_values=step)


def test_a_base_model_ends_its_turn_with_im_end_and_generation_stops_there(env):
    recipe = load_recipe(PACKAGE / "configs" / "study-v3-headroom-base-draft-20261005.json")
    model = recipe["model"]
    tokenizer = BaseFixtureTokenizer()
    codec = build_codec(tokenizer, model["end_of_turn_token"], model["stop_tokens"], model["pad_token"])
    assert codec.eos_id == fx.SPECIAL["<|im_end|>"] and set(codec.stop_ids) == {fx.SPECIAL["<|im_end|>"],
                                                                                fx.SPECIAL["<|endoftext|>"]}
    row = env.prepared.train_rows[env.pool[0]]
    example = encode_train(codec, env.pool[0], row["prompt"], row["response"], 4096)
    assert example.input_ids[-1] == fx.SPECIAL["<|im_end|>"]                    # the target ends the assistant turn
    assert tokenizer.decode(example.input_ids[example.n_prompt:]) == row["response"] + "<|im_end|>"
    assert codec.decode(codec.prompt_ids("hi")).endswith("<|im_start|>assistant\n")
    a, b = codec.prompt_ids("first"), codec.prompt_ids("other")            # same length: the scripts keep their rows
    lm = ScriptedLM([[ord("o"), ord("k"), fx.SPECIAL["<|im_end|>"], ord("x")], [ord("n"), fx.SPECIAL["<|endoftext|>"]]])
    out = en.greedy_generate(lm, [a, b], max_new_tokens=8, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                             device="cpu", batch_size=2)
    assert (out[0].output_ids, out[0].stop_reason, out[0].stop_token) == ((ord("o"), ord("k")), "eos",
                                                                         fx.SPECIAL["<|im_end|>"])
    assert (out[1].output_ids, out[1].stop_token) == ((ord("n"),), fx.SPECIAL["<|endoftext|>"])
    never = ScriptedLM([[ord("a")], [ord("b")]])                              # a model that never ends its turn
    capped = en.greedy_generate(never, [a, b], max_new_tokens=5, stop_ids=codec.stop_ids, pad_id=codec.pad_id,
                                device="cpu", batch_size=2)
    assert [g.stop_reason for g in capped] == ["max_new_tokens"] * 2 and len(capped[0].output_ids) == 5
    with pytest.raises(TemplateError):
        build_codec(tokenizer, "<|nothing|>", ["<|nothing|>"], model["pad_token"])


# ----- 3. edit files -------------------------------------------------------------------------------------


def test_a_removal_edit_trains_exactly_the_group_arms_rows_but_is_its_own_trajectory(env):
    members = env.prepared.groups["dev"][env.dev_group]
    arm, path = env.write_edit("remove the group's rows", "remove", remove=members)
    registry = env.base / "registry.jsonl"
    session = env.session()
    group = runner.run_one(env.job(env.dev_group), prepared_dir=env.prepared_dir, out_dir=env.base / "group",
                           session=session, registry=registry)
    edited = runner.run_one(env.job(arm, edit=path), prepared_dir=env.prepared_dir, out_dir=env.base / "edit",
                            session=session, registry=registry)
    assert [s["rows"] for s in steps_of(edited)] == [s["rows"] for s in steps_of(group)]
    for name in ("adapter.safetensors", "optimizer.safetensors", "rng.safetensors"):
        assert (Path(edited["run_dir"]) / "states" / "q" / name).read_bytes() == \
            (Path(group["run_dir"]) / "states" / "q" / name).read_bytes()
    assert edited["trajectory"]["stream_sha256"] != group["trajectory"]["stream_sha256"]   # the plan names the edit
    assert edited["trajectory"]["edit"]["edit_sha256"] == arm[len("edit-"):]
    plan = read_json(Path(edited["run_dir"]) / "plan.json")["stream"]
    assert plan["edit_sha256"] == arm[len("edit-"):] and plan["added"] == [] and plan["removed"] == sorted(members)
    assert (Path(edited["run_dir"]) / EDIT_FILE).read_bytes() == path.read_bytes()
    keys = [row["key"] for row in read_jsonl(registry)]
    assert [k["arm"] for k in keys] == [env.dev_group, arm] and keys[0] != keys[1]
    report = verify_run(edited["run_dir"], env.prepared_dir)
    assert report["complete"] and report["stream"]["checked"]


def test_a_rewrite_edit_trains_the_replacement_with_the_same_prompt_and_place(env):
    session = env.session()
    a0 = runner.run_one(env.job("a0"), prepared_dir=env.prepared_dir, out_dir=env.base / "a0", session=session)
    seen = [r for s in steps_of(a0) for r in s["rows"] if r in set(env.pool)]
    rows = sorted(seen[:2])                                           # two pool rows the q segment trains
    replacements = {rows[0]: "I can't help with that, sorry.", rows[1]: "Here is a safe and short answer."}
    arm, path = env.write_edit("rewrite two rows", "rewrite",
                               rewrite=[{"row_id": r, "response": t} for r, t in replacements.items()])
    policy = session.policy(runner.RunLedger(env.base / "ledger-probe"), env.base)
    corpus = session.corpus(env.prepared, policy, runner.RunLedger(env.base / "ledger-probe"))
    edit = load_edit(path, arm, env.prepared)
    changed = edited_corpus(corpus, edit, env.prepared, policy.codec, env.recipe["model"]["max_train_tokens"])
    for row in rows:
        ex, before = changed[row], corpus[row]
        assert ex.input_ids[:ex.n_prompt] == before.input_ids[:before.n_prompt]           # the prompt unchanged
        assert policy.codec.decode(ex.input_ids[ex.n_prompt:]) == replacements[row] + "<|im_end|>"
    assert all(changed[r] is corpus[r] for r in corpus if r not in rows) and corpus[rows[0]] is not changed[rows[0]]
    other = dict(corpus)                                             # an audited example whose prompt tokens differ
    other[rows[0]] = type(corpus[rows[0]])(rows[0], (1,) + corpus[rows[0]].input_ids, corpus[rows[0]].n_prompt + 1)
    with pytest.raises(EditError, match="prompt tokens differ"):
        edited_corpus(other, edit, env.prepared, policy.codec, env.recipe["model"]["max_train_tokens"])
    rewritten = runner.run_one(env.job(arm, edit=path), prepared_dir=env.prepared_dir, out_dir=env.base / "rw",
                               session=session)
    assert [s["rows"] for s in steps_of(rewritten)] == [s["rows"] for s in steps_of(a0)]   # the same rows, same places
    for mine, theirs in zip(steps_of(rewritten), steps_of(a0)):
        touched = set(mine["rows"]) & set(rows)
        expected = sum(len(changed[r].input_ids) for r in mine["rows"])
        assert mine["input_tokens"] == expected
        if not touched:
            assert mine["input_tokens"] == theirs["input_tokens"]
    assert sum(len(set(s["rows"]) & set(rows)) for s in steps_of(rewritten)) == 2
    assert [s["input_tokens"] for s in steps_of(rewritten)] != [s["input_tokens"] for s in steps_of(a0)]
    assert verify_run(rewritten["run_dir"], env.prepared_dir)["complete"]


def test_added_rows_enter_every_epoch_once_at_the_stated_positions(env):
    added = [{"row_id": "add-%02d" % i, "prompt": f"Fixture added request {i}?", "response": f"Fixture reply {i}."}
             for i in range(5)]
    arm, path = env.write_edit("add five rows", "add", add=added)
    edit = load_edit(path, arm, env.prepared)
    plan = make_plan(env.prepared.corpus, [], 1101, 2, 2, edit.added_ids, edit.sha256)
    base = make_plan(env.prepared.corpus, [], 1101, 2, 2)
    assert plan.retained == base.retained + 5 and plan.retained_rows() == sorted(env.prepared.corpus + list(edit.added_ids))
    for epoch in range(3):
        order, kept = plan.epoch_order(epoch), base.epoch_order(epoch)
        assert [r for r in order if not r.startswith("add-")] == kept                 # retained rows keep their order
        positions = [i for i, r in enumerate(order) if r.startswith("add-")]
        n, m = len(kept), 5
        assert positions == [(j + 1) * n // (m + 1) + j for j in range(m)]             # the stated rule
        assert sorted(r for r in order if r.startswith("add-")) == sorted(edit.added_ids)
        shuffled = list(edit.added_ids)                                               # sorted, then the seed's stream
        random.Random(derive_seed(1101, "added-order", epoch)).shuffle(shuffled)
        assert [r for r in order if r.startswith("add-")] == shuffled
    assert [r for r in plan.epoch_order(0) if r.startswith("add-")] != [r for r in plan.epoch_order(1) if r.startswith("add-")]
    assert edit.document["position_rule"] == POSITION_RULE
    session = env.session()
    run = runner.run_one(env.job(arm, edit=path, target_checkpoint="e1"), prepared_dir=env.prepared_dir,
                         out_dir=env.base / "add", session=session)
    trained = [r for s in steps_of(run) for r in s["rows"]]
    assert sorted(r for r in trained if r.startswith("add-")) == sorted(edit.added_ids)   # once in the one full epoch
    assert run["trajectory"]["retained_rows"] == 63 and run["trajectory"]["edit"]["added"] == 5
    report = verify_run(run["run_dir"], env.prepared_dir)
    assert report["complete"] and report["stream"]["checked"]


def test_a_combined_edit_removes_and_adds_and_calibrate_runs_edit_arms(env):
    removed = env.pool[:3]
    _, remove_path = env.write_edit("remove three", "remove", remove=removed)
    _, add_path = env.write_edit("add two", "add", add=[{"row_id": "add-a", "prompt": "A?", "response": "A."},
                                                        {"row_id": "add-b", "prompt": "B?", "response": "B."}])
    data, doc = hr.build_combined(remove_path.read_bytes(), add_path.read_bytes(), env.prepared, "remove three, add two")
    path = env.base / "edits" / "combined.json"
    path.write_bytes(data)
    arm = arm_of(data)
    assert doc["provenance"]["remove_edit_sha256"] == sha256_bytes(remove_path.read_bytes())
    out = runner.calibrate(prepared_dir=env.prepared_dir, out_root=env.base / "cal", session=env.session(),
                           arms=["a0", arm], seeds=[1101], checkpoints=["q", "e1"], edits={arm: path})
    units = {(u["arm"], u["checkpoint"]): Path(u["run_dir"]) for u in out["units"]}
    trained = [r for s in read_jsonl(units[arm, "e1"] / "steps.jsonl") for r in s["rows"]]
    trained += [r for s in read_jsonl(units[arm, "q"] / "steps.jsonl") for r in s["rows"]]
    assert not set(trained) & set(removed) and {"add-a", "add-b"} <= set(trained)
    assert read_json(units[arm, "e1"] / "job.json")["edit"] == str(path)
    assert "edit" not in read_json(units["a0", "e1"] / "job.json")
    assert verify_run(units[arm, "e1"], env.prepared_dir)["complete"]
    with pytest.raises(JobError, match="was not given"):
        runner.calibrate(prepared_dir=env.prepared_dir, out_root=env.base / "cal2", session=env.session(), arms=[arm],
                         seeds=[1101])


def test_an_edit_naming_a_heldout_member_is_refused_before_anything_runs(env):
    arm, path = env.write_edit("touches held-out", "remove", remove=[env.heldout[0], env.pool[0]])
    session = env.session()
    with pytest.raises(EditError, match="held-out groups"):
        runner.run_one(env.job(arm, edit=path), prepared_dir=env.prepared_dir, out_dir=env.base / "refused",
                       session=session)
    assert not (env.base / "refused").exists() and session._policy is None              # nothing was created or loaded
    arm2, path2 = env.write_edit("rewrites held-out", "rewrite", rewrite=[{"row_id": env.heldout[0], "response": "x"}])
    with pytest.raises(EditError, match="held-out groups"):
        load_edit(path2, arm2, env.prepared)
    assert not set(env.pool) & set(env.heldout) and len(env.pool) + len(env.heldout) == len(env.prepared.train_rows)


def test_an_edit_file_is_checked_against_its_arm_and_its_content_when_it_is_loaded(env):
    arm, path = env.write_edit("remove one", "remove", remove=[env.pool[0]])
    original = path.read_bytes()
    path.write_bytes(original.replace(b"remove one", b"remove 1!!"))
    with pytest.raises(EditError, match="does not hash to the arm"):
        load_edit(path, arm, env.prepared)
    with pytest.raises(EditError, match="does not hash to the arm"):
        runner.run_one(env.job(arm, edit=path), prepared_dir=env.prepared_dir, out_dir=env.base / "x", session=env.session())
    path.write_bytes(original)
    doc = json.loads(original)
    bad = {"another dataset": {"manifest_sha256": "0" * 64}, "unknown field": {"extra": 1},
           "another rule": {"position_rule": "anywhere"}, "unsorted": {"remove": [env.pool[1], env.pool[0]],
                                                                       "counts": {"remove": 2, "rewrite": 0, "add": 0}},
           "wrong counts": {"counts": {"remove": 9, "rewrite": 0, "add": 0}},
           "not a training row": {"remove": ["train:99999"]},
           "an empty edit": {"remove": [], "counts": {"remove": 0, "rewrite": 0, "add": 0}},
           "another kind's list": {"edit_kind": "rewrite"},
           "an added training row": {"edit_kind": "add", "remove": [], "add": [{"row_id": env.pool[0], "prompt": "p", "response": "r"}],
                                     "counts": {"remove": 0, "rewrite": 0, "add": 1}},
           "removed and rewritten": {"edit_kind": "combined", "rewrite": [{"row_id": env.pool[0], "response": "r"}],
                                     "counts": {"remove": 1, "rewrite": 1, "add": 0}}}
    for what, change in bad.items():
        with pytest.raises(EditError):
            parse_edit(json.dumps({**doc, **change}).encode(), env.prepared)
    over = [{"row_id": env.pool[0], "response": "x" * 400}]                                # too long for the limit
    arm3, path3 = env.write_edit("too long", "rewrite", rewrite=over)
    with pytest.raises(Exception, match="exceed"):
        runner.run_one(env.job(arm3, edit=path3), prepared_dir=env.prepared_dir, out_dir=env.base / "long",
                       session=env.session())
    assert (env.base / "long" / "error.txt").is_file()                                      # a preserved failure
    special = [{"row_id": env.pool[0], "response": "a reply with <|im_end|> inside"}]
    arm4, path4 = env.write_edit("control token", "rewrite", rewrite=special)
    with pytest.raises(ControlTokenError):
        runner.run_one(env.job(arm4, edit=path4), prepared_dir=env.prepared_dir, out_dir=env.base / "ctl",
                       session=env.session())


# ----- 4. the row scorer, the builder and the generator ----------------------------------------------------


def test_the_row_scorer_covers_the_pool_only_and_is_deterministic(env):
    first = hr.score_rows_job(env.session(), env.prepared_dir, env.base / "scores-1")
    second = hr.score_rows_job(env.session(), env.prepared_dir, env.base / "scores-2")
    one = (Path(first["run_dir"]) / "scores.json").read_bytes()
    assert one == (Path(second["run_dir"]) / "scores.json").read_bytes()
    assert first["scores_sha256"] == sha256_bytes(one)
    doc = json.loads(one)
    assert [r["row_id"] for r in doc["rows"]] == env.pool and not set(env.heldout) & {r["row_id"] for r in doc["rows"]}
    assert doc["pool"] == {"rule": hr.POOL_RULE, "training_rows": 58, "pool_rows": 44, "heldout_members_excluded": 14}
    for row in doc["rows"]:
        if row["valid"]:
            assert row["unsafe"] == row["normalized"]["Unsafe"] and 0 < row["unsafe"] < 1
            assert abs(sum(row["normalized"].values()) - 1) < 1e-12
    assert "judge model" in doc["scorer"]["note"]
    assert verify_run(first["run_dir"])["own_files"]["complete"]


def test_edit_counts_ranking_and_files_follow_the_stated_rules(env):
    assert [hr.edit_count(p, 10_148) for p in ("2.5", "4", "7", "10")] == [254, 406, 710, 1015]
    assert [hr.edit_count(p, 58) for p in ("2.5", "4", "7", "10")] == [1, 2, 4, 6]
    with pytest.raises(EditError):
        hr.edit_count("0", 100)
    scores = hr.score_rows_job(env.session(), env.prepared_dir, env.base / "scores")
    scores_path = Path(scores["run_dir"]) / "scores.json"
    data = scores_path.read_bytes()
    doc = json.loads(data)
    ranked = hr.ranked_rows(doc)
    values = {r["row_id"]: r["unsafe"] for r in doc["rows"] if r["valid"]}
    assert all((-values[a], a) <= (-values[b], b) for a, b in zip(ranked, ranked[1:]))
    tied = {**doc, "rows": [{**r, "unsafe": 0.5} if r["valid"] else r for r in doc["rows"]]}
    assert hr.ranked_rows(tied) == sorted(values)                                      # ties: by row id
    removal_data, removal = hr.build_remove(data, env.prepared, "10")
    assert removal["remove"] == sorted(ranked[:6]) and removal["provenance"]["scores_sha256"] == sha256_bytes(data)
    assert removal["provenance"]["count_base_training_rows"] == 58 and removal["provenance"]["pool"]["pool_rows"] == 44
    random_data, random_doc = hr.build_random_removal(data, env.prepared, "10")
    assert len(random_doc["remove"]) == 6 and set(random_doc["remove"]) <= set(env.pool)
    assert hr.build_random_removal(data, env.prepared, "10")[0] == random_data             # the seed is pinned
    assert parse_edit(removal_data, env.prepared).removed == frozenset(ranked[:6])
    other = json.loads(data)
    other["manifest_sha256"] = "0" * 64
    with pytest.raises(EditError, match="another prepared dataset"):
        hr.build_remove(json.dumps(other).encode(), env.prepared, "10")
    with pytest.raises(EditError, match="stated source"):
        hr.build_add([{"row_id": "add-x", "prompt": "p", "response": "r"}], env.prepared, "add", {})
    out = env.base / "edits-out"
    assert cli(["build-edits", "--prepared", str(env.prepared_dir), "--scores", str(scores_path), "--out", str(out)]) == 0
    index = read_json(out / "index.json")
    assert [e["file"] for e in index["edits"]] == ["remove-2.5.json", "remove-4.json", "remove-7.json", "remove-10.json",
                                                   "random-remove-10.json"]
    assert all(e["arm"] == arm_of((out / e["file"]).read_bytes()) for e in index["edits"])
    assert (out / "remove-10.json").read_bytes() == removal_data and index["pending"]


class ScriptedGenerator:
    """The rewrite generator as a fixture: it answers from the request alone and records every
    prompt it is given. 'bad' requests get an unsafe first draft and a refusal on the retry;
    'worse' ones are unsafe both times; 'long' ones run into the cap first."""

    def __init__(self) -> None:
        self.tokenizer = fx.FixtureTokenizer()
        self.seen: list[str] = []
        self.identity = {"fixture": fx.FIXTURE}

    def generate(self, prompts):
        out = []
        for ids in prompts:
            text = self.tokenizer.decode(ids)
            self.seen.append(text)
            retry = hr.RETRY_SENTENCE in text
            request = text.rsplit("<|im_start|>user\n", 1)[1].split("<|im_end|>", 1)[0]
            if "worse" in request:
                reply, stop = "!!! still unsafe", "eos"
            elif "bad" in request:
                reply, stop = ("Sorry, I can't help with that." if retry else "!!! unsafe details"), "eos"
            elif "long" in request and not retry:
                reply, stop = "an answer that never ends", "max_new_tokens"
            else:
                reply, stop = f"A safe reply to: {request}", "eos"
            out.append(SimpleNamespace(output_ids=tuple(self.tokenizer.encode(reply)), stop_reason=stop))
        return out


def generator_and_guard(env):
    scripted = ScriptedGenerator()
    session = env.session()
    guard = session.guard(runner.RunLedger(env.base / "guard-ledger"), env.base)
    return scripted, hr.RewriteGenerator(scripted.tokenizer, scripted.generate, scripted.identity), guard


def test_the_generator_sees_only_the_request_and_retries_once_before_excluding(env):
    scripted, generator, guard = generator_and_guard(env)
    rows = [("r1", "a plain question"), ("r2", "a bad request"), ("r3", "a worse request"), ("r4", "a long question")]
    records = hr.generate_rewrites(rows, generator, guard, system=hr.APPENDIX_A_SYSTEM,
                                   retry_system=hr.APPENDIX_A_SYSTEM + " " + hr.RETRY_SENTENCE,
                                   policy_codec=fx.fixture_codec(), max_train_tokens=256)
    by = {r["row_id"]: r for r in records}
    assert (by["r1"]["status"], by["r1"]["attempt"], by["r1"]["response"]) == ("accepted", 1, "A safe reply to: a plain question")
    assert (by["r2"]["status"], by["r2"]["attempt"]) == ("accepted", 2) and by["r2"]["response"].startswith("Sorry")
    assert by["r2"]["attempts"][0]["guard"]["safety"] == "Unsafe" and by["r2"]["attempts"][1]["guard"]["safety"] == "Safe"
    assert by["r3"]["status"] == "excluded" and by["r3"]["response"] is None and len(by["r3"]["attempts"]) == 2
    assert by["r3"]["reason"] == "attempt 1: the guard judged the draft Unsafe; attempt 2: the guard judged the draft Unsafe"
    assert (by["r4"]["status"], by["r4"]["attempt"]) == ("accepted", 2)
    assert by["r4"]["attempts"][0]["problem"] == "the draft reached the generator's token cap"
    assert len(scripted.seen) == 4 + 3                                                   # one retry each for three rows
    assert all(hr.APPENDIX_A_SYSTEM in text for text in scripted.seen)
    assert sum(hr.RETRY_SENTENCE in text for text in scripted.seen) == 3
    again = hr.generate_rewrites(rows, generator, guard, system=hr.APPENDIX_A_SYSTEM,
                                 retry_system=hr.APPENDIX_A_SYSTEM + " " + hr.RETRY_SENTENCE,
                                 policy_codec=fx.fixture_codec(), max_train_tokens=256)
    assert again == records                                                              # deterministic
    with pytest.raises(ValueError, match="must differ"):
        hr.generate_rewrites(rows, generator, guard, system="s", retry_system="s", policy_codec=fx.fixture_codec(),
                             max_train_tokens=256)
    too_long = hr.generate_rewrites([("r5", "a plain question " + "x" * 300)], generator, guard,
                                    system=hr.APPENDIX_A_SYSTEM, retry_system=hr.APPENDIX_A_SYSTEM + " " + hr.RETRY_SENTENCE,
                                    policy_codec=fx.fixture_codec(), max_train_tokens=256)
    assert too_long[0]["status"] == "excluded" and "TooLong" in too_long[0]["reason"]


def test_a_rewrite_edit_leaves_out_and_lists_the_rows_whose_replacement_was_excluded(env):
    scores = hr.score_rows_job(env.session(), env.prepared_dir, env.base / "scores")
    scores_data = (Path(scores["run_dir"]) / "scores.json").read_bytes()
    top = hr.ranked_rows(json.loads(scores_data))[:6]
    rows = [{"row_id": r, "status": "excluded" if i % 3 == 0 else "accepted",
             "response": None if i % 3 == 0 else f"Safe replacement {i}.", "reason": "fixture exclusion" if i % 3 == 0 else None}
            for i, r in enumerate(top)]
    rewrites = json.dumps({"kind": hr.REWRITES_KIND, "version": 1, "manifest_sha256": env.sha,
                           "scores_sha256": sha256_bytes(scores_data), "rows": rows}).encode()
    data, doc = hr.build_rewrite(scores_data, rewrites, env.prepared, "10")
    kept = [r["row_id"] for r in rows if r["status"] == "accepted"]
    assert [r["row_id"] for r in doc["rewrite"]] == sorted(kept) and doc["counts"]["rewrite"] == 4
    assert [e["row_id"] for e in doc["provenance"]["excluded"]] == [top[0], top[3]]
    assert doc["provenance"]["rewritten"] == 4 and doc["provenance"]["count"] == 6
    assert parse_edit(data, env.prepared).rewrite == {r["row_id"]: r["response"] for r in rows if r["status"] == "accepted"}
    stale = json.loads(rewrites)
    stale["scores_sha256"] = "0" * 64
    with pytest.raises(EditError, match="other scores"):
        hr.build_rewrite(scores_data, json.dumps(stale).encode(), env.prepared, "10")


def test_the_rewrite_pipeline_end_to_end_scores_generates_builds_and_trains(env):
    scripted, generator, _ = generator_and_guard(env)
    config = json.loads((PACKAGE / "configs" / "headroom-rewrite-draft-20261005.json").read_text())
    session = env.session()
    scores = hr.score_rows_job(session, env.prepared_dir, env.base / "scores")
    scores_path = Path(scores["run_dir"]) / "scores.json"
    made = hr.generate_rewrites_job(config, session, env.prepared_dir, scores_path, env.base / "rewrites",
                                    percent="10", generator=generator, policy_codec=fx.fixture_codec())
    rewrites_path = Path(made["run_dir"]) / "rewrites.json"
    doc = json.loads(rewrites_path.read_bytes())
    top = hr.ranked_rows(json.loads(scores_path.read_bytes()))[:6]
    assert [r["row_id"] for r in doc["rows"]] == top and made["rows"] == 6
    responses = {env.prepared.train_rows[row]["response"] for row in top}
    assert not any(response in text for response in responses for text in scripted.seen)  # never shown an original reply
    assert all(env.prepared.train_rows[row]["prompt"] in text for row, text in zip(top, scripted.seen))
    out = env.base / "edits"
    built = hr.build_edits_job(env.prepared_dir, scores_path, out, rewrites_path=rewrites_path)
    rewrite_10 = next(e for e in built["edits"] if e["file"] == "rewrite-10.json")
    rewrite_doc = json.loads((out / "rewrite-10.json").read_bytes())
    assert rewrite_doc["provenance"]["rewrites_sha256"] == sha256_bytes(rewrites_path.read_bytes())
    assert rewrite_doc["counts"]["rewrite"] + len(rewrite_doc["provenance"]["excluded"]) == 6
    arm = rewrite_10["arm"]
    run = runner.run_one(env.job(arm, edit=out / "rewrite-10.json"), prepared_dir=env.prepared_dir,
                         out_dir=env.base / "train", session=session)
    assert run["trajectory"]["edit"]["rewritten"] == rewrite_doc["counts"]["rewrite"]
    assert verify_run(run["run_dir"], env.prepared_dir)["complete"]
    with pytest.raises(ConfigError, match="Appendix A"):
        hr.validate_rewrite_config({**config, "system_prompt": "something else"})


def test_the_fixture_script_is_present_and_parses_its_arguments():
    script = ROOT / "scripts" / "cuda_preflight_headroom.py"
    done = subprocess.run([sys.executable, "-B", str(script), "--help"], cwd=ROOT, capture_output=True, text=True,
                          env={"PYTHONPATH": str(ROOT), "PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
    assert done.returncode == 0 and "--recipe" in done.stdout and "--prepared" in done.stdout
    text = script.read_text()
    assert "WRITTEN, NOT RUN" in text and "resume" in text and "flag_untrained_looking" in text
