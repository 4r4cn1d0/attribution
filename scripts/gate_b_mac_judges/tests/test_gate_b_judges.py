"""Tests of the Gate B Mac judge tools with fake judges and synthetic unit folders (no model, no real data)."""
from __future__ import annotations

import json
import os
import pathlib
import shutil
import subprocess
import sys

import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import synth  # noqa: E402
from synth import MANIFEST, MARK_A, MARK_P, PIDS, sha  # noqa: E402

import cache as cache_mod  # noqa: E402
import granite_files  # noqa: E402
import harmbench_files  # noqa: E402
import import_cache  # noqa: E402
import units as units_mod  # noqa: E402
import watchdog  # noqa: E402
import write_files  # noqa: E402
from common import GRANITE, HARMBENCH, Refusal, canonical_bytes  # noqa: E402

HB_ARGS = ["--expect-greedy", "0", "--expect-sampled", "0"]


def no_text(*blobs) -> None:
    for b in blobs:
        s = b.decode("utf-8") if isinstance(b, bytes) else str(b)
        assert MARK_P not in s and MARK_A not in s


def env(tmp_path, hosts=("hostA",), distinct_seeds=False, **unit_kw):
    """Units 1101-a0-e1-a1 on each host (one attempt per host), or with distinct_seeds a0 at 1101, 1102, ... (one
    (arm, seed, target) per host, so that one --out can hold every host's file)."""
    retrieved = tmp_path / "pod" / "retrieved"
    prepared = synth.make_bank(tmp_path)
    units = {}
    for i, h in enumerate(hosts):
        seed = 1101 + i if distinct_seeds else 1101
        units[h] = synth.make_unit(retrieved, h, f"{seed}-a0-e1-a1", seed=seed,
                                   completed_utc=f"2026-10-08T0{i + 1}:00:00+00:00", **unit_kw)
    return retrieved, prepared, units


def common_args(retrieved, prepared, cache):
    return ["--run-root", str(retrieved), "--prepared", str(prepared), "--manifest", MANIFEST, "--cache", str(cache)]


def run_hb(retrieved, prepared, cache, labels, calls, extra=()):
    return harmbench_files.main(["run", *common_args(retrieved, prepared, cache), *HB_ARGS, *extra],
                                judge_factory=synth.fake_factory(labels, calls))


def run_gr(retrieved, prepared, cache, labels, calls, extra=()):
    return granite_files.main(["run", *common_args(retrieved, prepared, cache), "--expect-greedy", "0", *extra],
                              judge_factory=synth.fake_factory(labels, calls))


def write(judge, retrieved, cache, out, extra=()):
    return write_files.main(["--judge", judge, "--cache", str(cache), "--out", str(out), "--run-root", str(retrieved),
                             *extra])


# ------------------------------------------------------------------------------------------------ units

def test_units_enumeration_fields_and_skips(tmp_path):
    retrieved = tmp_path / "retrieved"
    e1 = synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    init = synth.make_unit(retrieved, "hostA", "1101-a0-init-a1", target="init", completed_utc="2026-10-08T00:00:00+00:00")
    synth.make_unit(retrieved, "hostA", "1101-attr", kind="attributes")
    unsealed = synth.make_unit(retrieved, "hostA", "1101-r1-e1-a1", arm="r1")
    (unsealed / "COMPLETE.json").unlink()
    synth.make_unit(retrieved, "hostA", "1101-a0-retrain", job_extra={"evaluate_bank": None})     # the Gate B retrain
    preflight = retrieved / "hostA/tree/cuda-preflight-1"                # COMPLETE.json, no job.json (a pod's preflight)
    (preflight / "eval-sample").mkdir(parents=True)
    (preflight / "COMPLETE.json").write_text('{"complete": true}')
    (preflight / "eval-sample" / "COMPLETE.json").write_text("{}")
    found, skipped = units_mod.enumerate_units([retrieved])
    assert [u.unit for u in found] == ["round1/1101-a0-e1-a1", "round1/1101-a0-init-a1"]
    u = found[0]
    assert (u.host, u.arm, u.seed, u.target, u.name) == ("hostA", "a0", 1101, "e1", "1101-a0-e1-a1")
    assert u.complete_sha256 == sha((e1 / "COMPLETE.json").read_bytes())
    assert u.job_sha256 == sha((e1 / "job.json").read_bytes())
    for key, fname in units_mod.EVAL_FILES.items():
        assert u.files[key] == {"path": str(e1 / "eval/e1" / fname), "sha256": sha((e1 / "eval/e1" / fname).read_bytes())}
    assert found[1].target == "init" and found[1].path == init
    assert sorted((s["unit"], s["reason"]) for s in skipped) == [
        ("cuda-preflight-1", units_mod.NOT_A_JOB_UNIT), ("cuda-preflight-1/eval-sample", units_mod.NOT_A_JOB_UNIT),
        ("round1/1101-a0-retrain", "evaluates no bank"), ("round1/1101-attr", "job kind 'attributes' is not run-one"),
        ("round1/1101-r1-e1-a1", units_mod.UNSEALED)]
    assert units_mod.NOT_A_JOB_UNIT.startswith("not a job unit")
    again, _ = units_mod.enumerate_units([retrieved / "hostA"])        # one retrieved/HOST folder as a run root
    assert [x.complete_sha256 for x in again] == [x.complete_sha256 for x in found]
    explicit, _ = units_mod.enumerate_units((), [e1])
    assert explicit[0].host == "hostA" and explicit[0].unit == "round1/1101-a0-e1-a1"


def test_refuses_unit_without_complete_or_job(tmp_path):
    retrieved = tmp_path / "retrieved"
    a = synth.make_unit(retrieved, "hostA", "u1")
    (a / "COMPLETE.json").unlink()
    with pytest.raises(Refusal, match="no COMPLETE.json"):
        units_mod.enumerate_units((), [a])
    b = synth.make_unit(retrieved, "hostA", "u2")
    (b / "job.json").unlink()
    with pytest.raises(Refusal, match="no job.json"):
        units_mod.enumerate_units((), [b])
    found, skipped = units_mod.enumerate_units([retrieved])               # under a root it is not a job unit: skipped
    assert found == [] and sorted(skipped, key=lambda x: x["unit"]) == [
        {"host": "hostA", "unit": "round1/u1", "reason": units_mod.UNSEALED},
        {"host": "hostA", "unit": "round1/u2", "reason": units_mod.NOT_A_JOB_UNIT}]
    assert units_mod.main(["--run-root", str(retrieved)]) == 2            # ... and no judgeable unit is left


@pytest.mark.parametrize("damage", ["edit_listed", "unlisted_file", "listed_missing", "job_hash", "not_complete",
                                    "target_differs"])
def test_refuses_complete_json_not_matching_eval_files(tmp_path, damage):
    retrieved = tmp_path / "retrieved"
    unit = synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    ev = unit / "eval/e1"
    c = json.loads((unit / "COMPLETE.json").read_text())
    if damage == "edit_listed":
        (ev / "samples.jsonl").write_bytes((ev / "samples.jsonl").read_bytes() + b"\n")
    elif damage == "unlisted_file":
        (ev / "extra.jsonl").write_text("{}\n")
    elif damage == "listed_missing":
        (ev / "guard.jsonl").unlink()
    elif damage == "job_hash":
        c["job_sha256"] = "0" * 64
    elif damage == "not_complete":
        c["complete"] = False
    elif damage == "target_differs":
        c["target_checkpoint"] = "init"
    (unit / "COMPLETE.json").write_text(json.dumps(c))
    with pytest.raises(Refusal) as e:
        units_mod.enumerate_units([retrieved])
    no_text(e.value)


def test_one_attempt_at_two_paths_refuses(tmp_path):
    retrieved = tmp_path / "retrieved"
    unit = synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    shutil.copytree(unit, retrieved / "hostB/tree/round1/1101-a0-e1-a1")
    with pytest.raises(Refusal, match="two paths"):
        units_mod.enumerate_units([retrieved])


def test_load_items_split_only_on_newline(tmp_path):
    retrieved = tmp_path / "retrieved"
    synth.make_unit(retrieved, "hostA", "u")
    (u,), _ = units_mod.enumerate_units([retrieved])
    greedy = units_mod.load_items(u, "greedy", with_text=True)
    sampled = units_mod.load_items(u, "sampled")
    assert [(i.prompt_id, i.sample_index) for i in greedy] == [(p, None) for p in PIDS]      # the overrefusal row is out
    assert len(sampled) == 2 * len(PIDS) and all(i.text is None for i in sampled)
    assert greedy[0].answer_sha256 == sha(synth.answer("greedy", PIDS[0], None).encode("utf-8"))
    no_text(repr(greedy[0]))


# ------------------------------------------------------------------------------------------------ judge files

def test_harmbench_file_schema_exact_and_canonical(tmp_path):
    retrieved, prepared, units = env(tmp_path)
    labels = {("greedy", "p-001", None): "yes", ("greedy", "p-003", None): "unparsed",
              ("sampled", "p-001", 0): "yes", ("sampled", "p-002", 1): "yes", ("sampled", "p-003", 0): "unparsed"}
    cache, out, calls = tmp_path / "hb.jsonl", tmp_path / "out", {}
    assert run_hb(retrieved, prepared, cache, labels, calls) == 0
    assert calls == {"factory": 1, "pairs": 9, "judged": 9}
    assert write("harmbench", retrieved, cache, out) == 0
    unit = units["hostA"]
    name = f"harmbench--hostA--1101-a0-e1-a1--{sha((unit / 'COMPLETE.json').read_bytes())[:12]}.json"
    data = (out / name).read_bytes()
    doc = json.loads(data)
    assert list(doc) == sorted(write_files.FILE_KEYS)                    # sorted keys, exactly the schema's
    assert doc == {"kind": "gate-b judge file", "version": 1, "judge": HARMBENCH, "arm": "a0", "seed": 1101,
                   "host": "hostA", "complete_sha256": sha((unit / "COMPLETE.json").read_bytes()),
                   "job_sha256": sha((unit / "job.json").read_bytes()),
                   "greedy": {"n": 3, "harm": 1, "unparsed": 1}, "sampled": {"n": 6, "harm": 2, "unparsed": 1}}
    assert type(doc["seed"]) is int and type(doc["version"]) is int
    assert all(type(v) is int for b in ("greedy", "sampled") for v in doc[b].values())
    assert data == (json.dumps(doc, sort_keys=True, indent=2, ensure_ascii=False) + "\n").encode("utf-8")
    assert data == canonical_bytes(doc) and data.endswith(b"}\n") and data.startswith(b'{\n  "arm": "a0",')
    index = json.loads((out / write_files.INDEX).read_bytes())
    assert index == {"kind": "gate-b judge files index", "version": 2, "complete_allowlist": [],
                     "files": [{"file": name, "sha256": sha(data), "judge": HARMBENCH["name"], "arm": "a0",
                                "seed": 1101, "host": "hostA", "unit": "round1/1101-a0-e1-a1", "target": "e1",
                                "completed_utc": "2026-10-08T01:00:00+00:00",
                                "complete_sha256": doc["complete_sha256"]}]}
    for bad in ({**doc, "target": "e1"}, {k: v for k, v in doc.items() if k != "sampled"}, {**doc, "seed": "1101"},
                {**doc, "sampled": None}, {**doc, "greedy": {"n": 3, "harm": 1}}, {**doc, "version": True}):
        with pytest.raises(Refusal):
            write_files.check_judge_file(bad)


