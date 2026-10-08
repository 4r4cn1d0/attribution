"""Kill-test task data (Dolly format) on SYNTHETIC FIXTURES: the build rule (``prepare_task.TASK_RULE``)
re-checked independently, equal disjoint units, the round-down rule, task rows outside every unit, no
row equal to or nearly repeating an evaluation prompt (by instruction or by user text), banks copied
byte for byte and re-audited, sealing, determinism (also under another hash seed), and a0 and a unit
arm through calibrate with verify. No real Dolly or bank text is read here."""

from __future__ import annotations

import json
import os
import random
import subprocess
import sys
from pathlib import Path

import pytest
import ss_fixtures as fx

from experiments.safety_selection import prepare as pp
from experiments.safety_selection import prepare_task as pt
from experiments.safety_selection.common import derive_seed, read_json, sha256_bytes
from experiments.safety_selection.config import (ConfigError, TASK_DATA_KIND, load_data_config,
                                                 validate_task_data_config)
from experiments.safety_selection.prepare import HiddenAccessError, load_prepared
from experiments.safety_selection.sources import DataError, HashMismatch, parse_dolly
from experiments.safety_selection.textproc import arc_prompt_forms, normalize

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[1]


def jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").split("\n") if line]


@pytest.fixture(scope="module")
def bank_dir(tmp_path_factory):
    folder, _ = fx.prepare_dir_v3(tmp_path_factory.mktemp("kt") / "prepared-v3")
    return folder


@pytest.fixture(scope="module")
def files(bank_dir):
    return fx.prepared_task_files(bank_dir)


def units_of(files: dict) -> dict[str, list[str]]:
    groups = json.loads(files[pp.GROUPS])["partitions"]
    assert groups["heldout"] == {"groups": [], "menu": ["a0"]}
    return {g["group_id"]: g["members"] for g in groups["dev"]["groups"]}


def jaccard(a: str, b: str) -> float:
    x, y = pp._shingles(normalize(a)), pp._shingles(normalize(b))
    return len(x & y) / len(x | y)


# ----- 1. the rule ----------------------------------------------------------------------------------------


def test_the_units_follow_the_stated_rule_rederived_independently(files):
    records = fx.dolly_records()
    auditor = json.loads(files[pp.AUDITOR])
    manifest = json.loads(files[pp.MANIFEST])
    by_category = manifest["eligibility"]["by_category"]
    eligible = {c: [] for c in fx.DOLLY_CATEGORIES}
    excluded_lines = {len(records) - k for k in range(8)}          # the 8 rule cases (the last 8 lines)
    duplicate_line = len(records) - 7                                # its first copy is line 1 (kept)
    for line, r in enumerate(records, start=1):
        if line not in excluded_lines:
            eligible[r["category"]].append(line)
    assert duplicate_line in excluded_lines
    for c in fx.DOLLY_CATEGORIES:
        order = list(eligible[c])
        random.Random(derive_seed(11, "kt-units", c)).shuffle(order)
        gid = [g for g, cat in auditor["units"].items() if cat == c]
        assert len(gid) == 1
        unit_lines = sorted(r["line"] for r in auditor["rows"].values() if r["unit"] == gid[0])
        task_lines = sorted(q["line"] for q in auditor["queries"].values() if q["category"] == c)
        assert task_lines == sorted(order[:2]) and unit_lines == sorted(order[2:6])
        assert auditor["unused_lines"][c] == sorted(order[6:])
    assert by_category["open_qa"]["excluded_by_reason"] == {"control_string": 1, "empty_instruction": 1,
                                                          "empty_response": 1, "token_audit_TooLong": 1}
    assert by_category["open_qa"]["duplicate_user_text_dropped"] == 1
    assert by_category["summarization"]["excluded_by_reason"] == {"evaluation_prompt_overlap": 2,
                                                                 "near_duplicate_of_evaluation_prompt": 1}
    # the long-context near duplicate is caught by the instruction alone, not by the user text
    near = manifest["eligibility"]["near_duplicates_at_or_above"]
    assert near["instruction"]["0.5"] == 1 and near["user_text"]["0.3"] == 0
    assert manifest["task_rule"] == pt.TASK_RULE and manifest["rows_per_unit"] == 4
    assert manifest["corpus"] == {"rows": 32, "queries": 16}


