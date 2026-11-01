"""The inputs of the human-label-check draw, each verified before it is used (LN-31; HLC 4.1, 4.3 item 1, 8).

Order (LN-31: the draw reads block-A guard files only after block B is complete): the kit's plan.json (plan A), block
A's and block B's seals (sources.Kit.seal: plan.json's entry, the seal file at its SHA-256, a version-1 seal of that
block; seal.py records a seal only for a complete block), the inputs outside the kit by their pins (the 9 Oct key,
the prepared-v3 bank manifest, the dev bank and the auditor file), and only then any unit folder.

**Units** (HLC 4.1): each (arm, seed) of the settings' population from exactly one source, as the B16 input builder
reads it: a0 and R at the reused seeds from block A's re-judged units (stage1_rules.REJUDGED_PINS, by path,
COMPLETE.json and job.json SHA-256); every other cell from block A's table (stage1_rules.block_runs): the one
complete, pulled ``arm`` (``a0_arm`` for a0) job of that (arm, seed) on a done host of block A, its unit keyed by the
COMPLETE.json SHA-256 that plan.json records and checked against block A's seal; theta0 from its pin (checkpoint
init). Every file is read through ``Folder.file`` (listed by COMPLETE.json, by the seal for a kit unit, and hashing to
it). Of each unit only these fields are kept: the sampled answers' prompt id, sample index, output tokens and stop
reason (``samples.jsonl``) and their guard record's valid flag, safety label, categories and reason
(``guard_samples.jsonl``), lined up one to one, exactly 3 per prompt, the prompts exactly the dev bank's 200 harm
prompts, the counts equal to summary.json's harm.sampled block; the greedy over-refusal answers' prompt id,
output tokens and stop reason (``generations.jsonl``, kind overrefusal) and their guard record's valid flag, refusal
label, categories and reason (``guard.jsonl``, kind overrefusal), one per prompt, the prompts exactly the dev bank's
100 over-refusal prompts, the counts equal to summary.json's overrefusal block; and, for the minors rule only (HLC 8
(b): "any Qwen3Guard category of its answers"), the greedy harm answers' guard categories (``guard.jsonl``, kind
harm), one record per prompt, the prompts exactly the dev bank's 200 harm prompts, the counts equal to summary.json's
harm.greedy block. No text field is kept.

**HarmBench** (HLC 4.2): block A's judge files index as the builder checks it (build.judge_check, keyed by the
population's units) and its sealed label cache (hb.block_labels); each unit's labels cover exactly its sampled
answers, 3 per harm prompt, and their counts equal the unit's HarmBench judge file (hb.shares, hb.judge_file_counts).

**Bank and auditor** (HLC 8): the prepared-v3 manifest at the settings' pin (the kt data config's banks_from), the dev
bank at the manifest's and the settings' SHA-256, the auditor file at the manifest's; the bank's prompt text is kept in
memory for the term match only; the auditor file gives each population prompt's source and category, and it must name
rule a's source and category for some prompt of any bank (else rule a's names do not match the auditor's: refused).

**The 9 Oct key** (HLC 4.1 (a)): at its pre-registered SHA-256; only its units' unit_dir and complete_json_sha256 and
its items' unit, prompt_id and sample_index are read.

Messages hold names, paths, counts and hashes only; never a text, a label or a per-unit value.
"""

from __future__ import annotations

import dataclasses
from dataclasses import dataclass, field
from pathlib import Path

from scripts.stage1_s1.reading.settings import Refusal, strict_json
from scripts.stage1_s1.reading_input import build, hb
from scripts.stage1_s1.reading_input import items as it
from scripts.stage1_s1.reading_input.sources import Folder, Kit, pinned_folder, read_bytes, sha256_bytes

HARM, BENIGN = "harm", "benign"
SAFETY = ("Unsafe", "Controversial", "Safe")       # experiments/safety_selection/textproc.GUARD_SAFETY
REFUSAL = ("Yes", "No")                              # textproc.GUARD_REFUSAL
REUSED_ARMS = ("a0", "R")                           # build.cell_blocks: a0 and R at stage1_rules.REUSED_SEEDS
BANK_MANIFEST_KIND = "safety-selection prepared manifest"
PER_PROMPT = it.SAMPLES_PER_PROMPT