def test_granite_file_has_sampled_null(tmp_path):
    retrieved, prepared, units = env(tmp_path)
    cache, out, calls = tmp_path / "gr.jsonl", tmp_path / "out", {}
    assert run_gr(retrieved, prepared, cache, {("greedy", "p-002", None): "yes"}, calls) == 0
    assert calls["judged"] == 3                                          # greedy harm answers only
    assert write("granite", retrieved, cache, out) == 0
    (path,) = out.glob("granite--*.json")
    data = path.read_bytes()
    doc = json.loads(data)
    assert doc["sampled"] is None and b'"sampled": null' in data
    assert doc["greedy"] == {"n": 3, "harm": 1, "unparsed": 0} and doc["judge"] == GRANITE
    with pytest.raises(Refusal):
        write_files.check_judge_file({**doc, "sampled": {"n": 1, "harm": 0, "unparsed": 0}})


def test_missing_cache_item_refuses_the_file(tmp_path, capsys):
    retrieved, prepared, units = env(tmp_path, hosts=("hostA", "hostB"), distinct_seeds=True)
    cache, out = tmp_path / "gr.jsonl", tmp_path / "out"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    lines = cache.read_bytes().split(b"\n")
    dropped = json.loads(lines[1])
    cache.write_bytes(b"\n".join(lines[:1] + lines[2:]))                 # one hostA item gone
    capsys.readouterr()
    assert write("granite", retrieved, cache, out) == 1
    report = [json.loads(x) for x in capsys.readouterr().out.splitlines() if x.startswith('{"arm"')]
    status = {r["unit"]: (r["status"][:7], r["greedy"]["missing"]) for r in report}
    a_host = next(u for u, (s, m) in status.items() if m == 1)
    assert status[a_host] == ("refused", 1)
    assert sorted(s for s, _ in status.values()) == ["refused", "written"]
    files = list(out.glob("granite--*.json"))
    assert len(files) == 1 and dropped["complete_sha256"][:12] not in files[0].name     # no partial file


def test_stale_or_extra_cache_records_refuse(tmp_path):
    retrieved, prepared, _ = env(tmp_path)
    cache, out = tmp_path / "gr.jsonl", tmp_path / "out"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    recs = [json.loads(x) for x in cache.read_bytes().split(b"\n") if x.strip()]
    stale = dict(recs[0], answer_sha256="1" * 64)
    synth.write_jsonl(tmp_path / "stale.jsonl", [stale] + recs[1:])
    assert write("granite", retrieved, tmp_path / "stale.jsonl", out) == 1
    extra = dict(recs[0], prompt_id="p-999")
    synth.write_jsonl(tmp_path / "extra.jsonl", recs + [extra])
    assert write("granite", retrieved, tmp_path / "extra.jsonl", out) == 1
    assert not list(out.glob("granite--*.json"))


def test_two_hosts_same_unit_name_never_share(tmp_path, capsys):
    retrieved, prepared, units = env(tmp_path, hosts=("hostA", "hostB"))
    # same folder name, same job.json and byte-identical answers on both hosts; only COMPLETE.json differs
    synth.seal(units["hostB"], target="e1", arm="a0", seed=1101, completed_utc="2026-10-09T09:09:09+00:00")
    assert (units["hostA"] / "job.json").read_bytes() == (units["hostB"] / "job.json").read_bytes()
    found, _ = units_mod.enumerate_units([retrieved])
    assert len({u.complete_sha256 for u in found}) == 2
    a, b = sorted(found, key=lambda u: u.host)
    cache, calls = tmp_path / "hb.jsonl", {}
    assert run_hb(retrieved, prepared, cache, {("greedy", "p-001", None): "yes"}, calls) == 0
    assert calls["judged"] == 18                                         # 9 per host, none shared
    c = cache_mod.Cache(cache, HARMBENCH)
    assert len(c) == 18 and len({k[0] for k in c.entries}) == 2
    # one --out holds one file per (judge, arm, seed, target): two attempts refuse without --complete, nothing written
    capsys.readouterr()
    assert write("harmbench", retrieved, cache, tmp_path / "out") == 2
    assert "2 attempts" in capsys.readouterr().err and not list((tmp_path / "out").glob("harmbench--*"))
    # drop hostB's records: hostA's file is still written, hostB's refused (each attempt named into its own --out)
    keep = [x for x in cache.read_bytes().split(b"\n") if x.strip() and json.loads(x)["complete_sha256"] != b.complete_sha256]
    cache.write_bytes(b"\n".join(keep) + b"\n")
    assert write("harmbench", retrieved, cache, tmp_path / "outA", ["--complete", a.complete_sha256]) == 0
    assert write("harmbench", retrieved, cache, tmp_path / "outB", ["--complete", b.complete_sha256]) == 1
    assert not list((tmp_path / "outB").glob("harmbench--*"))
    assert run_hb(retrieved, prepared, cache, {("greedy", "p-001", None): "yes"}, calls) == 0
    assert calls["judged"] == 27
    assert write("harmbench", retrieved, cache, tmp_path / "outB", ["--complete", b.complete_sha256]) == 0
    docs = {}
    for out in ("outA", "outB"):
        (path,) = (tmp_path / out).glob("harmbench--*.json")
        docs[out] = json.loads(path.read_bytes())
    assert (docs["outA"]["host"], docs["outB"]["host"]) == ("hostA", "hostB")
    assert docs["outA"]["complete_sha256"] == a.complete_sha256 and docs["outB"]["complete_sha256"] == b.complete_sha256
    assert docs["outA"]["greedy"] == docs["outB"]["greedy"] == {"n": 3, "harm": 1, "unparsed": 0}


def test_resumable_second_run_judges_nothing(tmp_path, capsys):
    retrieved, prepared, _ = env(tmp_path)
    cache, calls = tmp_path / "hb.jsonl", {}
    assert run_hb(retrieved, prepared, cache, {}, calls, extra=["--limit", "4"]) == 0
    assert calls == {"factory": 1, "pairs": 4, "judged": 4}
    assert run_hb(retrieved, prepared, cache, {}, calls) == 0
    assert calls == {"factory": 2, "pairs": 9, "judged": 9}
    capsys.readouterr()
    assert run_hb(retrieved, prepared, cache, {}, calls) == 0
    assert calls == {"factory": 2, "pairs": 9, "judged": 9}             # no judge built, nothing judged
    plan = [json.loads(x) for x in capsys.readouterr().out.splitlines() if '"judge_plan"' in x][0]
    assert plan["todo"] == 0 and plan["cached"] == 9


def test_cut_last_line_is_rejudged_and_appending_stays_clean(tmp_path):
    retrieved, prepared, _ = env(tmp_path)
    cache, calls = tmp_path / "gr.jsonl", {}
    assert run_gr(retrieved, prepared, cache, {}, calls, extra=["--limit", "2"]) == 0
    data = cache.read_bytes()
    cache.write_bytes(data[:-25])                                        # a hard stop cut the second record
    c = cache_mod.Cache(cache, GRANITE)
    assert len(c) == 1 and c.undecodable == 1
    assert run_gr(retrieved, prepared, cache, {}, calls) == 0
    assert calls["judged"] == 4                                          # 2 + the cut one + the third
    c = cache_mod.Cache(cache, GRANITE)
    assert len(c) == 3 and c.undecodable == 1


def test_cache_conflicts_and_foreign_judge_refuse(tmp_path):
    retrieved, prepared, _ = env(tmp_path)
    cache = tmp_path / "gr.jsonl"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    recs = [json.loads(x) for x in cache.read_bytes().split(b"\n") if x.strip()]
    synth.write_jsonl(tmp_path / "dup.jsonl", recs + [recs[0]])          # an identical repeat is fine
    assert len(cache_mod.Cache(tmp_path / "dup.jsonl", GRANITE)) == 3
    synth.write_jsonl(tmp_path / "conflict.jsonl", recs + [dict(recs[0], label="yes")])
    with pytest.raises(Refusal, match="two different records"):
        cache_mod.Cache(tmp_path / "conflict.jsonl", GRANITE)
    with pytest.raises(Refusal, match="written by judge"):
        cache_mod.Cache(cache, HARMBENCH)
    synth.write_jsonl(tmp_path / "text.jsonl", [dict(recs[0], raw="judge output")])
    with pytest.raises(Refusal, match="keys differ"):
        cache_mod.Cache(tmp_path / "text.jsonl", GRANITE)


def test_existing_judge_file_is_never_overwritten(tmp_path, capsys):
    retrieved, prepared, _ = env(tmp_path)
    cache, out = tmp_path / "gr.jsonl", tmp_path / "out"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    assert write("granite", retrieved, cache, out) == 0
    (path,) = out.glob("granite--*.json")
    before = path.read_bytes()
    assert write("granite", retrieved, cache, out) == 0                  # unchanged
    recs = [json.loads(x) for x in cache.read_bytes().split(b"\n") if x.strip()]
    synth.write_jsonl(tmp_path / "other.jsonl", [dict(recs[0], label="yes")] + recs[1:])
    capsys.readouterr()
    assert write("granite", retrieved, tmp_path / "other.jsonl", out) == 1
    assert "a different file of this name exists" in capsys.readouterr().out
    assert path.read_bytes() == before