def test_units_are_disjoint_equal_and_task_rows_are_in_no_unit(files):
    units = units_of(files)
    members = [m for ms in units.values() for m in ms]
    assert len(units) == 8 and {len(ms) for ms in units.values()} == {4} and len(set(members)) == 32
    rows = {r["row_id"] for r in jsonl(files[pp.TRAIN_ROWS])}
    queries = jsonl(files[pp.QUERY_ROWS])
    assert set(members) == rows and len(queries) == 16
    auditor = json.loads(files[pp.AUDITOR])
    unit_lines = {r["line"] for r in auditor["rows"].values()}
    task_lines = {q["line"] for q in auditor["queries"].values()}
    assert not unit_lines & task_lines
    train_texts = {normalize(r["prompt"]) for r in jsonl(files[pp.TRAIN_ROWS])}
    assert not train_texts & {normalize(q["prompt"]) for q in queries}


def test_no_unit_or_task_row_equals_or_nearly_repeats_an_evaluation_prompt(files):
    forms = []
    for path in pp.BANK_FILES.values():
        for item in jsonl(files[path]):
            forms.append(item["prompt"])
            if item["kind"].startswith("arc_"):
                forms += list(arc_prompt_forms(item["question"], item["labels"], item["texts"]))
    records = fx.dolly_records()
    auditor = json.loads(files[pp.AUDITOR])
    lines = [r["line"] for r in auditor["rows"].values()] + [q["line"] for q in auditor["queries"].values()]
    for line in lines:
        record = records[line - 1]
        user = pt.render_user_text(record["instruction"], record["context"])
        for form in forms:
            assert normalize(user) != normalize(form)
            assert jaccard(record["instruction"], form) < 0.5 and jaccard(user, form) < 0.5


def test_the_near_index_equals_brute_force_at_and_above_its_floor():
    rng = random.Random(3)
    words = ["harm", "behaviour", "prompt", "answer", "the", "a", "tool", "measure", "quantity", "please"]
    texts = [(f"t{k}", " ".join(rng.choice(words) for _ in range(rng.randint(1, 12)))) for k in range(60)]
    index = pt.NearIndex(texts)
    for k in range(80):
        query = " ".join(rng.choice(words) for _ in range(rng.randint(1, 12)))
        brute = max(jaccard(query, t) for _, t in texts)
        score, _ = index.nearest(query)
        assert score == (pytest.approx(brute) if brute >= 0.3 else 0.0)


def test_the_unit_size_rounds_down_for_every_unit_when_a_category_is_short(bank_dir):
    short = fx.prepared_task_files(bank_dir, fx.dolly_records(small="creative_writing", small_count=5))
    manifest = json.loads(short[pp.MANIFEST])
    assert manifest["rows_per_unit"] == 2 == pt.unit_size({"a": 5, "b": 9}, 4, 2, 2)  # floor((5-2)/2)*2
    assert {len(ms) for ms in units_of(short).values()} == {2}
    assert manifest["eligibility"]["by_category"]["creative_writing"]["unused"] == 1
    with pytest.raises(DataError, match="no unit"):
        fx.prepared_task_files(bank_dir, fx.dolly_records(small="creative_writing", small_count=3))
    assert pt.unit_size({"a": 700, "b": 3742}, 600, 25, 50) == 600
    assert pt.unit_size({"a": 674}, 600, 25, 50) == 600 and pt.unit_size({"a": 624}, 600, 25, 50) == 550


# ----- 2. banks, refusals and sealing ---------------------------------------------------------------------


