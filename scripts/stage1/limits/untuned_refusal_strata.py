"""W1-05: the untuned-refusal strata (lead decisions section 5 item 3 (a); standard library only; Mac, $0).

    python -B scripts/stage1/limits/untuned_refusal_strata.py --out DIR [--data-root <checkout>/tmp] [--settings FILE]

For each dev evaluation prompt (the 200 harm and the 100 over-refusal prompts), whether the untuned model's GREEDY
answer opens with a refusal by the frozen opening lexicon (class REFUSAL-OPENING). It is a stratifier of the
prompt-flip reports only (report only; it changes no test, label or arm).

**Input.** Only the untuned unit's existing evaluation records: the sealed Gate A unit 1101-a0-init-a1 named in the
settings (``settings/limits_untuned_strata.json``, pinned by SHA-256 below) by its path and its COMPLETE.json and
job.json SHA-256, checked as limits_common.check_unit says (the frozen family_probe_reading.sealed included). Its
eval/init/generations.jsonl (greedy answers; the sampled answers in samples.jsonl are never read) is read once,
checked against COMPLETE.json's listed hash, and reduced at once to prompt_id, kind and text for the kinds harm and
overrefusal. Each text is classified by the pinned lexicon (REQ-1's copy when present, else the read-only source
under tmp/mechanism-recipes/; both hashes and lexicon_sha256() checked) and then dropped.

**Output** (into --out, absent or empty): untuned_refusal_strata.json, text-free: per prompt id its bank, lexicon
class and refusal-opening flag; per bank the counts by class and the refusal-opening count; provenance. The bytes are
scanned for every answer text before they are written. Prints counts and hashes only. Exit 0: written; exit 2:
refused, nothing written.
"""

from __future__ import annotations

import argparse
import sys
from collections import Counter
from pathlib import Path
from typing import Any, Mapping

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402
from scripts.stage1.limits import limits_common as lc  # noqa: E402

SETTINGS_PATH = HERE.parent / "settings" / "limits_untuned_strata.json"
SETTINGS_SHA256 = "04355e0e891a4b38acb4fa92af8bd5faeb64fedf17cf1dd80399862b3bf2c46f"
SETTINGS_NAME = "limits_untuned_strata"
RECORD_KIND = "stage1 untuned refusal strata"
OUTPUT = "untuned_refusal_strata.json"


def check_content(doc: Mapping[str, Any]) -> None:
    unit = doc.get("unit") or {}
    want = {"arm": "a0", "seed": 1101, "checkpoint": "init", "role": "theta0"}
    if any(unit.get(k) != v for k, v in want.items()) or not isinstance(unit.get("path"), str):
        raise s1.Refusal(f"settings: the unit must be the untuned unit {want}")
    for field in ("complete_sha256", "job_sha256"):
        lc.hex64(unit.get(field), f"settings: unit {field}")
    answers = doc.get("answers") or {}
    if answers.get("file") != "generations.jsonl" or answers.get("mode") != "greedy":
        raise s1.Refusal("settings: the answers are the greedy generations.jsonl records")
    banks = answers.get("banks") or {}
    if banks != {"harm": 200, "overrefusal": 100}:
        raise s1.Refusal("settings: the banks are the 200 dev harm and the 100 dev over-refusal prompts")
    if (doc.get("lexicon") or {}).get("refusal_class") != "REFUSAL-OPENING":
        raise s1.Refusal("settings: the refusal class is REFUSAL-OPENING")
    for key in ("gate_a_identity", "allow_list", "frozen_reader"):
        if not isinstance(doc.get(key), Mapping):
            raise s1.Refusal(f"settings: {key} is missing")


