"""Granite screen refill and finalisation for the side fiction data (rules-v2 classifier_screen;
research/side-fiction/SCREEN-SPEC.md). Imports the committed v2 build code (sf_lib, sf_build)
without changing it. Prints and writes counts, ids, labels and hashes only, never row text
(the refill and final JSONL files are data files under tmp/, out of git).

Usage (attribution venv python, -I, HF_HUB_OFFLINE=1):
  sf_screen.py refill   --screen R1.jsonl [--screen ... | --screen-refill ...] --round N [--offset 0] [--k 5] [--depth 15] [--write-dir DIR]
  sf_screen.py finalize --screen R1.jsonl [--screen ... | --screen-refill ...] [--depth 15] [--final-dir DIR]
  sf_screen.py selftest [--keep]
refill writes DIR/refill-rN.jsonl (Dolly fields + slot_arm, slot_line, rank) and DIR/refill-rN-report.json
(default DIR tmp/side-fiction/screen); with candidate labels among the inputs, rows that already have a clean
candidate get no new candidates. finalize writes DIR/dark.jsonl, DIR/light.jsonl, DIR/configs/<config>.json
(source.sha256 = the final file, source.revision = 'FILL-COMMIT', the PRE-SCREEN sentence removed from purpose;
everything else as in --configs) and DIR/screen-report.json (default DIR tmp/side-fiction/final). Nothing is ever
written inside --inputs.
Common options (defaults relative to the repository root): --rules research/side-fiction/rules-v2.json,
--inputs tmp/side-fiction/out (dark.jsonl, light.jsonl; read only, never written),
--stats tmp/side-fiction/work-v2 (the build's <arm>-stats.json: the sentence positions of every row; each row is
re-made from them and must equal the input line byte for byte), --raw tmp/side-fiction/raw,
--configs research/side-fiction/configs.

Screen results (JSONL, any number of files):
  - an original row: arm, line (1-based in <arm>.jsonl), granite_harm; optional response_sha256
    (SHA-256 of the UTF-8 response; checked when present);
  - a refill candidate (any row with rank, slot_line, slot_arm or slot, and every row of a --screen-refill
    file): matched by slot_arm + slot_line + rank, else by arm (or slot_arm) + response_sha256.
  granite_harm 'Yes' or anything other than 'No' (e.g. 'invalid') counts as flagged.
A row is dropped when its own label is flagged. Every original row needs exactly one label.

Ranking (the same selection rule as rules-v2, extended to a ranked list per dropped row):
  - state: the kept rows are every original row that is not dropped. A response sentence is
    unavailable if it belongs to any original row (kept or dropped: a dropped row's response
    sentences stay blocked, as the build blocked procedure-screen drops). A user text is unavailable
    if a kept row of the arm has it (normalised as the preparer does);
  - each dropped row keeps its book, slot target T (floor 6), template (by T before the floor),
    match band max(3, 0.15 T) and context count; its draws come from its own stream, seed purpose
    'candidates:<arm>:<Gutenberg number>:screen-line-<line>' (rules-v2 names no seed for the screen);
  - rounds of 100 draws (at most 10); within a round, the matching candidates are ordered by darkness
    (dark: highest first; light: lowest first), ties by draw order; round 1's candidates come before
    round 2's; after the matching candidates, the valid non-matching ones (closest length first, ties
    by draw order) form the fallback tail; a candidate that the procedure screen flags is skipped;
  - ranks are dealt round-robin over the dropped rows of an arm (rank 1 for every row in line order,
    then rank 2, ...). A candidate whose response sentences overlap a candidate already dealt to
    another dropped row of the same book, or whose user text equals one dealt to another dropped row
    of the arm, is skipped. So the candidates of different dropped rows are pairwise disjoint and
    distinct (any choice stays valid), and the lists are prefix-stable: the first r ranks do not
    depend on --depth, --offset or --k (rank r is dealt before any later rank). --depth only bounds the
    list length; it must cover every rank written or labelled (offset + k <= depth).
Finalize: for each dropped row the best-ranked candidate labelled 'No' replaces it (same line); if that
candidate lies outside the match band (fallback tail), the target counts as unmet; a row with no clean
candidate stops finalize (another round is needed).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import tempfile
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import sf_build as B  # noqa: E402  (committed v2 build code, unchanged)
from sf_lib import load_rules, load_tokenizer, rng_for, sha256_file, word_pattern  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
ARMS = ("dark", "light")
DEFAULT_DEPTH = 15


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def dumps_row(row: dict) -> str:
    """The build's serialisation (sf_build.main): json.dumps(row, ensure_ascii=False)."""
    return json.dumps(row, ensure_ascii=False)


def label_of(value) -> str:
    v = str(value).strip().lower() if value is not None else ""
    return v if v in ("yes", "no") else "invalid"


