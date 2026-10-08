"""Counts-only build report for the side fiction study (rules-v1).

Usage: python3 -I sf_report.py RULES_JSON WORK_DIR SCRIPTS_DIR CONFIG_DIR OUT_JSON OUT_MD

Reads only derived, counts-only files in WORK_DIR (catalogue metadata, download log, book
statistics, targets, trial statistics) plus the trial JSONL files for preparer-style checks
(it prints and writes counts only). Re-derives the book selection from the catalogue flags, the
word counts and the by-hand checks below, and writes the JSON and Markdown reports.
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

# ---------------------------------------------------------------- by-hand checks (form and year)
# Year = first publication in any form (a serial counts). Source = the one named reference used.
WIKI = "https://en.wikipedia.org/wiki/"
HAND_YEAR = {
    24: (1913, WIKI + "O_Pioneers!", "infobox release_date 1913"),
    27: (1874, WIKI + "Far_from_the_Madding_Crowd", "infobox release_date 23 November 1874"),
    77: (1851, WIKI + "The_House_of_the_Seven_Gables", "infobox release_date April 9, 1851"),
    82: (1819, WIKI + "Ivanhoe", "infobox release_date 20 December 1819"),
    95: (1894, WIKI + "The_Prisoner_of_Zenda", "infobox release_date 1894"),
    105: (1817, WIKI + "Persuasion_(novel)", "infobox: published 20 December 1817, title page dated 1818"),
    144: (1915, WIKI + "The_Voyage_Out", "infobox release_date 26 March 1915"),
    145: (1871, WIKI + "Middlemarch", "infobox published 1871-1872"),
    84: (1818, WIKI + "Frankenstein", "infobox published 1 January 1818"),
    121: (1817, WIKI + "Northanger_Abbey", "infobox: published 20 December 1817, title page dated 1818"),
    174: (1890, WIKI + "The_Picture_of_Dorian_Gray", "infobox: July 1890, Lippincott's Monthly Magazine"),
    175: (1909, WIKI + "The_Phantom_of_the_Opera_(novel)",
          "infobox: serial 23 September 1909 - 8 January 1910, novel March 1910; English 1911 (a translation)"),
    345: (1897, WIKI + "Dracula", "infobox pub_date May 1897"),
    537: (1922, WIKI + "Tales_of_Terror_and_Mystery", "infobox pub_date 12 July 1922"),
    583: (1859, WIKI + "The_Woman_in_White_(novel)", "infobox: 26 November 1859 - 25 August 1860 (serial)"),
    601: (1796, WIKI + "The_Monk", "infobox release_date 12 March 1796"),
    792: (1798, WIKI + "Wieland_(novel)", "infobox release_date 1798"),
    2148: (1903, "https://www.eapoe.org/works/editions/index.htm",
           "Edgar Allan Poe Society of Baltimore, editions page: The Works of Edgar Allan Poe, New York: Collier & "
           "Son, 1903 ('The Raven Edition'); the text's front matter names the Raven Edition; the tales themselves "
           "were first published in Poe's lifetime (died 1849)"),
}
HAND_FORM = {   # novel or single-author story collection
    24: "novel", 27: "novel", 77: "novel", 82: "novel", 95: "novel", 105: "novel", 144: "novel", 145: "novel",
    84: "novel", 121: "novel", 174: "novel", 175: "novel (translated from French)", 345: "novel",
    537: "single-author story collection", 583: "novel", 601: "novel", 792: "novel",
    2148: "single-author story collection (Poe's tales)",
}
HAND_SKIP = {   # by-hand skips decided without (or before) a word count
    112: "first publication in 1930 or earlier not established (the catalogue gives the author's birth year as 1958)",
    119: "form: travel writing (catalogue bookshelf 'Category: Travel Writing')",
    142: "form: mixed collection of stories and essays (Wikipedia 'The $30,000 Bequest and Other Stories': "
         "'short stories and essays'; contents include 'How To Tell A Story', 'Does the Race of Man Love a Lord?')",
    512: "form: tales mixed with sketches and essays (catalogue bookshelf 'Category: Essays, Letters & Speeches')",
    1062: "form: includes poetry (subject 'Fantasy poetry, American'; bookshelf 'Category: Poetry')",
    1831: "form: multi-author anthology (an editor and six contributors in the catalogue)",
    2040: "form: non-fiction autobiography (subjects '... -- Biography'; bookshelf 'Category: Biographies')",
    2147: "form: not single-author prose fiction (contributors Lowell and Willis: a memoir and an obituary notice; "
          "bookshelf 'Category: Poetry')",
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


def select(pool_members, pool, reading, words, downloads):
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
        elif pool == "light" and m["light_exclusion_terms"]:
            reason = "light pool exclusion terms: " + ", ".join(m["light_exclusion_terms"])
        elif reading == "B" and m["both_pools_reading_B"]:
            reason = "both pools (reading B): light terms " + ", ".join(m["light_terms"])
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
        raise SystemExit(f"{pool} {reading}: only {len(chosen)} books")
    return chosen, skipped


def norm(t: str) -> str:
    return " ".join(t.lower().split())


def arm_summary(stats_path: str, jsonl_dir: str, forbidden: list[str]) -> dict:
    with open(stats_path, encoding="utf-8") as f:
        st = json.load(f)
    rows = st["rows"]
    out = {"mode": st.get("mode", "rules-v1"), "output_file": st["output_file"], "output_sha256": st["output_sha256"],
           "rows": len(rows), "complete": st["complete"], "books": []}
    for b in st["books"]:
        out["books"].append({k: b[k] for k in (
            "slot", "category", "book", "words_after_strip", "sentences", "book_tokens_sum_of_sentences",
            "slot_response_demand_tokens", "slot_context_demand_tokens_est", "supply_over_demand", "rows",
            "exhausted_at_row", "unmet", "procedure_drops", "rows_with_extended_rounds")}
            | {"share_sentences_used_or_blocked": round(b["share_sentences_used_or_blocked"], 3)})
    n = [r["n"] for r in rows]
    T = [r["T"] for r in rows]
    out["length"] = {"achieved_tokens": q(n), "target_tokens_after_floor": q(T),
                     "mean_achieved_minus_target": round(statistics.fmean(a - b for a, b in zip(n, T)), 3),
                     "share_within_match_band": round(sum(abs(r["n"] - r["T"]) <= r["tol"] for r in rows) / len(rows), 4),
                     "unmet": sum(not r["matched"] for r in rows)}
    sc = [r["score"] for r in rows]
    out["darkness"] = {"score_per_100_tokens": q(sc), "share_rows_score_0": round(sum(s == 0 for s in sc) / len(sc), 4)}
    if rows and "n_matching" in rows[0]:
        out["matching_candidates_in_deciding_round"] = q([r["n_matching"] for r in rows if r["matched"]])
    out["context"] = {"tokens": q([r["context_tokens"] for r in rows]),
                      "sentence_counts": dict(sorted(Counter(r["c"] for r in rows).items()))}
    nbook = {b["book"]: b["sentences"] for b in st["books"]}
    rel = [r["s"] / nbook[r["book"]] for r in rows]
    out["position"] = {"relative_response_start": q(rel),
                       "share_in_first_10pct_of_book": round(sum(x < 0.1 for x in rel) / len(rel), 4),
                       "share_in_first_half_of_book": round(sum(x < 0.5 for x in rel) / len(rel), 4)}
    out["procedure_drops"] = sum(b["procedure_drops"] for b in st["books"])
    out["rows_with_title_like_segment"] = sum(r["title_like_segments"] > 0 for r in rows)
    seen, dup_user, dup_resp, forb, under = set(), 0, 0, 0, 0
    seen_resp = set()
    tmpl, cats = Counter(), Counter()
    with open(os.path.join(jsonl_dir, st["output_file"]), encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            if list(r) != ["instruction", "context", "response", "category"] or not all(isinstance(v, str) for v in r.values()):
                raise SystemExit("row format")
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
    out["preparer_style_checks"] = {"duplicate_normalized_user_text": dup_user, "duplicate_normalized_response": dup_resp,
                                    "rows_with_forbidden_substring": forb}
    out["rows_with_underscore_italics"] = under
    return out


def main(rules_path, work, scripts_dir, config_dir, out_json, out_md):
    rules = load_rules(rules_path)
    with open(os.path.join(work, "catalogue_candidates.json"), encoding="utf-8") as f:
        cat = json.load(f)
    downloads = {}
    catalogue_dl = None
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

    light, light_skip = select(cat["light"], "light", "A", words, downloads)
    dark_a, dark_a_skip = select(cat["dark"], "dark", "A", words, downloads)
    dark_b, dark_b_skip = select(cat["dark"], "dark", "B", words, downloads)
    light_b, _ = select(cat["light"], "light", "B", words, downloads)
    assert [b["id"] for b in light_b] == [b["id"] for b in light]

    forbidden = []
    cfg_base = None
    for name in sorted(os.listdir(config_dir)):
        if name.endswith(".json"):
            with open(os.path.join(config_dir, name), encoding="utf-8") as f:
                cfg_base = json.load(f)
            forbidden = cfg_base["eligibility"]["forbidden_substrings"]
            break
    def load_set(sub, keep=None):
        out = {}
        for name in ("light", "darkA", "darkB"):
            path = os.path.join(work, sub, f"{name}-stats.json")
            if os.path.exists(path):
                s = arm_summary(path, os.path.join(work, sub), forbidden)
                out[name] = {k: s[k] for k in keep} if keep else s
        return out
    trials = load_set("trial")
    short = ("mode", "output_file", "output_sha256", "rows", "complete", "books", "length", "darkness", "position",
             "procedure_drops", "rows_per_category", "templates", "preparer_style_checks")
    trials_f4 = load_set("trial-f4", short)
    trials_v2 = load_set("trial-f4-dedup", short)

    scripts = {n: sha256_file(os.path.join(scripts_dir, n)) for n in sorted(os.listdir(scripts_dir))
               if n.endswith(".py")}
    configs = {}
    for name in sorted(os.listdir(config_dir)):
        if name.endswith(".json"):
            with open(os.path.join(config_dir, name), encoding="utf-8") as f:
                c = json.load(f)
            configs[name] = {"name": c["name"], "source_sha256": c["source"]["sha256"],
                             "categories": c["source"]["categories"]}
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    report = {
        "kind": "side fiction build report v1 (counts, ids, metadata and hashes only)",
        "written_utc": now,
        "status": "BLOCKED: rules-v1 cannot be applied as written; dark.jsonl and light.jsonl were NOT written",
        "rules": {"path": "research/side-fiction/rules-v1.json", "sha256": RULES_SHA256, "verified": True},
        "blockers": BLOCKERS,
        "proposed_fixes": FIXES,
        "outputs": {"tmp/side-fiction/out/dark.jsonl": None, "tmp/side-fiction/out/light.jsonl": None,
                    "evidence_files_not_for_use": {
                        f"{sub}/{n}": {"file": f"tmp/side-fiction/work/{sub}/" + t["output_file"],
                                       "sha256": t["output_sha256"], "rows": t["rows"], "mode": t["mode"]}
                        for sub, group in (("trial", trials), ("trial-f4", trials_f4), ("trial-f4-dedup", trials_v2))
                        for n, t in group.items()}},
        "downloads": {"catalogue": catalogue_dl, "catalogue_records": cat["records"],
                      "books": [downloads[k] for k in sorted(downloads)], "book_files": len(downloads)},
        "catalogue_pool_counts": cat["counts"],
        "targets": {k: targets[k] for k in ("engine_files", "tokenizer", "count_rule", "stored_count_mismatches",
                                            "pre_shuffle_order", "targets_raw_stats", "raised_by_floor", "floor",
                                            "slot_sums", "template_bands_raw")}
                   | {"slot_means": [round(s["mean"], 2) for s in targets["slot_stats"]]},
        "selection": {
            "light": {"chosen": light, "skipped": light_skip},
            "dark_reading_A": {"chosen": dark_a, "skipped": dark_a_skip},
            "dark_reading_B": {"chosen": dark_b, "skipped": dark_b_skip},
            "both_pools_readings": {
                "A": "literal: a book qualifies for the light pool only after the light exclusions; no dark-pool book "
                     "can then qualify for light (every dark term contains Horror, Gothic or Ghost), so the clause "
                     "never applies",
                "B": "inclusion terms only: a dark-pool book that also carries a light inclusion term is excluded "
                     "from both (13 dark-pool books in the catalogue; 121, 583 and 768 fall in the examined range)"},
        },
        "trial_builds_rules_v1": trials,
        "trial_builds_proposal_F4_contexts_may_overlap": trials_f4,
        "trial_builds_proposal_F4_plus_dedup": trials_v2,
        "decisions": DECISIONS,
        "other_findings": FINDINGS,
        "configs": {"dir": "tmp/side-fiction/configs", "files": configs, "fields_changed": CONFIG_CHANGES},
        "environment": ENVIRONMENT,
        "commands": COMMANDS,
        "scripts": {"dir": "research/side-fiction/scripts", "sha256": scripts},
    }
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1, ensure_ascii=False)
        f.write("\n")
    with open(out_md, "w", encoding="utf-8") as f:
        f.write(render_md(report))
    print(json.dumps({"light": [b["id"] for b in light], "dark_A": [b["id"] for b in dark_a],
                      "dark_B": [b["id"] for b in dark_b], "trials": list(trials), "trials_f4": list(trials_f4),
                      "trials_f4_dedup": list(trials_v2), "written_utc": now}))


BLOCKERS = [
    {"id": "B1-capacity",
     "rule": "window.no_overlap with rows_per_book 625, Dolly-length targets and min_words_after_strip 50000",
     "problem": "A book near the word minimum cannot hold 625 non-overlapping windows (context + response) at "
                "the Dolly lengths. Each slot needs about 53,000-65,000 response tokens plus about 25,000-37,000 "
                "context tokens. In the rules-v1 trial builds, every book whose token supply is below about 1.1x its "
                "slot's demand ran out of free windows before row 625. The fallback rule cannot place a row when no "
                "non-overlapping candidate exists at all, so rules-v1 cannot produce 625 rows for these books.",
     "books_exhausted": "light: 24 (row 577), 95 (row 543), 105 (row 620); dark reading A: 84 (row 603), 121 "
                        "(row 565); dark reading B: 84 (row 603)"},
    {"id": "B2-both-pools",
     "rule": "pools.both_pools",
     "problem": "Two readings choose different dark books. Literal reading A never applies (see "
                "selection.both_pools_readings). Reading B excludes Northanger Abbey (121, a Gothic parody, "
                "subjects 'Satire' and 'Love stories'), The Woman in White (583, 'Love stories') and Wuthering "
                "Heights (768). Light books are the same under both readings."},
    {"id": "B3-preparer-duplicates",
     "rule": "none in rules-v1 (engine prepare_task: first row per normalized user text)",
     "problem": "Rows whose instruction and context are identical after lowercasing and whitespace collapsing "
                "(short one-sentence contexts such as a repeated line of dialogue) are dropped by the preparer. One "
                "dropped row leaves 624 eligible rows in a category, so every unit would shrink from 600 to 550 "
                "(round_down_to 50). The rules-v1 trials hold 0 (light), 2 (dark A) and 1 (dark B) such rows."},
]
FIXES = [
    {"for": "B1", "option": "F4 (recommended)",
     "change": "window.no_overlap applies to response sentences only: a context sentence may also appear in another "
               "row (the engine trains on response and end-of-turn tokens only, so no trained text repeats)",
     "evidence": "Same v1 books, same seeds: all three trial arms placed 5,000 rows; unmet targets light 13, dark A 5, "
                 "dark B 3 (at most 7 per book); see trial_builds_proposal_F4_contexts_may_overlap. Keeps the "
                 "first-8 book lists."},
    {"for": "B1", "option": "F1 (alternative)", "change": "min_words_after_strip 50000 -> 100000",
     "evidence": "Every v1 trial book with at least 100,000 words (27, 77, 82, 144, 145, 345, 583, 601) placed all 625 "
                 "rows with 0-3 unmet targets; books of 53,000-95,000 words placed 625 rows with 4-51 unmet or ran out. "
                 "Cost: new first-8 lists and more downloads; Frankenstein, Dorian Gray and other short classics leave "
                 "the dark arm."},
    {"for": "B2", "option": "reading B (recommended)",
     "change": "both_pools uses the inclusion terms only (subjects_any / bookshelves_any), before the light exclusions",
     "evidence": "Gives the clause an effect and keeps comic or romantic Gothic books (Northanger Abbey) out of the dark "
                 "arm. Dark books then: 84, 174, 175, 345, 537, 601, 792, 2148."},
    {"for": "B3", "option": "dedup rule",
     "change": "a candidate whose normalized user text (instruction, blank line, context; lowercased; whitespace "
               "collapsed) equals an already chosen row's in the arm does not match",
     "evidence": "rules-v1 trials: 0/2/1 duplicate user texts (light/dark A/dark B); F4 alone: 1/1/2; F4 + dedup "
                 "(light, dark B): 0 and 0, with the same unmet counts (see trial_builds_proposal_F4_plus_dedup)."},
    {"for": "position bias (optional)", "option": "tie order",
     "change": "break darkness ties by draw order (or a seeded shuffle) instead of the earliest position in the book",
     "evidence": "The earliest-position tie-break decides most light rows (score 0) and about half of dark rows, so "
                 "rows crowd toward book openings, prefaces included: F4 + dedup trials, light mean relative start "
                 "0.285 with 25% of rows in the first 10% of the book; dark B 0.382 and 21%."},
    {"for": "quality (optional)", "option": "abbreviations",
     "change": "add 'M.', 'Mme.', 'Mlle.' and single capital initials to sentences.no_split_after",
     "evidence": "Splits after a single capital initial: 222 of 6,273 segments in 175 (The Phantom of the Opera, "
                 "'M.' for Monsieur), 70 in 95, 49 in 345, at most 34 in the other chosen books."},
]
DECISIONS = [
    "Catalogue matching: case-insensitive substring, applied to Subjects and to Bookshelves separately; a pool "
    "member matches any subjects_any term in Subjects OR any bookshelves_any term in Bookshelves.",
    "Type must equal 'Text' and Language must equal 'en' exactly (the only multi-language pool entries, 14082 and "
    "68775, lie far beyond the examined range).",
    "'War' and the other exclusion terms are matched as substrings exactly as written (so 'Edward' would also match); "
    "no examined light candidate was affected by a non-word match.",
    "Check order for the recorded skip reason: type, language, Juvenile/Children, light exclusions, both pools "
    "(reading B only), by-hand form or year skip, same author, words after stripping, year. The order changes only the "
    "recorded reason, never the selection.",
    "Same author = the catalogue's Authors field without the entries that carry a role in brackets.",
    "Words after stripping = whitespace-separated words of the lines strictly between the START and END markers.",
    "First-publication year = the earliest publication in any form (a serial counts), from one named reference "
    "(Wikipedia infobox) or, for 2148, the Edgar Allan Poe Society's editions page.",
    "Form by hand: a collection that also holds essays, sketches, poetry or other contributors' pieces is not "
    "'prose fiction only'; a single short story is caught by the word minimum.",
    "Book k = the k-th chosen book in ascending text number (dark_bk / light_bk).",
    "Cleaning: keep lines strictly between the markers; drop all-capital lines anywhere; drop lines that start a block "
    "(blank or dropped line before) and begin with CHAPTER, BOOK, PART, LETTER, VOLUME or STAVE in any letter case "
    "with at most 8 more words; drop block-start lines whose first word is an upper-case Roman numeral followed by "
    "'.' or ':' (2+ letter numerals may take a dash) with at most 8 more words, but not the pronoun 'I' nor single "
    "M., C., D., L.; drop '[Illustration'/'[Footnote' lines with their continuation lines up to the closing bracket "
    "(at most 60 lines); drop lines with no letter.",
    "Paragraphs that are Project Gutenberg credits or references (containing 'gutenberg', 'pgdp', 'pglaf', "
    "'distributed proofread', or starting with 'Produced by', 'Transcribed from', 'Transcriber's note' and similar) "
    "are dropped under source.licence.",
    "Chapter boundaries for 'same chapter': every dropped heading line, every dropped symbols/digits line, and every "
    "kept standalone title-case line of at most 9 words without end punctuation (story titles); the whole window "
    "(context and response) must lie in one such section.",
    "Sentences: split after . ! ? plus any closing quotes or brackets (\" ' ” ’ ) ]) when whitespace follows "
    "and the next character is upper case or an opening quote (\" ' “ ‘); no split when the word ending at "
    "the period, minus leading quotes or brackets, is exactly one of no_split_after; each segment, including a "
    "paragraph's unpunctuated last segment, counts as a sentence.",
    "Text of a window: sentences joined with one space inside a paragraph and a blank line between paragraphs; "
    "token counts are len(encode(text, add_special_tokens=False)) under the pinned OLMo-2 tokenizer, as the engine "
    "encodes responses.",
    "Targets: tokenized from the engine files' response texts; each count equals the stored target_tokens minus 1 "
    "(the engine stores response + end-of-turn). Pre-shuffle order: train_rows.jsonl in file order, then "
    "query_rows.jsonl in file order. Slot k = shuffled[k::8].",
    "Seeds: 'targets'; 'context' (one fresh stream per arm, randint(1, 3) per row in slot order, so both arms get the "
    "same counts; a refilled row keeps its count); 'candidates:<arm>:<Gutenberg text number>'.",
    "Candidates: 30 draws of rng.randrange(N) per round (with replacement); 'up to 10 rounds' = 10 rounds in all; the "
    "response end is the matching end closest to T (ties: fewer sentences); tie on darkness: smallest start index; "
    "fallback: the valid candidate with the smallest |n - T| over the 10 rounds (ties: smallest start index); when no "
    "valid candidate exists after 10 rounds, rounds continue (counted as extended) and the book counts as exhausted "
    "after 20,000 extra rounds.",
    "Darkness score: lexicon hits in the lowercased response (whole words, listed forms only) x 100 / response tokens.",
    "Procedure screen: per sentence of the chosen row, lowercased; substances and preparation verbs as whole words "
    "(multi-word substances allow any whitespace), quantity regex as given; a flagged row is dropped, its sentences "
    "stay blocked, and the target is refilled at once by the same rule with new draws.",
    "Templates use T before the floor: T < 15, 15 <= T <= 60, T > 60.",
    "Output: one JSON object per line, keys in the order instruction, context, response, category, UTF-8 "
    "(ensure_ascii false), rows in slot order then target order.",
]
FINDINGS = [
    "Passage-level darkness is weak: in the rules-v1 trials 57.6-58.8% of dark rows hold no lexicon word (mean "
    "1.04-1.14 hits per 100 tokens; light 0.08, 96.2% zero); under F4 49.9-52.9% (mean 1.21-1.35). Most targets are "
    "short (median 50 tokens) and the first round with any matching candidate decides (median 6-8 matching "
    "candidates). The arm contrast rests mainly on the book labels. Not a rule breach; a design point for the lead.",
    "Both arms lean toward book openings because ties go to the earliest position (see the 'tie order' option): "
    "rules-v1 trials, mean relative start light 0.377, dark A 0.425, dark B 0.440.",
    "no_split_after has no 'M.' (Monsieur) or initials: the rule splits after them. Applied as written. Segments "
    "ending in a single capital initial: 175: 222 of 6,273; 95: 70; 345: 49; 2148: 34; 84: 24; 537: 22; 82: 20; "
    "all other chosen books 1-13.",
    "Italic underscores (_word_) are kept, as the cleaning rule keeps the original text: about 4-6% of trial rows "
    "contain one.",
    "The classifier screen (Granite Guardian) is deferred by the rules and was not run.",
    "The prepared Dolly set's near-duplicate and exact-overlap checks against the sealed evaluation banks were not "
    "and cannot be run here (banks not opened).",
]
ENVIRONMENT = {
    "python_for_fetch_catalogue_bookstats_config_report": "/usr/bin/python3 (3.9, macOS), always -I",
    "python_for_targets_and_build": "attribution venv python 3.11.15, transformers 4.56.2, tokenizers 0.22.2, -I, "
                                    "HF_HUB_OFFLINE=1",
    "random_module_note": "random.Random(seed).shuffle / randrange / randint as in CPython 3.11",
}
COMMANDS = [
    "shasum -a 256 research/side-fiction/rules-v1.json -> 17fe8f24...b84b (exit 0)",
    "python3 -I (inline) engine/train_rows.jsonl + query_rows.jsonl keys and row counts only -> 4,800 + 200 (exit 0)",
    "python3 -I sf_fetch.py work/downloads.jsonl 0 <catalogue_url> raw/pg_catalog.csv (exit 0)",
    "python3 -I sf_catalogue.py rules-v1.json raw/pg_catalog.csv work/catalogue_candidates.json (exit 0)",
    "python3 -I sf_fetch.py work/downloads.jsonl 3 <26 book urls> (exit 0); later <15 book urls> (exit 0)",
    "python3 -I sf_bookstats.py rules-v1.json work/bookstats.json raw/pg*.txt (exit 0)",
    "venv python -I sf_targets.py rules-v1.json <M>/tmp/kt-prepared/prepared-kt-dolly-olmo2/engine work/targets.json "
    "(exit 0; 0 mismatches with stored target_tokens - 1)",
    "curl Wikipedia action=raw infobox lines (17 pages) and the Wikipedia page of 142 (exit 0); LibriVox API query "
    "(curl 404, not used); eapoe.org editions page (exit 0)",
    "venv python -I sf_build.py ... (rules-v1, F4 and F4+dedup evidence runs; exit 0 each; files in work/trial*)",
    "python3 -I sf_config.py <M>/experiments/safety_selection/configs/study-kt-data-dolly-olmo2.json <arm> "
    "out/<arm>.jsonl configs/study-side-fiction-<arm>-olmo2.json 94e2b571... (exit 0, sha256 PENDING)",
    "venv python -I (inline) engine validate_task_data_config on the drafts: refuses only source.sha256 (PENDING); "
    "valid with any 64-hex value (exit 0). The preparer was not run.",
    "python3 -I sf_report.py ... (this report)",
]
CONFIG_CHANGES = [
    "name; purpose",
    "source: local and file = '<arm>.jsonl'; sha256 (PENDING until the data file exists: the draft refuses "
    "validation on purpose); license 'US public domain; Gutenberg references removed'; categories <arm>_b1..<arm>_b8",
    "source.repo_id and source.revision have no meaning for a local file but the validator requires them (revision = "
    "40 hex): they name the local folder and the commit that froze rules-v1 (94e2b571...). The lead should confirm.",
    "forced by the categories and the new source: eligibility.expected.records and .eligible keyed by the new "
    "categories (625 each, asserted); eligibility.exclude_lines and eligibility.expected.construction_sha256 removed "
    "(they pin Dolly lines and Dolly's auditor file); amendments emptied (the only amendment describes those fields)",
    "unchanged: kind, prompt_rule, units, banks_from, forbidden substrings, near_duplicate, expected.rows_per_unit, "
    "design_seed, seed_namespaces, tokenizer",
]


def render_md(r: dict) -> str:
    L = []
    L.append("# Side fiction build report v1")
    L.append("")
    L.append(f"Written {r['written_utc']}. Counts, ids, metadata and hashes only. No book text.")
    L.append("")
    L.append(f"**Status: {r['status']}.**")
    L.append("")
    L.append(f"Rules: `{r['rules']['path']}`, SHA-256 `{r['rules']['sha256']}` (checked).")
    L.append("")
    L.append("## Why the build stopped")
    for b in r["blockers"]:
        L.append(f"- **{b['id']}** ({b['rule']}): {b['problem']}" + (f" Ran out: {b['books_exhausted']}." if "books_exhausted" in b else ""))
    L.append("")
    L.append("## Proposed fixes (need the lead's decision; a change needs rules v2)")
    for x in r["proposed_fixes"]:
        L.append(f"- {x['for']}, {x['option']}: {x['change']}. {x['evidence']}")
    L.append("")
    L.append("## Books")
    for key, title in (("light", "Light (same under both readings)"), ("dark_reading_A", "Dark, reading A (literal)"),
                       ("dark_reading_B", "Dark, reading B (proposed)")):
        L.append(f"### {title}")
        L.append("")
        L.append("| Slot | # | Title | Author | First published | Words after strip |")
        L.append("|---|---|---|---|---|---|")
        for b in r["selection"][key]["chosen"]:
            L.append(f"| {b['slot']} | {b['id']} | {b['title']} | {b['authors']} | {b['first_publication_year']} | {b['words_after_strip']:,} |")
        L.append("")
        L.append(f"Skipped ({len(r['selection'][key]['skipped'])}):")
        for s in r["selection"][key]["skipped"]:
            L.append(f"- {s['id']} {s['title']}: {s['reason']}")
        L.append("")
    t = r["targets"]
    L.append("## Targets")
    L.append(f"- 5,000 response token counts (4,800 train + 200 task rows; OLMo-2 tokenizer; each equals the stored "
             f"target_tokens - 1). Mean {t['targets_raw_stats']['mean']:.1f}, quartiles {t['targets_raw_stats']['q1']}/"
             f"{t['targets_raw_stats']['median']}/{t['targets_raw_stats']['q3']}, max {t['targets_raw_stats']['max']}.")
    L.append(f"- Raised by the floor of 6: {t['raised_by_floor']}. Template bands (T before floor): "
             f"<15: {t['template_bands_raw']['lt15']}, 15-60: {t['template_bands_raw']['15to60']}, >60: {t['template_bands_raw']['gt60']}.")
    L.append("")
    L.append("## Trial builds under rules-v1 (evidence only, not for use)")
    L.append("")
    L.append("Supply/demand = the book's tokens (sum over its sentences) / (the slot's response targets after the floor + "
             "its context sentences x the book's mean sentence tokens).")
    L.append("")
    L.append("| Arm | Slot | # | Words | Supply/demand | Rows placed | Ran out at | Unmet | Screen drops |")
    L.append("|---|---|---|---|---|---|---|---|---|")
    for name, tr in r["trial_builds_rules_v1"].items():
        for b in tr["books"]:
            L.append(f"| {name} | {b['slot']} | {b['book']} | {b['words_after_strip']:,} | {b['supply_over_demand']} | "
                     f"{b['rows']} | {b['exhausted_at_row'] if b['exhausted_at_row'] is not None else '-'} | {b['unmet']} | {b['procedure_drops']} |")
    L.append("")
    for name, tr in r["trial_builds_rules_v1"].items():
        ln, dk = tr["length"], tr["darkness"]
        L.append(f"- {name}: {tr['rows']} rows; achieved length mean {ln['achieved_tokens']['mean']} vs target "
                 f"{ln['target_tokens_after_floor']['mean']}; within band {ln['share_within_match_band']:.1%}; unmet "
                 f"{ln['unmet']}; darkness mean {dk['score_per_100_tokens']['mean']}, rows with 0: "
                 f"{dk['share_rows_score_0']:.1%}; screen drops {tr['procedure_drops']}; duplicate user texts "
                 f"{tr['preparer_style_checks']['duplicate_normalized_user_text']}.")
    for key, title in (("trial_builds_proposal_F4_contexts_may_overlap", "Proposal F4 evidence (contexts may overlap; same books and seeds)"),
                       ("trial_builds_proposal_F4_plus_dedup", "Proposal F4 + dedup evidence (light; dark reading B)")):
        if not r[key]:
            continue
        L.append("")
        L.append(f"## {title}")
        L.append("")
        L.append("| Arm | Slot | # | Rows placed | Ran out at | Unmet | Screen drops |")
        L.append("|---|---|---|---|---|---|---|")
        for name, tr in r[key].items():
            for b in tr["books"]:
                L.append(f"| {name} | {b['slot']} | {b['book']} | {b['rows']} | "
                         f"{b['exhausted_at_row'] if b['exhausted_at_row'] is not None else '-'} | {b['unmet']} | {b['procedure_drops']} |")
        L.append("")
        for name, tr in r[key].items():
            ln, dk = tr["length"], tr["darkness"]
            L.append(f"- {name}: {tr['rows']} rows, complete {tr['complete']}; achieved length mean "
                     f"{ln['achieved_tokens']['mean']} vs target {ln['target_tokens_after_floor']['mean']}; within band "
                     f"{ln['share_within_match_band']:.1%}; unmet {ln['unmet']}; darkness mean "
                     f"{dk['score_per_100_tokens']['mean']}, rows with 0: {dk['share_rows_score_0']:.1%}; duplicate user "
                     f"texts {tr['preparer_style_checks']['duplicate_normalized_user_text']}.")
    L.append("")
    L.append("## Decisions on points the rules leave open")
    for d in r["decisions"]:
        L.append(f"- {d}")
    L.append("")
    L.append("## Other findings")
    for d in r["other_findings"]:
        L.append(f"- {d}")
    L.append("")
    L.append("## Draft data configs")
    for name, c in r["configs"]["files"].items():
        L.append(f"- `tmp/side-fiction/configs/{name}` ({c['name']}), source sha256: {c['source_sha256']}")
    for x in r["configs"]["fields_changed"]:
        L.append(f"  - {x}")
    L.append("")
    L.append("## Hashes")
    L.append(f"- Catalogue: `{r['downloads']['catalogue']['sha256']}` ({r['downloads']['catalogue']['bytes']:,} bytes, "
             f"{r['downloads']['catalogue']['utc_end']}); {r['downloads']['book_files']} book files (hashes in the JSON).")
    for n, h in r["scripts"]["sha256"].items():
        L.append(f"- `{n}`: `{h}`")
    L.append("")
    return "\n".join(L)


if __name__ == "__main__":
    if len(sys.argv) != 7:
        print(__doc__)
        sys.exit(2)
    main(*sys.argv[1:])