@dataclass(frozen=True)
class Answer:
    """One answer, reduced at once to the fields the draw uses (no text)."""
    block: str                                   # "harm" (sampled) or "benign" (greedy over-refusal)
    prompt_id: str
    sample_index: int | None                     # None for a greedy answer
    label: str | None                            # the cell label (safety or refusal); None when the record is invalid
    categories: tuple
    safety: str | None
    refusal: str | None
    reason: str | None
    output_tokens: int
    capped: bool
    harmbench: str | None = None                 # the sampled answer's HarmBench label (harm only)


@dataclass
class Unit:
    label: str                                   # "a0 1101", "S4 1104", "theta0"
    arm: str
    seed: int | None
    source: str                                  # "pinned" or "kit"
    path: str                                    # the pin's repository path, or "kit:HOST/UNIT"
    folder: Folder
    target: str
    harm: list = field(default_factory=list)
    benign: list = field(default_factory=list)
    greedy_harm: dict = field(default_factory=dict)    # harm prompt id -> its greedy answer's guard categories


def norm(text: str) -> str:
    """Lower case, every run of whitespace one space (the minors rule's match form)."""
    return " ".join(str(text).lower().split())


@dataclass
class Bank:
    harm: dict                                   # prompt id -> prompt text (memory only)
    benign: dict
    category: dict                               # prompt id -> (source, category) from the auditor file
    hashes: dict                                 # what was read, by SHA-256


# ----- the kit ------------------------------------------------------------------------------------------------------


def open_kit(kit_root: Path, cfg: dict) -> Kit:
    """plan.json at plan A's code and both seals (LN-31), before anything else of the kit is read."""
    kit = Kit(kit_root)
    if kit.plan_code() != cfg["plan_code"]:
        raise Refusal(f"plan.json records plan {kit.plan_code()}; the draw is fixed for plan {cfg['plan_code']} "
                      "(HLC 4.1: under plan B, L1 and S3 do not run, and no plan-B draw is built)")
    for block in cfg["blocks"]["sealed_before_any_unit_is_opened"]:
        kit.seal(block)                          # refuses an unsealed block: block B must be complete (LN-31)
    return kit


def _job_fields(folder: Folder, want: dict, marker: bool) -> None:
    """job.json against the fields plan.json (or the pin) fixes; a kit unit's COMPLETE.json names it (job_sha256)."""
    job = folder.job(marker=marker)
    wrong = sorted(k for k, v in want.items() if job.get(k) != v)
    if wrong:
        raise Refusal(f"{folder.label}: job.json's {', '.join(wrong)} differ from the unit the draw needs")


def _pinned(repo: Path, pins: dict, arm: str, seed, cfg: dict) -> Unit:
    name = arm if seed is None else f"{arm} {seed}"
    pin = pins.get((arm, seed))
    if pin is None:
        raise Refusal(f"{name}: no pin in REJUDGED_PINS['A']")
    folder = pinned_folder(repo, pin)
    target = cfg["theta0"]["target"] if arm == cfg["theta0"]["name"] else cfg["checkpoint"]
    if pin.get("target") != target or (seed is not None and pin.get("seed") != seed):
        raise Refusal(f"{folder.label}: the pin is not {name} at checkpoint {target}")
    _job_fields(folder, {"arm": pin.get("arm"), "seed": pin.get("seed"), "target_checkpoint": target}, marker=False)
    return Unit(name, arm, seed, "pinned", pin["path"], folder, target)


