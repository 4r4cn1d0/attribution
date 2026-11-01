"""Synthetic fixtures for the Part F tests (REQ-19, W1-05, W1-18), and tests of the fixtures themselves.

Nothing here reads real data. Units are written in the shapes the engine writes (job.json, COMPLETE.json with its
file list, eval/<ck>/summary.json, query_loss.jsonl, guard.jsonl, generations.jsonl, samples.jsonl) at the real
Gate A and development paths, under a temporary data root. Every text field holds a synthetic sentinel string that
the tests search for in every output (no text may leak).

The O design (the hand case of REQ-19's end-to-end test; 100 prompts p000-p099):
theta0 refuses p000-p016 (17). a0 1101 refuses {p000, p017, p018, p019} (4); a0 1102 refuses {p000, p001, p017,
p018, p020, p021} (6); a0 1103 refuses {p001, p017, p022, p023} (4). The task losses alternate around exact binary
means: theta0 2.0, a0 1101 1.0, 1102 1.25, 1103 1.5 (so s_L = 0.25 exactly).
"""

from __future__ import annotations

import copy
import json
import math
from pathlib import Path

from experiments.safety_selection.common import canonical_json, jsonl_bytes, sha256_bytes
from scripts.stage1 import s1common as s1

SETTINGS_DIR = Path(s1.__file__).resolve().parent / "settings"
GATE_A_IDENTITY = {"code_sha256": "552538748acec1a8ffd1ee976b9eb3c3fdfe9ca01b8148ee8810291409357441",
                   "recipe_sha256": "9e9bde6f2f32876098410479883deff5ef3141e471a79ed231c7a5db15ad399b",
                   "manifest_sha256": "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"}
RECIPE_S = "ceffe0efb5d75bacfbd62743f530259deeedeca8950605d1bd3ff66e5391fe46"
QUERY_BANK = "ab31576dab2f7bd530268a38146ce9339342ed7e7c77cf58127df579ea22ee87"
O_IDS = [f"p{i:03d}" for i in range(100)]
HARM_IDS = [f"h{i:03d}" for i in range(200)]
QUERY_IDS = [f"q{i:03d}" for i in range(200)]
THETA0_REFUSES = set(O_IDS[:17])
A0_REFUSES = {"1101": {"p000", "p017", "p018", "p019"},
              "1102": {"p000", "p001", "p017", "p018", "p020", "p021"},
              "1103": {"p001", "p017", "p022", "p023"}}
LOSS_MEANS = {"untuned": 2.0, "1101": 1.0, "1102": 1.25, "1103": 1.5}
SENTINELS: list[str] = []


def sentinel(tag: str) -> str:
    text = f"Synthetic sentinel text {tag}: the lighthouse keeper counts gulls at dawn."
    SENTINELS.append(text)
    return text


def real_settings(name: str) -> dict:
    return json.loads((SETTINGS_DIR / f"{name}.json").read_bytes())


def write_file(folder: Path, rel: str, data: bytes, listed: dict) -> None:
    path = folder / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    listed[rel] = sha256_bytes(data)


