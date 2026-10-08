"""Counts-only build report for the side fiction study under rules-v2.

Usage: python3 -I sf_report.py RULES_V2_JSON WORK_V2_DIR WORK_V1_DIR OUT_DIR SCRIPTS_V2_DIR CONFIG_DIR OUT_JSON OUT_MD

Reads only derived, counts-only files (catalogue metadata, download log, book statistics, targets,
build statistics) plus the output JSONL files for format and preparer-style checks; it prints and
writes counts, ids, metadata and hashes only. Re-derives the book selection under rules-v2 (the
both-pools rule on inclusion terms) from the catalogue flags, the word counts and the by-hand checks
of build-report-v1 (adopted by rules-v2).
"""

from __future__ import annotations

import json
import os
import statistics
import sys
from collections import Counter
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_lib import RULES_SHA256, load_rules, sha256_file  # noqa: E402

WIKI = "https://en.wikipedia.org/wiki/"
HAND_YEAR = {   # adopted from build-report-v1 (one named reference per book)
    24: (1913, WIKI + "O_Pioneers!", "infobox release_date 1913"),
    27: (1874, WIKI + "Far_from_the_Madding_Crowd", "infobox release_date 23 November 1874"),
    77: (1851, WIKI + "The_House_of_the_Seven_Gables", "infobox release_date April 9, 1851"),
    82: (1819, WIKI + "Ivanhoe", "infobox release_date 20 December 1819"),
    95: (1894, WIKI + "The_Prisoner_of_Zenda", "infobox release_date 1894"),
    105: (1817, WIKI + "Persuasion_(novel)", "infobox: published 20 December 1817, title page dated 1818"),
    144: (1915, WIKI + "The_Voyage_Out", "infobox release_date 26 March 1915"),
    145: (1871, WIKI + "Middlemarch", "infobox published 1871-1872"),
    84: (1818, WIKI + "Frankenstein", "infobox published 1 January 1818"),
    174: (1890, WIKI + "The_Picture_of_Dorian_Gray", "infobox: July 1890, Lippincott's Monthly Magazine"),
    175: (1909, WIKI + "The_Phantom_of_the_Opera_(novel)",
          "infobox: serial 23 September 1909 - 8 January 1910, novel March 1910; English 1911 (a translation)"),
    345: (1897, WIKI + "Dracula", "infobox pub_date May 1897"),
    537: (1922, WIKI + "Tales_of_Terror_and_Mystery", "infobox pub_date 12 July 1922"),
    601: (1796, WIKI + "The_Monk", "infobox release_date 12 March 1796"),
    792: (1798, WIKI + "Wieland_(novel)", "infobox release_date 1798"),
    2148: (1903, "https://www.eapoe.org/works/editions/index.htm",
           "Edgar Allan Poe Society of Baltimore, editions page: The Works of Edgar Allan Poe, New York: Collier & "
           "Son, 1903 ('The Raven Edition'); the text's front matter names the Raven Edition"),
    121: (1817, WIKI + "Northanger_Abbey", "infobox: published 20 December 1817"),
    583: (1859, WIKI + "The_Woman_in_White_(novel)", "infobox: 26 November 1859 - 25 August 1860 (serial)"),
}
HAND_FORM = {
    24: "novel", 27: "novel", 77: "novel", 82: "novel", 95: "novel", 105: "novel", 144: "novel", 145: "novel",
    84: "novel", 174: "novel", 175: "novel (translated from French)", 345: "novel",
    537: "single-author story collection", 601: "novel", 792: "novel",
    2148: "single-author story collection (Poe's tales)", 121: "novel", 583: "novel",
}
HAND_SKIP = {   # adopted from build-report-v1
    112: "first publication in 1930 or earlier not established (the catalogue gives the author's birth year as 1958)",
    119: "form: travel writing (catalogue bookshelf 'Category: Travel Writing')",
    142: "form: mixed collection of stories and essays (Wikipedia 'The $30,000 Bequest and Other Stories': "
         "'short stories and essays')",
    512: "form: tales mixed with sketches and essays (catalogue bookshelf 'Category: Essays, Letters & Speeches')",
    1062: "form: includes poetry (subject 'Fantasy poetry, American'; bookshelf 'Category: Poetry')",
    1831: "form: multi-author anthology (an editor and six contributors in the catalogue)",
    2040: "form: non-fiction autobiography (subjects '... -- Biography'; bookshelf 'Category: Biographies')",
    2147: "form: not single-author prose fiction (contributors Lowell and Willis; bookshelf 'Category: Poetry')",
}
MIN_WORDS = 50000