def test_bank_and_unit_manifest_checks(tmp_path, capsys):
    retrieved, prepared, _ = env(tmp_path)
    cache = tmp_path / "gr.jsonl"
    (prepared / "manifest.sha256").write_text("e" * 64 + "\n")
    rc = granite_files.main(["run", *common_args(retrieved, prepared, cache), "--expect-greedy", "0"],
                            judge_factory=synth.fake_factory({}, {}))
    assert rc == 2 and "the prepared set's manifest differs" in capsys.readouterr().err
    (prepared / "manifest.sha256").write_text(MANIFEST + "\n")
    other = tmp_path / "other"
    synth.make_unit(other / "retrieved", "hostZ", "u", manifest="f" * 64)
    rc = granite_files.main(["run", "--run-root", str(other / "retrieved"), "--prepared", str(prepared), "--manifest",
                             MANIFEST, "--cache", str(cache), "--expect-greedy", "0"],
                            judge_factory=synth.fake_factory({}, {}))
    assert rc == 2 and "manifest_sha256 is not the prepared manifest" in capsys.readouterr().err
    assert not cache.exists()


def test_prompt_missing_from_bank_refuses_without_text(tmp_path, capsys):
    retrieved = tmp_path / "retrieved"
    prepared = synth.make_bank(tmp_path, pids=PIDS[:2])
    synth.make_unit(retrieved, "hostA", "u")
    rc = harmbench_files.main(["run", *common_args(retrieved, prepared, tmp_path / "hb.jsonl"), *HB_ARGS],
                              judge_factory=synth.fake_factory({}, {}))
    io = capsys.readouterr()
    assert rc == 2 and "p-003" in io.err and "not in the bank" in io.err
    no_text(io.out, io.err)


def test_harmbench_count_and_prompt_set_checks(tmp_path, capsys):
    retrieved, prepared, units = env(tmp_path)
    cache = tmp_path / "hb.jsonl"
    rc = harmbench_files.main(["run", *common_args(retrieved, prepared, cache)], judge_factory=synth.fake_factory({}, {}))
    assert rc == 2 and "expected 200" in capsys.readouterr().err                # the default 200 / 600
    ev = units["hostA"] / "eval/e1"
    synth.write_jsonl(ev / "samples.jsonl", [{"kind": "harm", "prompt_id": "p-001", "sample_index": 0,
                                              "text": synth.answer("sampled", "p-001", 0)}])
    synth.seal(units["hostA"], target="e1", arm="a0", seed=1101, completed_utc="2026-10-08T01:00:00+00:00")
    rc = harmbench_files.main(["run", *common_args(retrieved, prepared, cache), *HB_ARGS],
                              judge_factory=synth.fake_factory({}, {}))
    assert rc == 2 and "sampled and greedy prompt ids differ" in capsys.readouterr().err


def test_judge_label_outside_rule_refuses(tmp_path, capsys):
    retrieved, prepared, _ = env(tmp_path)
    rc = granite_files.main(["run", *common_args(retrieved, prepared, tmp_path / "gr.jsonl"), "--expect-greedy", "0"],
                            judge_factory=synth.fake_factory({}, {}, default="maybe"))
    io = capsys.readouterr()
    assert rc == 2 and "label outside" in io.err
    no_text(io.out, io.err)


def test_no_prompt_or_answer_text_in_any_output(tmp_path, capsys):
    retrieved, prepared, _ = env(tmp_path, hosts=("hostA", "hostB"), distinct_seeds=True)
    leaky = lambda p, a: {"raw": a, "prompt": p}                          # a judge that returns text: never stored
    hb, gr, out, calls = tmp_path / "hb.jsonl", tmp_path / "gr.jsonl", tmp_path / "out", {}
    assert harmbench_files.main(["run", *common_args(retrieved, prepared, hb), *HB_ARGS],
                                judge_factory=synth.fake_factory({}, calls, extra=leaky)) == 0
    assert granite_files.main(["run", *common_args(retrieved, prepared, gr), "--expect-greedy", "0"],
                              judge_factory=synth.fake_factory({}, calls, extra=leaky)) == 0
    assert harmbench_files.main(["check", *common_args(retrieved, prepared, hb), *HB_ARGS],
                                judge_factory=synth.fake_factory({}, calls)) == 0
    assert granite_files.main(["check", *common_args(retrieved, prepared, gr), "--expect-greedy", "0"],
                              judge_factory=synth.fake_factory({}, calls)) == 0
    assert write("harmbench", retrieved, hb, out) == 0 and write("granite", retrieved, gr, out) == 0
    assert units_mod.main(["--run-root", str(retrieved)]) == 0
    io = capsys.readouterr()
    no_text(io.out, io.err, hb.read_bytes(), gr.read_bytes(), *(p.read_bytes() for p in out.iterdir()))
    # refusals that touch answers name ids only
    unit = next(retrieved.glob("hostA/tree/round1/*"))
    (unit / "eval/e1/generations.jsonl").write_bytes((unit / "eval/e1/generations.jsonl").read_bytes() + b"{}\n")
    for argv in (["--run-root", str(retrieved)],):
        assert units_mod.main(argv) == 2
    io = capsys.readouterr()
    assert "does not match its SHA-256" in io.err
    no_text(io.out, io.err)


# ------------------------------------------------------------------------------------------------ import

def _old_env(tmp_path):
    retrieved, prepared, units = env(tmp_path)
    init = synth.make_unit(retrieved, "hostA", "1101-a0-init-a1", target="init", completed_utc="2026-10-08T00:00:00+00:00")
    label_units = {"untuned": init, "e1-1101": units["hostA"]}
    return retrieved, label_units


def test_import_harmbench_maps_by_hash(tmp_path):
    retrieved, label_units = _old_env(tmp_path)
    labels = {("untuned", "sampled", "p-001", 1): "yes", ("e1-1101", "greedy", "p-002", None): "yes",
              ("e1-1101", "sampled", "p-003", 0): "unparsed"}
    synth.old_harmbench_cache(tmp_path / "old.jsonl", label_units, labels)
    synth.old_summary(tmp_path / "old-summary.json", label_units)
    found, _ = units_mod.enumerate_units([retrieved])
    summary = json.loads((tmp_path / "old-summary.json").read_text())
    new = cache_mod.Cache(tmp_path / "new.jsonl", HARMBENCH)
    rep = import_cache.import_old("harmbench", tmp_path / "old.jsonl", summary, found, {}, new)   # by job_sha256
    assert rep["imported"] == rep["added"] == 18 and rep["undecodable_old_lines"] == 0
    assert {k: v["complete_sha256"] for k, v in rep["labels"].items()} == {
        k: sha((u / "COMPLETE.json").read_bytes()) for k, u in label_units.items()}
    out = tmp_path / "out"
    assert write("harmbench", retrieved, tmp_path / "new.jsonl", out) == 0
    docs = {json.loads(p.read_bytes())["complete_sha256"]: json.loads(p.read_bytes()) for p in out.glob("harmbench--*")}
    init = docs[sha((label_units["untuned"] / "COMPLETE.json").read_bytes())]
    e1 = docs[sha((label_units["e1-1101"] / "COMPLETE.json").read_bytes())]
    assert init["greedy"] == {"n": 3, "harm": 0, "unparsed": 0} and init["sampled"] == {"n": 6, "harm": 1, "unparsed": 0}
    assert e1["greedy"] == {"n": 3, "harm": 1, "unparsed": 0} and e1["sampled"] == {"n": 6, "harm": 0, "unparsed": 1}
    rep = import_cache.import_old("harmbench", tmp_path / "old.jsonl", summary, found, {},
                                  cache_mod.Cache(tmp_path / "new.jsonl", HARMBENCH))
    assert rep["added"] == 0 and rep["already_present"] == 18           # idempotent
    recs = [json.loads(x) for x in (tmp_path / "new.jsonl").read_bytes().split(b"\n") if x.strip()]
    assert {r["source"] for r in recs} == {"import:" + sha((tmp_path / "old.jsonl").read_bytes())}


@pytest.mark.parametrize("case", ["answer_hash", "label_not_in_summary", "pin_unknown", "prompt_not_in_unit",
                                  "pinned_label_absent"])
def test_import_refuses_unmatched(tmp_path, case):
    retrieved, label_units = _old_env(tmp_path)
    synth.old_harmbench_cache(tmp_path / "old.jsonl", label_units, {})
    synth.old_summary(tmp_path / "old-summary.json", label_units)
    rows = [json.loads(x) for x in (tmp_path / "old.jsonl").read_bytes().split(b"\n") if x.strip()]
    summary = json.loads((tmp_path / "old-summary.json").read_text())
    pins = {}
    if case == "answer_hash":
        rows[3]["generation_sha256"] = "2" * 64
    elif case == "label_not_in_summary":
        del summary["units"]["untuned"]
    elif case == "pin_unknown":
        pins = {"untuned": "3" * 64}
    elif case == "prompt_not_in_unit":
        rows[0]["prompt_id"] = "p-404"
    elif case == "pinned_label_absent":
        pins = {"e1-1102": "4" * 64}
    synth.write_jsonl(tmp_path / "old.jsonl", rows)
    found, _ = units_mod.enumerate_units([retrieved])
    new = tmp_path / "new.jsonl"
    with pytest.raises(Refusal) as e:
        import_cache.import_old("harmbench", tmp_path / "old.jsonl", summary, found, pins,
                                cache_mod.Cache(new, HARMBENCH))
    assert case == "pinned_label_absent" or "unmatched" in str(e.value)
    no_text(e.value)
    assert not new.exists() or new.read_bytes() == b""                 # nothing written


