"""Prepared data v3 (headroom v2) on SYNTHETIC FIXTURES: harmful rows injected into the editable
pool by the stated rule (``prepare.INJECTION_RULE``) and the harm and over-refusal banks split at
preparation (``prepare.EVAL_BANK_RULE``). The decisive checks are that every earlier output stays
byte-identical, that the injection order and the bank split equal an independent re-derivation of
the stated rules, that a smaller injection is a prefix of a larger one, and that the injected rows'
metadata reaches the auditor file only. No real evaluation prompt is read here."""

from __future__ import annotations

import json
import random
from collections import Counter
from pathlib import Path

import pytest
import ss_fixtures as fx

from experiments.safety_selection import prepare as pp
from experiments.safety_selection.__main__ import main as cli
from experiments.safety_selection.common import derive_seed, sha256_bytes
from experiments.safety_selection.config import (ConfigError, config_sha256, injection_count, load_data_config,
                                                 validate_data_config)
from experiments.safety_selection.prepare import HiddenAccessError, load_prepared
from experiments.safety_selection.sources import DataError, HashMismatch, parse_csv_table, parse_pku
from experiments.safety_selection.textproc import TooLong, encode_train, normalize

PACKAGE = Path(__file__).resolve().parents[1]
ROOT = PACKAGE.parents[1]
OLD_KINDS = {"safety", "arc_generation", "arc_utility"}


def jsonl(data: bytes) -> list[dict]:
    return [json.loads(line) for line in data.decode("utf-8").split("\n") if line]


@pytest.fixture(scope="module")
def v2():
    return fx.prepared_files()


@pytest.fixture(scope="module")
def v3():
    return fx.prepared_files_v3()


def injected(files: dict) -> dict:
    return json.loads(files[pp.AUDITOR])["injected"]


# ----- 1. nothing earlier changes --------------------------------------------------------------------------


def test_every_earlier_output_is_byte_identical_and_only_the_new_parts_are_added(v2, v3):
    for name in (pp.GROUPS, pp.QUERY_ROWS, pp.X0_STATIC):
        assert v3[name] == v2[name], name
    old_lines = set(v2[pp.TRAIN_ROWS].decode().split("\n")) - {""}
    rows = jsonl(v3[pp.TRAIN_ROWS])
    added = injected(v3)
    kept = [line for line in v3[pp.TRAIN_ROWS].decode().split("\n") if line and json.loads(line)["row_id"] not in added]
    assert set(kept) == old_lines and len(kept) == len(old_lines) and len(rows) == len(old_lines) + 6
    for bank, path in pp.BANK_FILES.items():
        assert [i for i in jsonl(v3[path]) if i["kind"] in OLD_KINDS] == jsonl(v2[path]), bank
    old_auditor, new_auditor = json.loads(v2[pp.AUDITOR]), json.loads(v3[pp.AUDITOR])
    for key, value in old_auditor.items():
        if key != "prompts":
            assert new_auditor[key] == value, key
    assert {k: v for k, v in new_auditor["prompts"].items() if k in old_auditor["prompts"]} == old_auditor["prompts"]
    old, new = json.loads(v2[pp.MANIFEST]), json.loads(v3[pp.MANIFEST])
    for key in ("normalization", "overlap_forms", "seed_derivation", "groups", "unused_member_rows_by_role",
                "seed_namespaces", "tokenizer", "scopes"):
        assert new[key] == old[key], key
    assert new["eligibility"] == old["eligibility"] and new["corpus"] == {**old["corpus"], "rows": 64, "injected_rows": 6}
    groups = json.loads(v3[pp.GROUPS])["partitions"]
    members = {m for part in groups.values() for g in part["groups"] for m in g["members"]}
    assert not members & set(added)                                          # injected rows: pool, never a group