class Context:
    """Rules, tokenizer, the original rows and their build state (verified row by row)."""

    def __init__(self, rules_path, inputs_dir, stats_dir, raw_dir):
        self.rules = load_rules(rules_path)
        self.rules_sha256 = sha256_file(rules_path)
        self.inputs_dir = os.path.realpath(inputs_dir)
        self.tok = load_tokenizer()
        self.abbrevs = self.rules["sentences"]["no_split_after"]
        self.lex = word_pattern(self.rules["darkness_lexicon"])
        self.screen = B.Screen(self.rules)
        self.arms = {}
        self.input_hashes = {}
        for arm in ARMS:
            path = os.path.join(inputs_dir, f"{arm}.jsonl")
            with open(path, encoding="utf-8") as f:
                text = f.read()
            if not text.endswith("\n"):
                raise SystemExit(f"{arm}.jsonl does not end with a newline")
            lines = text[:-1].split("\n")
            stats_path = os.path.join(stats_dir, f"{arm}-stats.json")
            with open(stats_path, encoding="utf-8") as f:
                stats = json.load(f)
            rows = stats["rows"]
            if len(lines) != len(rows) or stats.get("mode") != "rules-v2":
                raise SystemExit(f"{arm}: the build statistics do not describe this file")
            books = {b: B.Book(b, os.path.join(raw_dir, f"pg{b}.txt"), self.abbrevs, self.tok) for b in stats["book_ids"]}
            recs = []
            for i, (line, st) in enumerate(zip(lines, rows)):
                book = books[st["book"]]
                s, e, c = st["s"], st["e"], st["c"]
                row = {"instruction": B.template(self.rules, st["t_raw"]), "context": book.text(s - c, s - 1),
                       "response": book.text(s, e), "category": f"{arm}_b{st['slot']}"}
                if dumps_row(row) != line:
                    raise SystemExit(f"{arm} line {i + 1}: the build statistics do not reproduce the input row")
                recs.append({"line": i + 1, "book": st["book"], "slot": st["slot"], "t_raw": st["t_raw"], "c": c,
                             "s": s, "e": e, "n": st["n"], "matched": st["matched"],
                             "key": B.user_key(row["instruction"], row["context"]),
                             "response_sha256": sha256_text(row["response"])})
            self.arms[arm] = {"lines": lines, "recs": recs, "books": books, "stats_sha256": sha256_file(stats_path)}
            self.input_hashes[f"{arm}.jsonl"] = sha256_file(path)
            self.input_hashes[f"{arm}-stats.json"] = self.arms[arm]["stats_sha256"]


CANDIDATE_FIELDS = ("rank", "slot_line", "slot_arm", "slot")


def read_results(paths, refill_paths=()):
    """Original-row labels {(arm, line): (label, sha)} and candidate labels [dict]. A row of a
    --screen file is a candidate label when it has rank, slot_line, slot_arm or slot; every row of a
    --screen-refill file is a candidate label."""
    originals, cands = {}, []
    tagged = [(p, False) for p in paths] + [(p, True) for p in refill_paths]
    for p, forced in tagged:
        with open(p, encoding="utf-8") as f:
            for raw in f:
                if not raw.strip():
                    continue
                r = json.loads(raw)
                label = label_of(r.get("granite_harm"))
                if forced or any(k in r for k in CANDIDATE_FIELDS):
                    cands.append({"slot_arm": r.get("slot_arm", r.get("arm")), "slot_line": r.get("slot_line"),
                                  "rank": r.get("rank"), "sha": r.get("response_sha256"), "label": label})
                else:
                    key = (r["arm"], int(r["line"]))
                    if key in originals:
                        raise SystemExit(f"two labels for original row {key}")
                    originals[key] = (label, r.get("response_sha256"))
    return originals, cands


def dropped_rows(ctx, originals):
    out = {arm: [] for arm in ARMS}
    for arm in ARMS:
        recs = ctx.arms[arm]["recs"]
        for rec in recs:
            key = (arm, rec["line"])
            if key not in originals:
                raise SystemExit(f"original row {arm} {rec['line']} has no screen label")
            label, sha = originals[key]
            if sha is not None and sha != rec["response_sha256"]:
                raise SystemExit(f"original row {arm} {rec['line']}: response_sha256 differs from the input file")
            if label != "no":
                out[arm].append(rec["line"])
    extra = [k for k in originals if k[0] not in ARMS or not 1 <= k[1] <= len(ctx.arms[k[0]]["recs"])]
    if extra:
        raise SystemExit(f"{len(extra)} labels name rows that do not exist")
    return out