def test_import_refuses_ambiguous(tmp_path):
    retrieved, prepared, units = env(tmp_path, hosts=("hostA", "hostB"))
    synth.seal(units["hostB"], target="e1", arm="a0", seed=1101, completed_utc="2026-10-09T09:09:09+00:00")
    found, _ = units_mod.enumerate_units([retrieved])
    synth.old_harmbench_cache(tmp_path / "old.jsonl", {"e1-1101": units["hostA"]}, {})
    synth.old_summary(tmp_path / "old-summary.json", {"e1-1101": units["hostA"]})
    summary = json.loads((tmp_path / "old-summary.json").read_text())
    new = tmp_path / "new.jsonl"
    with pytest.raises(Refusal, match="ambiguous: 2 units"):             # same job.json on two hosts, no pin
        import_cache.import_old("harmbench", tmp_path / "old.jsonl", summary, found, {}, cache_mod.Cache(new, HARMBENCH))
    pin = {"e1-1101": sha((units["hostA"] / "COMPLETE.json").read_bytes())}
    rep = import_cache.import_old("harmbench", tmp_path / "old.jsonl", summary, found, pin, cache_mod.Cache(new, HARMBENCH))
    assert rep["labels"]["e1-1101"]["unit"] == "hostA/round1/1101-a0-e1-a1" and rep["added"] == 9
    # two old records of one item with different labels
    rows = [json.loads(x) for x in (tmp_path / "old.jsonl").read_bytes().split(b"\n") if x.strip()]
    synth.write_jsonl(tmp_path / "old2.jsonl", rows + [dict(rows[0], label="yes")])
    with pytest.raises(Refusal, match="ambiguous: .*another label"):
        import_cache.import_old("harmbench", tmp_path / "old2.jsonl", summary, found, pin,
                                cache_mod.Cache(tmp_path / "new2.jsonl", HARMBENCH))
    # two old labels mapped to one unit
    synth.write_jsonl(tmp_path / "old3.jsonl", rows + [dict(r, unit="copy") for r in rows])
    summary3 = {"units": {"e1-1101": summary["units"]["e1-1101"], "copy": summary["units"]["e1-1101"]}}
    with pytest.raises(Refusal, match="ambiguous: old labels"):
        import_cache.import_old("harmbench", tmp_path / "old3.jsonl", summary3, found,
                                {"e1-1101": pin["e1-1101"], "copy": pin["e1-1101"]},
                                cache_mod.Cache(tmp_path / "new3.jsonl", HARMBENCH))
    # a new-cache record of the item with another label
    synth.write_jsonl(tmp_path / "old4.jsonl", [dict(r, label="yes") for r in rows])
    with pytest.raises(Refusal, match="already holds"):
        import_cache.import_old("harmbench", tmp_path / "old4.jsonl", summary, found, pin, cache_mod.Cache(new, HARMBENCH))


def test_import_granite_by_folder_name_and_target(tmp_path):
    retrieved, label_units = _old_env(tmp_path)
    init, e1 = label_units["untuned"], label_units["e1-1101"]
    kit = retrieved.parent                                               # the old cache sits in its kit, beside retrieved/
    synth.old_granite_cache(kit / "old.jsonl", [e1, init],
                            {("1101-a0-e1-a1", "p-001"): "yes", ("1101-a0-e1-a1", "p-002"): None,
                             ("1101-a0-init-a1", "p-003"): "yes"})
    synth.old_summary(tmp_path / "old-summary.json", {e1.name: e1, init.name: init})
    summary = json.loads((tmp_path / "old-summary.json").read_text())
    found, _ = units_mod.enumerate_units([retrieved])
    new = tmp_path / "new.jsonl"
    rep = import_cache.import_old("granite", kit / "old.jsonl", summary, found, {}, cache_mod.Cache(new, GRANITE))
    assert rep["added"] == 6
    out = tmp_path / "out"
    assert write("granite", retrieved, new, out) == 0
    docs = {json.loads(p.read_bytes())["complete_sha256"]: json.loads(p.read_bytes()) for p in out.glob("granite--*")}
    assert docs[sha((e1 / "COMPLETE.json").read_bytes())]["greedy"] == {"n": 3, "harm": 1, "unparsed": 1}
    assert docs[sha((init / "COMPLETE.json").read_bytes())]["greedy"] == {"n": 3, "harm": 1, "unparsed": 0}
    assert all(d["sampled"] is None for d in docs.values())
    no_text(new.read_bytes())
    assert b"<score>" not in new.read_bytes()                            # the old output tail is not imported
    rows = [json.loads(x) for x in (kit / "old.jsonl").read_bytes().split(b"\n") if x.strip()]
    rows[0]["target"] = "init"
    synth.write_jsonl(kit / "bad.jsonl", rows)
    with pytest.raises(Refusal, match="unmatched: .*target"):
        import_cache.import_old("granite", kit / "bad.jsonl", summary, found, {},
                                cache_mod.Cache(tmp_path / "new2.jsonl", GRANITE))


def test_import_cli_and_pin_syntax(tmp_path, capsys):
    retrieved, label_units = _old_env(tmp_path)
    synth.old_harmbench_cache(tmp_path / "old.jsonl", label_units, {})
    synth.old_summary(tmp_path / "old-summary.json", label_units)
    base = ["--judge", "harmbench", "--old-cache", str(tmp_path / "old.jsonl"), "--old-summary",
            str(tmp_path / "old-summary.json"), "--cache", str(tmp_path / "new.jsonl"), "--run-root", str(retrieved)]
    assert import_cache.main(base + ["--map", "untuned=xyz"]) == 2
    pins = [f"--map={k}={sha((u / 'COMPLETE.json').read_bytes())}" for k, u in label_units.items()]
    capsys.readouterr()
    assert import_cache.main(base + pins) == 0
    rep = json.loads(capsys.readouterr().out)
    assert rep["added"] == 18


# ------------------------------------------------------------------------------------------------ misc

def test_harmbench_label_rule():
    f = harmbench_files.label_from_token
    assert [f("Yes", True), f("no", True), f("NO", True), f(" yes", True), f("Yes", False), f("", True)] == \
        ["yes", "no", "no", "unparsed", "unparsed", "unparsed"]


def test_watchdog_rule_and_defaults():
    a = watchdog.parser().parse_args(["--pid", "1", "--log", "/dev/null"])
    assert (a.swap_gb, a.disk_gb, a.interval) == (8.0, 40.0, 20.0)
    assert watchdog.stop_reason(8.5, 100, 1, 8.0, 40.0).startswith("swap used")
    assert watchdog.stop_reason(1.0, 39, 1, 8.0, 40.0).startswith("free disk")
    assert watchdog.stop_reason(1.0, 100, 4, 8.0, 40.0).startswith("memory pressure")
    assert watchdog.stop_reason(8.0, 40.0, 2, 8.0, 40.0) is None


def test_cli_scripts_run_as_files_and_write_no_bytecode(tmp_path):
    retrieved, prepared, _ = env(tmp_path)
    cache, out = tmp_path / "gr.jsonl", tmp_path / "out"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    py = [sys.executable, "-B"]
    e = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    mods = synth.MODULES
    r = subprocess.run(py + [str(mods / "write_files.py"), "--judge", "granite", "--cache", str(cache), "--out", str(out),
                             "--run-root", str(retrieved)], capture_output=True, text=True, env=e, cwd=tmp_path)
    assert r.returncode == 0 and '"status": "written"' in r.stdout
    r = subprocess.run(py + [str(mods / "write_files.py"), "--judge", "granite", "--cache", str(tmp_path / "none.jsonl"),
                             "--out", str(out), "--run-root", str(retrieved)], capture_output=True, text=True, env=e)
    assert r.returncode == 2 and "no cache file" in r.stderr
    r = subprocess.run(py + [str(mods / "units.py"), "--run-root", str(retrieved)], capture_output=True, text=True, env=e)
    assert r.returncode == 0 and json.loads(r.stdout)["units"][0]["host"] == "hostA"
    no_text(r.stdout, r.stderr)
    assert not (mods / "__pycache__").exists() and not (mods / "tests" / "__pycache__").exists()


def test_heavy_libraries_never_imported():
    assert not {"torch", "transformers", "llama_cpp"} & set(sys.modules)


# ------------------------------------------------------------------------------------------------ review fixes (8 Oct)

import ast  # noqa: E402
import re  # noqa: E402
import time  # noqa: E402
import uuid  # noqa: E402

import judging  # noqa: E402
from common import bank_prompts  # noqa: E402

READING = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp/claude-workspaces/gate-b-engine-kit-reading-20261008/"
                       "workspace/scripts/gate_b_reading.py")


def reseal(unit, **kw):
    job = json.loads((unit / "job.json").read_text())
    synth.seal(unit, target=job["target_checkpoint"], arm=job["arm"], seed=job["seed"],
               completed_utc=kw.get("completed_utc", "2026-10-08T01:00:00+00:00"))


def rows_of(path):
    return [json.loads(x) for x in path.read_bytes().split(b"\n") if x.strip()]


# H1 / M2: run-root enumeration on pod trees, and the evaluate_bank rule

def test_units_evaluate_bank_rules(tmp_path):
    retrieved = tmp_path / "retrieved"
    retrain = synth.make_unit(retrieved, "hostA", "1101-a0-retrain", job_extra={"evaluate_bank": None})
    with pytest.raises(Refusal, match="not judgeable \\(evaluates no bank\\)"):      # named explicitly: refused
        units_mod.enumerate_units((), [retrain])
    absent = synth.make_unit(tmp_path / "r2", "hostA", "u-absent")                  # key absent = null: no bank
    job = json.loads((absent / "job.json").read_text())
    del job["evaluate_bank"]
    (absent / "job.json").write_text(json.dumps(job, sort_keys=True))
    reseal(absent)
    assert units_mod.enumerate_units([tmp_path / "r2"])[1][0]["reason"] == "evaluates no bank"
    other = synth.make_unit(tmp_path / "r3" / "retrieved", "hostA", "u-test", job_extra={"evaluate_bank": "test"})
    with pytest.raises(Refusal, match="evaluate_bank is not 'dev'"):
        units_mod.enumerate_units([tmp_path / "r3" / "retrieved"])
    with pytest.raises(Refusal, match="evaluate_bank is not 'dev'"):
        units_mod.enumerate_units((), [other])


def test_explicit_unit_without_job_json_still_refuses(tmp_path):
    preflight = tmp_path / "retrieved/hostA/tree/cuda-preflight-1"
    preflight.mkdir(parents=True)
    (preflight / "COMPLETE.json").write_text("{}")
    assert units_mod.enumerate_units([tmp_path / "retrieved"], ()) == ([], [
        {"host": "hostA", "unit": "cuda-preflight-1", "reason": units_mod.NOT_A_JOB_UNIT}])
    with pytest.raises(Refusal, match="no job.json"):
        units_mod.enumerate_units((), [preflight])


# job.json first: tool folders and no-bank units are skipped before COMPLETE.json is examined; identity.json rule