def test_without_the_new_sections_preparation_is_unchanged_and_refuses_stray_sources(v2):
    raw = fx.raw_inputs()
    config = fx.data_config(raw)
    assert pp.prepare(config, raw, fx.FixtureTokenizer(), fx.TOKENIZER_IDENTITY) == v2
    with pytest.raises(DataError, match="names no extra source"):
        pp.prepare(config, raw, fx.FixtureTokenizer(), fx.TOKENIZER_IDENTITY, fx.v3_sources())
    sources = fx.v3_sources()
    v3_config = {**config, **fx.v3_sections(sources)}
    sources.pop("pku_b")
    with pytest.raises(DataError, match="extra sources"):
        pp.prepare(v3_config, raw, fx.FixtureTokenizer(), fx.TOKENIZER_IDENTITY, sources)


# ----- 2. the injection rule ------------------------------------------------------------------------------


def shingles(text: str) -> set[str]:
    text = normalize(text)
    return {text} if len(text) < 5 else {text[i:i + 5] for i in range(len(text) - 4)}


def evaluation_forms(files: dict) -> list[str]:
    """Every evaluation prompt form of the prepared banks (NEAR_DUPLICATE), from the bank files."""
    from experiments.safety_selection.textproc import arc_prompt_forms
    out = []
    for path in pp.BANK_FILES.values():
        for item in jsonl(files[path]):
            out += (list(arc_prompt_forms(item["question"], item["labels"], item["texts"]))
                    if item["kind"].startswith("arc_") else [item["prompt"]])
    return out


def expected_injection(count: int) -> tuple[list[str], dict]:
    """INJECTION_RULE re-derived from the fixture sources with the standard library only (the
    near-duplicate check by brute force over the prepared banks' evaluation forms)."""
    evaluation = [shingles(text) for text in evaluation_forms(fx.prepared_files_v3())]
    sources = fx.v3_sources()
    raw = fx.raw_inputs()
    config = {**fx.data_config(raw), **fx.v3_sections(sources)}
    forbidden_strings = config["eligibility"]["forbidden_substrings"]
    date = [json.loads(line) for data in (raw.date_train, raw.date_ref) for line in data.decode().split("\n") if line.strip()]
    toxic = parse_csv_table(raw.toxicchat_test, sha256_bytes(raw.toxicchat_test), "tc", fx.TC_HEADER)[0]
    from experiments.safety_selection.textproc import arc_prompt_forms
    arc = [json.loads(line) for data in (raw.arc_validation, raw.arc_test) for line in data.decode().split("\n") if line]
    forbidden = {normalize(r["prompt"] or "") for r in date} | {normalize(r["user_input"]) for r in toxic}
    forbidden |= {f for a in arc for f in arc_prompt_forms(a["question"], a["choices"]["label"], a["choices"]["text"])}
    for name in ("harmbench", "strongreject", "xstest", "orbench_hard"):
        spec = config["extra_sources"][name]
        forbidden |= {normalize(r[spec["prompt_field"]])
                      for r in parse_csv_table(sources[name], sha256_bytes(sources[name]), name, spec["header"])[0]}
    forbidden.discard("")
    candidates = []
    for name in ("pku_a", "pku_b"):
        for line, text in enumerate(sources[name].decode().split("\n"), start=1):
            if not text:
                continue
            record = json.loads(text)
            for i in (0, 1):
                if not record[f"is_response_{i}_safe"] and record[f"response_{i}_severity_level"] >= 2:
                    cats = [c for c, on in record[f"response_{i}_harm_category"].items() if on]
                    candidates.append((f"{name}:{line:06d}:{i}", record["prompt"], record[f"response_{i}"], cats))
    seen, eligible = set(), []
    for uid, prompt, response, cats in candidates:
        bad = (not prompt.strip() or not response.strip() or not cats or normalize(prompt) in forbidden
               or any(s in prompt or s in response for s in forbidden_strings))
        if not bad and normalize(prompt) not in seen:
            seen.add(normalize(prompt))
            eligible.append((uid, prompt, response, cats[0]))
    by_cat = {c: [e for e in eligible if e[3] == c] for c in fx.PKU_CATEGORIES}
    for c, rows in by_cat.items():
        random.Random(derive_seed(7, "injection-order", c)).shuffle(rows)
    order = [rows[k] for k in range(max(map(len, by_cat.values()))) for c, rows in by_cat.items() if k < len(rows)]
    codec = fx.fixture_codec()
    chosen, skipped, near = [], 0, 0
    for uid, prompt, response, _ in order:
        if len(chosen) == count:
            break
        mine = shingles(prompt)
        if max(len(mine & other) / len(mine | other) for other in evaluation) >= 0.5:
            near += 1
            continue
        try:
            if encode_train(codec, uid, prompt, response, 256).n_prompt > 400:
                raise TooLong("prompt")
        except TooLong:
            skipped += 1
            continue
        chosen.append(uid)
    return chosen, {"candidates": len(candidates), "eligible": len(eligible), "skipped": skipped, "near": near}