def write_unit(data_root: Path, rel: str, *, seed: int, checkpoint: str, arm: str = "a0",
               identity: dict | None = None, guard: list[dict] | None = None, losses: list[float] | None = None,
               generations: list[dict] | None = None, samples: list[dict] | None = None,
               overrefusal_summary: dict | None = None, query_bank: str = QUERY_BANK) -> dict:
    """One sealed unit. Returns its pins {complete_sha256, job_sha256, summary_sha256, query_loss_sha256}."""
    folder = data_root / rel
    folder.mkdir(parents=True, exist_ok=True)
    listed: dict[str, str] = {}
    job = {"kind": "run-one", "arm": arm, "seed": seed, "target_checkpoint": checkpoint, "evaluate_bank": "dev",
           **(identity if identity is not None else GATE_A_IDENTITY)}
    write_file(folder, "job.json", canonical_json(job), listed)
    ev = f"eval/{checkpoint}"
    pins: dict[str, str] = {"job_sha256": listed["job.json"]}
    summary: dict = {"checkpoint": checkpoint}
    mean = None
    if losses is not None:
        write_file(folder, f"{ev}/query_loss.jsonl",
                   jsonl_bytes({"query_id": q, "loss": v, "tokens": 7} for q, v in zip(QUERY_IDS, losses)), listed)
        mean = math.fsum(losses) / len(losses)
        summary["query_loss"] = {"mean": mean, "n": len(losses), "query_bank_sha256": query_bank}
        pins["query_loss_sha256"] = listed[f"{ev}/query_loss.jsonl"]
    if guard is not None:
        write_file(folder, f"{ev}/guard.jsonl", jsonl_bytes(guard), listed)
        over = [g for g in guard if g["kind"] == "overrefusal"]
        summary["overrefusal"] = overrefusal_summary if overrefusal_summary is not None else {
            "n": len(over), "refusals": sum(g["valid"] and g["refusal"] == "Yes" for g in over), "refusal_rate": None}
    if generations is not None:
        write_file(folder, f"{ev}/generations.jsonl", jsonl_bytes(generations), listed)
    if samples is not None:
        write_file(folder, f"{ev}/samples.jsonl", jsonl_bytes(samples), listed)
    write_file(folder, f"{ev}/summary.json", canonical_json(summary), listed)
    pins["summary_sha256"] = listed[f"{ev}/summary.json"]
    complete = {"kind": "run-one", "complete": True, "files": listed,
                "evaluation": {"query_loss": {"mean": mean}} if mean is not None else {}}
    data = canonical_json(complete)
    (folder / "COMPLETE.json").write_bytes(data)
    pins["complete_sha256"] = sha256_bytes(data)
    return pins


def guard_records(refuses: set[str], invalid: set[str] = frozenset(), harm: int = 3) -> list[dict]:
    """guard.jsonl in the engine's shape: a few harm records, then the 100 over-refusal records."""
    out = [{"prompt_id": HARM_IDS[i], "kind": "harm", "item_id": HARM_IDS[i], "valid": True, "safety": "Safe",
            "refusal": "No", "categories": [], "guard_answer": sentinel(f"guard harm {i}")} for i in range(harm)]
    for pid in O_IDS:
        valid = pid not in invalid
        out.append({"prompt_id": pid, "kind": "overrefusal", "item_id": pid, "valid": valid,
                    "safety": "Safe" if valid else None, "refusal": ("Yes" if pid in refuses else "No") if valid else None,
                    "categories": [], "guard_answer": sentinel(f"guard {pid}")})
    return out


def alternating(mean: float, n: int = 200, half: float = 0.25) -> list[float]:
    return [mean - half if i % 2 == 0 else mean + half for i in range(n)]


def gate_a_generations(tag: str) -> list[dict]:
    """Greedy answers with sentinel text (REQ-19 must never read them)."""
    return [{"prompt_id": pid, "kind": "overrefusal", "output_ids": [3, 4], "text": sentinel(f"{tag} answer {pid}"),
             "stop_reason": "eos"} for pid in O_IDS]


def build_gate_a(data_root: Path) -> dict:
    """The four allow-listed Gate A units of the O design. Returns a test settings doc for limits_check whose pins
    and known answer fit them (the real settings with the synthetic pins)."""
    settings = real_settings("limits_check")
    refuses = {"untuned": THETA0_REFUSES, **A0_REFUSES}
    for name, spec in settings["units"].items():
        pins = write_unit(data_root, spec["path"], seed=spec["seed"], checkpoint=spec["checkpoint"],
                          guard=guard_records(refuses[name]), losses=alternating(LOSS_MEANS[name]),
                          generations=gate_a_generations(name))
        spec.update(pins)
    settings["tau_l"]["known_answer"] = {"s": 0.25, "tau_l": 0.5 * 2 ** 0.5, "se_one_difference": 0.25 * 2 ** 0.5,
                                         "se_6v6": 0.25 * (1 / 3) ** 0.5, "source": "the synthetic fixture"}
    return settings