def test_units_tool_folders_skip_before_complete_format_and_identity_rule(tmp_path):
    retrieved = tmp_path / "retrieved"
    good = synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    tool = retrieved / "hostA/tree/round1/1101-score-rows"               # a score-rows tool folder: another format
    tool.mkdir(parents=True)
    (tool / "job.json").write_text(json.dumps({"kind": "score-rows", "seed": 1101}))
    (tool / "identity.json").write_text("{}")
    (tool / "COMPLETE.json").write_text(json.dumps([{"rows": 3}]))     # not an object, no files list
    retrain = synth.make_unit(retrieved, "hostA", "1101-a0-retrain", job_extra={"evaluate_bank": None})
    (retrain / "COMPLETE.json").write_text(json.dumps({"complete": True, "outputs": {}}))   # no files list, no job_sha256
    no_id = synth.make_unit(retrieved, "hostA", "1101-r1-e1-a1", arm="r1", identity=False)
    (no_id / "COMPLETE.json").write_text("not json")                    # never read: no identity.json, not an attempt
    unsealed_no_id = synth.make_unit(retrieved, "hostA", "1101-r2-e1-a1", arm="r2", identity=False)
    (unsealed_no_id / "COMPLETE.json").unlink()
    found, skipped = units_mod.enumerate_units([retrieved])
    assert [u.path for u in found] == [good]
    assert sorted((x["unit"], x["reason"]) for x in skipped) == [
        ("round1/1101-a0-retrain", units_mod.NO_BANK),
        ("round1/1101-r1-e1-a1", units_mod.NO_IDENTITY),
        ("round1/1101-r2-e1-a1", units_mod.NO_IDENTITY),
        ("round1/1101-score-rows", "job kind 'score-rows' is not run-one")]
    assert units_mod.NO_IDENTITY == "not an attempt (no identity.json)"
    assert units_mod.main(["--run-root", str(retrieved)]) == 0
    # named explicitly with --unit, each of them still refuses
    for unit, why in ((tool, "not judgeable \\(job kind 'score-rows' is not run-one\\)"),
                      (retrain, "not judgeable \\(evaluates no bank\\)"),
                      (no_id, "not judgeable \\(not an attempt \\(no identity.json\\)\\)"),
                      (unsealed_no_id, "no COMPLETE.json")):
        with pytest.raises(Refusal, match=why):
            units_mod.enumerate_units((), [unit])
    # a run-one dev unit with a defective COMPLETE.json still refuses the enumeration
    (good / "COMPLETE.json").write_text(json.dumps([]))
    with pytest.raises(Refusal, match="COMPLETE.json is not an object"):
        units_mod.enumerate_units([retrieved])


# H2: the judge identities are the frozen reading's

@pytest.mark.skipif(not READING.exists(), reason="the frozen reading is not on this machine")
def test_judge_identities_equal_the_frozen_reading():
    consts = {}
    for node in ast.parse(READING.read_text(encoding="utf-8")).body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            if node.targets[0].id in ("JUDGE_GRANITE", "JUDGE_HARMBENCH", "HARMBENCH_REVISION_PREFIX", "HARMBENCH_REVISION", "JUDGE_KIND"):
                consts[node.targets[0].id] = ast.literal_eval(node.value)
    assert GRANITE["name"] == consts["JUDGE_GRANITE"] == "granite-guardian-3.3-8b"
    assert HARMBENCH["name"] == consts["JUDGE_HARMBENCH"]
    if "HARMBENCH_REVISION" in consts:                                       # [D17] item 7: the full revision, exact
        assert HARMBENCH["revision"] == consts["HARMBENCH_REVISION"]
    else:                                                                    # before [D17]: the 8-hex prefix
        assert HARMBENCH["revision"].startswith(consts["HARMBENCH_REVISION_PREFIX"])
    assert write_files.KIND == consts["JUDGE_KIND"]
    assert GRANITE["revision"] == granite_files.GGUF_SHA256                   # the pinned GGUF file's SHA-256


# M1: Granite imports stay with the attempt they judged (the refuter's two-attempt case)

def _granite_kit(tmp_path):
    """A kit holding attempt A only, the old Granite cache made from A beside its retrieved/, and A's summary."""
    kit = tmp_path / "kit"
    retrieved = kit / "retrieved"
    a = synth.make_unit(retrieved, "hostA", "1101-a0-e1-a1")
    old = kit / "second-judge-probe-items.jsonl"
    synth.old_granite_cache(old, [a], {("1101-a0-e1-a1", "p-001"): "yes"})       # the old run judged attempt A
    synth.old_summary(tmp_path / "summary.json", {"1101-a0-e1-a1": a})
    return kit, retrieved, a, old, json.loads((tmp_path / "summary.json").read_text())


def test_import_granite_binds_records_to_the_judged_attempt(tmp_path):
    kit, retrieved, a, old, summary = _granite_kit(tmp_path)
    pin_a = sha((a / "COMPLETE.json").read_bytes())
    found, _ = units_mod.enumerate_units([retrieved])
    new = tmp_path / "new.jsonl"
    # pinned to the judged attempt, alone in its kit: accepted, every record on A's COMPLETE.json
    rep = import_cache.import_old("granite", old, summary, found, {"1101-a0-e1-a1": pin_a}, cache_mod.Cache(new, GRANITE))
    assert rep["added"] == 3 and {r["complete_sha256"] for r in rows_of(new)} == {pin_a}
    # a record whose guard fields were lost (or never written) is refused
    rows = rows_of(old)
    rows[1]["qwen_refusal"] = None
    synth.write_jsonl(kit / "lost.jsonl", rows)
    with pytest.raises(Refusal, match="Qwen3Guard labels differ"):
        import_cache.import_old("granite", kit / "lost.jsonl", summary, found, {"1101-a0-e1-a1": pin_a},
                                cache_mod.Cache(tmp_path / "new2.jsonl", GRANITE))
    # attempt C: A's copy, re-sealed, in another kit (identical guard rows): outside the old cache's kit
    c = shutil.copytree(a, tmp_path / "otherkit/retrieved/hostC/tree/round1/1101-a0-e1-a1")
    reseal(c, completed_utc="2026-10-10T10:10:10+00:00")
    found, _ = units_mod.enumerate_units([retrieved, tmp_path / "otherkit/retrieved"])
    pin_c = sha((c / "COMPLETE.json").read_bytes())
    new3 = tmp_path / "new3.jsonl"
    with pytest.raises(Refusal, match="unmatched: .*not under the old cache's kit"):
        import_cache.import_old("granite", old, summary, found, {"1101-a0-e1-a1": pin_c}, cache_mod.Cache(new3, GRANITE))
    assert not new3.exists() or new3.read_bytes() == b""
    # attempt B (same job.json, byte-identical answers, the guard label of p-002 differs) alone in a kit beside a copy
    # of the old cache (A was replaced by B after the old probe ran): the kit has one folder of that name, and the
    # guard rows tell B apart
    kit2 = tmp_path / "kit2"
    b = synth.make_unit(kit2 / "retrieved", "hostB", "1101-a0-e1-a1", completed_utc="2026-10-09T09:09:09+00:00",
                        guard_safety={"p-002": "Unsafe"})
    assert (a / "job.json").read_bytes() == (b / "job.json").read_bytes()
    assert (a / "eval/e1/generations.jsonl").read_bytes() == (b / "eval/e1/generations.jsonl").read_bytes()
    shutil.copyfile(old, kit2 / old.name)
    found, _ = units_mod.enumerate_units([kit2 / "retrieved"])
    new4 = tmp_path / "new4.jsonl"
    with pytest.raises(Refusal) as e:
        import_cache.import_old("granite", kit2 / old.name, summary, found, {"1101-a0-e1-a1": sha((b / "COMPLETE.json")
                                .read_bytes())}, cache_mod.Cache(new4, GRANITE))
    assert "Qwen3Guard labels differ" in str(e.value) and "p-002" in str(e.value)
    no_text(e.value)
    assert not new4.exists() or new4.read_bytes() == b""
    # the residual limit (README): a kit whose one folder of that name holds another attempt D with guard rows
    # identical to A's cannot be told apart by a Granite record
    kit3 = tmp_path / "kit3"
    d = synth.make_unit(kit3 / "retrieved", "hostD", "1101-a0-e1-a1", completed_utc="2026-10-11T11:11:11+00:00")
    shutil.copyfile(old, kit3 / old.name)
    found, _ = units_mod.enumerate_units([kit3 / "retrieved"])
    rep = import_cache.import_old("granite", kit3 / old.name, summary, found,
                                  {"1101-a0-e1-a1": sha((d / "COMPLETE.json").read_bytes())},
                                  cache_mod.Cache(tmp_path / "new5.jsonl", GRANITE))
    assert rep["added"] == 3


@pytest.mark.parametrize("second", ["identical_guard_rows", "other_guard_rows"])
def test_import_granite_refuses_two_folders_of_one_name_in_the_kit(tmp_path, second):
    """The old probe's own rule (second_judge_probe.discover_units refused a unit name found on more than one host):
    a second attempt of the unit in the same kit refuses, whichever attempt is pinned. With identical guard rows this
    was the accepted Granite-import limit before; it now refuses."""
    kit, retrieved, a, old, summary = _granite_kit(tmp_path)
    second_unit = synth.make_unit(retrieved, "hostD", "1101-a0-e1-a1", completed_utc="2026-10-11T11:11:11+00:00",
                                  guard_safety=None if second == "identical_guard_rows" else {"p-002": "Unsafe"})
    if second == "identical_guard_rows":
        assert (a / "eval/e1/guard.jsonl").read_bytes() == (second_unit / "eval/e1/guard.jsonl").read_bytes()
    found, _ = units_mod.enumerate_units([retrieved])
    new = tmp_path / "new.jsonl"
    with pytest.raises(Refusal, match="ambiguous: 2 units"):                     # no pin: two units have that job.json
        import_cache.import_old("granite", old, summary, found, {}, cache_mod.Cache(new, GRANITE))
    for unit in (a, second_unit):
        pin = {"1101-a0-e1-a1": sha((unit / "COMPLETE.json").read_bytes())}
        with pytest.raises(Refusal, match="ambiguous: 2 folders named '1101-a0-e1-a1'") as e:
            import_cache.import_old("granite", old, summary, found, pin, cache_mod.Cache(new, GRANITE))
        no_text(e.value)
    assert not new.exists() or new.read_bytes() == b""
    # a unit folder whose name is not the old label is not the kit's folder of that name
    renamed = tmp_path / "kit4/retrieved/hostA/tree/round1/1101-a0-e1-a1-copy"
    shutil.copytree(a, renamed)
    shutil.copyfile(old, tmp_path / "kit4" / old.name)
    found, _ = units_mod.enumerate_units([tmp_path / "kit4/retrieved"])
    with pytest.raises(Refusal, match="unmatched: no folder named '1101-a0-e1-a1'"):
        import_cache.import_old("granite", tmp_path / "kit4" / old.name, summary, found, {},
                                cache_mod.Cache(tmp_path / "new4.jsonl", GRANITE))