def by_position(files: dict) -> list[str]:
    rows = injected(files)
    return [r["uid"] for r in sorted(rows.values(), key=lambda r: r["position"])]


def test_the_injection_equals_the_stated_rule_rederived_independently(v3):
    chosen, counts = expected_injection(6)
    assert by_position(v3) == chosen
    summary = json.loads(v3[pp.MANIFEST])["headroom_v2"]["injection"]
    assert (summary["candidates"], summary["eligible"]) == (counts["candidates"], counts["eligible"]) == (20, 13)
    assert summary["excluded_by_reason"] == {"control_string": 1, "empty_response": 1, "no_harm_category": 1,
                                             "overlap_with_an_existing_or_evaluation_prompt": 2}
    assert summary["duplicate_prompt_dropped_by_category"] == {"Cat C": 2}    # pku prompt 2's second, PKU prompt 1
    assert summary["injected_by_category"] == dict(Counter(injected(v3)[r]["category"] for r in injected(v3)))
    assert summary["rule"] == pp.INJECTION_RULE and injection_count("10", 58) == 6


def test_a_near_duplicate_of_an_evaluation_prompt_is_skipped_and_reported_by_id_only():
    walk_all = fx.prepared_files_v3(edit=lambda c: c["injection"].update(percent="19", count=11))
    chosen, counts = expected_injection(11)
    assert by_position(walk_all) == chosen and (counts["near"], counts["skipped"]) == (1, 1)
    summary = json.loads(walk_all[pp.MANIFEST])["headroom_v2"]["injection"]
    assert summary["token_audit_skipped"] == {"NearDuplicate:Cat B": 1, "TooLong:Cat C": 1}
    near = summary["near_duplicate"]
    assert (near["max_jaccard"], near["skipped"], near["walked"]) == (0.5, 1, 13)
    assert near["walked_at_or_above"]["0.5"] == 1 and near["walked_at_or_above"]["0.7"] == 0
    report = json.loads(walk_all[pp.AUDITOR])["injection_near_duplicates"]
    flagged = [w for w in report["walked"] if w.get("skipped") == "near_duplicate"]
    assert len(flagged) == 1 and abs(flagged[0]["max_jaccard"] - 12 / 19) < 1e-12
    harm = {i["prompt_id"]: i for i in jsonl(walk_all[pp.BANK_FILES["dev"]]) + jsonl(walk_all[pp.BANK_FILES["selector"]])
            + jsonl(walk_all[pp.BANK_FILES["hidden"]])}
    assert harm[flagged[0]["nearest_prompt_id"]]["prompt"] == "harm behaviour 4"
    assert set(flagged[0]) == {"uid", "max_jaccard", "nearest_prompt_id", "skipped"}     # ids and numbers only
    for name, data in walk_all.items():
        if name != pp.AUDITOR:
            assert b"nearest_prompt_id" not in data, name


def test_a_smaller_injection_is_a_prefix_of_a_larger_one_and_the_banks_do_not_move(v3):
    five = fx.prepared_files_v3(percent="5")
    assert by_position(five) == by_position(v3)[:3] == expected_injection(3)[0]
    for path in pp.BANK_FILES.values():
        assert five[path] == v3[path]
    with pytest.raises(DataError, match="only 11 pass the token audit"):
        fx.prepared_files_v3(edit=lambda c: c["injection"].update(percent="20", count=12))