def _kit_unit(kit: Kit, jobs: dict, arm: str, seed: int, cfg: dict) -> Unit:
    block = cfg["blocks"]["read"]
    kind = "a0_arm" if arm == "a0" else "arm"
    found = jobs.get((kind, arm, seed), [])
    if len(found) != 1:
        raise Refusal(f"{arm} at {seed}: {len(found)} complete, pulled {kind} units in block {block} (the draw needs "
                      "one)")
    host, i, job = found[0]
    label, where = f"{arm} {seed}", f"kit:{host}/{job.get('unit')}"
    folder = kit.folder(block, host, job.get("unit"), job.get("complete_sha256"), f"{label} {where}")
    want = "a0" if arm == "a0" else build.engine_arm(job)
    _job_fields(folder, {"kind": "run-one", "arm": want, "seed": seed, "target_checkpoint": cfg["checkpoint"],
                         "evaluate_bank": "dev", "split": "dev"}, marker=True)
    return Unit(label, arm, seed, "kit", where, folder, cfg["checkpoint"])


def population(kit: Kit, repo: Path, rules, cfg: dict) -> list[Unit]:
    """The settings' units in draw order (module doc); COMPLETE.json and job.json are read, no evaluation file."""
    pins = build.pins_by_cell(rules)
    table = set(rules.block_runs(cfg["plan_code"], cfg["blocks"]["read"]))
    scanned = build.scan(kit, (cfg["blocks"]["read"],))
    jobs: dict = {}
    for _, host, i, job in [*scanned.get("arm", []), *scanned.get("a0_arm", [])]:
        jobs.setdefault((job.get("kind"), job.get("arm"), job.get("seed")), []).append((host, i, job))
    reused = set(rules.REUSED_SEEDS)
    out = []
    for arm in cfg["arms"]:
        for seed in cfg["seeds"][arm]:
            if arm in REUSED_ARMS and seed in reused:
                out.append(_pinned(repo, pins, arm, seed, cfg))
            elif (arm, seed) in table:
                out.append(_kit_unit(kit, jobs, arm, seed, cfg))
            else:
                raise Refusal(f"{arm} at {seed} is neither a reused pin nor a cell of block "
                              f"{cfg['blocks']['read']}'s table (the draw reads block {cfg['blocks']['read']} only)")
    out.append(_pinned(repo, pins, cfg["theta0"]["name"], None, cfg))
    seen = [u.folder.complete_sha256 for u in out]
    if len(set(seen)) != len(seen):
        raise Refusal("two cells of the population name one unit (one COMPLETE.json SHA-256)")
    return out


# ----- one unit's answers -------------------------------------------------------------------------------------------


def _count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _categories(value, where: str) -> tuple:
    if value is None:
        return ()
    if not isinstance(value, list) or not all(isinstance(c, str) for c in value):
        raise Refusal(f"{where}: a guard record's categories are not a list of names")
    return tuple(value)


def _label(rec: dict, labels: tuple, field_name: str, where: str) -> str | None:
    """The cell label of a valid guard record (its safety or refusal field), None for an invalid record."""
    if not isinstance(rec["valid"], bool):
        raise Refusal(f"{where}: a guard record has no boolean valid")
    if not rec["valid"]:
        return None
    if rec[field_name] not in labels:
        raise Refusal(f"{where}: a valid guard record has no {field_name} label of {'/'.join(labels)}")
    return rec[field_name]


def _text_or_none(value, where: str, what: str):
    if value is not None and not isinstance(value, str):
        raise Refusal(f"{where}: a guard record's {what} is not a text or null")
    return value


def _answer(block: str, gen: dict, guard: dict, labels: tuple, field_name: str, where: str) -> Answer:
    if not _count(gen["output_tokens"]) or not isinstance(gen["stop_reason"], str):
        raise Refusal(f"{where}: an answer has no output token count or stop reason")
    return Answer(block, gen["prompt_id"], gen.get("sample_index"), _label(guard, labels, field_name, where),
                  _categories(guard["categories"], where), _text_or_none(guard["safety"], where, "safety"),
                  _text_or_none(guard["refusal"], where, "refusal"), _text_or_none(guard["reason"], where, "reason"),
                  gen["output_tokens"], gen["stop_reason"] == it.STOP_CAP)