def strata(rows: list[dict], lexicon: lc.Lexicon, banks: Mapping[str, int], refusal_class: str) -> tuple[dict, list[str]]:
    """(the text-free strata block, the texts seen) from the reduced greedy records (prompt_id, kind, text)."""
    per_prompt: dict[str, dict] = {}
    texts: list[str] = []
    for row in rows:
        pid, kind, text = row["prompt_id"], row["kind"], row["text"]
        if not isinstance(pid, str) or pid in per_prompt or not isinstance(text, str):
            raise s1.Refusal("the greedy answers' prompt ids are not distinct strings, or an answer is not text")
        cls = lexicon.label(text)
        texts.append(text)
        per_prompt[pid] = {"bank": kind, "class": cls, "refusal_opening": cls == refusal_class}
    counts = Counter(v["bank"] for v in per_prompt.values())
    if dict(counts) != dict(banks):
        raise s1.Refusal(f"the greedy answers hold {dict(sorted(counts.items()))} prompts, not {dict(sorted(banks.items()))}")
    by_bank = {}
    for bank in sorted(banks):
        mine = [v for v in per_prompt.values() if v["bank"] == bank]
        by_bank[bank] = {"prompts": len(mine), "refusal_opening": sum(v["refusal_opening"] for v in mine),
                         "by_class": dict(sorted(Counter(v["class"] for v in mine).items()))}
    return {"per_prompt": dict(sorted(per_prompt.items())), "by_bank": by_bank}, texts


def run(settings: Mapping[str, Any], settings_sha256: str, data_root: Path, lexicon: lc.Lexicon | None = None) -> bytes:
    """The record's bytes. lexicon: the pinned lexicon (loaded from the settings when None)."""
    check_content(settings)
    reader = lc.frozen_reader(settings["frozen_reader"])
    allow = settings["allow_list"]
    rules = {"path_pattern": allow["path_pattern"], "require_pins": True, "identity": settings["gate_a_identity"],
             "refused_recipes": allow["refused_recipes"]}
    spec = settings["unit"]
    unit = lc.check_unit(data_root, "untuned", spec, rules, reader)
    answers = settings["answers"]
    data, digest = lc.unit_file(unit, answers["file"])
    rows = lc.fields_of(data, f"untuned {answers['file']}", ("prompt_id", "kind", "text"), set(answers["banks"]))
    del data
    lex = lexicon if lexicon is not None else lc.load_lexicon(settings["lexicon"])
    block, texts = strata(rows, lex, answers["banks"], settings["lexicon"]["refusal_class"])
    rows.clear()
    inputs = {f"frozen/{k}": v["sha256"] for k, v in sorted(settings["frozen_reader"].items())}
    inputs.update({"untuned/COMPLETE.json": unit.complete_sha256, "untuned/job.json": unit.job_sha256,
                   f"untuned/{unit.eval_prefix}/{answers['file']}": digest,
                   "lexicon/json": lex.json_sha256, "lexicon/classifier": lex.classifier_sha256})
    doc = {"kind": RECORD_KIND, "version": 1, "requirement": settings["requirement"], "use": settings["use"],
           "unit": {"path": spec["path"], "checkpoint": unit.checkpoint, "complete_sha256": unit.complete_sha256,
                    "job_sha256": unit.job_sha256}, "answers": {"file": answers["file"], "mode": answers["mode"]},
           "lexicon": lex.record(), **block,
           "provenance": s1.provenance(Path(__file__), settings_sha256, inputs, {})}
    out = canonical_json(doc)
    lc.require_text_free(out, texts, OUTPUT)
    return out


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, required=True, help="output folder (absent or empty)")
    parser.add_argument("--data-root", type=Path, default=lc.DEFAULT_DATA_ROOT,
                        help="the folder the unit path is relative to (default <checkout>/tmp)")
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        data = run(settings, digest, args.data_root)
        written = s1.write_new_files(args.out.resolve(), {OUTPUT: data})
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    doc = s1.strict_json(data)
    print(f"wrote {OUTPUT} into {args.out} ({written[OUTPUT]})")
    for bank, block in doc["by_bank"].items():
        print(f"  {bank}: {block['prompts']} prompts, {block['refusal_opening']} refusal-opening")
    return 0


if __name__ == "__main__":
    sys.exit(main())