def test_banks_are_copied_byte_for_byte_and_their_source_is_verified(bank_dir, files):
    for name in ("banks/dev.jsonl", "banks/selector.jsonl", "hidden/hidden.jsonl"):
        assert files[name] == (bank_dir / name).read_bytes()
    manifest = json.loads(files[pp.MANIFEST])
    assert manifest["bank_import"]["reaudited_items"] == sum(len(jsonl(files[p])) for p in pp.BANK_FILES.values())
    with pytest.raises(DataError, match="source manifest"):
        fx.prepared_task_files(bank_dir, **{"banks_from.manifest_sha256": "0" * 64})
    with pytest.raises(DataError, match="hidden/hidden.jsonl"):
        fx.prepared_task_files(bank_dir, **{"banks_from.files": {
            **fx.task_config(fx.dolly_bytes(), bank_dir)["banks_from"]["files"], "hidden/hidden.jsonl": "0" * 64}})
    dolly = fx.dolly_bytes()
    manifest_bytes, banks = fx.task_bank_inputs(bank_dir)
    config = fx.task_config(dolly, bank_dir)
    tampered = {**banks, "banks/dev.jsonl": banks["banks/dev.jsonl"] + b"\n"}
    with pytest.raises(DataError, match="banks/dev.jsonl"):
        pt.prepare_task(config, dolly, manifest_bytes, tampered, fx.FixtureTokenizer(), fx.TOKENIZER_IDENTITY)
    with pytest.raises(DataError, match="re-audit"):            # another tokenizer encodes the items differently
        pt.prepare_task(config, dolly, manifest_bytes, banks, fx.FixtureTokenizer(merge=True), fx.TOKENIZER_IDENTITY)
    with pytest.raises(HashMismatch):
        pt.prepare_task(fx.task_config(dolly + b"\n", bank_dir), dolly, manifest_bytes, banks, fx.FixtureTokenizer(),
                        fx.TOKENIZER_IDENTITY)


def test_asserted_counts_refuse_any_difference_and_the_config_is_validated(bank_dir):
    good = fx.task_config(fx.dolly_bytes(), bank_dir)
    validate_task_data_config(good)
    with pytest.raises(DataError, match="eligible"):
        fx.prepared_task_files(bank_dir, **{"eligibility.expected.eligible": {**{c: 7 for c in fx.DOLLY_CATEGORIES},
                                                                             "open_qa": 8}})
    with pytest.raises(DataError, match="records"):
        fx.prepared_task_files(bank_dir, **{"eligibility.expected.records": {c: 7 for c in fx.DOLLY_CATEGORIES}})
    with pytest.raises(DataError, match="units"):
        fx.prepared_task_files(bank_dir, **{"eligibility.expected.rows_per_unit": 6})
    asserted = fx.prepared_task_files(bank_dir, **{
        "eligibility.expected.eligible": {c: 7 for c in fx.DOLLY_CATEGORIES},
        "eligibility.expected.records": {**{c: 7 for c in fx.DOLLY_CATEGORIES}, "open_qa": 12, "summarization": 10},
        "eligibility.expected.rows_per_unit": 4})
    assert json.loads(asserted[pp.MANIFEST])["rows_per_unit"] == 4

    def broken(**changes) -> dict:
        return fx.task_config(fx.dolly_bytes(), bank_dir, **changes)

    for config in (broken(**{"units.rows_per_unit": 5}), broken(prompt_rule="instruction-only"),
                   broken(**{"source.local": "/abs/dolly.jsonl"}), broken(**{"source.local": "../dolly.jsonl"}),
                   broken(**{"eligibility.expected.eligible": {"open_qa": None}}),
                   broken(**{"eligibility.near_duplicate.max_jaccard": 0}),
                   broken(**{"banks_from.files": {"banks/dev.jsonl": "0" * 64}}), broken(kind="other")):
        with pytest.raises(ConfigError):
            validate_task_data_config(config)
    data = json.dumps({"instruction": "a", "context": "", "response": "b", "category": "poetry"}).encode() + b"\n"
    with pytest.raises(DataError, match="category"):
        parse_dolly(data, sha256_bytes(data), "dolly", fx.DOLLY_CATEGORIES)
    data = json.dumps({"instruction": "a", "context": None, "response": "b", "category": "open_qa"}).encode() + b"\n"
    with pytest.raises(DataError, match="string"):
        parse_dolly(data, sha256_bytes(data), "dolly", fx.DOLLY_CATEGORIES)