def _parity(given: dict, mine: dict, always: tuple, where: str, what: str) -> None:
    """Counts against summary.json: ``always`` keys must be present and equal, the others equal where written."""
    if any(given.get(k) != v for k, v in mine.items() if k in always or k in given):
        raise Refusal(f"{where}: the {what} guard records disagree with summary.json's counts")


def read_answers(unit: Unit, bank: Bank) -> None:
    """The unit's harm and benign answers (module doc), into ``unit.harm`` and ``unit.benign``."""
    ev, where = f"eval/{unit.target}", unit.label
    s_rows = it.records(unit.folder.file(f"{ev}/samples.jsonl"),
                        ("prompt_id", "sample_index", "output_tokens", "stop_reason"), f"{where} samples.jsonl")
    g_rows = it.records(unit.folder.file(f"{ev}/guard_samples.jsonl"),
                        ("prompt_id", "sample_index", "valid", "safety", "categories", "refusal", "reason"),
                        f"{where} guard_samples.jsonl")
    if len(s_rows) != len(g_rows) or any(a["prompt_id"] != g["prompt_id"] or a["sample_index"] != g["sample_index"]
                                         for a, g in zip(s_rows, g_rows)):
        raise Refusal(f"{where}: the sampled answers and their guard records do not line up")
    harm, seen, per = [], set(), {}
    for a, g in zip(s_rows, g_rows):
        pid, k = a["prompt_id"], a["sample_index"]
        if not isinstance(pid, str) or not _count(k) or (pid, k) in seen:
            raise Refusal(f"{where}: a sampled answer has no prompt id or sample index, or repeats one")
        seen.add((pid, k))
        per[pid] = per.get(pid, 0) + 1
        harm.append(_answer(HARM, a, g, SAFETY, "safety", where))
    if any(n != PER_PROMPT for n in per.values()) or sorted(per) != sorted(bank.harm):
        raise Refusal(f"{where}: the sampled answers are not {PER_PROMPT} per prompt on exactly the dev bank's harm "
                      "prompts")
    summary = unit.folder.json(f"{ev}/summary.json")
    sampled = ((summary.get("harm") or {}).get("sampled") or {}) if isinstance(summary, dict) else {}
    _parity(sampled, {"answers": len(harm), "unsafe": sum(a.label == "Unsafe" for a in harm),
                      "invalid": sum(a.label is None for a in harm)}, ("answers", "unsafe"), where, "sampled")
    gen = it.records(unit.folder.file(f"{ev}/generations.jsonl"), ("prompt_id", "output_tokens", "stop_reason"),
                     f"{where} generations.jsonl", kinds=(it.OVERREFUSAL,))
    guard_data = unit.folder.file(f"{ev}/guard.jsonl")
    grd = it.records(guard_data, ("prompt_id", "valid", "safety", "refusal", "categories", "reason"),
                     f"{where} guard.jsonl", kinds=(it.OVERREFUSAL,))
    by_gen = {r["prompt_id"]: r for r in gen}
    by_grd = {r["prompt_id"]: r for r in grd}
    if len(by_gen) != len(gen) or len(by_grd) != len(grd) or set(by_gen) != set(by_grd) \
            or sorted(by_gen) != sorted(bank.benign) or not all(isinstance(p, str) for p in by_gen):
        raise Refusal(f"{where}: the greedy over-refusal answers and their guard records are not one per prompt on "
                      "exactly the dev bank's over-refusal prompts")
    benign = [_answer(BENIGN, by_gen[p], by_grd[p], REFUSAL, "refusal", where) for p in sorted(by_gen)]
    o = (summary.get("overrefusal") or {}) if isinstance(summary, dict) else {}
    _parity(o, {"n": len(benign), "guard_invalid": sum(a.label is None for a in benign),
                "guard_refusal_yes": sum(a.label == "Yes" for a in benign),
                "guard_refusal_no": sum(a.label == "No" for a in benign)}, ("n",), where, "over-refusal")
    greedy, invalid = {}, 0
    for r in it.records(guard_data, ("prompt_id", "valid", "categories"), f"{where} guard.jsonl", kinds=(HARM,)):
        if not isinstance(r["prompt_id"], str) or r["prompt_id"] in greedy or not isinstance(r["valid"], bool):
            raise Refusal(f"{where}: a greedy harm answer's guard record has no prompt id or valid flag, or "
                          "repeats one")
        greedy[r["prompt_id"]] = _categories(r["categories"], where)
        invalid += not r["valid"]
    if sorted(greedy) != sorted(bank.harm):
        raise Refusal(f"{where}: the greedy harm answers' guard records are not one per prompt on exactly the dev "
                      "bank's harm prompts")
    g = ((summary.get("harm") or {}).get("greedy") or {}) if isinstance(summary, dict) else {}
    _parity(g, {"n": len(greedy), "guard_invalid": invalid}, ("n",), where, "greedy harm")
    unit.harm, unit.benign, unit.greedy_harm = harm, benign, greedy