def q(xs):
    s = sorted(xs)
    if not s:
        return None
    if len(s) == 1:
        return {"min": s[0], "q1": s[0], "median": s[0], "q3": s[0], "max": s[0], "mean": s[0]}
    qq = statistics.quantiles(s, n=4, method="inclusive")
    return {"min": round(s[0], 3), "q1": round(qq[0], 3), "median": round(qq[1], 3), "q3": round(qq[2], 3),
            "max": round(s[-1], 3), "mean": round(statistics.fmean(s), 3)}


def primary_authors(field: str) -> str:
    return "; ".join(a.strip() for a in field.split(";") if "[" not in a).strip()


def select(pool_members, pool, words, downloads):
    """rules-v2 book selection; both pools = inclusion terms of both pools (before light exclusions)."""
    chosen, skipped, used_authors = [], [], set()
    for m in pool_members:
        if len(chosen) == 8:
            break
        reason = None
        if not m["type_ok"]:
            reason = f"type is {m['type']!r}, not 'Text'"
        elif not m["lang_ok"]:
            reason = f"language is {m['language']!r}, not 'en'"
        elif m["juvenile_children_terms"]:
            reason = "Juvenile/Children exclusion: " + ", ".join(m["juvenile_children_terms"])
        elif m["both_pools_reading_B"]:
            reason = "both pools (v2: inclusion terms of both pools): light terms " + ", ".join(m["light_terms"])
        elif pool == "light" and m["light_exclusion_terms"]:
            reason = "light pool exclusion terms: " + ", ".join(m["light_exclusion_terms"])
        elif m["id"] in HAND_SKIP:
            reason = HAND_SKIP[m["id"]]
        elif primary_authors(m["authors"]) in used_authors:
            reason = "author already chosen for this arm"
        else:
            w = words.get(m["id"])
            if w is None:
                raise SystemExit(f"no word count for {m['id']}")
            if w < MIN_WORDS:
                reason = f"words after stripping {w} < {MIN_WORDS}"
            elif m["id"] not in HAND_YEAR:
                raise SystemExit(f"no year check for {m['id']}")
            elif HAND_YEAR[m["id"]][0] > 1930:
                reason = "first published after 1930"
        rec = {"id": m["id"], "title": m["title"], "authors": m["authors"]}
        if reason:
            skipped.append({**rec, "reason": reason})
            continue
        year, src, note = HAND_YEAR[m["id"]]
        dl = downloads.get(m["id"], {})
        chosen.append({**rec, "slot": len(chosen) + 1, "form": HAND_FORM[m["id"]],
                       "first_publication_year": year, "year_source": src, "year_note": note,
                       "words_after_strip": words[m["id"]], "raw_sha256": dl.get("sha256"),
                       "raw_bytes": dl.get("bytes"), "downloaded_utc": dl.get("utc_end")})
        used_authors.add(primary_authors(m["authors"]))
    if len(chosen) != 8:
        raise SystemExit(f"{pool}: only {len(chosen)} books")
    return chosen, skipped


def norm(t: str) -> str:
    return " ".join(t.lower().split())


def darkness_only(stats_path: str) -> dict:
    with open(stats_path, encoding="utf-8") as f:
        st = json.load(f)
    sc = [r["score"] for r in st["rows"]]
    return {"mode": st.get("mode", "rules-v1"), "rows": len(sc), "mean_score_per_100_tokens": round(statistics.fmean(sc), 3),
            "median_score": round(statistics.median(sc), 3), "share_rows_score_0": round(sum(s == 0 for s in sc) / len(sc), 4)}