def resettle(settings: dict, data_root: Path, name: str) -> None:
    """Re-pin one unit after a test changed its files (COMPLETE.json rewritten over the files on disk)."""
    spec = settings["units"][name]
    folder = data_root / spec["path"]
    listed = {}
    for path in sorted(folder.rglob("*")):
        if path.is_file() and path.name != "COMPLETE.json":
            listed[path.relative_to(folder).as_posix()] = sha256_bytes(path.read_bytes())
    marker = json.loads((folder / "COMPLETE.json").read_bytes())
    marker["files"] = listed
    data = canonical_json(marker)
    (folder / "COMPLETE.json").write_bytes(data)
    spec["complete_sha256"] = sha256_bytes(data)
    spec["job_sha256"] = listed["job.json"]
    ck = spec["checkpoint"]
    for field, rel in (("summary_sha256", f"eval/{ck}/summary.json"), ("query_loss_sha256", f"eval/{ck}/query_loss.jsonl")):
        if rel in listed:
            spec[field] = listed[rel]


# ----- W1-05: the untuned unit's greedy answers ------------------------------------------------------------------

STRATA_REFUSE_HARM = 30
STRATA_REFUSE_OVER = 12


def strata_texts() -> tuple[list[dict], list[dict]]:
    """(generations, samples): harm h000-h199 (the first 30 refusal-opening), over-refusal p000-p099 (the first 12
    refusal-opening; p099 empty), plus safety rows that must be ignored; the samples are all refusal-opening."""
    gens = []
    for i, pid in enumerate(HARM_IDS):
        head = "SYN-REF " if i < STRATA_REFUSE_HARM else "SYN-OK "
        gens.append({"prompt_id": pid, "kind": "harm", "output_ids": [1], "text": head + sentinel(f"greedy {pid}"),
                     "stop_reason": "eos"})
    for i, pid in enumerate(O_IDS):
        text = "" if pid == "p099" else ("SYN-REF " if i < STRATA_REFUSE_OVER else "SYN-OK ") + sentinel(f"greedy {pid}")
        gens.append({"prompt_id": pid, "kind": "overrefusal", "output_ids": [1], "text": text, "stop_reason": "eos"})
    for i in range(5):
        gens.append({"prompt_id": f"s{i:03d}", "kind": "safety", "output_ids": [1], "text": "SYN-REF " + sentinel(f"safety {i}"),
                     "stop_reason": "eos"})
    samples = [{"prompt_id": pid, "kind": "harm", "sample_index": k, "output_ids": [1],
                "text": "SYN-REF " + sentinel(f"sample {pid} {k}"), "stop_reason": "eos"} for pid in HARM_IDS for k in range(3)]
    return gens, samples


def fake_classify(text: str, sensitivity: bool = False) -> str:
    """A stand-in for the pinned lexicon in logic tests (the real lexicon is tested apart)."""
    if not text.strip():
        return "EMPTY"
    return "REFUSAL-OPENING" if text.startswith("SYN-REF") or text.startswith("w5") else "DIRECT"


def fake_lexicon():
    from scripts.stage1.limits import limits_common as lc

    return lc.Lexicon(fake_classify, "test/fake-lexicon.json", "test/fake-lexicon.py", "a" * 64, "b" * 64, False,
                      ("CAVEAT-OPENING", "DIRECT", "EMPTY", "REFUSAL-OPENING"))


def build_untuned(data_root: Path) -> dict:
    settings = real_settings("limits_untuned_strata")
    gens, samples = strata_texts()
    spec = settings["unit"]
    pins = write_unit(data_root, spec["path"], seed=1101, checkpoint="init", guard=guard_records(set()),
                      losses=alternating(2.0), generations=gens, samples=samples)
    spec.update({k: pins[k] for k in ("complete_sha256", "job_sha256")})
    return settings


# ----- W1-18: the over-refusal checks ----------------------------------------------------------------------------

MARK_YES, MARK_NO, MARK_INVALID, MARK_LEX, FILL = 7, 8, 9, 5, 3


def fake_decode(ids) -> str:
    return " ".join(f"w{i}" for i in ids)


def fake_judge_records(items):
    """Refusal Yes when the answer holds w7 and not w8; invalid when it holds w9; the guard answer is sentinel text
    (it must be dropped)."""
    out = []
    for item_id, _prompt, text in items:
        words = set(text.split())
        if "w9" in words:
            out.append({"item_id": item_id, "valid": False, "refusal": None, "safety": None,
                        "guard_answer": "Synthetic judge output that must never be stored"})
            continue
        yes = "w7" in words and "w8" not in words
        out.append({"item_id": item_id, "valid": True, "refusal": "Yes" if yes else "No", "safety": "Safe",
                    "guard_answer": "Synthetic judge output that must never be stored"})
    return out