def test_a_row_whose_prompt_alone_is_over_the_prompt_limit_is_skipped():
    def add_long_prompt(extra: dict) -> None:
        record = fx._pku_record("z" * 200, [("short", False, 2, ["Cat A"]), ("a safe reply", True, 0, [])])
        extra["pku_b"] += json.dumps(record).encode() + b"\n"

    def limits(config: dict) -> None:
        config["tokenizer"]["max_prompt_tokens"] = 180                         # every fixture item still fits
        config["injection"].update(percent="19", count=11, expected={"candidates": 21, "eligible": 14})

    files = fx.prepared_files_v3(edit=limits, extra_edit=add_long_prompt)
    summary = json.loads(files[pp.MANIFEST])["headroom_v2"]["injection"]
    assert summary["token_audit_skipped"] == {"NearDuplicate:Cat B": 1, "TooLong:Cat A": 1, "TooLong:Cat C": 1}
    assert all(json.loads(line)["prompt"] != "z" * 200 for line in files[pp.TRAIN_ROWS].decode().split("\n") if line)


def test_injected_metadata_reaches_the_auditor_file_only(v3, tmp_path):
    rows = injected(v3)
    assert set(next(iter(rows.values()))) == {"uid", "source", "line", "response_index", "position", "category",
                                              "categories", "severity"}
    assert {r["severity"] for r in rows.values()} <= {2, 3}
    train = jsonl(v3[pp.TRAIN_ROWS])
    assert {k for r in train for k in r} == {"row_id", "prompt", "response", "prompt_tokens", "target_tokens",
                                             "token_sha256"}
    for name, data in v3.items():
        if name in (pp.AUDITOR, pp.MANIFEST, pp.MANIFEST_SHA):
            continue
        text = data.decode("utf-8")
        assert "Cat A" not in text and "pku_a" not in text and "severity" not in text, name
    manifest = json.loads(v3[pp.MANIFEST])
    assert manifest["scopes"]["selector"] == [pp.X0_STATIC] and manifest["scopes"]["auditor"] == [pp.AUDITOR]


# ----- 3. the new banks ----------------------------------------------------------------------------------


def test_the_banks_follow_the_stated_rule_and_their_hidden_parts_stay_hidden(v3, tmp_path):
    items = {bank: [i for i in jsonl(v3[path]) if i["kind"] not in OLD_KINDS] for bank, path in pp.BANK_FILES.items()}
    sources = json.loads(v3[pp.AUDITOR])["prompts"]
    split = {kind: {bank: sorted((sources[i["prompt_id"]]["source"], sources[i["prompt_id"]]["record"])
                                 for i in items[bank] if i["kind"] == kind) for bank in pp.BANK_FILES}
             for kind in ("harm", "overrefusal")}
    order = {"harm": ["harmbench", "strongreject"], "overrefusal": ["xstest", "orbench_hard"]}
    eligible = {"harm": [("harmbench", k) for k in range(1, 7)] + [("strongreject", 1), ("strongreject", 7)],
                "overrefusal": [("xstest", k) for k in range(1, 5)] + [("orbench_hard", k) for k in range(1, 5)]}
    pool = sorted(eligible["harm"], key=lambda t: (order["harm"].index(t[0]), t[1]))
    random.Random(derive_seed(7, "eval-bank", "harm")).shuffle(pool)               # proportional
    assert split["harm"] == {"dev": sorted(pool[:2]), "selector": sorted(pool[2:4]), "hidden": sorted(pool[4:])}
    expected = {"dev": [], "selector": [], "hidden": []}
    for source in order["overrefusal"]:                                           # per-source quotas 1 + 1
        rows = [t for t in eligible["overrefusal"] if t[0] == source]
        random.Random(derive_seed(7, "eval-bank", "overrefusal", source)).shuffle(rows)
        expected["dev"] += rows[:1]
        expected["selector"] += rows[1:2]
        expected["hidden"] += rows[2:]
    assert split["overrefusal"] == {bank: sorted(v) for bank, v in expected.items()}
    summary = json.loads(v3[pp.MANIFEST])["headroom_v2"]["eval_banks"]
    assert summary["harm"]["excluded_by_reason"] == {"control_string": 1, "duplicate_prompt": 1, "not_kept_by_filter": 3,
                                                     "overlap_with_training_reference_toxicchat_or_arc": 2,
                                                     "token_audit_TooLong": 1}
    assert summary["overrefusal"]["excluded_by_reason"] == {"duplicate_prompt": 1, "not_kept_by_filter": 3}
    assert summary["harm"]["split"] == {"dev": 2, "selector": 2, "hidden": 4}
    item = items["dev"][0]
    assert set(item) == {"prompt_id", "kind", "prompt", "prompt_tokens", "token_sha256"}
    prompts = [normalize(i["prompt"]) for bank in items.values() for i in bank]
    assert len(set(prompts)) == len(prompts)
    training = {normalize(r["prompt"]) for r in jsonl(v3[pp.TRAIN_ROWS])}
    assert not set(prompts) & training
    folder, digest = fx.prepare_dir_v3(tmp_path / "prepared")
    with pytest.raises(HiddenAccessError):
        load_prepared(folder, digest, banks=("hidden",))
    dev = load_prepared(folder, digest, banks=("dev",)).banks["dev"]
    assert Counter(i["kind"] for i in dev) == {"safety": 3, "arc_generation": 2, "arc_utility": 3, "harm": 2,
                                               "overrefusal": 2}
    hidden = load_prepared(folder, digest, banks=("hidden",), allow_hidden=True).banks["hidden"]
    assert Counter(i["kind"] for i in hidden)["harm"] == 4


