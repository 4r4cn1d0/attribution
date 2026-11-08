"""encode_count_78b.py on synthetic fixtures only (R1 Track C; Part 2 section 1.8 with AM1; DES DESO items 6, 17,
DESO3 item 38, E1; GXB O6, O13). A fake codec (one token per word; the word <ctrl> encodes to a special id) stands in for
the tokenizer; the lists, the s-pool record, the O-ext bank and the anchor list are written under pytest's tmp_path.
Every fixture text holds a planted sentinel, and the tests prove that it never reaches stdout, stderr, the record or a
message. The real recipes (committed configs) and the committed records are read for their hashes and limits only; no
real list, bank, prepared set or tokenizer is opened."""

from __future__ import annotations

import copy
import json
from pathlib import Path

import pytest

from experiments.safety_selection.common import canonical_json, sha256_bytes
from scripts.scale78b import encode_count_78b as ec

ROOT = Path(__file__).resolve().parents[3]
SENT = "QZXJ-planted-sentinel-text-4471"
CTRL = 99


class FakeCodec:
    """ENGINEERING FIXTURE: one id per whitespace word; <ctrl> is a special id; prompt_ids adds two header ids."""

    eos_id = 2

    def encode(self, text):
        return [CTRL if w == "<ctrl>" else 7 for w in text.split()]

    def prompt_ids(self, text):
        return [5] + self.encode(text) + [6]

    def has_special(self, ids):
        return CTRL in ids


TOKENIZERS = {"olmo2-7b": {"repo_id": "allenai/OLMo-2-0425-1B-Instruct",
                           "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e", "end_of_turn_token": "<|endoftext|>"},
              "llama31-8b": {"repo_id": "meta-llama/Llama-3.1-8B-Instruct",
                             "revision": "0e9e39f249a16976918f6564b8830bc894c89659", "end_of_turn_token": "<|eot_id|>"}}


def fake_context(codec=None, tokenizer=None):
    def make(family, prepared):
        return ec.Context(codec or FakeCodec(), tokenizer or TOKENIZERS[family], "f" * 64)
    return make


def text(i, extra=""):
    return f"{SENT} prompt number {i} {extra}".strip()


# ----- the lists fixture ------------------------------------------------------------------------------------------


def lists_fixture(tmp, *, bad=True, mutate=None):
    """A synthetic S-pool: S3 subset r-000..r-019, S1 = r-015..r-024 (r-020..r-024 outside the subset), S4 = r-030..r-041.
    With bad: r-003's prompt holds <ctrl> (both checks), r-021 (S1, outside the subset) has an empty response
    (encode_train NoTargets), r-007's pair is too long for encode_train only, r-033's prompt is too long."""
    long_prompt = " ".join(["w"] * 1600)                    # > 1536 generation tokens
    long_pair_prompt = " ".join(["w"] * 1000)               # 1002 prompt ids: a generation prompt is fine
    long_response = " ".join(["w"] * 2500)                  # 1002 + 2500 + 1 > 3072
    rows = {}
    for i in range(42):
        rid = f"r-{i:03d}"
        rows[rid] = {"id": rid, "prompt": text(i), "response": f"{SENT} safe response {i}"}
    if bad:
        rows["r-003"]["prompt"] = text(3, "<ctrl>")
        rows["r-021"]["response"] = ""
        rows["r-007"]["prompt"], rows["r-007"]["response"] = f"{SENT} {long_pair_prompt}", long_response
        rows["r-033"]["prompt"] = f"{SENT} {long_prompt}"
    subset = [f"r-{i:03d}" for i in range(20)]
    s1_ids = [f"r-{i:03d}" for i in range(15, 25)]
    s4_ids = [f"r-{i:03d}" for i in range(30, 42)]
    pool_ids = subset + [i for i in s1_ids if i not in subset]

    def prompt_list(name, ids):
        return canonical_json({"kind": "stage1 prompt list", "version": 1, "name": name, "items": [rows[i] for i in ids]})

    files = {"s1": prompt_list("s1", s1_ids), "s4_candidates": prompt_list("s4_candidates", s4_ids),
             "s3_subset": prompt_list("s3_subset", subset),
             "s3_safe": canonical_json({"kind": "stage1 text pool", "version": 1, "name": "s3_safe",
                                        "items": [rows[i] for i in pool_ids]})}
    if mutate:
        files = mutate(files, rows) or files
    folder = tmp / "sealed"
    folder.mkdir()
    paths = {}
    for name, data in files.items():
        paths[name] = folder / f"{name}.json"
        paths[name].write_bytes(data)
    record = {"kind": "stage1 s-pool record", "version": 1,
              "lists": {"s1": {"file": "s1.json", "sha256": sha256_bytes(files["s1"]), "ids": s1_ids},
                        "s3_subset": {"file": "s3_subset.json", "sha256": sha256_bytes(files["s3_subset"]), "ids": subset},
                        "s4_candidates": {"file": "s4_candidates.json", "sha256": sha256_bytes(files["s4_candidates"]),
                                          "ids": s4_ids}},
              "s3_pool": {"file": "s3_safe.pool.json", "name": "s3_safe", "sha256": sha256_bytes(files["s3_safe"]),
                          "items": len(pool_ids)}}
    rec_dir = tmp / "records"
    rec_dir.mkdir()
    rec_path = rec_dir / "s_pool_record.json"
    rec_path.write_bytes(canonical_json(record))
    pins = {"list_pins": {"s1": (sha256_bytes(files["s1"]), len(s1_ids)),
                          "s3_safe": (sha256_bytes(files["s3_safe"]), len(pool_ids)),
                          "s4_candidates": (sha256_bytes(files["s4_candidates"]), len(s4_ids))},
            "record_pin": sha256_bytes(rec_path.read_bytes()),
            "subset_pin": (sha256_bytes(files["s3_subset"]), len(subset))}
    return paths, rec_path, pins