def answer_ids(*, lex: bool = False, yes_at: int | None = None, no_at: int | None = None, invalid: bool = False,
               length: int = 20) -> list[int]:
    ids = [FILL] * length
    if lex:
        ids[0] = MARK_LEX
    if yes_at is not None:
        ids[yes_at] = MARK_YES
    if no_at is not None:
        ids[no_at] = MARK_NO
    if invalid:
        ids[2] = MARK_INVALID
    return ids


def checks_unit_design(kind: str) -> dict[str, list[int]]:
    """prompt id -> output ids. A: 2 answers lose their refusal at the cut (agree 98, move 2: pass), with the
    lexicon and agreement design; B: 3 lose it (agree 97, move 3: fail); C: 2 lose and 2 gain (agree 96, move 0:
    fail); D: 2 lose, 1 gains (agree 97, move 1: pass); E: one marker at index 128 exactly (lost at a 128 cap);
    G: 3 GAIN a refusal at the cut and none loses one (agree 97, move 3 upwards: fail); S: the cap boundary, answers
    of exactly 128 tokens (p010 refused, p012 not) and one of 129 tokens (p011 refused, judged at the cut)."""
    design = {pid: answer_ids() for pid in O_IDS}
    if kind == "A":
        for i in range(10):
            design[O_IDS[i]] = answer_ids(lex=True, yes_at=1 if i < 8 else None)
        design["p020"] = answer_ids(yes_at=1)
        design["p021"] = answer_ids(yes_at=1)
        design["p030"] = answer_ids(yes_at=150, length=200)
        design["p031"] = answer_ids(yes_at=150, length=200)
        design["p040"] = answer_ids(invalid=True)
    elif kind in ("B", "C", "D"):
        lose = {"B": 3, "C": 2, "D": 2}[kind]
        gain = {"B": 0, "C": 2, "D": 1}[kind]
        for i in range(lose):
            design[O_IDS[50 + i]] = answer_ids(yes_at=140, length=180)
        for i in range(gain):
            design[O_IDS[70 + i]] = answer_ids(yes_at=1, no_at=150, length=180)
    elif kind == "E":
        design["p060"] = answer_ids(yes_at=128, length=160)
    elif kind == "G":
        for i in range(3):
            design[O_IDS[80 + i]] = answer_ids(yes_at=1, no_at=150, length=180)
    elif kind == "S":
        design["p010"] = answer_ids(yes_at=1, length=128)
        design["p011"] = answer_ids(yes_at=1, length=129)
        design["p012"] = answer_ids(length=128)
    return design


def write_prepared(folder: Path, files: dict[str, bytes], extra: dict | None = None) -> str:
    """A prepared folder: the files, manifest.json naming their hashes (plus extra fields) and manifest.sha256."""
    for name, data in files.items():
        (folder / name).parent.mkdir(parents=True, exist_ok=True)
        (folder / name).write_bytes(data)
    manifest = canonical_json({"kind": "safety-selection prepared manifest", **(extra or {}),
                               "files": {name: sha256_bytes(data) for name, data in files.items()}})
    (folder / "manifest.json").write_bytes(manifest)
    (folder / "manifest.sha256").write_text(sha256_bytes(manifest) + "\n", encoding="ascii")
    return sha256_bytes(manifest)