# L1: one file per (judge, arm, seed, target) in one --out; the --complete allowlist; the index entries

def test_one_out_holds_one_file_per_judge_arm_seed_target(tmp_path, capsys):
    retrieved, prepared, units = env(tmp_path, hosts=("hostA", "hostB"))
    reseal(units["hostB"], completed_utc="2026-10-09T09:09:09+00:00")
    found, _ = units_mod.enumerate_units([retrieved])
    a, b = sorted(found, key=lambda u: u.host)
    cache, out = tmp_path / "gr.jsonl", tmp_path / "out"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    capsys.readouterr()
    assert write("granite", retrieved, cache, out) == 2                      # two attempts, no --complete
    assert "has 2 attempts" in capsys.readouterr().err and not list(out.glob("granite--*"))
    for extra, msg in ((["--complete", "e" * 64], "no given unit"), (["--complete", "xyz"], "64 lowercase hex"),
                       (["--complete", a.complete_sha256, "--complete", b.complete_sha256], "named now: 2")):
        assert write("granite", retrieved, cache, out, extra) == 2
        assert msg in capsys.readouterr().err and not list(out.glob("granite--*"))
    assert write("granite", retrieved, cache, out, ["--complete", a.complete_sha256]) == 0
    lines = [json.loads(x) for x in capsys.readouterr().out.splitlines() if x.startswith("{")]
    assert {(r["unit"], r["status"]) for r in lines if "status" in r} == {
        (a.label, "written"), (b.label, write_files.NOT_NAMED)}
    assert [p.name for p in out.glob("granite--*")] == [write_files.file_name("granite", a)]
    index = json.loads((out / write_files.INDEX).read_bytes())
    assert index["complete_allowlist"] == [a.complete_sha256]
    assert [(e["unit"], e["target"], e["completed_utc"], e["complete_sha256"]) for e in index["files"]] == [
        ("round1/1101-a0-e1-a1", "e1", "2026-10-08T01:00:00+00:00", a.complete_sha256)]
    # naming B into the same --out later: A's file is already there, so it refuses until A's file is moved aside
    assert write("granite", retrieved, cache, out, ["--complete", b.complete_sha256]) == 2
    assert "move it aside" in capsys.readouterr().err
    # the untuned init unit and the a0 e1 unit of seed 1101 share arm and seed but not target: both fit one --out
    synth.make_unit(retrieved, "hostA", "1101-a0-init-a1", target="init", completed_utc="2026-10-08T00:00:00+00:00")
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    assert write("granite", retrieved, cache, out, ["--complete", a.complete_sha256]) == 0
    index = json.loads((out / write_files.INDEX).read_bytes())
    assert sorted((e["arm"], e["seed"], e["target"]) for e in index["files"]) == [("a0", 1101, "e1"), ("a0", 1101, "init")]


def test_index_keeps_entries_of_files_whose_units_are_not_given(tmp_path, capsys):
    retrieved, prepared, units = env(tmp_path, hosts=("hostA", "hostB"), distinct_seeds=True)
    cache, out = tmp_path / "gr.jsonl", tmp_path / "out"
    assert run_gr(retrieved, prepared, cache, {}, {}) == 0
    assert write("granite", retrieved, cache, out) == 0
    full = json.loads((out / write_files.INDEX).read_bytes())
    assert len(full["files"]) == 2 and all(set(e) == write_files.ENTRY_KEYS for e in full["files"])
    (out / ".DS_Store").write_bytes(b"\x00\x01")                              # ignored in --out
    only_a = ["--judge", "granite", "--cache", str(cache), "--out", str(out), "--unit", str(units["hostA"])]
    assert write_files.main(only_a) == 0
    assert json.loads((out / write_files.INDEX).read_bytes())["files"] == full["files"]   # B's entry carried over
    (out / write_files.INDEX).unlink()
    capsys.readouterr()
    assert write_files.main(only_a) == 2                                      # B's file: no unit, no index entry
    assert "previous index has no entry" in capsys.readouterr().err
    assert write("granite", retrieved, cache, out) == 0                       # both units given again: fine
    b_file = next(out.glob("granite--hostB--*.json"))
    b_file.write_bytes(b_file.read_bytes().replace(b'"seed": 1102', b'"seed": 1103'))
    assert write("granite", retrieved, cache, out) == 2                       # a file that disagrees with its unit


# README step 5b: the reading's judges list is built by name from judge-files-index.json, never from a glob

def _readme_recipe() -> str:
    s = (synth.MODULES / "README.md").read_text(encoding="utf-8")
    a = s.index("```bash\npython3 -B - \"$KIT/judges\" $ACCEPTED <<'EOF'") + len("```bash\n")
    return s[a:s.index("EOF\n```\n", a) + len("EOF\n")]


def test_readme_judges_list_comes_from_the_index_by_name(tmp_path):
    retrieved, prepared, units = env(tmp_path, hosts=("hostA", "hostB"), distinct_seeds=True)
    kit = tmp_path / "kit"
    out = kit / "judges"
    assert run_gr(retrieved, prepared, tmp_path / "gr.jsonl", {}, {}) == 0
    assert run_hb(retrieved, prepared, tmp_path / "hb.jsonl", {}, {}) == 0
    assert write("granite", retrieved, tmp_path / "gr.jsonl", out) == 0
    assert write("harmbench", retrieved, tmp_path / "hb.jsonl", out) == 0
    a, b = (sha((units[h] / "COMPLETE.json").read_bytes()) for h in ("hostA", "hostB"))
    stray = next(out.glob("granite--hostA--*.json"))
    shutil.copyfile(stray, out / (stray.stem + " copy.json"))             # a Finder-style copy: a glob would take it
    recipe = _readme_recipe()

    def run(*accepted):
        return subprocess.run(["bash", "-c", recipe], capture_output=True, text=True, cwd=tmp_path, timeout=60,
                              env=dict(os.environ, KIT=str(kit), ACCEPTED=" ".join(accepted)))
    r = run(a)
    assert r.returncode == 0, r.stderr[-300:]
    index = json.loads((out / write_files.INDEX).read_bytes())["files"]
    assert json.loads(r.stdout) == {"judges": [str(out / e["file"]) for e in index if e["complete_sha256"] == a]}
    assert len(json.loads(r.stdout)["judges"]) == 2 and len(list(out.glob("granite--hostA--*.json"))) == 2
    r = run(a, b)
    assert r.returncode == 0 and len(json.loads(r.stdout)["judges"]) == 4
    assert all(" copy" not in x for x in json.loads(r.stdout)["judges"])
    assert run().returncode == 1 and "no accepted COMPLETE.json SHA-256 given" in run().stderr
    r = run(a, "e" * 64)
    assert r.returncode == 1 and "2 accepted (judge, attempt) pair(s) have no file" in r.stderr
    gone = out / write_files.file_name("harmbench", units_mod.enumerate_units([retrieved])[0][1])
    gone.unlink()                                                         # listed in the index, gone from disk
    r = run(a, b)
    assert r.returncode == 1 and f"{gone.name} is missing or differs from its index SHA-256" in r.stderr
    no_text(r.stdout, r.stderr)


# L2: every answer id is among the guard records' ids

@pytest.mark.parametrize("case", ["greedy_row_missing", "sampled_row_missing", "no_guard_samples_file"])
def test_answers_without_guard_records_refuse(tmp_path, capsys, case):
    retrieved, prepared, units = env(tmp_path)
    ev = units["hostA"] / "eval/e1"
    if case == "greedy_row_missing":
        synth.write_jsonl(ev / "guard.jsonl", [r for r in rows_of(ev / "guard.jsonl") if r["prompt_id"] != "p-002"])
        want = "prompt p-002 sample None"
    elif case == "sampled_row_missing":
        synth.write_jsonl(ev / "guard_samples.jsonl",
                          [r for r in rows_of(ev / "guard_samples.jsonl") if (r["prompt_id"], r["sample_index"]) != ("p-003", 1)])
        want = "prompt p-003 sample 1"
    else:
        (ev / "guard_samples.jsonl").unlink()
        want = "no guard_samples.jsonl"
    reseal(units["hostA"])
    rc = harmbench_files.main(["check", *common_args(retrieved, prepared, tmp_path / "hb.jsonl"), *HB_ARGS],
                              judge_factory=synth.fake_factory({}, {}))
    io = capsys.readouterr()
    assert rc == 2 and want in io.err
    if case != "no_guard_samples_file":
        assert "not among the guard records' ids" in io.err
    no_text(io.out, io.err)


# L5: every refusal path of units.load_items names ids only; no text names reach raise/print calls

@pytest.mark.parametrize("case", ["duplicate_id", "missing_sample_index", "non_harm_sampled_row", "missing_prompt_id",
                                  "not_an_object", "not_json"])
def test_load_items_refusals_name_ids_only(tmp_path, case):
    retrieved = tmp_path / "retrieved"
    unit = synth.make_unit(retrieved, "hostA", "u")
    ev = unit / "eval/e1"
    gens, samp = rows_of(ev / "generations.jsonl"), rows_of(ev / "samples.jsonl")
    mode, phrase = "greedy", ""
    if case == "duplicate_id":
        gens.append(dict(gens[0]))
        phrase = "holds prompt p-001 sample None twice"
    elif case == "missing_sample_index":
        del samp[2]["sample_index"]
        mode, phrase = "sampled", "line 3 has no integer sample_index"
    elif case == "non_harm_sampled_row":
        samp[1]["kind"] = "overrefusal"
        mode, phrase = "sampled", "line 2 is not a harm answer"
    elif case == "missing_prompt_id":
        del gens[1]["prompt_id"]
        phrase = "line 2 has no string prompt_id"
    synth.write_jsonl(ev / "generations.jsonl", gens)
    synth.write_jsonl(ev / "samples.jsonl", samp)
    if case == "not_an_object":
        (ev / "generations.jsonl").write_bytes((ev / "generations.jsonl").read_bytes()
                                               + json.dumps([MARK_A, "list"]).encode() + b"\n")
        phrase = "line 5 is not an object"
    elif case == "not_json":
        (ev / "generations.jsonl").write_bytes((ev / "generations.jsonl").read_bytes() + f"{MARK_A} cut".encode() + b"\n")
        phrase = "line 5 is not JSON"
    reseal(unit)
    (u,), _ = units_mod.enumerate_units([retrieved])
    with pytest.raises(Refusal) as e:
        units_mod.load_items(u, mode, with_text=True)
    assert phrase in str(e.value)
    no_text(e.value, repr(e.value))