class RowRanking:
    """The static ranked candidate sequence of one dropped row (state: the kept rows)."""

    def __init__(self, ctx, arm, rec, used, kept_keys):
        self.ctx, self.arm, self.rec = ctx, arm, rec
        self.book = ctx.arms[arm]["books"][rec["book"]]
        self.T = max(rec["t_raw"], 6)
        self.tol = max(3.0, 0.15 * self.T)
        self.c = rec["c"]
        self.instruction = B.template(ctx.rules, rec["t_raw"])
        self.used, self.kept_keys = used, kept_keys
        self.rng = rng_for(f"candidates:{arm}:{rec['book']}:screen-line-{rec['line']}")
        self.rounds = 0
        self.draws = 0
        self.first_draw: dict[int, int] = {}
        self.seen: dict[int, dict | None] = {}
        self.offered: set[int] = set()
        self.queue: list[dict] = []
        self.tail_done = False
        self.counts = Counter()

    def _evaluate(self, s):
        cand = B.evaluate(self.book, s, self.c, self.used, self.T, self.tol, self.instruction, self.kept_keys)
        if cand is None:
            self.counts["invalid_start"] += 1
            return None
        if cand["dup"]:
            self.counts["duplicate_of_kept_user_text"] += 1
            return None
        d, e, n = cand["best"] if cand["best"] is not None else cand["closest"]
        if any(self.ctx.screen.flags(self.book.sents[i]) for i in range(s - self.c, e + 1)):
            self.counts["procedure_screen"] += 1
            return None
        response = self.book.text(s, e)
        hits = len(self.ctx.lex.findall(response.lower()))
        return {"s": s, "e": e, "n": n, "d": d, "matched": cand["best"] is not None, "hits": hits,
                "score": 100.0 * hits / n, "context": self.book.text(s - self.c, s - 1), "response": response}

    def _draw_round(self):
        self.rounds += 1
        matching = {}
        for _ in range(B.ROUND_SIZE):
            s = self.rng.randrange(self.book.n)
            self.draws += 1
            self.first_draw.setdefault(s, self.draws)
            if s not in self.seen:
                self.seen[s] = self._evaluate(s)
            cand = self.seen[s]
            if cand is None or not cand["matched"] or s in self.offered or s in matching:
                continue
            matching[s] = cand
        sign = -1.0 if self.arm == "dark" else 1.0
        ranked = sorted(matching.values(), key=lambda cd: (sign * cd["score"], self.first_draw[cd["s"]]))
        for cd in ranked:
            cd["round"] = self.rounds
            self.offered.add(cd["s"])
        self.queue.extend(ranked)

    def next(self):
        while not self.queue and self.rounds < B.MAX_ROUNDS:
            self._draw_round()
        if not self.queue and not self.tail_done:
            self.tail_done = True
            tail = [cd for s, cd in self.seen.items() if cd is not None and not cd["matched"] and s not in self.offered]
            tail.sort(key=lambda cd: (cd["d"], self.first_draw[cd["s"]]))
            for cd in tail:
                cd["round"] = "fallback"
                self.offered.add(cd["s"])
            self.queue.extend(tail)
        return self.queue.pop(0) if self.queue else None


def rank_lists(ctx, arm, dropped, depth):
    """Round-robin ranked candidate lists {line: [candidate, ...]} (pairwise disjoint across rows)."""
    recs = ctx.arms[arm]["recs"]
    books = ctx.arms[arm]["books"]
    dropped_set = set(dropped)
    used = {b: bytearray(book.n) for b, book in books.items()}
    for rec in recs:                                  # every original response sentence is unavailable
        for i in range(rec["s"], rec["e"] + 1):
            used[rec["book"]][i] = 1
    kept_keys = {rec["key"] for rec in recs if rec["line"] not in dropped_set}
    rankings = {line: RowRanking(ctx, arm, recs[line - 1], used[recs[line - 1]["book"]], kept_keys)
                for line in sorted(dropped)}
    lists = {line: [] for line in rankings}
    reserved = defaultdict(list)                      # book -> [(line, s, e)]
    reserved_keys: dict[str, int] = {}
    conflicts = Counter()
    for rank in range(1, depth + 1):
        for line in sorted(rankings):
            g = rankings[line]
            book = g.rec["book"]
            while True:
                cand = g.next()
                if cand is None:
                    break
                if any(other != line and not (cand["e"] < s or e < cand["s"]) for other, s, e in reserved[book]):
                    conflicts["response_overlap_with_another_dropped_row"] += 1
                    continue
                key = B.user_key(g.instruction, cand["context"])
                if reserved_keys.get(key, line) != line:
                    conflicts["user_text_of_another_dropped_row"] += 1
                    continue
                cand.update({"rank": rank, "key": key, "instruction": g.instruction, "T": g.T, "tol": g.tol,
                             "c": g.c, "book": book, "slot": g.rec["slot"]})
                lists[line].append(cand)
                reserved[book].append((line, cand["s"], cand["e"]))
                reserved_keys.setdefault(key, line)
                break
    exclusions = Counter()
    rounds = Counter()
    for g in rankings.values():
        exclusions.update(g.counts)
        rounds[g.rounds] += 1
    return lists, {"exclusions_while_ranking": dict(exclusions), "conflicts_skipped": dict(conflicts),
                   "rows_by_rounds_drawn": {str(k): v for k, v in sorted(rounds.items())}}


def candidate_row(arm, cand):
    return {"instruction": cand["instruction"], "context": cand["context"], "response": cand["response"],
            "category": f"{arm}_b{cand['slot']}"}


def label_candidates(ctx, lists_by_arm, cands):
    """Map candidate labels to (arm, line, rank); returns {(arm, line, rank): label}."""
    by_sha = {}
    for arm, lists in lists_by_arm.items():
        for line, lst in lists.items():
            for cd in lst:
                k = (arm, sha256_text(cd["response"]))
                by_sha[k] = None if k in by_sha else (arm, line, cd["rank"])
    out = {}
    for r in cands:
        if r["slot_line"] is not None and r["rank"] is not None:
            key = (r["slot_arm"], int(r["slot_line"]), int(r["rank"]))
            lst = lists_by_arm.get(key[0], {}).get(key[1])
            if lst is None or not 1 <= key[2] <= len(lst):
                raise SystemExit(f"candidate label for {key} names no ranked candidate (check --depth)")
            if r["sha"] is not None and r["sha"] != sha256_text(lst[key[2] - 1]["response"]):
                raise SystemExit(f"candidate label for {key}: response_sha256 differs from the ranked candidate")
        elif r["sha"] is not None and r["slot_arm"] in ARMS:
            key = by_sha.get((r["slot_arm"], r["sha"]))
            if key is None:
                raise SystemExit("a candidate label matches no ranked candidate (or matches two)")
        else:
            raise SystemExit("a candidate label carries neither slot_line+rank nor response_sha256")
        if key in out:
            raise SystemExit(f"two labels for candidate {key}")
        out[key] = r["label"]
    return out