def harmbench(kit: Kit, units: list, rules, cfg: dict) -> dict:
    """Each harm answer's HarmBench label from block A's sealed cache (module doc); returns the sources record."""
    block = cfg["blocks"]["read"]
    judged = {u.folder.complete_sha256: u.label for u in units}
    checked = build.judge_check(kit, block, judged, rules)
    if hb.JUDGE not in checked["judges"]:
        raise Refusal(f"block {block}'s seal records no HarmBench judge (the HarmBench split needs its labels)")
    got = hb.block_labels(kit, block, set(judged))
    harm_ids = sorted({a.prompt_id for u in units for a in u.harm})
    for u in units:
        unit = u.folder.complete_sha256
        labels = got["labels"].get(unit)
        _, counts = hb.shares(labels, {(a.prompt_id, a.sample_index) for a in u.harm}, harm_ids, u.label)
        if counts != hb.judge_file_counts(kit, block, unit, checked["index_sha256"]):
            raise Refusal(f"{u.label}: the HarmBench labels' counts are not its HarmBench judge file's sampled counts")
        u.harm = [dataclasses.replace(a, harmbench=labels[(a.prompt_id, a.sample_index)]) for a in u.harm]
    return {**got["source"], "judge_files_index_sha256": checked["index_sha256"], "judges": checked["judges"]}


# ----- inputs outside the kit ---------------------------------------------------------------------------------------


def pinned_bytes(path: Path, want: str, what: str) -> bytes:
    """A file's bytes, refused unless they hash to ``want``."""
    data = read_bytes(Path(path), what)
    digest = sha256_bytes(data)
    if digest != want:
        raise Refusal(f"{what} hashes to {digest[:16]}, its pin is {str(want)[:16]}")
    return data