# ----- 4. refusals --------------------------------------------------------------------------------------


def test_asserted_counts_and_source_hashes_refuse_any_difference():
    with pytest.raises(DataError, match="harm bank"):
        fx.prepared_files_v3(edit=lambda c: c["eval_banks"]["harm"].update(expected_eligible=9))
    with pytest.raises(DataError, match="injection"):
        fx.prepared_files_v3(edit=lambda c: c["injection"]["expected"].update(candidates=21))
    with pytest.raises(HashMismatch):
        fx.prepared_files_v3(edit=lambda c: c["extra_sources"]["xstest"].update(sha256="0" * 64))
    with pytest.raises(DataError, match="non-empty hidden part"):
        fx.prepared_files_v3(edit=lambda c: c["eval_banks"]["harm"].update(dev=4, selector=4))
    with pytest.raises(DataError, match="xstest"):
        fx.prepared_files_v3(edit=lambda c: c["eval_banks"]["overrefusal"].update(
            dev=3, selector=3, per_source={"xstest": {"dev": 2, "selector": 2}, "orbench_hard": {"dev": 1, "selector": 1}}))
    bad = fx.bank_files()["xstest"].replace(b"id,prompt", b"id,text", 1)
    with pytest.raises(DataError, match="header"):
        parse_csv_table(bad, sha256_bytes(bad), "xstest", fx.XS_HEADER)
    record = json.loads(fx.pku_files()["pku_a"].decode().split("\n")[0])
    for change in ({"response_0_severity_level": 4}, {"is_response_0_safe": "no"}, {"extra": 1}):
        data = json.dumps({**record, **change}).encode() + b"\n"
        with pytest.raises(DataError):
            parse_pku(data, sha256_bytes(data), "pku")
    reordered = {**record, "response_1_harm_category": dict(reversed(list(record["response_1_harm_category"].items())))}
    data = json.dumps(reordered).encode() + b"\n"
    with pytest.raises(DataError, match="order"):
        parse_pku(data, sha256_bytes(data), "pku")


def test_leakage_errors_name_ids_and_counts_never_prompt_text():
    secret = "a held-out prompt that must never be printed"
    item = {"prompt_id": "p-hidden", "kind": "harm", "prompt": secret}
    with pytest.raises(pp.LeakageError) as error:
        pp._assert_disjoint([{"uid": "train:00001", "prompt": secret.upper()}], [],
                            {"dev": [], "selector": [], "hidden": [item]})
    assert "p-hidden" in str(error.value) and "train:00001" in str(error.value)
    assert "held-out" not in str(error.value).lower() and "printed" not in str(error.value)