TEXT_NAMES = frozenset({"text", "prompt", "prompts", "answer", "answers", "response", "responses", "generation",
                        "raw", "output", "out", "messages", "content", "clipped", "tail", "guard_answer"})
# Records and pairs that hold text: one of these names passed whole into a sink (not through .attr, [key] or len())
# leaks every field it holds.
WHOLE_NAMES = frozenset({"pair", "pairs", "rec"})
SINKS = frozenset({"print", "log", "emit", "write", "Refusal", "SystemExit", "refuse"})


def text_names_in_sinks(source: str) -> list:
    """(line, name) for every text-like name inside a raise or an output call's arguments (keyword names included),
    every string constant equal to a text-like name there (r["text"], r.get("text"), {"raw": ...}), and every
    record/pair name passed whole into one."""
    bad = []
    for node in ast.walk(ast.parse(source)):
        roots = []
        if isinstance(node, ast.Raise) and node.exc is not None:
            roots.append((node.exc, node))
        if isinstance(node, ast.Call):
            f = node.func
            if (f.attr if isinstance(f, ast.Attribute) else f.id if isinstance(f, ast.Name) else None) in SINKS:
                roots += [(a, node) for a in node.args] + [(k.value, node) for k in node.keywords]
                bad += [(node.lineno, k.arg) for k in node.keywords if k.arg in TEXT_NAMES]
        for root, sink in roots:
            parent = {root: sink}
            for n in ast.walk(root):
                for child in ast.iter_child_nodes(n):
                    parent[child] = n
            for n in ast.walk(root):
                name = n.id if isinstance(n, ast.Name) else n.attr if isinstance(n, ast.Attribute) else None
                if name in TEXT_NAMES:
                    bad.append((node.lineno, name))
                if isinstance(n, ast.Constant) and isinstance(n.value, str) and n.value in TEXT_NAMES:
                    bad.append((node.lineno, repr(n.value)))
                if isinstance(n, ast.Name) and n.id in WHOLE_NAMES:
                    p = parent[n]
                    # through .attr, [key], len() or a division (a record cannot be divided: harmbench_files'
                    # VERBATIM load_judge logs `rec / 1024 ** 3`, rec = torch.mps.recommended_max_memory(), a number);
                    # "%" formatting and every other use count as whole
                    # a Pair (pair/pairs) holds prompt and answer text, so only .attr passes for it; a positional
                    # subscript of a pair is text (lead's fix, 8 Oct); rec may still pass through [key]
                    through = ((isinstance(p, ast.Attribute) and p.value is n)
                               or (isinstance(p, ast.Subscript) and p.value is n and n.id == "rec")
                               or (isinstance(p, ast.Call) and isinstance(p.func, ast.Name) and p.func.id == "len"
                                   and n in p.args)
                               or (isinstance(p, ast.BinOp) and isinstance(p.op, (ast.Div, ast.FloorDiv))
                                   and p.left is n))
                    if not through:
                        bad.append((node.lineno, n.id))
    return bad


def test_no_text_names_in_raise_or_print_calls():
    for snippet in ('raise Refusal(f"x {it.text}")', "print(prompt)", "log(n=len(answer))", "log(text=1)",
                    'emit(json.dumps({"a": out}))', 'raise SystemExit("x %s" % response)',
                    'raise Refusal(f"x {r[\'text\']}")', 'print(r.get("text"))', 'log(**{"raw": 1})',
                    'emit(json.dumps({"guard_answer": g}))', "print(rec)", 'raise Refusal(f"{pair}")',
                    "log(items=pairs)", 'fh.write(json.dumps(rec) + "\\n")', 'raise Refusal(str([rec]))',
                    'raise Refusal("x %s" % rec)', 'log(n=f(tok, pairs))', 'raise Refusal(f"{1 / rec}")'):
        assert text_names_in_sinks(snippet), snippet                         # the check sees each kind of leak
    for clean in ('raise Refusal(f"{u.label}: prompt {it.prompt_id} sample {it.sample_index}")',
                  'raise Refusal(f"{pair.where} ({n} tokens)")', 'log(items=len(pairs), label=rec["label"])',
                  'raise Refusal(f"{rec[\'prompt_id\']}: has no string prompt_id and text")',
                  "log(gib=round(rec / 1024 ** 3, 2))"):
        assert not text_names_in_sinks(clean), clean
    files = sorted(synth.MODULES.glob("*.py"))
    assert len(files) == 10
    found = {p.name: text_names_in_sinks(p.read_text(encoding="utf-8")) for p in files}
    assert {k: v for k, v in found.items() if v} == {}


# L3 (HarmBench side): the pre-load length check names the item

def test_harmbench_factory_input_is_ids_plus_texts(tmp_path):
    retrieved, prepared, _ = env(tmp_path)
    (u,), _ = units_mod.enumerate_units([retrieved])
    seen = []

    def factory(pairs):
        seen.extend(pairs)
        return lambda p, a: {"label": "no"}
    judging.run([u], ("greedy",), bank_prompts(prepared, MANIFEST), factory,
                cache_mod.Cache(tmp_path / "c.jsonl", HARMBENCH))
    assert [p.where for p in seen] == [f"hostA/round1/1101-a0-e1-a1 greedy prompt {pid} sample None" for pid in PIDS]
    no_text(*(p.where for p in seen))
    assert all(MARK_P in p.prompt and MARK_A in p.answer for p in seen)


# L4: pinned packages, importlib.metadata only

def test_require_packages_reads_metadata_only(monkeypatch):
    versions = {"torch": "2.8.0", "transformers": "4.56.2"}

    def fake_version(dist):
        if dist not in versions:
            raise judging.metadata.PackageNotFoundError(dist)
        return versions[dist]
    monkeypatch.setattr(judging.metadata, "version", fake_version)
    assert judging.require_packages(harmbench_files.PACKAGES) == versions
    with pytest.raises(Refusal, match="llama-cpp-python is not installed"):
        judging.require_packages(granite_files.PACKAGES)
    versions["transformers"] = "4.57.0"
    with pytest.raises(Refusal, match="transformers is 4.57.0 .* not the pinned 4.56.2"):
        judging.require_packages(harmbench_files.PACKAGES)
    del versions["torch"]
    with pytest.raises(Refusal, match="torch is not installed"):
        judging.require_packages(harmbench_files.PACKAGES)
    assert judging.require_packages({"transformers": None}) == {"transformers": "4.57.0"}
    assert not {"torch", "transformers", "llama_cpp"} & set(sys.modules)


@pytest.mark.parametrize("module", [harmbench_files, granite_files], ids=["harmbench", "granite"])
def test_real_main_checks_packages_first(tmp_path, monkeypatch, capsys, module):
    monkeypatch.setattr(judging.metadata, "version", lambda dist: "0.0.0")
    rc = module.main(["run", "--run-root", str(tmp_path / "absent"), "--cache", str(tmp_path / "c.jsonl")])
    err = capsys.readouterr().err
    assert rc == 2 and "is 0.0.0" in err and "run root" not in err and not (tmp_path / "c.jsonl").exists()


def test_this_venv_has_the_harmbench_pins():
    try:
        judging.metadata.version("torch")
    except judging.metadata.PackageNotFoundError:
        pytest.skip("not the minimal venv")
    assert judging.require_packages(harmbench_files.PACKAGES) == harmbench_files.PACKAGES


# M3: the Mac GPU lock and the other-judge check (fake lock holders; never the real lock file)

def _holder(lock):
    code = ("import fcntl, sys, time; f = open(sys.argv[1], 'a'); fcntl.flock(f, fcntl.LOCK_EX); "
            "print('locked', flush=True); time.sleep(60)")
    p = subprocess.Popen([sys.executable, "-B", "-c", code, str(lock)], stdout=subprocess.PIPE, text=True)
    assert p.stdout.readline().strip() == "locked"
    return p


def test_gpu_lock_refuses_while_another_process_holds_it(tmp_path):
    lock, marker = tmp_path / "mac-gpu.lock", f"no-such-judge-{uuid.uuid4().hex}"
    assert lock != judging.GPU_LOCK
    holder = _holder(lock)
    try:
        with pytest.raises(Refusal, match="is held by another process"):
            judging.take_gpu_lock(lock, pattern=marker)
    finally:
        holder.kill()
        holder.wait()
    try:
        judging.take_gpu_lock(lock, pattern=marker)                          # free now: taken and kept
        assert lock.read_text().strip() == str(os.getpid())
        judging.take_gpu_lock(lock, pattern=marker)                          # held by this process: no error
        code = "import fcntl, sys; f = open(sys.argv[1], 'a'); fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)"
        assert subprocess.run([sys.executable, "-B", "-c", code, str(lock)], capture_output=True).returncode != 0
    finally:
        judging.release_gpu_lock(lock)


def test_gpu_lock_refuses_while_another_judge_process_runs(tmp_path):
    lock, marker = tmp_path / "mac-gpu.lock", f"second_judge_probe-fake-{uuid.uuid4().hex}"
    fake = subprocess.Popen([sys.executable, "-B", "-c", "import time; time.sleep(60)", marker])
    try:
        deadline = time.time() + 10
        while fake.pid not in judging.other_judges(marker) and time.time() < deadline:
            time.sleep(0.1)
        with pytest.raises(Refusal, match=f"another Mac judge process is running \\(pid {fake.pid}\\)"):
            judging.take_gpu_lock(lock, pattern=marker)
    finally:
        fake.kill()
        fake.wait()
    holder_free = subprocess.run([sys.executable, "-B", "-c",
                                  "import fcntl, sys; f = open(sys.argv[1], 'a'); fcntl.flock(f, fcntl.LOCK_EX | fcntl.LOCK_NB)",
                                  str(lock)], capture_output=True)
    assert holder_free.returncode == 0                                       # the refusal released the lock
    # a process whose own command line (or its parent shell's) matches is not "another" judge
    code = (f"import sys; sys.path.insert(0, {str(synth.MODULES)!r}); import judging; "
            f"judging.take_gpu_lock({str(lock)!r}, pattern={marker!r}); print('ok')")
    r = subprocess.run(["/bin/sh", "-c", f"{sys.executable} -B -c \"{code}\" {marker}; true"], capture_output=True,
                       text=True)
    assert r.stdout.strip() == "ok", r.stderr[-300:]
    pat = re.compile(judging.OTHER_JUDGES)
    for cmd in ("../judge-venv/bin/python second_judge_probe.py", "python -B /k/harmbench_files.py run --cache c",
                "python -B /k/granite_files.py check --cache c", "python harmbench_judge.py smoke"):
        assert pat.search(cmd), cmd
    for cmd in ("python -B /k/watchdog.py --pid 1 --tag watchdog-granite", "bash /k/run_granite.sh L -- run --cache c",
                "python -B /k/tests/test_granite_files.py /tmp/bt"):
        assert not pat.search(cmd), cmd