def build_checks(data_root: Path, kinds: dict[str, str]) -> tuple[dict, dict[str, dict[str, list[int]]], Path]:
    """The bank source prepared set (its dev bank and an auditor map of prompt sources), the prepared set P (a
    re-tokenized copy of that dev bank: the same ids and prompts, other token fields, so other bytes; its own auditor
    without a prompts map; and bank_import naming the source and its dev bank hash), and one unit per name with
    the design of kinds[name]. Returns (a test settings doc for overrefusal_checks naming only these units, the
    designs, the bank source folder)."""
    settings = real_settings("limits_overrefusal_checks")
    bank = [{"prompt_id": pid, "kind": "harm", "prompt": sentinel(f"harm prompt {pid}")} for pid in HARM_IDS[:5]]
    bank += [{"prompt_id": pid, "kind": "overrefusal", "prompt": sentinel(f"benign prompt {pid}")} for pid in O_IDS]
    bank_bytes = jsonl_bytes({**item, "prompt_tokens": 7} for item in bank)          # the bank source's tokenizer
    p_bank_bytes = jsonl_bytes({**item, "prompt_tokens": 9} for item in bank)        # P's re-tokenized copy
    auditor = canonical_json({"kind": "AUDITOR ONLY: synthetic", "prompts": {
        pid: {"bank": "dev", "kind": "overrefusal", "source": "xstest" if i < 50 else "orbench", "record": i}
        for i, pid in enumerate(O_IDS)} | {"hidden-1": {"bank": "hidden", "kind": "overrefusal", "source": "orbench"}}})
    source = data_root / "bank-source-prepared"
    source_sha256 = write_prepared(source, {"banks/dev.jsonl": bank_bytes, "auditor/construction.json": auditor})
    p_auditor = canonical_json({"kind": "AUDITOR ONLY: Dolly lines and categories (synthetic)", "rows": {}})
    prep = data_root / settings["prepared"]["path"]
    settings["prepared"]["manifest_sha256"] = write_prepared(
        prep, {"banks/dev.jsonl": p_bank_bytes, "auditor/construction.json": p_auditor},
        {"bank_import": {"source_manifest_sha256": source_sha256, "files": {"banks/dev.jsonl": sha256_bytes(bank_bytes)},
                         "retokenized": ["banks/dev.jsonl"]}})
    settings["source_map"]["extraction"]["bank_source_manifest_sha256"] = source_sha256
    real_units = settings["units"]
    settings["units"] = {}
    designs = {}
    for name, kind in kinds.items():
        spec = copy.deepcopy(real_units[name])
        design = checks_unit_design(kind)
        designs[name] = design
        gens = [{"prompt_id": pid, "kind": "overrefusal", "output_ids": design[pid], "text": fake_decode(design[pid]),
                 "stop_reason": "eos"} for pid in O_IDS]
        sealed = fake_judge_records([(pid, "", fake_decode(design[pid])) for pid in O_IDS])
        if kind == "A":                                        # one device difference: the pod said No on p020
            sealed[20] = {**sealed[20], "refusal": "No"}
        guard = [{"prompt_id": pid, "kind": "overrefusal", **{k: v for k, v in rec.items() if k != "item_id"}}
                 for pid, rec in zip(O_IDS, sealed)]
        pins = write_unit(data_root, spec["path"], seed=spec["seed"], checkpoint=spec["checkpoint"],
                          identity={**GATE_A_IDENTITY, "recipe_sha256": "c" * 64}, guard=guard, generations=gens)
        spec.update({k: pins[k] for k in ("complete_sha256", "job_sha256")})
        settings["units"][name] = spec
    return settings, designs, source


SOURCE_MAP_REL = "sealed-maps/dev_overrefusal_source_map.json"
RULING = "the lead's synthetic ruling for the tests"


def seal_source_map(settings: dict, data_root: Path, source: Path, rel: str = SOURCE_MAP_REL) -> bytes:
    """The lead's one-time extraction on the synthetic sets: the map written at rel under the data root and pinned
    in the test settings (mode sealed_map). Returns the map's bytes."""
    from scripts.stage1.limits import overrefusal_checks as orc

    data = orc.extract_source_map(settings, "e" * 64, data_root, source, RULING)
    path = data_root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    settings["source_map"]["sealed_map"].update(path=rel, sha256=sha256_bytes(data))
    return data


# ----- tests of the fixtures -------------------------------------------------------------------------------------


def test_the_o_design_has_the_gate_a_counts():
    assert len(THETA0_REFUSES) == 17 and [len(A0_REFUSES[s]) for s in ("1101", "1102", "1103")] == [4, 6, 4]
    assert all(p in O_IDS for v in A0_REFUSES.values() for p in v)


def test_a_synthetic_unit_is_sealed_by_the_frozen_reader(tmp_path):
    from scripts.stage1.limits import limits_common as lc

    settings = build_gate_a(tmp_path)
    reader = lc.frozen_reader(settings["frozen_reader"])
    for spec in settings["units"].values():
        reader.sealed(tmp_path / spec["path"])
    assert sorted(settings["units"]) == ["1101", "1102", "1103", "untuned"]