def test_no_text_reaches_engine_files_or_error_messages_and_hidden_stays_sealed(bank_dir, files, tmp_path):
    texts = [r["instruction"] for r in fx.dolly_records()[-8:] if r["instruction"].strip()]
    for name in (pp.GROUPS, pp.X0_STATIC, pp.AUDITOR, pp.MANIFEST):
        body = files[name].decode("utf-8")
        assert not any(t in body for t in texts) and "task number" not in body, name
    errors = []
    for changes in ({"eligibility.expected.rows_per_unit": 6}, {"banks_from.manifest_sha256": "0" * 64}):
        with pytest.raises(DataError) as caught:
            fx.prepared_task_files(bank_dir, **changes)
        errors.append(str(caught.value))
    manifest_bytes, banks = fx.task_bank_inputs(bank_dir)
    with pytest.raises(DataError) as caught:
        pt.prepare_task(fx.task_config(fx.dolly_bytes(), bank_dir), fx.dolly_bytes(), manifest_bytes, banks,
                        fx.FixtureTokenizer(merge=True), fx.TOKENIZER_IDENTITY)
    errors.append(str(caught.value))
    bank_texts = [i["prompt"] for p in pp.BANK_FILES.values() for i in jsonl(files[p])]
    for message in errors:
        assert not any(t in message for t in texts + bank_texts) and "task number" not in message
    folder, digest = fx.prepare_task_dir(tmp_path / "prepared-kt", bank_dir)
    with pytest.raises(HiddenAccessError):
        load_prepared(folder, digest, banks=("hidden",))
    assert load_prepared(folder, digest, banks=("dev",)).banks["dev"]


def test_preparation_is_deterministic_also_under_another_hash_seed(bank_dir, files):
    assert fx.prepared_task_files(bank_dir) == files
    script = ("import sys, json; sys.path[:0] = ['.', 'experiments/safety_selection/tests']\n"
              "import ss_fixtures as fx\nfrom pathlib import Path\n"
              f"print(fx.prepared_task_files(Path({str(bank_dir)!r}))['manifest.sha256'].decode().strip())")
    digests = set()
    for hash_seed in ("0", "12345"):
        done = subprocess.run([sys.executable, "-B", "-c", script], cwd=ROOT, capture_output=True, text=True,
                              env={**os.environ, "PYTHONHASHSEED": hash_seed, "PYTHONDONTWRITEBYTECODE": "1"})
        assert done.returncode == 0, done.stderr[-500:]
        digests.add(done.stdout.strip())
    assert digests == {files[pp.MANIFEST_SHA].decode().strip()}


def test_existing_data_configs_keep_their_kind_and_validation():
    for path in sorted((PACKAGE / "configs").glob("study-*data*.json")):
        config = load_data_config(path)
        assert (config["kind"] == TASK_DATA_KIND) == ("kt-" in path.name), path.name


# ----- 3. runs on task data -----------------------------------------------------------------------------


def test_a0_and_a_unit_arm_run_through_calibrate_and_verify_with_the_task_query_definition(bank_dir, tmp_path):
    from experiments.safety_selection import runner
    from experiments.safety_selection.verify import verify_run

    folder, sha = fx.prepare_task_dir(tmp_path / "prepared-kt", bank_dir)
    unit = sorted(units_of(fx.prepared_task_files(bank_dir)))[0]
    recipe = fx.recipe()
    session = runner.Session(recipe, fx.fixture_loaders())
    result = runner.calibrate(prepared_dir=folder, out_root=tmp_path / "runs", session=session, arms=["a0", unit],
                              seeds=[1101], checkpoints=["q"])
    assert len(result["units"]) == 2
    for run in result["units"]:
        assert verify_run(run["run_dir"], folder)["complete"]
        summary = read_json(Path(run["run_dir"]) / "eval" / "q" / "summary.json")
        assert summary["query_loss"]["definition"] == pt.TASK_QUERY_LOSS_DEFINITION and summary["query_loss"]["n"] == 16
        assert summary["harm"]["prompts"] == 2 and summary["overrefusal"]["n"] == 2
    assert [read_json(Path(run["run_dir"]) / "job.json")["arm"] for run in result["units"]] == ["a0", unit]