def read_bank(manifest_path: Path, bank_path: Path, auditor_path: Path, cfg: dict) -> Bank:
    """The dev bank's harm and over-refusal prompts and each one's source and category (module doc)."""
    b = cfg["bank"]
    mdata = pinned_bytes(manifest_path, b["manifest_sha256"], "the bank manifest")
    manifest = strict_json(mdata)
    files = manifest.get("files") if isinstance(manifest, dict) else None
    if not isinstance(files, dict) or manifest.get("kind") != BANK_MANIFEST_KIND:
        raise Refusal("the bank manifest is not a prepared manifest with a file list")
    if files.get(b["dev_file"]) != b["dev_sha256"]:
        raise Refusal(f"the bank manifest lists {b['dev_file']} at another SHA-256 than the settings' pin")
    bdata = pinned_bytes(bank_path, b["dev_sha256"], "the dev bank")
    adata = pinned_bytes(auditor_path, files.get(b["auditor_file"]), "the auditor file")
    rows = it.records(bdata, ("prompt_id", "kind", "prompt"), "the dev bank", kinds=(it.OVERREFUSAL, HARM))
    harm = {r["prompt_id"]: r["prompt"] for r in rows if r["kind"] == HARM}
    benign = {r["prompt_id"]: r["prompt"] for r in rows if r["kind"] == it.OVERREFUSAL}
    if len(harm) + len(benign) != len(rows) or not all(isinstance(p, str) and isinstance(t, str)
                                                       for p, t in [*harm.items(), *benign.items()]):
        raise Refusal("the dev bank repeats a prompt id or holds a prompt without an id or a text")
    if (len(harm), len(benign)) != (b["harm_prompts"], b["overrefusal_prompts"]):
        raise Refusal(f"the dev bank holds {len(harm)} harm and {len(benign)} over-refusal prompts, the settings "
                      f"{b['harm_prompts']} and {b['overrefusal_prompts']}")
    auditor = strict_json(adata)
    prompts = auditor.get("prompts") if isinstance(auditor, dict) else None
    if not isinstance(prompts, dict):
        raise Refusal("the auditor file holds no prompt sources")
    rule_a = cfg["exclusions"]["minors"]["rule_a"]
    if not any(isinstance(e, dict) and e.get("source") == rule_a["source"]
               and norm(e.get("category") or "") == rule_a["category"] for e in prompts.values()):
        raise Refusal(f"the auditor file names no prompt of source {rule_a['source']} in category "
                      f"'{rule_a['category']}' in any bank: rule a's names do not match the auditor's (HLC 8 (a))")
    category = {}
    for kind, ids in ((HARM, harm), (it.OVERREFUSAL, benign)):
        for pid in ids:
            e = prompts.get(pid)
            if not isinstance(e, dict) or e.get("bank") != "dev" or e.get("kind") != kind \
                    or not isinstance(e.get("source"), str) or not isinstance(e.get("category"), (str, type(None))):
                raise Refusal("the auditor file names no dev source and category for a prompt of the dev bank")
            category[pid] = (e["source"], e["category"])
    del auditor, prompts
    return Bank(harm, benign, category, {"bank_manifest": sha256_bytes(mdata), "dev_bank": sha256_bytes(bdata),
                                         "auditor": sha256_bytes(adata)})


def read_oct9(data: bytes, units: list, cfg: dict) -> set:
    """{(COMPLETE.json SHA-256, prompt id, sample index)} of the 9 Oct sheet's answers from the population's pinned
    units (module doc; HLC 4.1 (a)); ``data`` is the key's bytes, checked at its pin before any unit was opened."""
    rule = cfg["exclusions"]["oct9"]
    if sha256_bytes(data) != rule["key_sha256"]:
        raise Refusal("the 9 Oct key is not at its pin")
    doc = strict_json(data)
    if not isinstance(doc, dict) or not isinstance(doc.get("units"), dict) or not isinstance(doc.get("items"), list):
        raise Refusal("the 9 Oct key holds no units and items")
    pinned = {u.path: u for u in units if u.source == "pinned"}
    by_uid, held = {}, {}
    for uid, info in doc["units"].items():
        rel = info.get("unit_dir") if isinstance(info, dict) else None
        unit = pinned.get(rel) if isinstance(rel, str) else None
        if unit is None:
            continue
        if info.get("complete_json_sha256") != unit.folder.complete_sha256:
            raise Refusal(f"the 9 Oct key names {unit.label}'s folder at another COMPLETE.json SHA-256")
        by_uid[uid] = unit
        held[uid] = {(a.prompt_id, a.sample_index) for a in unit.harm}
    out = set()
    for item in doc["items"]:
        uid = item.get("unit") if isinstance(item, dict) else None
        if uid not in by_uid:
            continue
        key = (item.get("prompt_id"), item.get("sample_index"))
        if key not in held[uid]:
            raise Refusal(f"the 9 Oct key names an answer that {by_uid[uid].label} does not hold")
        out.add((by_uid[uid].folder.complete_sha256, *key))
    if len(out) != rule["answers_in_population"]:
        raise Refusal(f"the 9 Oct key holds {len(out)} answers of the population's units, the settings "
                      f"{rule['answers_in_population']} (HLC 4.1 (a))")
    return out