def test_the_new_config_sections_are_validated():
    raw = fx.raw_inputs()
    good = {**fx.data_config(raw), **fx.v3_sections(fx.v3_sources())}
    validate_data_config(good)

    def broken(change) -> dict:
        config = json.loads(json.dumps(good))
        change(config)
        return config

    for change in (lambda c: c.pop("eval_banks"),
                   lambda c: c["injection"].update(count=7),
                   lambda c: c["injection"].update(sources=["harmbench"]),
                   lambda c: c["eval_banks"]["overrefusal"].update(sources=["harmbench"]),
                   lambda c: c["extra_sources"]["xstest"].update(local="/abs/xstest.csv"),
                   lambda c: c["extra_sources"]["xstest"].update(local="../xstest.csv"),
                   lambda c: c["extra_sources"]["xstest"]["keep"].update(other=["x"]),
                   lambda c: c["extra_sources"]["xstest"].update(prompt_field="text"),
                   lambda c: c["extra_sources"].update(unused=dict(c["extra_sources"]["xstest"])),
                   lambda c: c["extra_sources"]["pku_a"].update(format="parquet"),
                   lambda c: c["eval_banks"]["overrefusal"]["per_source"]["xstest"].update(dev=2),
                   lambda c: c["eval_banks"]["overrefusal"]["per_source"].pop("xstest"),
                   lambda c: c["injection"]["near_duplicate"].update(max_jaccard=0),
                   lambda c: c["injection"].pop("near_duplicate")):
        with pytest.raises(ConfigError):
            validate_data_config(broken(change))
    assert [injection_count(p, 10_148) for p in ("2", "5", "10")] == [203, 507, 1015]


def test_prepare_needs_the_sources_root_exactly_when_the_config_names_extra_sources(tmp_path, capsys):
    raw = fx.raw_inputs()
    config_path = tmp_path / "v3.json"
    config_path.write_text(json.dumps({**fx.data_config(raw), **fx.v3_sections(fx.v3_sources())}))
    args = ["prepare", "--data-config", str(config_path), "--out", str(tmp_path / "out")]
    for name in ("date-train", "date-ref", "toxicchat-test", "arc-validation", "arc-test"):
        args += [f"--{name}", str(tmp_path / "missing")]
    assert cli(args) == 2 and "--sources-root is required" in capsys.readouterr().err
    assert not (tmp_path / "out").exists()


# ----- 5. the real configs (hashes and fields only; no source text is read) --------------------------------


def test_the_v3_data_configs_extend_prepared_v2s_config_and_pin_the_v2_sources():
    base = load_data_config(PACKAGE / "configs" / "study-v2-data-expanded-arc.json")
    configs = {tag: load_data_config(PACKAGE / "configs" / f"study-v3-data-{tag}.json") for tag in ("inj05", "inj10")}
    for tag, config in configs.items():
        for key, value in base.items():
            if key not in ("name", "purpose", "amendments"):
                assert config[key] == value, (tag, key)
        assert config["amendments"][:len(base["amendments"])] == base["amendments"]
    five, ten = configs["inj05"], configs["inj10"]
    assert (five["injection"]["count"], ten["injection"]["count"]) == (507, 1015)
    assert {k: v for k, v in five.items() if k not in ("name", "purpose", "injection")} == \
        {k: v for k, v in ten.items() if k not in ("name", "purpose", "injection")}
    assert {k: v for k, v in five["injection"].items() if k not in ("percent", "count")} == \
        {k: v for k, v in ten["injection"].items() if k not in ("percent", "count")}
    manifest = ROOT / "sources" / "v2" / "sources-manifest.json"
    if manifest.exists():
        pinned = {f["local"]: f for f in json.loads(manifest.read_text())["files"]}
        for spec in ten["extra_sources"].values():
            assert pinned[spec["local"]]["sha256"] == spec["sha256"]
            assert pinned[spec["local"]]["license"] == spec["license"]
    assert config_sha256(five) != config_sha256(ten)