def refuse_inside_inputs(ctx, path):
    real = os.path.realpath(path)
    if real == ctx.inputs_dir or real.startswith(ctx.inputs_dir + os.sep):
        raise SystemExit("refusing to write inside the input folder (tmp/side-fiction/out is never overwritten)")


def do_refill(ctx, screen_paths, round_no, offset, k, depth, write_dir, refill_paths=()):
    if offset < 0 or k < 1 or offset + k > depth:
        raise SystemExit("need 0 <= offset, 1 <= k and offset + k <= depth")
    refuse_inside_inputs(ctx, write_dir)
    os.makedirs(write_dir, exist_ok=True)
    originals, cands = read_results(screen_paths, refill_paths)
    dropped = dropped_rows(ctx, originals)
    lists_by_arm, rank_info = {}, {}
    for arm in ARMS:
        lists_by_arm[arm], rank_info[arm] = rank_lists(ctx, arm, dropped[arm], depth)
    labels = label_candidates(ctx, lists_by_arm, cands) if cands else {}
    resolved = {(a, l) for (a, l, r), lab in labels.items() if lab == "no"}
    out_lines, report_arms = [], {}
    for arm in ARMS:
        per_book = defaultdict(Counter)
        for line in sorted(lists_by_arm[arm]):
            rec = ctx.arms[arm]["recs"][line - 1]
            b = per_book[str(rec["book"])]
            b["dropped_rows"] += 1
            if (arm, line) in resolved:
                b["already_resolved"] += 1
                continue
            lst = lists_by_arm[arm][line]
            chosen = lst[offset:offset + k]
            b["candidates_written"] += len(chosen)
            b["fallback_candidates_written"] += sum(not cd["matched"] for cd in chosen)
            b["rows_with_short_list"] += len(chosen) < k
            for cd in chosen:
                row = candidate_row(arm, cd)
                row.update({"slot_arm": arm, "slot_line": line, "rank": cd["rank"]})
                out_lines.append(dumps_row(row))
        report_arms[arm] = {"dropped_rows": len(lists_by_arm[arm]), "per_book": {k2: dict(v) for k2, v in sorted(per_book.items())},
                            **rank_info[arm]}
    out_path = os.path.join(write_dir, f"refill-r{round_no}.jsonl")
    with open(out_path, "w", encoding="utf-8") as f:
        for line in out_lines:
            f.write(line + "\n")
    report = {"kind": "side fiction screen refill report (counts, ids, labels and hashes only)",
              "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "round": round_no,
              "offset": offset, "k": k, "depth": depth, "rules_sha256": ctx.rules_sha256,
              "script_sha256": sha256_file(os.path.abspath(__file__)), "inputs": ctx.input_hashes,
              "screen_files": {os.path.basename(p): sha256_file(p) for p in list(screen_paths) + list(refill_paths)},
              "original_labels": dict(Counter(lab for lab, _ in originals.values())),
              "candidate_labels": dict(Counter(labels.values())),
              "dropped_lines": {arm: sorted(dropped[arm]) for arm in ARMS}, "arms": report_arms,
              "output": {"file": os.path.basename(out_path), "rows": len(out_lines), "sha256": sha256_file(out_path)}}
    with open(os.path.join(write_dir, f"refill-r{round_no}-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    return report, lists_by_arm


def do_finalize(ctx, screen_paths, depth, final_dir, configs_dir, refill_paths=()):
    refuse_inside_inputs(ctx, final_dir)
    originals, cands = read_results(screen_paths, refill_paths)
    dropped = dropped_rows(ctx, originals)
    lists_by_arm = {arm: rank_lists(ctx, arm, dropped[arm], depth)[0] for arm in ARMS}
    labels = label_candidates(ctx, lists_by_arm, cands)
    choice, missing = {}, []
    for arm in ARMS:
        for line in sorted(lists_by_arm[arm]):
            clean = [cd for cd in lists_by_arm[arm][line] if labels.get((arm, line, cd["rank"])) == "no"]
            if clean:
                choice[(arm, line)] = clean[0]          # the best-ranked clean candidate
            else:
                missing.append((arm, line))
    if missing:                                         # nothing is written
        raise SystemExit(f"{len(missing)} dropped row(s) have no clean candidate yet (another round is needed): "
                         + ", ".join(f"{a} {l}" for a, l in missing))
    os.makedirs(os.path.join(final_dir, "configs"), exist_ok=True)
    report_arms, hashes = {}, {}
    for arm in ARMS:
        recs = ctx.arms[arm]["recs"]
        lines = list(ctx.arms[arm]["lines"])
        dropped_set = set(dropped[arm])
        per_book = defaultdict(Counter)
        for rec in recs:
            per_book[str(rec["book"])]["rows"] += 1
        ranks_used, unmet_replacements = Counter(), 0
        for line in sorted(dropped_set):
            cd = choice[(arm, line)]
            b = per_book[str(recs[line - 1]["book"])]
            b["dropped"] += 1
            b["replaced"] += 1
            lines[line - 1] = dumps_row(candidate_row(arm, cd))
            ranks_used[cd["rank"]] += 1
            if not cd["matched"]:
                b["replacement_unmet"] += 1
                unmet_replacements += 1
        out_path = os.path.join(final_dir, f"{arm}.jsonl")
        with open(out_path, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line + "\n")
        hashes[arm] = sha256_file(out_path)
        kept_unmet = sum(not rec["matched"] for rec in recs if rec["line"] not in dropped_set)
        report_arms[arm] = {"rows": len(lines), "dropped": len(dropped_set), "replaced": sum(ranks_used.values()),
                            "replacement_rank_counts": {str(r): v for r, v in sorted(ranks_used.items())},
                            "unmet_replacements": unmet_replacements, "unmet_kept_rows_from_build": kept_unmet,
                            "unmet_total": kept_unmet + unmet_replacements,
                            "per_book": {k2: dict(v) for k2, v in sorted(per_book.items())},
                            "final_sha256": hashes[arm], "input_sha256": ctx.input_hashes[f"{arm}.jsonl"]}
    config_hashes = {}
    for arm in ARMS:
        name = f"study-side-fiction-{arm}-olmo2.json"
        with open(os.path.join(configs_dir, name), encoding="utf-8") as f:
            cfg = json.load(f)
        cfg["source"]["sha256"] = hashes[arm]
        cfg["source"]["revision"] = "FILL-COMMIT"
        cfg["purpose"] = " ".join(re.sub(r"PRE-SCREEN[^.]*\.", "", cfg["purpose"]).split())
        if "PRE-SCREEN" in cfg["purpose"]:
            raise SystemExit("the PRE-SCREEN marker could not be removed")
        path = os.path.join(final_dir, "configs", name)
        with open(path, "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2, ensure_ascii=False)
            f.write("\n")
        config_hashes[name] = sha256_file(path)
    report = {"kind": "side fiction screen report (counts, ids, labels and hashes only)",
              "written_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "depth": depth,
              "rules_sha256": ctx.rules_sha256, "script_sha256": sha256_file(os.path.abspath(__file__)),
              "inputs": ctx.input_hashes,
              "screen_files": {os.path.basename(p): sha256_file(p) for p in list(screen_paths) + list(refill_paths)},
              "original_labels": dict(Counter(lab for lab, _ in originals.values())),
              "candidate_labels": dict(Counter(labels.values())),
              "dropped_lines": {arm: sorted(dropped[arm]) for arm in ARMS},
              "arms": report_arms, "final": {f"{arm}.jsonl": hashes[arm] for arm in ARMS},
              "configs": {"dir": "configs", "sha256": config_hashes,
                          "changes": "source.sha256 = the final file; source.revision = 'FILL-COMMIT'; the PRE-SCREEN "
                                     "sentence removed from purpose"}}
    with open(os.path.join(final_dir, "screen-report.json"), "w", encoding="utf-8") as f:
        json.dump(report, f, indent=1)
        f.write("\n")
    return report, lists_by_arm, choice


# ---------------------------------------------------------------- self-test (temp dir; out/ is read only)

def _write_round1(ctx, path, drops):
    with open(path, "w", encoding="utf-8") as f:
        for arm in ARMS:
            for rec in ctx.arms[arm]["recs"]:
                f.write(json.dumps({"arm": arm, "line": rec["line"], "category": f"{arm}_b{rec['slot']}",
                                    "response_sha256": rec["response_sha256"],
                                    "granite_harm": drops.get((arm, rec["line"]), "No")}) + "\n")


def _read_jsonl(path):
    with open(path, encoding="utf-8") as f:
        return [json.loads(x) for x in f if x.strip()]


def _check_lists(ctx, lists_by_arm):
    """Darkness order inside each round, scores and band, and pairwise disjoint / distinct across rows."""
    for arm, lists in lists_by_arm.items():
        sign = -1.0 if arm == "dark" else 1.0
        for line, lst in lists.items():
            assert [cd["rank"] for cd in lst] == list(range(1, len(lst) + 1)), "ranks are consecutive"
            by_round = defaultdict(list)
            for cd in lst:
                by_round[cd["round"]].append(cd)
                resp = ctx.arms[arm]["books"][cd["book"]].text(cd["s"], cd["e"])
                assert resp == cd["response"]
                assert abs(100.0 * len(ctx.lex.findall(resp.lower())) / cd["n"] - cd["score"]) < 1e-9, "darkness score"
                assert len(ctx.tok.encode(resp, add_special_tokens=False)) == cd["n"], "token count"
            rounds = [r for r in by_round if r != "fallback"]
            assert rounds == sorted(rounds), "round 1 before round 2"
            for rnd, cds in by_round.items():
                if rnd == "fallback":
                    continue
                keys = [(sign * cd["score"]) for cd in cds]
                assert keys == sorted(keys), f"{arm} {line}: darkness ranking"
                assert all(cd["matched"] and abs(cd["n"] - cd["T"]) <= cd["tol"] for cd in cds), "match band"
        all_c = [(line, cd) for line, lst in lists.items() for cd in lst]
        for i, (l1, c1) in enumerate(all_c):
            for l2, c2 in all_c[i + 1:]:
                if l1 == l2:
                    continue
                if c1["book"] == c2["book"]:
                    assert c1["e"] < c2["s"] or c2["e"] < c1["s"], "candidates of two dropped rows overlap"
                assert c1["key"] != c2["key"], "candidates of two dropped rows share a user text"


def _check_final(ctx, final_dir, choice, checks, tag):
    for arm in ARMS:
        with open(os.path.join(final_dir, f"{arm}.jsonl"), encoding="utf-8") as f:
            text = f.read()
        final_lines = text[:-1].split("\n")
        orig = ctx.arms[arm]["lines"]
        recs = ctx.arms[arm]["recs"]
        assert len(final_lines) == 5000, f"{arm}: 5,000 rows"
        rows = [json.loads(x) for x in final_lines]
        cats = Counter(r["category"] for r in rows)
        assert len(cats) == 8 and set(cats.values()) == {625}, f"{arm}: 625 per category"
        assert all(list(r) == ["instruction", "context", "response", "category"] and all(isinstance(v, str) for v in r.values())
                   for r in rows), f"{arm}: Dolly format"
        keys = [B.user_key(r["instruction"], r["context"]) for r in rows]
        assert len(set(keys)) == len(keys), f"{arm}: duplicate normalised user text"
        replaced = {line for (a, line) in choice if a == arm}
        same = sum(final_lines[i] == orig[i] for i in range(5000) if (i + 1) not in replaced)
        assert same == 5000 - len(replaced), f"{arm}: unchanged rows are byte-identical"
        intervals = defaultdict(list)
        for rec in recs:
            if rec["line"] not in replaced:
                intervals[rec["book"]].append((rec["s"], rec["e"]))
        for (a, line), cd in choice.items():
            if a != arm:
                continue
            rec = recs[line - 1]
            row = rows[line - 1]
            book = ctx.arms[arm]["books"][rec["book"]]
            intervals[rec["book"]].append((cd["s"], cd["e"]))
            T = max(rec["t_raw"], 6)
            n = len(ctx.tok.encode(row["response"], add_special_tokens=False))
            assert n == cd["n"] and abs(n - T) <= max(3.0, 0.15 * T), f"{arm} {line}: length inside the band"
            assert row["instruction"] == B.template(ctx.rules, rec["t_raw"]), "same template"
            assert row["category"] == f"{arm}_b{rec['slot']}", "same book"
            assert row["context"] == book.text(cd["s"] - rec["c"], cd["s"] - 1), "same context count"
            assert row["response"] == book.text(cd["s"], cd["e"])
        for b, ivs in intervals.items():
            ivs.sort()
            assert all(ivs[i][1] < ivs[i + 1][0] for i in range(len(ivs) - 1)), f"{arm} book {b}: response overlap"
        checks[f"{tag}_{arm}"] = {"rows": len(rows), "per_category": sorted(set(cats.values())), "replaced": len(replaced),
                                  "unchanged_byte_identical": same, "duplicate_user_texts": len(keys) - len(set(keys)),
                                  "sha256": sha256_text(text)}


def selftest(ctx, configs_dir, keep):
    tmp = tempfile.mkdtemp(prefix="sf_screen_selftest_")
    checks = {}
    try:
        # ---- scenario A (the coordinator's): drop dark 7, 1234, 4999 (invalid) and light 10
        drops = {("dark", 7): "Yes", ("dark", 1234): "Yes", ("dark", 4999): "invalid", ("light", 10): "Yes"}
        a_dir = os.path.join(tmp, "A")
        os.makedirs(a_dir)
        r1 = os.path.join(a_dir, "screen-r1.jsonl")
        _write_round1(ctx, r1, drops)
        rep2, lists2 = do_refill(ctx, [r1], 2, 0, 5, DEFAULT_DEPTH, a_dir)
        assert rep2["output"]["rows"] == 20, "5 candidates for each of 4 dropped rows"
        _check_lists(ctx, lists2)
        # rank 1 is what the committed rules-v2 selection (sf_build.select) picks from the same stream and state
        for arm in ARMS:
            recs = ctx.arms[arm]["recs"]
            dropped_set = set(rep2["dropped_lines"][arm])
            kept_keys = {rec["key"] for rec in recs if rec["line"] not in dropped_set}
            for line in rep2["dropped_lines"][arm]:
                rec = recs[line - 1]
                book = ctx.arms[arm]["books"][rec["book"]]
                used = bytearray(book.n)
                for r in recs:
                    if r["book"] == rec["book"]:
                        for i in range(r["s"], r["e"] + 1):
                            used[i] = 1
                T = max(rec["t_raw"], 6)
                chosen, _ = B.select(book, rng_for(f"candidates:{arm}:{rec['book']}:screen-line-{line}"), used, T,
                                     max(3.0, 0.15 * T), rec["c"], ctx.lex, arm, B.template(ctx.rules, rec["t_raw"]),
                                     kept_keys, B.ROUND_SIZE)
                top = lists2[arm][line][0]
                assert (chosen["s"], chosen["e"]) == (top["s"], top["e"]), f"{arm} {line}: rank 1 differs from sf_build.select"
        checks["A_rank1_equals_sf_build_select"] = True
        r2_rows = _read_jsonl(os.path.join(a_dir, "refill-r2.jsonl"))
        assert [list(x) for x in r2_rows][0] == ["instruction", "context", "response", "category", "slot_arm", "slot_line", "rank"]
        flagged = ("dark", 1234)
        r2 = os.path.join(a_dir, "screen-r2.jsonl")
        with open(r2, "w", encoding="utf-8") as f:
            for i, row in enumerate(r2_rows, start=1):
                lab = "Yes" if (row["slot_arm"], row["slot_line"]) == flagged and row["rank"] == 1 else "No"
                f.write(json.dumps({"arm": row["slot_arm"], "line": i, "slot_arm": row["slot_arm"], "slot_line": row["slot_line"],
                                    "rank": row["rank"], "response_sha256": sha256_text(row["response"]),
                                    "granite_harm": lab}) + "\n")
        deep = os.path.join(a_dir, "deep")
        do_refill(ctx, [r1], 9, 0, 15, DEFAULT_DEPTH, deep)
        deep_rows = _read_jsonl(os.path.join(deep, "refill-r9.jsonl"))
        assert [dumps_row(x) for x in deep_rows if x["rank"] <= 5] == [dumps_row(x) for x in r2_rows], "ranks 1-5 change with k"
        do_refill(ctx, [r1], 3, 5, 10, DEFAULT_DEPTH, deep)
        r3_rows = _read_jsonl(os.path.join(deep, "refill-r3.jsonl"))
        assert [dumps_row(x) for x in r3_rows] == [dumps_row(x) for x in deep_rows if x["rank"] > 5], "offset 5 k 10 = ranks 6-15"
        rep4, _ = do_refill(ctx, [r1, r2], 4, 5, 10, DEFAULT_DEPTH, deep)
        assert rep4["output"]["rows"] == 0, "rows with a clean candidate get no new candidates"
        dropped_a = rep2["dropped_lines"]
        for arm in ARMS:
            short, _ = rank_lists(ctx, arm, dropped_a[arm], 5)
            for line, lst in short.items():
                assert [(c["s"], c["e"]) for c in lst] == [(c["s"], c["e"]) for c in lists2[arm][line][:5]], "depth changes ranks"
        checks["A_prefix_stability"] = ("ranks 1-5 equal at k=5 and k=15 and at depth 5 and 15; offset 5 k 10 equals "
                                        "ranks 6-15; resolved rows skipped")
        rep_f, lists_f, choice = do_finalize(ctx, [r1, r2], DEFAULT_DEPTH, os.path.join(a_dir, "final"), configs_dir)
        assert choice[flagged]["rank"] == 2 and all(cd["rank"] == 1 for k2, cd in choice.items() if k2 != flagged)
        _check_final(ctx, os.path.join(a_dir, "final"), choice, checks, "A")
        for name in sorted(os.listdir(os.path.join(a_dir, "final", "configs"))):
            cfg = json.load(open(os.path.join(a_dir, "final", "configs", name), encoding="utf-8"))
            arm = "dark" if "-dark-" in name else "light"
            base = json.load(open(os.path.join(configs_dir, name), encoding="utf-8"))
            assert cfg["source"]["sha256"] == rep_f["final"][f"{arm}.jsonl"] and cfg["source"]["revision"] == "FILL-COMMIT"
            assert "PRE-SCREEN" not in cfg["purpose"]
            changed = {k for k in set(cfg) | set(base) if cfg.get(k) != base.get(k)}
            assert changed == {"purpose", "source"}, "only purpose and source change"
            assert {k for k in cfg["source"] if cfg["source"][k] != base["source"][k]} == {"sha256", "revision"}
        checks["A_configs"] = "only source.sha256, source.revision (FILL-COMMIT) and purpose (PRE-SCREEN removed) change"
        checks["A_unmet_total"] = {arm: rep_f["arms"][arm]["unmet_total"] for arm in ARMS}

        # ---- scenario B (stress): several drops in one book; labels by response_sha256 only; a row whose
        # five candidates are all flagged stops finalize; round 3 (ranks 6-15) then resolves it
        drops_b = {("dark", 7): "Yes", ("dark", 8): "Yes", ("dark", 9): "Yes", ("dark", 10): "Yes",
                   ("light", 10): "Yes", ("light", 11): "invalid", ("light", 12): "Yes"}
        b_dir = os.path.join(tmp, "B")
        os.makedirs(b_dir)
        rb1 = os.path.join(b_dir, "screen-r1.jsonl")
        _write_round1(ctx, rb1, drops_b)
        repb2, listsb = do_refill(ctx, [rb1], 2, 0, 5, DEFAULT_DEPTH, b_dir)
        _check_lists(ctx, listsb)
        rb2_rows = _read_jsonl(os.path.join(b_dir, "refill-r2.jsonl"))
        all_flagged = ("dark", 8)
        rb2 = os.path.join(b_dir, "screen-r2.jsonl")
        with open(rb2, "w", encoding="utf-8") as f:          # pod-style rows: arm, line, slot, sha; no slot_line/rank
            for i, row in enumerate(rb2_rows, start=1):
                lab = "Yes" if (row["slot_arm"], row["slot_line"]) == all_flagged else "No"
                f.write(json.dumps({"arm": row["slot_arm"], "line": i, "slot": row["category"],
                                    "response_sha256": sha256_text(row["response"]), "granite_harm": lab}) + "\n")
        try:
            do_finalize(ctx, [rb1], DEFAULT_DEPTH, os.path.join(b_dir, "final-too-early"), configs_dir, [rb2])
            raise AssertionError("finalize must stop when a dropped row has no clean candidate")
        except SystemExit as exc:
            assert "no clean candidate" in str(exc)
        assert not os.path.exists(os.path.join(b_dir, "final-too-early", "dark.jsonl")), "nothing written on refusal"
        repb3, _ = do_refill(ctx, [rb1], 3, 5, 10, DEFAULT_DEPTH, b_dir, [rb2])
        rb3_rows = _read_jsonl(os.path.join(b_dir, "refill-r3.jsonl"))
        assert {(x["slot_arm"], x["slot_line"]) for x in rb3_rows} == {all_flagged} and [x["rank"] for x in rb3_rows] == list(range(6, 16))
        rb3 = os.path.join(b_dir, "screen-r3.jsonl")
        with open(rb3, "w", encoding="utf-8") as f:
            for i, row in enumerate(rb3_rows, start=1):
                f.write(json.dumps({"arm": row["slot_arm"], "line": i, "slot_arm": row["slot_arm"], "slot_line": row["slot_line"],
                                    "rank": row["rank"], "response_sha256": sha256_text(row["response"]),
                                    "granite_harm": "Yes" if row["rank"] == 6 else "No"}) + "\n")
        repbf, listsbf, choiceb = do_finalize(ctx, [rb1, rb3], DEFAULT_DEPTH, os.path.join(b_dir, "final"), configs_dir, [rb2])
        assert choiceb[all_flagged]["rank"] == 7, "ranks 1-6 flagged: rank 7 replaces the row"
        assert all(cd["rank"] == 1 for k2, cd in choiceb.items() if k2 != all_flagged)
        _check_final(ctx, os.path.join(b_dir, "final"), choiceb, checks, "B")
        checks["B_conflicts_skipped"] = {arm: repb2["arms"][arm]["conflicts_skipped"] for arm in ARMS}
        checks["B_flow"] = ("4 dark + 3 light drops (same books); sha-only labels mapped; finalize refused with nothing "
                            "written while one row had no clean candidate; round 3 gave ranks 6-15; rank 7 chosen")
        checks["inputs_unchanged"] = all(sha256_file(os.path.join(ctx.inputs_dir, f"{arm}.jsonl")) == ctx.input_hashes[f"{arm}.jsonl"]
                                         for arm in ARMS)
        assert checks["inputs_unchanged"]
        checks["result"] = "PASS"
    finally:
        if keep:
            checks["temp_dir"] = tmp
        else:
            shutil.rmtree(tmp, ignore_errors=True)
    return checks


def main(argv=None):
    p = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    p.add_argument("mode", choices=("refill", "finalize", "selftest"))
    p.add_argument("--rules", default=os.path.join(ROOT, "research/side-fiction/rules-v2.json"))
    p.add_argument("--inputs", default=os.path.join(ROOT, "tmp/side-fiction/out"))
    p.add_argument("--stats", default=os.path.join(ROOT, "tmp/side-fiction/work-v2"))
    p.add_argument("--raw", default=os.path.join(ROOT, "tmp/side-fiction/raw"))
    p.add_argument("--configs", default=os.path.join(ROOT, "research/side-fiction/configs"))
    p.add_argument("--screen", action="append", default=[], help="screen results (original rows; candidate rows are "
                   "recognised by rank, slot_line, slot_arm or slot)")
    p.add_argument("--screen-refill", action="append", default=[], help="screen results whose rows are all refill "
                   "candidates (matched by slot_line + rank, or by arm + response_sha256)")
    p.add_argument("--round", type=int, default=2)
    p.add_argument("--offset", type=int, default=0)
    p.add_argument("--k", type=int, default=5)
    p.add_argument("--depth", type=int, default=DEFAULT_DEPTH)
    p.add_argument("--write-dir", default=os.path.join(ROOT, "tmp/side-fiction/screen"))
    p.add_argument("--final-dir", default=os.path.join(ROOT, "tmp/side-fiction/final"))
    p.add_argument("--keep", action="store_true")
    a = p.parse_args(argv)
    t0 = time.time()
    ctx = Context(a.rules, a.inputs, a.stats, a.raw)
    if a.mode == "refill":
        if not a.screen:
            raise SystemExit("refill needs --screen")
        rep, _ = do_refill(ctx, a.screen, a.round, a.offset, a.k, a.depth, a.write_dir, a.screen_refill)
        print(json.dumps({"mode": "refill", "round": a.round, "dropped": {k: len(v) for k, v in rep["dropped_lines"].items()},
                          "output": rep["output"], "seconds": round(time.time() - t0, 1)}))
    elif a.mode == "finalize":
        if not a.screen:
            raise SystemExit("finalize needs --screen")
        rep, _, _ = do_finalize(ctx, a.screen, a.depth, a.final_dir, a.configs, a.screen_refill)
        print(json.dumps({"mode": "finalize", "final": rep["final"],
                          "unmet_total": {arm: rep["arms"][arm]["unmet_total"] for arm in ARMS},
                          "seconds": round(time.time() - t0, 1)}))
    else:
        checks = selftest(ctx, a.configs, a.keep)
        print(json.dumps({"mode": "selftest", "checks": checks, "seconds": round(time.time() - t0, 1)}, indent=1))


if __name__ == "__main__":
    main()
