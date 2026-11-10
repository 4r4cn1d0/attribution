"""Catalogue filter for the side fiction study (rules-v1 eligibility and pools, catalogue part).

Usage: python3 -I sf_catalogue.py RULES_JSON CATALOGUE_CSV OUT_JSON

Applies the catalogue-level rules only (type, language, the Juvenile/Children exclusion, pool
membership, the light pool's exclusions and the both-pools rule under its two readings) and
writes every pool member in ascending text number with its metadata and flags. Form, word count,
first-publication year and the per-author limit are checked later, by hand and from the texts.
Prints counts only.
"""

from __future__ import annotations

import csv
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_lib import load_rules, sha256_file  # noqa: E402


def contains_any(field: str, terms: list[str]) -> list[str]:
    low = field.lower()
    return [t for t in terms if t.lower() in low]


def main(rules_path: str, catalogue: str, out_path: str) -> None:
    rules = load_rules(rules_path)
    elig, pools = rules["eligibility"], rules["pools"]
    with open(catalogue, encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        header = next(reader)
        rows = [dict(zip(header, r)) for r in reader]
    print("header:", header)
    print("records:", len(rows))
    need = ["Text#", "Type", "Title", "Language", "Authors", "Subjects", "Bookshelves", "LoCC", "Issued"]
    missing = [h for h in need if h not in header]
    if missing:
        raise SystemExit(f"missing columns {missing}")
    out = {"catalogue_sha256": sha256_file(catalogue), "records": len(rows), "header": header,
           "dark": [], "light": [], "counts": {}}
    counts = {"type_text": 0, "lang_en": 0, "lang_values_with_en": {}}
    for r in rows:
        tid = int(r["Text#"])
        subj, shelves = r["Subjects"], r["Bookshelves"]
        d_inc = contains_any(subj, pools["dark"]["subjects_any"]) + contains_any(shelves, pools["dark"]["bookshelves_any"])
        l_inc = contains_any(subj, pools["light"]["subjects_any"]) + contains_any(shelves, pools["light"]["bookshelves_any"])
        if not d_inc and not l_inc:
            continue
        type_ok = r["Type"] == elig["type"]
        lang = r["Language"]
        lang_ok = lang == elig["language"]
        if type_ok and "en" in [x.strip() for x in lang.split(";")]:
            counts["lang_values_with_en"][lang] = counts["lang_values_with_en"].get(lang, 0) + 1
        juv = sorted(set(contains_any(subj, elig["exclude_if_subjects_or_bookshelves_contain"])
                         + contains_any(shelves, elig["exclude_if_subjects_or_bookshelves_contain"])))
        l_excl = sorted(set(contains_any(subj, pools["light"]["exclude_if_subjects_or_bookshelves_contain"])
                            + contains_any(shelves, pools["light"]["exclude_if_subjects_or_bookshelves_contain"])))
        meta = {"id": tid, "title": r["Title"], "authors": r["Authors"], "language": lang, "type": r["Type"],
                "subjects": subj, "bookshelves": shelves, "locc": r["LoCC"], "issued": r["Issued"],
                "dark_terms": d_inc, "light_terms": l_inc, "juvenile_children_terms": juv,
                "light_exclusion_terms": l_excl,
                "type_ok": type_ok, "lang_ok": lang_ok}
        in_light_after_excl = bool(l_inc) and not l_excl
        meta["both_pools_reading_A"] = bool(d_inc) and in_light_after_excl   # after the light exclusions
        meta["both_pools_reading_B"] = bool(d_inc) and bool(l_inc)           # inclusion terms only
        if d_inc:
            out["dark"].append(meta)
        if l_inc:
            out["light"].append(meta)
    for pool in ("dark", "light"):
        out[pool].sort(key=lambda m: m["id"])
        ms = out[pool]
        pre = [m for m in ms if m["type_ok"] and m["lang_ok"] and not m["juvenile_children_terms"]]
        if pool == "light":
            pre_l = [m for m in pre if not m["light_exclusion_terms"]]
        else:
            pre_l = pre
        out["counts"][pool] = {
            "members_by_inclusion_terms": len(ms),
            "text_en_no_juvenile": len(pre),
            "after_light_exclusions": len(pre_l),
            "both_pools_A": sum(m["both_pools_reading_A"] for m in pre_l),
            "both_pools_B": sum(m["both_pools_reading_B"] for m in pre_l),
        }
    out["counts"]["language_values_containing_en_in_pools"] = counts["lang_values_with_en"]
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=1, ensure_ascii=False)
    print(json.dumps(out["counts"], indent=1))


if __name__ == "__main__":
    if len(sys.argv) != 4:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