def lists_argv(tmp, paths, rec_path, pins, family="olmo2-7b", out=None, extra=()):
    out = out or (tmp / "out" / "rec.json")
    out.parent.mkdir(exist_ok=True)
    argv = ["--family", family, "--prepared", str(tmp / "prepared")]
    for name in ("s1", "s3_safe", "s4_candidates"):
        argv += ["--list", f"{name}={paths[name]}:{pins['list_pins'][name][0]}"]
    argv += ["--s-pool-record", f"{rec_path}:{pins['record_pin']}", "--out", str(out), *extra]
    return argv, out


def run_main(argv, capsys, **kw):
    code = ec.main(argv, **kw)
    cap = capsys.readouterr()
    return code, cap.out, cap.err


def no_text(*blobs):
    for blob in blobs:
        data = blob if isinstance(blob, str) else blob.decode("utf-8")
        assert SENT not in data
        assert "planted" not in data and "safe response" not in data and "prompt number" not in data


def test_lists_counts_by_reason(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_SOME, se
    doc = json.loads(out.read_bytes())
    c = doc["checks"]
    assert c["s1"]["generation_prompt"] == {"n": 10, "accepted": 10, "refused": 0, "refused_by_reason": {},
                                            "refused_ids": []}
    assert c["s1"]["encode_train"]["refused_by_reason"] == {"NoTargets": 1}
    assert c["s1"]["encode_train"]["refused_ids"] == ["r-021"]
    assert c["s3_safe"]["generation_prompt"]["refused_by_reason"] == {"ControlTokenError": 1}
    assert c["s3_safe"]["generation_prompt"]["refused_ids"] == ["r-003"]
    assert c["s3_safe"]["encode_train"]["refused_by_reason"] == {"ControlTokenError": 1, "NoTargets": 1, "TooLong": 1}
    assert c["s3_safe"]["encode_train"]["refused_ids"] == ["r-003", "r-007", "r-021"]
    assert c["s3_safe"]["encode_train"]["n"] == 25 and c["s3_safe"]["encode_train"]["accepted"] == 22
    assert c["s4_candidates"] == {"generation_prompt": {"n": 12, "accepted": 11, "refused": 1,
                                                        "refused_by_reason": {"TooLong": 1}, "refused_ids": ["r-033"]}}
    # the S3 subset: s3_safe's counts on the record's 20 subset ids (r-021 is S1's row outside the subset)
    assert c["s3_subset"]["generation_prompt"]["n"] == 20
    assert c["s3_subset"]["generation_prompt"]["refused_ids"] == ["r-003"]
    assert c["s3_subset"]["encode_train"]["refused_ids"] == ["r-003", "r-007"]
    assert c["s3_subset"]["encode_train"]["refused_by_reason"] == {"ControlTokenError": 1, "TooLong": 1}
    assert doc["all_accepted"] is False
    assert doc["recipe"]["config_sha256"] == ec.RECIPES["olmo2-7b"][1]
    assert (doc["recipe"]["max_prompt_tokens"], doc["recipe"]["max_train_tokens"]) == (1536, 3072)
    assert doc["tokenizer"] == {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision_prefix": "48d788eca847"}
    assert doc["inputs"]["s1"] == {"sha256": pins["list_pins"]["s1"][0], "items": 10}
    assert doc["inputs"]["s3_subset"]["sha256"] == pins["subset_pin"][0]
    assert doc["inputs"]["s_pool_record"] == {"sha256": pins["record_pin"]}
    assert doc["kind"] == ec.KIND and doc["mode"] == "lists" and doc["family"] == "olmo2-7b"
    assert "r-033" in so and "TooLong" in so and "all accepted: False" in so
    no_text(so, se, out.read_bytes())


def test_lists_all_accepted_exit_0(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path, bad=False)
    argv, out = lists_argv(tmp_path, paths, rec, pins, family="llama31-8b")
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_ALL, se
    doc = json.loads(out.read_bytes())
    assert doc["all_accepted"] is True and doc["family"] == "llama31-8b"
    assert doc["recipe"]["config_sha256"] == ec.RECIPES["llama31-8b"][1]
    assert all(t["refused"] == 0 for e in doc["checks"].values() for t in e.values())
    no_text(so, se, out.read_bytes())


def test_lists_limits_are_the_recipes(tmp_path, capsys):
    """A prompt of exactly 1536 generation ids passes and 1537 is refused (the recipe's model.max_prompt_tokens);
    a pair of exactly 3072 ids passes and 3073 is refused (model.max_train_tokens)."""
    def mutate(files, rows):
        rows["r-030"]["prompt"] = " ".join(["w"] * 1534)        # 1534 + 2 header ids = 1536
        rows["r-031"]["prompt"] = " ".join(["w"] * 1535)        # 1537
        rows["r-016"]["prompt"] = " ".join(["w"] * 1000)        # 1002 ids
        rows["r-016"]["response"] = " ".join(["w"] * 2069)      # 1002 + 2069 + 1 = 3072
        rows["r-017"]["prompt"] = " ".join(["w"] * 1000)
        rows["r-017"]["response"] = " ".join(["w"] * 2070)      # 3073
        ids = {name: [i["id"] for i in json.loads(files[name])["items"]] for name in files}
        out = {}
        for name, data in files.items():
            doc = json.loads(data)
            doc["items"] = [rows[i] for i in ids[name]]
            out[name] = canonical_json(doc)
        return out
    paths, rec, pins = lists_fixture(tmp_path, bad=False, mutate=mutate)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_SOME, se
    c = json.loads(out.read_bytes())["checks"]
    assert c["s4_candidates"]["generation_prompt"]["refused_ids"] == ["r-031"]
    assert c["s1"]["encode_train"]["refused_ids"] == ["r-017"]
    assert c["s3_safe"]["encode_train"]["refused_ids"] == ["r-017"]


def test_lists_off_pin_command_line_refused(tmp_path, capsys):
    """The module's real pins: a fixture list's own SHA-256 is not the pin, so the run refuses before reading."""
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context())
    assert code == ec.EXIT_REFUSED and not out.exists() and so == ""
    assert "list s1: the command line names" in se and "the pin is 389c20ad00261b1a" in se
    no_text(so, se)


def test_lists_bytes_off_pin_refused(tmp_path, capsys):
    """The command line names the pin, but the file's bytes hash to something else: the frozen reader refuses."""
    paths, rec, pins = lists_fixture(tmp_path)
    paths["s4_candidates"].write_bytes(paths["s4_candidates"].read_bytes() + b" ")
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and not out.exists()
    assert "s4_candidates hashes to" in se
    no_text(so, se)


def test_record_off_pin_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    bad = dict(pins, record_pin="0" * 64)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=bad)
    assert code == ec.EXIT_REFUSED and not out.exists() and "the s-pool record" in se