def test_forced_gpu_guard_stops_the_run_before_the_factory(tmp_path):
    retrieved, prepared, _ = env(tmp_path)
    found, _ = units_mod.enumerate_units([retrieved])
    lock, marker = tmp_path / "mac-gpu.lock", f"no-such-judge-{uuid.uuid4().hex}"
    cache, calls = tmp_path / "hb.jsonl", {}
    holder = _holder(lock)
    try:
        with pytest.raises(Refusal, match="is held by another process"):
            judging.run(found, ("greedy", "sampled"), bank_prompts(prepared, MANIFEST), synth.fake_factory({}, calls),
                        cache_mod.Cache(cache, HARMBENCH), gpu_guard=lambda: judging.take_gpu_lock(lock, pattern=marker))
    finally:
        holder.kill()
        holder.wait()
    assert calls == {} and (not cache.exists() or cache.read_bytes() == b"")


def test_real_harmbench_run_takes_the_gpu_lock_before_the_factory(tmp_path, monkeypatch, capsys):
    retrieved, prepared, _ = env(tmp_path)
    monkeypatch.setattr(judging, "require_packages", lambda pins: {})
    monkeypatch.setattr(harmbench_files, "SNAPSHOT", tmp_path)                 # a real main requires the snapshot folder
    events, calls = [], {}

    def held():
        events.append("lock")
        raise Refusal("fake: the GPU lock is held")
    monkeypatch.setattr(judging, "take_gpu_lock", held)
    monkeypatch.setattr(harmbench_files, "harmbench_judge", lambda pairs: events.append("factory"))
    argv = ["run", *common_args(retrieved, prepared, tmp_path / "hb.jsonl"), *HB_ARGS]
    assert harmbench_files.main(argv) == 2 and events == ["lock"]
    assert "fake: the GPU lock is held" in capsys.readouterr().err
    fake = synth.fake_factory({}, calls)
    monkeypatch.setattr(judging, "take_gpu_lock", lambda: events.append("lock taken"))
    monkeypatch.setattr(harmbench_files, "harmbench_judge", lambda pairs: (events.append("factory"), fake(pairs))[1])
    assert harmbench_files.main(argv) == 0 and events == ["lock", "lock taken", "factory"] and calls["judged"] == 9
    monkeypatch.setattr(judging, "take_gpu_lock", held)                         # a fake factory never takes the lock
    assert run_hb(retrieved, prepared, tmp_path / "hb2.jsonl", {}, {}) == 0 and events[-1] == "factory"


# Exit 5: a run stopped by SIGTERM (the watchdog) before its last item

@pytest.mark.parametrize("module", [harmbench_files, granite_files], ids=["harmbench", "granite"])
def test_main_returns_5_when_stopped_by_sigterm(tmp_path, capsys, module):
    import signal
    retrieved, prepared, _ = env(tmp_path)
    cache, calls = tmp_path / "c.jsonl", {}
    before = signal.getsignal(signal.SIGTERM)

    def term_on_second(prompt, ans):                     # the watchdog's SIGTERM arrives while item 2 is judged
        if calls["judged"] == 2:
            os.kill(os.getpid(), signal.SIGTERM)
        return {}
    args = ["run", *common_args(retrieved, prepared, cache),
            *(HB_ARGS if module is harmbench_files else ["--expect-greedy", "0"])]
    capsys.readouterr()
    assert module.main(args, judge_factory=synth.fake_factory({}, calls, extra=term_on_second)) == 5
    done = [json.loads(x) for x in capsys.readouterr().out.splitlines() if '"run_done"' in x][0]
    assert done["stopped"] is True and done["judged"] == 2 and calls["judged"] == 2
    assert len(rows_of(cache)) == 2 and signal.getsignal(signal.SIGTERM) == before
    total = 9 if module is harmbench_files else 3
    assert module.main(args, judge_factory=synth.fake_factory({}, calls)) == 0      # resumed: the rest, exit 0
    assert calls["judged"] == total and len(rows_of(cache)) == total
    assert module.main(args, judge_factory=synth.fake_factory({}, calls)) == 0      # nothing left: exit 0
    assert calls["judged"] == total


# L6: the launchers validate SWAP_GB and stop the judge when the watchdog is not alive

FAKE_JUDGE = """import os, sys, time
a = sys.argv[1:]
open(a[a.index("--pidfile") + 1], "w").write(str(os.getpid()))
time.sleep(float(a[a.index("--sleep") + 1]))
sys.exit(int(a[a.index("--exit") + 1]) if "--exit" in a else 0)
"""
FAKE_WATCHDOG = """import os, subprocess, sys, time
a = sys.argv[1:]
pid = int(a[a.index("--pid") + 1])
if os.environ.get("FAKE_WATCHDOG") == "dead":
    sys.exit(0)
while True:                       # exits once the judge has ended (gone or a zombie), as the real watchdog does
    st = subprocess.run(["ps", "-p", str(pid), "-o", "stat="], capture_output=True, text=True).stdout.strip()
    if not st or st.startswith("Z"):
        break
    time.sleep(0.2)
"""


def _launcher(tmp_path, script):
    """A copy of the launcher that differs in its interpreter and pgrep pattern only, beside a fake judge and a fake
    watchdog; returns launch(logdir, swap, sleep, watchdog, exit_code) -> (CompletedProcess, pidfile, log path)."""
    src = (synth.MODULES / script).read_text()
    lines, changed = [], 0
    for line in src.splitlines(keepends=True):
        if line.startswith("PY="):
            line, changed = f"PY={sys.executable}\n", changed + 1
        elif line.startswith("JUDGES="):
            line, changed = f"JUDGES='no-such-judge-{uuid.uuid4().hex}'\n", changed + 1
        lines.append(line)
    assert changed == 2
    kit = tmp_path / "kit"
    kit.mkdir()
    (kit / script).write_text("".join(lines))
    (kit / ("granite_files.py" if "granite" in script else "harmbench_files.py")).write_text(FAKE_JUDGE)
    (kit / "watchdog.py").write_text(FAKE_WATCHDOG)
    tag = "granite" if "granite" in script else "harmbench"

    def launch(logdir, swap, sleep, watchdog, exit_code=0):
        pidfile = tmp_path / f"{logdir}.pid"
        r = subprocess.run(["bash", str(kit / script), str(tmp_path / logdir), swap, "--", "run", "--pidfile",
                            str(pidfile), "--sleep", sleep, "--exit", str(exit_code)], capture_output=True, text=True,
                           timeout=60, env=dict(os.environ, FAKE_WATCHDOG=watchdog))
        return r, pidfile, tmp_path / logdir / f"{tag}-run.log"
    return launch, tag


@pytest.mark.parametrize("script", ["run_granite.sh", "run_harmbench.sh"])
def test_launcher_swap_gb_and_watchdog_liveness(tmp_path, script):
    launch, tag = _launcher(tmp_path, script)
    for bad in ("abc", "0", "0.0", "-1", "8GB", "1e3"):
        r, pidfile, _ = launch("bad", bad, "30", "alive")
        assert r.returncode == 2 and "SWAP_GB must be a positive number" in r.stdout, bad
        assert not pidfile.exists() and not (tmp_path / "bad").exists()
    t0 = time.time()
    r, pidfile, logp = launch("dead", "8", "30", "dead")                     # the judge keeps running, the watchdog died
    assert r.returncode == 4 and time.time() - t0 < 20
    pid = int(pidfile.read_text())
    with pytest.raises(ProcessLookupError):
        os.kill(pid, 0)                                                      # the judge was stopped
    log = logp.read_text()
    assert "WATCHDOG NOT ALIVE" in log and f"END {tag} exit=4" in log
    r, pidfile, logp = launch("ok", "8.5", "2.5", "alive")
    log = logp.read_text()
    assert r.returncode == 0 and f"END {tag} exit=0" in log and "WATCHDOG NOT ALIVE" not in log


@pytest.mark.parametrize("script", ["run_granite.sh", "run_harmbench.sh"])
def test_launcher_passes_the_judges_own_exit_code(tmp_path, script):
    """A judge that ends before the 2 s liveness check takes its watchdog with it; the launcher must report the judge's
    own exit code (0 done, 2 refused, 5 stopped), never exit 4."""
    launch, tag = _launcher(tmp_path, script)
    for logdir, sleep, watchdog, code in (("quick0", "0", "alive", 0), ("quick2", "0", "alive", 2),
                                          ("quick2-dead-watchdog", "0", "dead", 2), ("stopped5", "2.5", "alive", 5)):
        r, pidfile, logp = launch(logdir, "8", sleep, watchdog, code)
        log = logp.read_text()
        assert r.returncode == code, (logdir, r.returncode)
        assert f"END {tag} exit={code} (GPU free)" in log and "WATCHDOG NOT ALIVE" not in log, logdir
        assert pidfile.exists()


# L8: HarmBench's lower-only rule equals "strip, then lower" on every single decoded token

@pytest.mark.skipif(not (harmbench_files.SNAPSHOT / "tokenizer.model").exists(), reason="no HarmBench tokenizer.model")
def test_harmbench_rule_needs_no_strip_on_the_pinned_vocabulary():
    data = (harmbench_files.SNAPSHOT / "tokenizer.model").read_bytes()
    assert sha(data) == harmbench_files.TOKENIZER_MODEL_SHA256
    proto = harmbench_files._SpmModel()
    proto.ParseFromString(data)
    assert len(proto.pieces) == 32000
    differ = []
    for i, piece in enumerate(proto.pieces):
        s = piece.piece.replace("▁", " ")
        s = s[1:] if s.startswith(" ") else s          # the Llama decoder strips one leading space
        if (harmbench_files.label_from_token(s, True) != "unparsed") != (s.strip().lower() in ("yes", "no")):
            differ.append(i)
    assert differ == []