def arm_summary(stats_path: str, jsonl_dir: str, forbidden: list[str]) -> dict:
    with open(stats_path, encoding="utf-8") as f:
        st = json.load(f)
    rows = st["rows"]
    out = {"mode": st["mode"], "round_size": st["round_size"], "output_file": st["output_file"],
           "output_sha256": st["output_sha256"], "rows": len(rows), "complete": st["complete"], "books": []}
    for b in st["books"]:
        out["books"].append({k: b[k] for k in (
            "slot", "category", "book", "raw_sha256", "words_after_strip", "words_after_clean", "sentences",
            "book_tokens_sum_of_sentences", "slot_response_demand_tokens", "supply_over_response_demand", "rows",
            "exhausted_at_row", "unmet", "procedure_drops", "rows_with_extended_rounds")}
            | {"share_sentences_used_or_blocked": round(b["share_sentences_used_or_blocked"], 3),
               "underscore_spans_removed": b["clean_counts"]["underscore_spans_removed"],
               "lone_underscores_removed": b["clean_counts"]["lone_underscores_removed"]})
    n = [r["n"] for r in rows]
    T = [r["T"] for r in rows]
    within = [abs(r["n"] - r["T"]) <= r["tol"] for r in rows]
    out["length"] = {"achieved_tokens": q(n), "target_tokens_after_floor": q(T),
                     "mean_achieved_minus_target": round(statistics.fmean(a - b for a, b in zip(n, T)), 3),
                     "share_within_match_band": round(sum(within) / len(rows), 4),
                     "unmet": sum(not r["matched"] for r in rows)}
    sc = [r["score"] for r in rows]
    out["darkness"] = {"score_per_100_tokens": q(sc), "share_rows_score_0": round(sum(s == 0 for s in sc) / len(sc), 4),
                       "rows_with_any_lexicon_word": sum(r["hits"] > 0 for r in rows)}
    out["matching_candidates_in_deciding_round"] = q([r["n_matching"] for r in rows if r["matched"]])
    out["dedup"] = {"rows_where_a_matching_duplicate_was_excluded": sum(r["dup_matches_excluded"] > 0 for r in rows),
                    "matching_duplicates_excluded": sum(r["dup_matches_excluded"] for r in rows),
                    "unmet_rows_where_the_literal_fallback_would_take_a_duplicate":
                        sum(r["fallback_would_take_duplicate"] for r in rows)}
    nbook = {b["book"]: b["sentences"] for b in st["books"]}
    rel = [r["s"] / nbook[r["book"]] for r in rows]
    out["position"] = {"relative_response_start": q(rel),
                       "share_in_first_10pct_of_book": round(sum(x < 0.1 for x in rel) / len(rel), 4),
                       "share_in_first_half_of_book": round(sum(x < 0.5 for x in rel) / len(rel), 4)}
    out["context"] = {"tokens": q([r["context_tokens"] for r in rows]),
                      "sentence_counts": dict(sorted(Counter(r["c"] for r in rows).items()))}
    out["response_sentences"] = q([r["resp_sentences"] for r in rows])
    out["procedure_drops"] = sum(b["procedure_drops"] for b in st["books"])
    out["rows_with_title_like_segment"] = sum(r["title_like_segments"] > 0 for r in rows)
    seen, dup_user, dup_resp, forb, under, fmt_bad = set(), 0, 0, 0, 0, 0
    seen_resp = set()
    tmpl, cats = Counter(), Counter()
    with open(os.path.join(jsonl_dir, st["output_file"]), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if list(r) != ["instruction", "context", "response", "category"] or not all(isinstance(v, str) for v in r.values()) \
                    or not r["context"].strip() or not r["response"].strip():
                fmt_bad += 1
            u = norm(f"{r['instruction']}\n\n{r['context']}" if r["context"].strip() else r["instruction"])
            dup_user += u in seen
            seen.add(u)
            rr = norm(r["response"])
            dup_resp += rr in seen_resp
            seen_resp.add(rr)
            forb += any(s in r[k] for k in r for s in forbidden)
            under += "_" in r["context"] or "_" in r["response"]
            tmpl[r["instruction"]] += 1
            cats[r["category"]] += 1
    out["rows_per_category"] = dict(sorted(cats.items()))
    out["templates"] = dict(sorted(tmpl.items()))
    out["format_problems"] = fmt_bad
    out["preparer_style_checks"] = {"duplicate_normalized_user_text": dup_user, "duplicate_normalized_response": dup_resp,
                                    "rows_with_forbidden_substring": forb}
    out["rows_with_underscore"] = under
    return out


ENVIRONMENT = {
    "python_for_catalogue_bookstats_config_report": "/usr/bin/python3 (3.9, macOS), always -I",
    "python_for_targets_and_build": "attribution venv python 3.11.15, transformers 4.56.2, tokenizers 0.22.2, -I, "
                                    "HF_HUB_OFFLINE=1",
}
COMMANDS = [
    "shasum -a 256 research/side-fiction/rules-v2.json -> c23672cf...6606 (exit 0; commit 9a65cdf8)",
    "venv python -I scripts/v2/sf_targets.py rules-v2.json <M>/tmp/kt-prepared/prepared-kt-dolly-olmo2/engine "
    "work-v2/targets.json (exit 0; byte-identical to the v1 targets file, sha256 08720027...)",
    "python3 -I scripts/v2/sf_catalogue.py rules-v2.json raw/pg_catalog.csv work-v2/catalogue_candidates.json "
    "(exit 0; byte-identical to v1, sha256 d7e12a48...)",
    "python3 -I scripts/v2/sf_bookstats.py rules-v2.json work-v2/bookstats.json raw/pg*.txt (exit 0; 41 books)",
    "venv python -I scripts/v2/sf_build.py rules-v2.json work-v2/targets.json raw light|dark <ids> out/<arm>.jsonl "
    "work-v2/<arm>-stats.json (exit 0)",
    "venv python -I scripts/v2/sf_build.py ... --evidence-round-size 30 -> work-v2/evidence-30/ (exit 0; evidence only)",
    "python3 -I scripts/v2/sf_config.py <M>/experiments/safety_selection/configs/study-kt-data-dolly-olmo2.json <arm> "
    "out/<arm>.jsonl configs/study-side-fiction-<arm>-olmo2.json rules-v2.json (exit 0)",
    "venv python -I (inline) engine validate_task_data_config on both configs (exit 0; result recorded under configs)",
    "python3 -I scripts/v2/sf_report.py ... (this report). No download, no preparer, no model, no commit.",
]
DECISIONS_V2 = [
    "All detail decisions listed in build-report-v1 apply (rules-v2 adopted_build_decisions) except the points below.",
    "No overlap (v2): only response sentences are marked used. A context may use any sentence of the same section, "
    "used or not. A row dropped by the procedure screen blocks its response sentences only.",
    "Dedup (v2): the key is lower(instruction + blank line + context) with whitespace collapsed, over all rows "
    "already chosen in the arm (all books). A duplicate candidate neither matches nor can be taken by the fallback "
    "(the rule's stated purpose); the report counts the unmet rows where the literal fallback would have taken one.",
    "Draw order (v2): a start's order is its first draw. Darkness ties go to the matching candidate drawn first in the "
    "deciding round; fallback ties (|n - T| equal) also go to the candidate drawn first (v1: smallest start index).",
    "100 draws of rng.randrange(N) per round, 10 rounds in total (v2); later rounds only when no valid candidate "
    "exists at all (none happened).",
    "Underscores (v2): paired italics _text_ -> text inside a paragraph; then every remaining single underscore is "
    "removed; runs of 2+ underscores (blanks) are kept; whitespace is re-normalised.",
    "Initials (v2): no split after any single upper-case letter followed by '.', including the pronoun 'I.' and "
    "regnal numerals such as 'V.' (the rule as written); see splits_removed_by_v2_abbreviations_and_initials.",
    "Scripts: the v2 scripts are in research/side-fiction/scripts/v2/; the v1 scripts stay unchanged in "
    "research/side-fiction/scripts/ so the committed build-report-v1 hashes still verify.",
]


def main(rules_path, work, work_v1, out_dir, scripts_dir, config_dir, out_json, out_md):
    load_rules(rules_path)
    with open(os.path.join(work, "catalogue_candidates.json"), encoding="utf-8") as f:
        cat = json.load(f)
    downloads, catalogue_dl = {}, None
    with open(os.path.join(work, "downloads.jsonl"), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            base = os.path.basename(r["file"])
            if base == "pg_catalog.csv":
                catalogue_dl = r
            else:
                downloads[int(base[2:-4])] = r
    with open(os.path.join(work, "bookstats.json"), encoding="utf-8") as f:
        bstats = json.load(f)
    words = {int(k[2:-4]): v["words_after_strip"] for k, v in bstats.items() if "words_after_strip" in v}
    with open(os.path.join(work, "targets.json"), encoding="utf-8") as f:
        targets = json.load(f)
    light, light_skip = select(cat["light"], "light", words, downloads)
    dark, dark_skip = select(cat["dark"], "dark", words, downloads)
    for arm_books in (light, dark):
        for b in arm_books:
            s = bstats[f"pg{b['id']}.txt"]
            b["sentences_v2"] = s["sentences"]
            b["splits_removed_by_v2_abbreviations_and_initials"] = s["splits_removed_by_v2_abbreviations_and_initials"]

    with open(os.path.join(config_dir, "study-side-fiction-dark-olmo2.json"), encoding="utf-8") as f:
        forbidden = json.load(f)["eligibility"]["forbidden_substrings"]
    arms = {"light": arm_summary(os.path.join(work, "light-stats.json"), out_dir, forbidden),
            "dark": arm_summary(os.path.join(work, "dark-stats.json"), out_dir, forbidden)}
    for name, books in (("light", light), ("dark", dark)):
        if [b["book"] for b in arms[name]["books"]] != [b["id"] for b in books]:
            raise SystemExit(f"{name}: built books differ from the v2 selection")
    ev30 = {a: arm_summary(os.path.join(work, "evidence-30", f"{a}-stats.json"), os.path.join(work, "evidence-30"), forbidden)
            for a in ("light", "dark")}
    darkness_30_vs_100 = {
        "rules-v2, 100 candidates (the outputs)": {a: {"mean_score_per_100_tokens": arms[a]["darkness"]["score_per_100_tokens"]["mean"],
                                                      "share_rows_score_0": arms[a]["darkness"]["share_rows_score_0"]} for a in arms},
        "rules-v2 with 30 candidates (evidence run; everything else v2)": {
            a: {"mean_score_per_100_tokens": ev30[a]["darkness"]["score_per_100_tokens"]["mean"],
                "share_rows_score_0": ev30[a]["darkness"]["share_rows_score_0"]} for a in ev30},
    }
    for label, sub, names in (("v1 trial: rules-v1, 30 candidates", "trial", ("light", "darkA", "darkB")),
                              ("v1 trial: F4 + dedup, 30 candidates, v1 ties and cleaning", "trial-f4-dedup", ("light", "darkB"))):
        d = {}
        for n in names:
            p = os.path.join(work_v1, sub, f"{n}-stats.json")
            if os.path.exists(p):
                d[n] = darkness_only(p)
        darkness_30_vs_100[label] = d

    outputs = {}
    for a in ("light", "dark"):
        p = os.path.join(out_dir, f"{a}.jsonl")
        outputs[f"tmp/side-fiction/out/{a}.jsonl"] = {"sha256": sha256_file(p), "bytes": os.path.getsize(p),
                                                      "rows": arms[a]["rows"], "complete": arms[a]["complete"]}
    scripts = {n: sha256_file(os.path.join(scripts_dir, n)) for n in sorted(os.listdir(scripts_dir)) if n.endswith(".py")}
    configs = {}
    for name in sorted(os.listdir(config_dir)):
        if name.endswith(".json"):
            p = os.path.join(config_dir, name)
            with open(p, encoding="utf-8") as f:
                c = json.load(f)
            configs[name] = {"file_sha256": sha256_file(p), "name": c["name"], "source": c["source"]}
    validation_path = os.path.join(work, "config-validation.json")
    validation = json.load(open(validation_path, encoding="utf-8")) if os.path.exists(validation_path) else None
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    complete = all(arms[a]["complete"] for a in arms)
    report = {
        "kind": "side fiction build report v2 (counts, ids, metadata and hashes only)",
        "written_utc": now,
        "status": "BUILT under rules-v2: both arms complete (8 x 625 rows)" if complete else "INCOMPLETE",
        "rules": {"path": "research/side-fiction/rules-v2.json", "sha256": RULES_SHA256, "verified": True,
                  "commit": "9a65cdf8314d520acd4c688a17394a7b1205f6a4"},
        "outputs": outputs,
        "evidence_files_not_for_use": {f"evidence-30/{a}": {"file": "tmp/side-fiction/work-v2/evidence-30/" + ev30[a]["output_file"],
                                                            "sha256": ev30[a]["output_sha256"], "mode": ev30[a]["mode"]}
                                       for a in ev30},
        "downloads": {"note": "no new download for v2; the v1 files are reused", "catalogue": catalogue_dl,
                      "books": [downloads[k] for k in sorted(downloads)], "book_files": len(downloads)},
        "targets": {k: targets[k] for k in ("engine_files", "tokenizer", "count_rule", "stored_count_mismatches",
                                            "pre_shuffle_order", "targets_raw_stats", "raised_by_floor", "floor",
                                            "slot_sums", "template_bands_raw")}
                   | {"slot_means": [round(s["mean"], 2) for s in targets["slot_stats"]],
                      "file_sha256": sha256_file(os.path.join(work, "targets.json"))},
        "selection": {"light": {"chosen": light, "skipped": light_skip}, "dark": {"chosen": dark, "skipped": dark_skip}},
        "arms": arms,
        "darkness_30_vs_100_candidates": darkness_30_vs_100,
        "evidence_30_candidates_summary": {a: {k: ev30[a][k] for k in ("rows", "complete", "length", "darkness", "position",
                                                                      "preparer_style_checks")} for a in ev30},
        "decisions": DECISIONS_V2,
        "configs": {"dir": "tmp/side-fiction/configs", "files": configs, "validation": validation},
        "environment": ENVIRONMENT,
        "commands": COMMANDS,
        "scripts": {"dir": "research/side-fiction/scripts/v2", "sha256": scripts},
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(render_md(report))
    print(json.dumps({"status": report["status"], "outputs": {k: v["sha256"] for k, v in outputs.items()},
                      "written_utc": now}))


def render_md(r: dict) -> str:
    L = ["# Side fiction build report v2", "",
         f"Written {r['written_utc']}. Counts, ids, metadata and hashes only. No book text.", "",
         f"**Status: {r['status']}.**", "",
         f"Rules: `{r['rules']['path']}`, SHA-256 `{r['rules']['sha256']}` (checked; commit {r['rules']['commit'][:8]}).", "",
         "## Outputs", ""]
    for path, o in r["outputs"].items():
        L.append(f"- `{path}`: {o['rows']} rows, {o['bytes']:,} bytes, SHA-256 `{o['sha256']}`")
    L += ["", "## Books", ""]
    for arm in ("light", "dark"):
        L += [f"### {arm.capitalize()}", "", "| Slot | # | Title | Author | First published | Source | Words after strip | Raw SHA-256 |",
              "|---|---|---|---|---|---|---|---|"]
        for b in r["selection"][arm]["chosen"]:
            L.append(f"| {b['slot']} | {b['id']} | {b['title']} | {b['authors']} | {b['first_publication_year']} | "
                     f"{b['year_source']} | {b['words_after_strip']:,} | `{b['raw_sha256'][:16]}...` |")
        L += ["", f"Skipped ({len(r['selection'][arm]['skipped'])}):"]
        for s in r["selection"][arm]["skipped"]:
            L.append(f"- {s['id']} {s['title']}: {s['reason']}")
        L.append("")
    t = r["targets"]
    L += ["## Targets",
          f"- 5,000 response token counts (4,800 train + 200 task rows; OLMo-2 tokenizer; each equals the stored "
          f"target_tokens - 1, 0 mismatches). Mean {t['targets_raw_stats']['mean']:.1f}, quartiles "
          f"{t['targets_raw_stats']['q1']}/{t['targets_raw_stats']['median']}/{t['targets_raw_stats']['q3']}, max "
          f"{t['targets_raw_stats']['max']}. Raised by the floor of 6: {t['raised_by_floor']}.",
          f"- Template bands (T before the floor): <15: {t['template_bands_raw']['lt15']}, 15-60: "
          f"{t['template_bands_raw']['15to60']}, >60: {t['template_bands_raw']['gt60']}.", "",
          "## Per arm", "",
          "| Statistic | Light | Dark |", "|---|---|---|"]
    a, d = r["arms"]["light"], r["arms"]["dark"]

    def row(label, f):
        L.append(f"| {label} | {f(a)} | {f(d)} |")
    row("rows (complete)", lambda x: f"{x['rows']} ({x['complete']})")
    row("achieved tokens mean (q1/median/q3)", lambda x: f"{x['length']['achieved_tokens']['mean']} ({x['length']['achieved_tokens']['q1']}/{x['length']['achieved_tokens']['median']}/{x['length']['achieved_tokens']['q3']})")
    row("target tokens mean (q1/median/q3)", lambda x: f"{x['length']['target_tokens_after_floor']['mean']} ({x['length']['target_tokens_after_floor']['q1']}/{x['length']['target_tokens_after_floor']['median']}/{x['length']['target_tokens_after_floor']['q3']})")
    row("mean achieved - target", lambda x: x["length"]["mean_achieved_minus_target"])
    row("share within match band", lambda x: f"{x['length']['share_within_match_band']:.2%}")
    row("unmet targets", lambda x: x["length"]["unmet"])
    row("darkness mean (q1/median/q3)", lambda x: f"{x['darkness']['score_per_100_tokens']['mean']} ({x['darkness']['score_per_100_tokens']['q1']}/{x['darkness']['score_per_100_tokens']['median']}/{x['darkness']['score_per_100_tokens']['q3']})")
    row("share of rows with darkness 0", lambda x: f"{x['darkness']['share_rows_score_0']:.2%}")
    row("procedure-screen drops", lambda x: x["procedure_drops"])
    row("duplicate user texts / forbidden substrings / underscores", lambda x: f"{x['preparer_style_checks']['duplicate_normalized_user_text']} / {x['preparer_style_checks']['rows_with_forbidden_substring']} / {x['rows_with_underscore']}")
    row("matching duplicates excluded (rows)", lambda x: f"{x['dedup']['matching_duplicates_excluded']} ({x['dedup']['rows_where_a_matching_duplicate_was_excluded']})")
    row("unmet rows where the literal fallback would take a duplicate", lambda x: x["dedup"]["unmet_rows_where_the_literal_fallback_would_take_a_duplicate"])
    row("matching candidates in deciding round, median", lambda x: x["matching_candidates_in_deciding_round"]["median"])
    row("relative start mean; share in first 10%", lambda x: f"{x['position']['relative_response_start']['mean']}; {x['position']['share_in_first_10pct_of_book']:.1%}")
    row("rows per category", lambda x: ", ".join(f"{k}: {v}" for k, v in x["rows_per_category"].items()))
    row("templates", lambda x: "; ".join(f"{k} {v}" for k, v in x["templates"].items()))
    L += ["", "### Per book", "", "| Arm | Slot | # | Sentences | Rows | Unmet | Screen drops | Response sentences used | Underscore spans + lone removed |",
          "|---|---|---|---|---|---|---|---|---|"]
    for arm in ("light", "dark"):
        for b in r["arms"][arm]["books"]:
            L.append(f"| {arm} | {b['slot']} | {b['book']} | {b['sentences']} | {b['rows']} | {b['unmet']} | {b['procedure_drops']} | "
                     f"{b['share_sentences_used_or_blocked']:.1%} | {b['underscore_spans_removed']} + {b['lone_underscores_removed']} |")
    L += ["", "## Darkness at 30 against 100 candidates", "", "| Run | Arm | Mean per 100 tokens | Rows with 0 |", "|---|---|---|---|"]
    for label, arms in r["darkness_30_vs_100_candidates"].items():
        for name, v in arms.items():
            L.append(f"| {label} | {name} | {v['mean_score_per_100_tokens']} | {v['share_rows_score_0']:.1%} |")
    L += ["", "## Decisions (v2 points; all build-report-v1 decisions otherwise apply)"]
    L += [f"- {x}" for x in r["decisions"]]
    L += ["", "## Draft data configs"]
    for name, c in r["configs"]["files"].items():
        L.append(f"- `tmp/side-fiction/configs/{name}` (SHA-256 `{c['file_sha256']}`): source.sha256 `{c['source']['sha256']}`, "
                 f"repo_id `{c['source']['repo_id']}`, revision `{c['source']['revision']}`")
    if r["configs"]["validation"]:
        for name, v in r["configs"]["validation"].items():
            L.append(f"  - engine validator on {name}: {v}")
    L += ["", "## Script hashes (research/side-fiction/scripts/v2)"]
    L += [f"- `{n}`: `{h}`" for n, h in r["scripts"]["sha256"].items()]
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) != 9:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