def test_record_list_hash_must_be_the_pin(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    bad = copy.deepcopy(pins)
    bad["subset_pin"] = ("e" * 64, pins["subset_pin"][1])
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=bad)
    assert code == ec.EXIT_REFUSED and "list s3_subset is not the pinned list" in se


def test_record_kind_checked(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    doc = json.loads(rec.read_bytes())
    doc["kind"] = "something else"
    rec.write_bytes(canonical_json(doc))
    pins = dict(pins, record_pin=sha256_bytes(rec.read_bytes()))
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "not a stage1 s-pool record" in se


def test_list_ids_must_be_the_records(tmp_path, capsys):
    def mutate(files, rows):
        doc = json.loads(files["s4_candidates"])
        doc["items"] = doc["items"][::-1]
        files["s4_candidates"] = canonical_json(doc)
    paths, rec, pins = lists_fixture(tmp_path, mutate=mutate)
    doc = json.loads(rec.read_bytes())
    doc["lists"]["s4_candidates"]["sha256"] = sha256_bytes(paths["s4_candidates"].read_bytes())
    rec.write_bytes(canonical_json(doc))
    pins = dict(pins, record_pin=sha256_bytes(rec.read_bytes()))
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "list s4_candidates's ids are not the s-pool record's" in se


def test_s1_ids_must_be_the_records(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    doc = json.loads(rec.read_bytes())
    doc["lists"]["s1"]["ids"] = doc["lists"]["s1"]["ids"][1:] + doc["lists"]["s1"]["ids"][:1]
    rec.write_bytes(canonical_json(doc))
    pins = dict(pins, record_pin=sha256_bytes(rec.read_bytes()))
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "list s1's ids are not the s-pool record's" in se


def test_s3_safe_order_checked(tmp_path, capsys):
    def mutate(files, rows):
        doc = json.loads(files["s3_safe"])
        doc["items"] = doc["items"][1:] + doc["items"][:1]
        files["s3_safe"] = canonical_json(doc)
    paths, rec, pins = lists_fixture(tmp_path, mutate=mutate)
    doc = json.loads(rec.read_bytes())
    doc["s3_pool"]["sha256"] = sha256_bytes(paths["s3_safe"].read_bytes())
    rec.write_bytes(canonical_json(doc))
    pins = copy.deepcopy(pins)
    pins["record_pin"] = sha256_bytes(rec.read_bytes())
    pins["list_pins"]["s3_safe"] = (sha256_bytes(paths["s3_safe"].read_bytes()), 25)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "s3_safe's ids are not the S3 subset then S1's rows" in se


def test_s1_and_s3_safe_must_agree(tmp_path, capsys):
    def mutate(files, rows):
        doc = json.loads(files["s1"])
        doc["items"][0]["response"] = f"{SENT} another response"
        files["s1"] = canonical_json(doc)
    paths, rec, pins = lists_fixture(tmp_path, mutate=mutate)
    doc = json.loads(rec.read_bytes())
    doc["lists"]["s1"]["sha256"] = sha256_bytes(paths["s1"].read_bytes())
    rec.write_bytes(canonical_json(doc))
    pins = copy.deepcopy(pins)
    pins["record_pin"] = sha256_bytes(rec.read_bytes())
    pins["list_pins"]["s1"] = (sha256_bytes(paths["s1"].read_bytes()), 10)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "differ on row r-015" in se
    no_text(so, se)


def test_list_size_checked_against_the_record(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    bad = copy.deepcopy(pins)
    bad["list_pins"]["s4_candidates"] = (pins["list_pins"]["s4_candidates"][0], 13)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=bad)
    assert code == ec.EXIT_REFUSED and "list s4_candidates is not the pinned list" in se


def test_list_kind_checked_by_the_frozen_reader(tmp_path, capsys):
    def mutate(files, rows):
        doc = json.loads(files["s4_candidates"])
        doc["kind"] = "not a list"
        files["s4_candidates"] = canonical_json(doc)
    paths, rec, pins = lists_fixture(tmp_path, mutate=mutate)
    doc = json.loads(rec.read_bytes())
    doc["lists"]["s4_candidates"]["sha256"] = sha256_bytes(paths["s4_candidates"].read_bytes())
    rec.write_bytes(canonical_json(doc))
    pins = copy.deepcopy(pins)
    pins["record_pin"] = sha256_bytes(rec.read_bytes())
    pins["list_pins"]["s4_candidates"] = (sha256_bytes(paths["s4_candidates"].read_bytes()), 12)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "is not a stage-1 prompt list or text pool" in se


def test_every_list_is_required(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    i = argv.index("--list")
    argv = argv[:i] + argv[i + 2:]                               # drop s1
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "--list needs s1" in se


def test_a_list_named_twice_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    argv += ["--list", f"s1={paths['s1']}:{pins['list_pins']['s1'][0]}"]
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "names s1 twice" in se


def test_unknown_list_name_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    argv += ["--list", f"s3_subset={paths['s3_subset']}:{pins['subset_pin'][0]}"]
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "NAME one of s1, s3_safe, s4_candidates" in se


def test_recipe_of_the_other_family_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins, extra=("--recipe", str(ROOT / ec.RECIPES["llama31-8b"][0])))
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "olmo2-7b's main recipe is 18cc31d7" in se and not out.exists()


def test_recipe_g_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    g = ROOT / "experiments/safety_selection/configs/study-kt-olmo2-7b-r64-g-mb2-20261011.json"
    argv, out = lists_argv(tmp_path, paths, rec, pins, extra=("--recipe", str(g)))
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "main recipe" in se


@pytest.mark.parametrize("field,value", [("revision", "0" * 40), ("repo_id", "someone/else"),
                                         ("end_of_turn_token", "<|eot_id|>")])
def test_tokenizer_must_be_the_recipes(tmp_path, capsys, field, value):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    tk = dict(TOKENIZERS["olmo2-7b"], **{field: value})
    code, so, se = run_main(argv, capsys, context=fake_context(tokenizer=tk), run_options=pins)
    assert code == ec.EXIT_REFUSED and "the prepared manifest's" in se and not out.exists()


def test_out_is_created_once(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    out.write_bytes(b"x")
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "exists" in se and out.read_bytes() == b"x"


def test_out_beside_an_input_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins, out=paths["s1"].parent / "sub" / "rec.json")
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "must not lie inside an input's folder (at any depth)" in se and not out.exists()
    argv, out = lists_argv(tmp_path, paths, rec, pins, out=paths["s1"].parent / "rec.json")
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and not out.exists()


def test_out_inside_the_prepared_folder_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    (tmp_path / "prepared").mkdir()
    argv, out = lists_argv(tmp_path, paths, rec, pins, out=tmp_path / "prepared" / "rec.json")
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and not out.exists()


def test_options_of_another_mode_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins, extra=("--prompts", f"{paths['s1']}:{'a' * 64}"))
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "another mode" in se


def test_bad_spec_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    argv[argv.index("--s-pool-record") + 1] = f"{rec}:ABC"
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "PATH:SHA256" in se


def test_record_bytes_off_pin_refused(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    good = pins["record_pin"]
    rec.write_bytes(rec.read_bytes() + b" ")
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=dict(pins, record_pin=good))
    assert code == ec.EXIT_REFUSED and f"the s-pool record hashes to" in se and f"the pin is {good}" in se


def test_record_s3_pool_must_be_the_pin(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    doc = json.loads(rec.read_bytes())
    doc["s3_pool"]["sha256"] = "e" * 64
    rec.write_bytes(canonical_json(doc))
    pins = dict(pins, record_pin=sha256_bytes(rec.read_bytes()))
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "s3_pool is not the pinned s3_safe pool" in se


def test_a_pair_list_needs_responses(tmp_path, capsys):
    def mutate(files, rows):
        doc = json.loads(files["s1"])
        del doc["items"][-1]["response"]
        files["s1"] = canonical_json(doc)
    paths, rec, pins = lists_fixture(tmp_path, mutate=mutate)
    doc = json.loads(rec.read_bytes())
    doc["lists"]["s1"]["sha256"] = sha256_bytes(paths["s1"].read_bytes())
    rec.write_bytes(canonical_json(doc))
    pins = copy.deepcopy(pins)
    pins["record_pin"] = sha256_bytes(rec.read_bytes())
    pins["list_pins"]["s1"] = (sha256_bytes(paths["s1"].read_bytes()), 10)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "list s1: an item holds no text response" in se


def test_write_once_never_overwrites(tmp_path):
    out = tmp_path / "rec.json"
    out.write_bytes(b"x")
    with pytest.raises(ec.Refusal, match="created once"):
        ec.write_once(out, b"y")
    assert out.read_bytes() == b"x"


# ----- no text anywhere --------------------------------------------------------------------------------------------


class RaisingCodec(FakeCodec):
    """ENGINEERING FIXTURE: raises an exception whose message holds the text it was given."""

    def __init__(self, exc_type):
        self.exc_type = exc_type

    def prompt_ids(self, text):
        if "number 5" in text:
            raise self.exc_type(f"cannot encode {text!r}")
        return super().prompt_ids(text)


def test_an_unexpected_error_prints_no_text(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(codec=RaisingCodec(RuntimeError)), run_options=pins)
    assert code == ec.EXIT_REFUSED and not out.exists()
    assert "RuntimeError" in se and "withheld" in se
    no_text(so, se)


def test_a_valueerror_with_text_is_counted_by_class_only(tmp_path, capsys):
    class TemplateTrouble(ValueError):
        pass
    paths, rec, pins = lists_fixture(tmp_path, bad=False)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(codec=RaisingCodec(TemplateTrouble)), run_options=pins)
    assert code == ec.EXIT_SOME, se
    doc = json.loads(out.read_bytes())
    assert doc["checks"]["s3_safe"]["generation_prompt"]["refused_by_reason"] == {"TemplateTrouble": 1}
    no_text(so, se, out.read_bytes())


def test_a_refusal_holding_text_is_withheld():
    guard = ec.TextGuard()
    guard.add(f"{SENT} some prompt")
    assert "withheld" in guard.message(ec.Refusal(f"bad row {SENT} some prompt"))
    assert guard.message(ec.Refusal("list s1 hashes to abc")) == "list s1 hashes to abc"
    assert "withheld" in guard.message(KeyError("x"))


# ----- the bank mode -----------------------------------------------------------------------------------------------


def bank_fixture(tmp, n=6, bad=(2,)):
    from scripts.stage1_s1 import oext_eval

    real = json.loads((ROOT / "scripts/stage1_s1/settings/oext_eval.json").read_bytes())
    spec = real["bank"]["phtest"]
    rows = [{"id": f"ph-{k:03d}", "prompt": text(100 + k, "<ctrl>" if k in bad else "")} for k in range(n)]
    bank = canonical_json({"kind": spec["bank_kind"], "version": 1, "source": spec["source"], "items": rows})
    folder = tmp / "oext"
    folder.mkdir()
    bank_path = folder / "oext_bank.json"
    bank_path.write_bytes(bank)
    record = {"kind": spec["record_kind"], "version": 1, "bank_size": n, "shortfall": None,
              "provenance": {"settings_sha256": spec["builder"]["settings_sha256"]},
              "bank": {"kind": spec["sealed_kind"], "version": 1, "n_items": n,
                       "full_file": {"sha256": sha256_bytes(bank), "bytes": len(bank)},
                       "items": [{"id": r["id"], "prompt_sha256": sha256_bytes(r["prompt"].encode("utf-8"))}
                                 for r in rows]}}
    rec_path = folder / "oext_record.json"
    rec_path.write_bytes(canonical_json(record))
    doc = copy.deepcopy(real)
    doc["bank"]["phtest"]["record_sha256"] = sha256_bytes(rec_path.read_bytes())
    doc["bank"]["phtest"]["planned"] = n
    settings = oext_eval.settings_from_doc(doc)
    options = {"settings": settings, "record_pin": sha256_bytes(rec_path.read_bytes()), "planned": n}
    return bank_path, rec_path, options


def bank_argv(tmp, bank_path, rec_path, bank_sha=None, rec_sha=None, family="llama31-8b"):
    out = tmp / "out" / "bank.json"
    out.parent.mkdir(exist_ok=True)
    return (["--bank", "--family", family, "--prepared", str(tmp / "prepared"),
             "--oext-record", f"{rec_path}:{rec_sha or sha256_bytes(rec_path.read_bytes())}",
             "--oext-bank", f"{bank_path}:{bank_sha or sha256_bytes(bank_path.read_bytes())}", "--out", str(out)], out)


def test_bank_counts(tmp_path, capsys):
    bank_path, rec_path, options = bank_fixture(tmp_path, n=6, bad=(2, 4))
    argv, out = bank_argv(tmp_path, bank_path, rec_path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_SOME, se
    doc = json.loads(out.read_bytes())
    assert doc["mode"] == "bank" and doc["family"] == "llama31-8b"
    assert doc["checks"]["phtest"]["generation_prompt"] == {"n": 6, "accepted": 4, "refused": 2,
                                                            "refused_by_reason": {"ControlTokenError": 2},
                                                            "refused_ids": ["ph-002", "ph-004"]}
    assert doc["inputs"]["oext_record"]["sha256"] == options["record_pin"]
    assert doc["inputs"]["oext_bank"] == {"sha256": sha256_bytes(bank_path.read_bytes()), "items": 6}
    assert doc["inputs"]["oext_eval_settings"]["sha256"] == options["settings"].sha256
    assert doc["tokenizer"]["revision_prefix"] == "0e9e39f249a1"
    no_text(so, se, out.read_bytes())


def test_bank_all_accepted(tmp_path, capsys):
    bank_path, rec_path, options = bank_fixture(tmp_path, n=4, bad=())
    argv, out = bank_argv(tmp_path, bank_path, rec_path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_ALL, se


def test_bank_real_pins_refuse_a_fixture_record(tmp_path, capsys):
    """The module's pins and oext_eval's real pinned settings: a fixture record is not a810574e…"""
    bank_path, rec_path, _ = bank_fixture(tmp_path)
    argv, out = bank_argv(tmp_path, bank_path, rec_path)
    code, so, se = run_main(argv, capsys, context=fake_context())
    assert code == ec.EXIT_REFUSED and "the pin is a810574e958ca0e5" in se and not out.exists()
    argv, out = bank_argv(tmp_path, bank_path, rec_path, rec_sha=ec.OEXT_RECORD_SHA256)
    code, so, se = run_main(argv, capsys, context=fake_context())
    assert code == ec.EXIT_REFUSED and "the settings pin a810574e958ca0e5" in se   # oext_eval.load_bank's own check
    no_text(so, se)


def test_real_oext_settings_pin_the_record():
    from scripts.stage1_s1 import oext_eval

    settings = oext_eval.load_pinned_settings()
    assert settings.doc["bank"]["phtest"]["record_sha256"] == ec.OEXT_RECORD_SHA256
    assert settings.doc["bank"]["phtest"]["planned"] == ec.OEXT_PLANNED == 400


def test_bank_settings_must_pin_this_record(tmp_path, capsys):
    bank_path, rec_path, options = bank_fixture(tmp_path)
    argv, out = bank_argv(tmp_path, bank_path, rec_path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=dict(options, record_pin="1" * 64))
    assert code == ec.EXIT_REFUSED and "this count needs" in se
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=dict(options, planned=7))
    assert code == ec.EXIT_REFUSED and "this count needs" in se


def test_bank_file_pin_must_be_the_records(tmp_path, capsys):
    bank_path, rec_path, options = bank_fixture(tmp_path)
    argv, out = bank_argv(tmp_path, bank_path, rec_path, bank_sha="c" * 64)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and "full_file SHA-256" in se and not out.exists()


def test_bank_file_bytes_checked_by_the_frozen_reader(tmp_path, capsys):
    bank_path, rec_path, options = bank_fixture(tmp_path)
    good = sha256_bytes(bank_path.read_bytes())
    bank_path.write_bytes(bank_path.read_bytes() + b"\n")
    argv, out = bank_argv(tmp_path, bank_path, rec_path, bank_sha=good)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and "is not the file the record names" in se


def test_bank_with_a_shortfall_is_not_the_400(tmp_path, capsys):
    """oext_eval.load_bank accepts a record with a matching shortfall (LN-24); this count needs the planned count."""
    from scripts.stage1_s1 import oext_eval

    bank_path, rec_path, options = bank_fixture(tmp_path, n=5, bad=())
    record = json.loads(rec_path.read_bytes())
    record["shortfall"] = {"eligible": 5, "planned": 6}
    rec_path.write_bytes(canonical_json(record))
    doc = copy.deepcopy(options["settings"].doc)
    doc["bank"]["phtest"]["record_sha256"] = sha256_bytes(rec_path.read_bytes())
    doc["bank"]["phtest"]["planned"] = 6
    options = {"settings": oext_eval.settings_from_doc(doc), "record_pin": sha256_bytes(rec_path.read_bytes()),
               "planned": 6}
    argv, out = bank_argv(tmp_path, bank_path, rec_path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and "holds 5 prompts, not 6" in se


def test_bank_needs_both_files(tmp_path, capsys):
    bank_path, rec_path, options = bank_fixture(tmp_path)
    argv, out = bank_argv(tmp_path, bank_path, rec_path)
    i = argv.index("--oext-bank")
    code, so, se = run_main(argv[:i] + argv[i + 2:], capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and "--bank needs" in se


# ----- the anchor mode ---------------------------------------------------------------------------------------------


def anchor_fixture(tmp, harmful_bad=(3, 10), generation_bad=(100,), n=128, long_prompts=()):
    long_response = " ".join(["w"] * 3100)
    prompts = []
    for k in range(n):
        prompt = text(200 + k, "<ctrl>" if k in generation_bad else " ".join(["w"] * 1600) if k in long_prompts else "")
        response = long_response if k in harmful_bad else f"{SENT} unsafe response {k}"
        prompts.append({"index": k, "prompt": prompt, "unsafe_response": response})
    doc = {"kind": "gate-c anchor prompt list", "version": 1,
           "source": {"repo_id": "fixture/none", "revision": "0" * 40, "file_sha256": {"f": "0" * 64}},
           "prompts": prompts, "provenance": {}}
    folder = tmp / "anchor"
    folder.mkdir()
    path = folder / "anchor_prompts.json"
    path.write_bytes(canonical_json(doc))
    return path, {"list_pin": sha256_bytes(path.read_bytes())}


def anchor_argv(tmp, path, sha=None, family="olmo2-7b"):
    out = tmp / "out" / "anchor.json"
    out.parent.mkdir(exist_ok=True)
    return (["--anchor", "--family", family, "--prepared", str(tmp / "prepared"),
             "--prompts", f"{path}:{sha or sha256_bytes(path.read_bytes())}", "--out", str(out)], out)


def test_anchor_counts_every_failure_and_is_informational(tmp_path, capsys):
    path, options = anchor_fixture(tmp_path)
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_ALL, se                               # informational: written means exit 0
    doc = json.loads(out.read_bytes())
    a = doc["checks"]["anchor_prompts"]
    h, g = a["harmful_pairs_encode_train"], a["generation_prompt"]
    assert h["n"] == 64 and h["refused_ids"] == [3, 10] and h["refused_by_reason"] == {"TooLong": 2}
    assert h["first_refused_index"] == 3
    assert g["n"] == 128 and g["refused_ids"] == [100] and g["refused_by_reason"] == {"ControlTokenError": 1}
    assert g["first_refused_index"] == 100
    assert doc["anchor"]["informational_only"] is True
    assert doc["anchor"]["first_check_that_would_refuse"] == "harmful_pair"
    assert doc["anchor"]["recipe_query_bank_is_ref"] is True
    assert doc["all_accepted"] is False
    assert doc["inputs"]["anchor_prompt_list"] == {"sha256": options["list_pin"], "prompts": 128, "harmful": 64}
    assert "informational only" in so
    no_text(so, se, out.read_bytes())


def test_anchor_harmful_check_covers_the_first_64_only(tmp_path, capsys):
    """A long unsafe response at index 64 or later is not a harmful pair (make_anchor_answers.py:118)."""
    path, options = anchor_fixture(tmp_path, harmful_bad=(63, 64, 127), generation_bad=())
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_ALL, se
    doc = json.loads(out.read_bytes())
    assert doc["checks"]["anchor_prompts"]["harmful_pairs_encode_train"]["refused_ids"] == [63]


def test_anchor_generation_only_failure(tmp_path, capsys):
    path, options = anchor_fixture(tmp_path, harmful_bad=(), generation_bad=(70, 100))
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    doc = json.loads(out.read_bytes())
    assert doc["anchor"]["first_check_that_would_refuse"] == "generation_prompt"
    assert doc["checks"]["anchor_prompts"]["generation_prompt"]["refused_ids"] == [70, 100]
    assert doc["checks"]["anchor_prompts"]["harmful_pairs_encode_train"]["refused_ids"] == []


def test_anchor_harmful_prompt_with_a_control_token_fails_both_checks(tmp_path, capsys):
    path, options = anchor_fixture(tmp_path, harmful_bad=(), generation_bad=(5,))
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    a = json.loads(out.read_bytes())["checks"]["anchor_prompts"]
    assert a["harmful_pairs_encode_train"]["refused_by_reason"] == {"ControlTokenError": 1}
    assert a["generation_prompt"]["refused_ids"] == [5]


def test_anchor_generation_limit_is_max_prompt_tokens(tmp_path, capsys):
    """A 1600-word prompt (> 1536, < 3072) at index 80 fails the generation check only."""
    path, options = anchor_fixture(tmp_path, harmful_bad=(), generation_bad=(), long_prompts=(80,))
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    a = json.loads(out.read_bytes())["checks"]["anchor_prompts"]
    assert a["generation_prompt"]["refused_ids"] == [80] and a["generation_prompt"]["refused_by_reason"] == {"TooLong": 1}


def test_anchor_clean_list(tmp_path, capsys):
    path, options = anchor_fixture(tmp_path, harmful_bad=(), generation_bad=())
    argv, out = anchor_argv(tmp_path, path, family="llama31-8b")
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    doc = json.loads(out.read_bytes())
    assert code == ec.EXIT_ALL and doc["all_accepted"] is True
    assert doc["anchor"]["first_check_that_would_refuse"] is None


def test_anchor_real_pin_refuses_a_fixture(tmp_path, capsys):
    path, _ = anchor_fixture(tmp_path)
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context())
    assert code == ec.EXIT_REFUSED and "the pin is 78467c97c40e7e9f" in se and not out.exists()
    argv, out = anchor_argv(tmp_path, path, sha=ec.ANCHOR_LIST_SHA256)
    code, so, se = run_main(argv, capsys, context=fake_context())
    assert code == ec.EXIT_REFUSED and "SHA-256 is not the pinned value" in se    # the frozen reader's own check
    no_text(so, se)


def test_anchor_schema_checked_by_the_frozen_reader(tmp_path, capsys):
    path, options = anchor_fixture(tmp_path, n=127)
    argv, out = anchor_argv(tmp_path, path)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and "holds 127 prompts, not 128" in se


def test_anchor_needs_prompts(tmp_path, capsys):
    path, options = anchor_fixture(tmp_path)
    argv, out = anchor_argv(tmp_path, path)
    i = argv.index("--prompts")
    code, so, se = run_main(argv[:i] + argv[i + 2:], capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and "--anchor needs --prompts" in se


# ----- the real path's pins and limits (committed files only) ------------------------------------------------------


def test_pins_equal_the_committed_sources():
    pins = json.loads((ROOT / "scripts/scale78b/settings/pins_78b.json").read_bytes())
    sealed = pins["shared"]["sealed_lists_1b"]
    assert {n: (sealed[n]["sha256"], sealed[n].get("rows", sealed[n].get("items"))) for n in ec.LIST_PINS} == ec.LIST_PINS
    assert (sealed["record"]["path"], sealed["record"]["sha256"]) == ec.S_POOL_RECORD
    assert pins["shared"]["anchor_prompt_list_sha256"] == ec.ANCHOR_LIST_SHA256
    for f in ec.FAMILIES:
        fam = pins["families"][f]
        assert (fam["main_recipe"]["path"], fam["main_recipe"]["config_sha256"]) == ec.RECIPES[f]
        assert fam["manifest_sha256"] == ec.MANIFESTS[f]
    from scripts import make_anchor_answers as maa
    assert (maa.LIST_SHA256, maa.N_PROMPTS, maa.N_HARMFUL) == (ec.ANCHOR_LIST_SHA256, ec.ANCHOR_PROMPTS,
                                                                ec.ANCHOR_HARMFUL)


def test_the_committed_s_pool_record_names_the_pins():
    data = (ROOT / ec.S_POOL_RECORD[0]).read_bytes()
    assert sha256_bytes(data) == ec.S_POOL_RECORD[1]
    ids = ec.read_s_pool_record(ROOT / ec.S_POOL_RECORD[0], ec.S_POOL_RECORD[1], ec.LIST_PINS, ec.S3_SUBSET_PIN)
    assert {n: len(v) for n, v in ids.items()} == {"s1": 48, "s3_subset": 855, "s4_candidates": 512}
    assert len(set(ids["s3_subset"]) | set(ids["s1"])) == 861


@pytest.mark.parametrize("family", ec.FAMILIES)
def test_the_limits_are_main_fs_model_block(family):
    recipe, digest, label, limits = ec.load_recipe(family, None)
    assert digest == ec.RECIPES[family][1] and label.endswith(ec.RECIPES[family][0])
    assert limits == {"max_prompt_tokens": 1536, "max_train_tokens": 3072}
    assert "max_prompt_tokens" not in recipe["generation"]      # the brief's generation.max_prompt_tokens does not exist
    from experiments.safety_selection.config import tokenizer_of
    assert tokenizer_of(recipe) == (TOKENIZERS[family]["repo_id"], TOKENIZERS[family]["revision"])
    assert recipe["model"]["end_of_turn_token"] == TOKENIZERS[family]["end_of_turn_token"]


def test_real_context_refuses_an_unpinned_manifest(tmp_path, capsys):
    """The real path (no fixture context): a prepared folder whose manifest is not the family's pin refuses with the
    class name only, before any tokenizer is loaded."""
    prepared = tmp_path / "prepared"
    prepared.mkdir()
    manifest = canonical_json({"data_config": {"tokenizer": {"repo_id": "x", "revision": "y", "end_of_turn_token": "z"}}})
    (prepared / "manifest.json").write_bytes(manifest)
    (prepared / "manifest.sha256").write_text(sha256_bytes(manifest) + "\n", encoding="ascii")
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, run_options=pins)
    assert code == ec.EXIT_REFUSED and "cannot be loaded (DataError)" in se and not out.exists()


def test_real_context_uses_build_s_pool_real_codec(tmp_path, monkeypatch):
    """real_context reads the manifest at the family's pin and builds the codec with build_s_pool.real_codec."""
    from experiments.safety_selection import prepare
    from scripts.stage1 import build_s_pool

    seen = {}
    tk = dict(TOKENIZERS["olmo2-7b"], max_prompt_tokens=1536, max_train_tokens=3072)

    def fake_read_manifest(root, expected=None):
        seen["manifest"] = (Path(root), expected)
        return {"data_config": {"tokenizer": tk}}, expected

    def fake_real_codec(root, settings):
        seen["codec"] = (Path(root), settings)
        return "CODEC"
    monkeypatch.setattr(prepare, "read_manifest", fake_read_manifest)
    monkeypatch.setattr(build_s_pool, "real_codec", fake_real_codec)
    ctx = ec.real_context("olmo2-7b", tmp_path)
    assert ctx.codec == "CODEC" and ctx.manifest_sha256 == ec.MANIFESTS["olmo2-7b"]
    assert seen["manifest"] == (tmp_path, ec.MANIFESTS["olmo2-7b"])
    assert seen["codec"] == (tmp_path, {"inputs": {"prepared_manifest_sha256": ec.MANIFESTS["olmo2-7b"]}})
    assert ctx.tokenizer == TOKENIZERS["olmo2-7b"]


# ----- the fix round (verifier C1-C3, C5, C9) ----------------------------------------------------------------------


def mode_case(tmp, mode):
    """(argv, out, run_options, {kind: a text read in this mode}) for one mode's fixture."""
    if mode == "lists":
        paths, rec, pins = lists_fixture(tmp)
        argv, out = lists_argv(tmp, paths, rec, pins)
        return argv, out, pins, {"prompt": text(4), "response": f"{SENT} safe response 4"}
    if mode == "bank":
        bank_path, rec_path, options = bank_fixture(tmp, n=6, bad=())
        argv, out = bank_argv(tmp, bank_path, rec_path)
        return argv, out, options, {"prompt": text(101)}
    path, options = anchor_fixture(tmp)
    argv, out = anchor_argv(tmp, path)
    return argv, out, options, {"prompt": text(201), "response": f"{SENT} unsafe response 1"}


LEAK_CASES = [("lists", "prompt"), ("lists", "response"), ("bank", "prompt"), ("anchor", "prompt"),
              ("anchor", "response")]


@pytest.mark.parametrize("mode,kind", LEAK_CASES)
def test_a_record_holding_text_is_not_written(tmp_path, capsys, monkeypatch, mode, kind):
    """C2: in every mode, a record that held a prompt or a response read (a planted fault) is not written, and nothing
    but the refusal is printed."""
    argv, out, options, leaks = mode_case(tmp_path, mode)
    real = ec.doc_of

    def leaky(*a, **k):
        doc = real(*a, **k)
        doc["leak"] = leaks[kind]
        return doc
    monkeypatch.setattr(ec, "doc_of", leaky)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and not out.exists() and so == ""
    assert "would hold text" in se
    assert list(out.parent.iterdir()) == []
    no_text(so, se)


@pytest.mark.parametrize("mode,kind", LEAK_CASES)
def test_a_printout_holding_text_is_not_written(tmp_path, capsys, monkeypatch, mode, kind):
    argv, out, options, leaks = mode_case(tmp_path, mode)
    monkeypatch.setattr(ec, "summary_lines", lambda doc: ["counts", leaks[kind]])
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    assert code == ec.EXIT_REFUSED and not out.exists() and so == ""
    assert "would hold text" in se
    no_text(so, se)


class ResponseCrashCodec(FakeCodec):
    """ENGINEERING FIXTURE (C3): encode raises a non-ValueError, holding the text, on one response only (responses
    reach encode only through encode_train)."""

    def encode(self, text):
        if text == f"{SENT} safe response 16":
            raise RuntimeError(f"tokenizer crash on {text!r}")
        return super().encode(text)


def test_an_encode_train_crash_refuses_the_run(tmp_path, capsys):
    paths, rec, pins = lists_fixture(tmp_path, bad=False)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    code, so, se = run_main(argv, capsys, context=fake_context(codec=ResponseCrashCodec()), run_options=pins)
    assert code == ec.EXIT_REFUSED and not out.exists() and so == ""
    assert "RuntimeError" in se and "withheld" in se
    no_text(so, se)


class ExitCodec(FakeCodec):
    """ENGINEERING FIXTURE (C5): a SystemExit that carries the text it was given."""

    def prompt_ids(self, text):
        raise SystemExit(f"stop at {text!r}")


@pytest.mark.parametrize("mode", ["lists", "bank", "anchor"])
def test_a_systemexit_with_text_is_caught(tmp_path, capsys, mode):
    argv, out, options, _ = mode_case(tmp_path, mode)
    code, so, se = run_main(argv, capsys, context=fake_context(codec=ExitCodec()), run_options=options)
    assert code == ec.EXIT_REFUSED and not out.exists() and so == ""
    assert "SystemExit" in se and "withheld" in se
    no_text(so, se)


class FailingHandle:
    """ENGINEERING FIXTURE (C1): writes half the bytes, then raises ENOSPC (the verifier's probe)."""

    def __init__(self, handle):
        self.handle = handle

    def write(self, data):
        import errno

        self.handle.write(data[: len(data) // 2])
        self.handle.flush()
        raise OSError(errno.ENOSPC, "No space left on device")

    def __getattr__(self, name):
        return getattr(self.handle, name)

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.handle.close()
        return False


def enospc_open(monkeypatch, folder):
    import builtins

    real_open = builtins.open

    def failing_open(file, mode="r", *a, **k):
        handle = real_open(file, mode, *a, **k)
        if "x" in mode and Path(file).resolve().parent == Path(folder).resolve():
            return FailingHandle(handle)
        return handle
    monkeypatch.setattr(builtins, "open", failing_open)


@pytest.mark.parametrize("mode", ["lists", "bank", "anchor"])
def test_a_failed_write_leaves_no_file(tmp_path, capsys, monkeypatch, mode):
    """C1: a write that fails partway (ENOSPC after half the bytes) leaves neither --out nor a partial file."""
    argv, out, options, _ = mode_case(tmp_path, mode)
    enospc_open(monkeypatch, out.parent)
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=options)
    monkeypatch.undo()
    assert code == ec.EXIT_REFUSED and "cannot be written (OSError)" in se
    assert not out.exists() and list(out.parent.iterdir()) == []


def test_write_once_leaves_only_the_complete_record(tmp_path):
    out = tmp_path / "rec.json"
    assert ec.write_once(out, b"abc") == sha256_bytes(b"abc")
    assert out.read_bytes() == b"abc" and [p.name for p in tmp_path.iterdir()] == ["rec.json"]


def test_record_command_line_hash_must_be_the_pin(tmp_path, capsys):
    """C9: the bytes are the pinned record, but the command line names another hash."""
    paths, rec, pins = lists_fixture(tmp_path)
    argv, out = lists_argv(tmp_path, paths, rec, pins)
    argv[argv.index("--s-pool-record") + 1] = f"{rec}:{'a' * 64}"
    code, so, se = run_main(argv, capsys, context=fake_context(), run_options=pins)
    assert code == ec.EXIT_REFUSED and "the s-pool record: the command line names" in se