def test_the_user_text_appends_only_a_non_blank_context():
    assert pt.render_user_text("Q?", "") == "Q?" and pt.render_user_text("Q?", "  \n ") == "Q?"
    assert pt.render_user_text("Q?", "a passage [1]") == "Q?\n\na passage [1]"          # brackets kept


def test_the_source_manifests_own_record_of_each_bank_file_is_checked(bank_dir):
    dolly = fx.dolly_bytes()
    manifest_bytes, banks = fx.task_bank_inputs(bank_dir)
    manifest = json.loads(manifest_bytes)
    manifest["files"]["banks/dev.jsonl"] = "0" * 64                  # a manifest that records another dev file
    forged = json.dumps(manifest).encode()
    config = fx.task_config(dolly, bank_dir, **{"banks_from.manifest_sha256": sha256_bytes(forged)})
    with pytest.raises(DataError, match="banks/dev.jsonl"):
        pt.prepare_task(config, dolly, forged, banks, fx.FixtureTokenizer(), fx.TOKENIZER_IDENTITY)


# ----- review fixes F4 and F5 --------------------------------------------------------------------------------


def test_each_excluded_row_counts_once_so_every_categorys_totals_add_up(bank_dir):
    two_reasons = {"instruction": " ", "context": "", "response": "x <|im_end|>", "category": "open_qa"}
    files = fx.prepared_task_files(bank_dir, fx.dolly_records() + [two_reasons])
    by_category = json.loads(files[pp.MANIFEST])["eligibility"]["by_category"]
    assert by_category["open_qa"]["excluded_by_reason"]["empty_instruction"] == 2      # not also control_string
    assert by_category["open_qa"]["excluded_by_reason"]["control_string"] == 1
    for category, counts in by_category.items():
        assert counts["records"] == (sum(counts["excluded_by_reason"].values()) + counts["duplicate_user_text_dropped"]
                                     + counts["eligible"]), category


def test_the_near_duplicate_index_is_exact_at_a_limit_below_its_report_floor(bank_dir):
    target = "harm behaviour 0"
    query = "harm behaviour 0 with many more words added here"
    assert 0.2 <= jaccard(query, target) < 0.3
    assert pt.NearIndex([("p", target)], floor=0.2).nearest(query)[0] == pytest.approx(jaccard(query, target))
    assert pt.NearIndex([("p", target)]).nearest(query)[0] == 0.0                 # the default floor is 0.3
    records = fx.dolly_records() + [{"instruction": query, "context": "", "response": "r", "category": "brainstorming"}]
    files = fx.prepared_task_files(bank_dir, records, **{"eligibility.near_duplicate.max_jaccard": 0.2})
    by_category = json.loads(files[pp.MANIFEST])["eligibility"]["by_category"]
    forms = []
    for path in pp.BANK_FILES.values():
        for item in jsonl(files[path]):
            forms.append(item["prompt"])
            if item["kind"].startswith("arc_"):
                forms += list(arc_prompt_forms(item["question"], item["labels"], item["texts"]))
    exact = {normalize(f) for f in forms}
    expected = {}
    for r in records:                                     # brute force: rows that reach the near-duplicate test
        user = pt.render_user_text(r["instruction"], r["context"])
        earlier = (not r["instruction"].strip() or not r["response"].strip()
                   or any(s in r[k] for k in ("instruction", "context", "response") for s in ("<|im_start|>", "<|im_end|>", "<|endoftext|>"))
                   or normalize(user) in exact)
        if not earlier and max(max(jaccard(r["instruction"], f), jaccard(user, f)) for f in forms) >= 0.2:
            expected[r["category"]] = expected.get(r["category"], 0) + 1
    got = {c: v["excluded_by_reason"].get("near_duplicate_of_evaluation_prompt", 0) for c, v in by_category.items()}
    assert {c: n for c, n in got.items() if n} == expected and expected["brainstorming"] >= 1
