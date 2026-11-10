"""Build one arm of the side fiction data under rules-v2 (window, selection, lexicon, screen,
templates).

Usage: <attribution venv python> -I sf_build.py RULES_V2_JSON TARGETS_JSON RAW_DIR ARM BOOK_IDS OUT_JSONL STATS_JSON [--evidence-round-size N]
  ARM       dark | light
  BOOK_IDS  comma-separated Gutenberg text numbers in slot order (book k uses slot k)
  --evidence-round-size N  NOT rules-v2: draws N candidates per round instead of 100 (used only to
                           compare passage darkness at 30 against 100 candidates; evidence output).

Writes the Dolly-format JSONL (instruction, context, response, category) and a counts-only
statistics file. Prints counts only; no book text is printed.

rules-v2 behaviour (changes from the v1 build): only RESPONSE sentences are marked used (context
sentences may repeat and may appear in other rows' responses); a candidate whose normalised user
text equals an already chosen row's in the arm does not match; 100 candidates per round, at most
10 rounds; darkness ties go to the candidate drawn first.

Detail decisions adopted from build-report-v1 (unless v2 changes them):
- book k = the k-th chosen book in ascending text number; candidate seed purpose
  'candidates:<arm>:<Gutenberg text number>';
- context counts: one fresh random.Random(seed 'context') per arm, randint(1, 3) per row in slot
  order; a refilled row keeps its count;
- a candidate start s is drawn with rng.randrange(N) (with replacement); it is valid when s-c >= 0,
  the c context sentences and every response sentence lie in s's section (chapter or story), the
  response sentences are unused, and its user text is not a duplicate;
- the response runs from s to the end e (same section, unused) whose token count is closest to T
  among the ends that match (ties: fewer sentences); without a matching end, the candidate's length
  for the fallback is its closest end;
- the fallback takes the valid candidate with the smallest |n - T| over the 10 rounds; v2 ties are
  broken by draw order, so a fallback tie goes to the candidate drawn first (v1: smallest start
  index); a duplicate user text is never taken by the fallback either (the dedup rule's purpose);
  if no valid candidate exists after 10 rounds, rounds continue (counted as extended) and the book
  counts as exhausted after 20,000 extra rounds;
- the procedure screen runs on each chosen row; a flagged row is dropped, its response sentences
  stay blocked (v2: only response sentences can be used), and the target is refilled at once by the
  same rule with new draws;
- substances, preparation verbs and the darkness lexicon: lowercase whole-word matches of the
  listed forms; the quantity regex runs on the lowercased sentence;
- sentences are joined with one space inside a paragraph and a blank line between paragraphs;
  token counts are len(encode(text, add_special_tokens=False)).
"""

from __future__ import annotations

import json
import os
import re
import statistics
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sf_lib import (clean_book, is_title_like, load_rules, load_tokenizer, rng_for, sha256_file,  # noqa: E402
                    split_sentences, word_pattern)

ROUND_SIZE = 100          # rules-v2 selection.candidates
MAX_ROUNDS = 10           # rules-v2 selection.fallback: at most 10 rounds in total
EXTENDED_CAP = 20000
MAX_REFILLS = 200


class Exhausted(Exception):
    """No valid candidate exists: the row cannot be placed."""


def user_key(instruction: str, context: str) -> str:
    """rules-v2 window.dedup: instruction, a blank line, context; lowercased; whitespace collapsed
    (the engine preparer's normalize(render_user_text(...)))."""
    return " ".join(f"{instruction}\n\n{context}".lower().split())


class Book:
    def __init__(self, book_id: int, path: str, abbrevs: list[str], tokenizer):
        self.id = book_id
        with open(path, "rb") as f:
            raw = f.read()
        self.sha256 = sha256_file(path)
        text = raw.decode("utf-8").lstrip("﻿")
        cleaned = clean_book(text)
        self.clean_counts = cleaned["counts"]
        self.words_after_strip = cleaned["words_after_strip"]
        self.words_after_clean = cleaned["words_after_clean"]
        sents, section, para = [], [], []
        for p_index, p in enumerate(cleaned["paragraphs"]):
            for s in split_sentences(p["text"], abbrevs):
                sents.append(s)
                section.append(p["section"])
                para.append(p_index)
        self.sents, self.section, self.para = sents, section, para
        self.n = len(sents)
        self.tok = tokenizer
        self.cache: dict[tuple[int, int], int] = {}
        self.sent_tokens = None

    def text(self, a: int, b: int) -> str:
        """Sentences a..b inclusive: one space inside a paragraph, a blank line between paragraphs."""
        out = [self.sents[a]]
        for i in range(a + 1, b + 1):
            out.append("\n\n" if self.para[i] != self.para[i - 1] else " ")
            out.append(self.sents[i])
        return "".join(out)

    def ntok(self, a: int, b: int) -> int:
        key = (a, b)
        v = self.cache.get(key)
        if v is None:
            v = len(self.tok.encode(self.text(a, b), add_special_tokens=False))
            self.cache[key] = v
        return v

    def total_tokens(self) -> int:
        if self.sent_tokens is None:
            self.sent_tokens = [len(self.tok.encode(s, add_special_tokens=False)) for s in self.sents]
        return sum(self.sent_tokens)


class Screen:
    def __init__(self, rules: dict):
        ps = rules["procedure_screen"]
        self.subst = word_pattern(ps["substances"])
        self.verbs = word_pattern(ps["preparation_verbs"])
        self.qty = re.compile(ps["quantity_regex"])

    def flags(self, sentence: str) -> bool:
        low = sentence.lower()
        if not self.subst.search(low):
            return False
        return bool(self.qty.search(low) or self.verbs.search(low))


def template(rules: dict, t_raw: int) -> str:
    tp = rules["templates"]
    if t_raw < 15:
        return tp["T_lt_15"]
    if t_raw <= 60:
        return tp["T_15_to_60"]
    return tp["T_gt_60"]


def evaluate(book: Book, s: int, c: int, used: bytearray, T: int, tol: float, instruction: str, chosen_keys):
    """A candidate start s, or None when it cannot form a row (position, section, used response)."""
    if s - c < 0 or used[s]:
        return None
    sec = book.section[s]
    for j in range(s - c, s):
        if book.section[j] != sec:          # v2: context sentences may repeat, so only the section counts
            return None
    best = None      # (|n-T|, e, n) among matching ends
    closest = None   # (|n-T|, e, n) among all ends tried
    e = s
    while e < book.n and book.section[e] == sec and not used[e]:
        n = book.ntok(s, e)
        d = abs(n - T)
        if closest is None or d < closest[0]:
            closest = (d, e, n)
        if d <= tol and (best is None or d < best[0]):
            best = (d, e, n)
        if n > T + tol:
            break
        e += 1
    dup = user_key(instruction, book.text(s - c, s - 1)) in chosen_keys
    return {"s": s, "best": best, "closest": closest, "dup": dup}


def select(book: Book, rng, used: bytearray, T: int, tol: float, c: int, lex, arm: str, instruction: str,
           chosen_keys, round_size: int):
    seen: dict[int, dict | None] = {}
    first_draw: dict[int, int] = {}      # start -> index of its first draw (all rounds)
    draws = 0
    rounds = 0
    extended = 0
    dup_excluded: set[int] = set()       # distinct matching starts excluded as duplicate user texts
    while True:
        rounds += 1
        if rounds > MAX_ROUNDS:
            extended += 1
        matching = {}                     # start -> (first draw index in this round, candidate)
        for _ in range(round_size):
            s = rng.randrange(book.n)
            draws += 1
            first_draw.setdefault(s, draws)
            if s not in seen:
                seen[s] = evaluate(book, s, c, used, T, tol, instruction, chosen_keys)
            cand = seen[s]
            if cand is None or cand["best"] is None or s in matching:
                continue
            if cand["dup"]:
                dup_excluded.add(s)
                continue
            matching[s] = (draws, cand)
        if matching and rounds <= MAX_ROUNDS:
            scored = []
            for s, (order, cand) in matching.items():
                d, e, n = cand["best"]
                hits = len(lex.findall(book.text(s, e).lower()))
                scored.append((100.0 * hits / n, order, s, e, n))
            if arm == "dark":
                score, order, s, e, n = sorted(scored, key=lambda x: (-x[0], x[1]))[0]
            else:
                score, order, s, e, n = sorted(scored, key=lambda x: (x[0], x[1]))[0]
            return ({"s": s, "e": e, "n": n, "matched": True},
                    {"rounds": rounds, "extended_rounds": 0, "n_matching": len(scored),
                     "dup_matches_excluded": len(dup_excluded), "fallback_would_take_duplicate": False})
        valid = [cd for cd in seen.values() if cd is not None]
        pool = [cd for cd in valid if not cd["dup"]]
        if rounds >= MAX_ROUNDS and pool:
            best = sorted(pool, key=lambda cd: (cd["closest"][0], first_draw[cd["s"]]))[0]
            literal = sorted(valid, key=lambda cd: (cd["closest"][0], first_draw[cd["s"]]))[0]
            d, e, n = best["closest"]
            return ({"s": best["s"], "e": e, "n": n, "matched": False},
                    {"rounds": min(rounds, MAX_ROUNDS), "extended_rounds": extended, "n_matching": 0,
                     "dup_matches_excluded": len(dup_excluded),
                     "fallback_would_take_duplicate": bool(literal["dup"])})
        if extended > EXTENDED_CAP:
            raise Exhausted(f"no valid candidate after {rounds} rounds")


def place_row(book, rng, used, t_raw, c, lex, screen, arm, instruction, chosen_keys, round_size):
    """One row for target t_raw with context count c: selection, procedure screen, refill."""
    T = max(t_raw, 6)
    tol = max(3.0, 0.15 * T)
    drops, extended = 0, 0
    while True:
        chosen, info = select(book, rng, used, T, tol, c, lex, arm, instruction, chosen_keys, round_size)
        extended += info["extended_rounds"]
        ctx_ids = list(range(chosen["s"] - c, chosen["s"]))
        resp_ids = list(range(chosen["s"], chosen["e"] + 1))
        if any(screen.flags(book.sents[i]) for i in ctx_ids + resp_ids):
            drops += 1
            for i in resp_ids:
                used[i] = 1
            if drops > MAX_REFILLS:
                raise SystemExit(f"book {book.id}: too many refills")
            continue
        for i in resp_ids:
            used[i] = 1
        chosen_keys.add(user_key(instruction, book.text(ctx_ids[0], ctx_ids[-1])))
        return {"T": T, "tol": tol, "ctx_ids": ctx_ids, "resp_ids": resp_ids, "n": chosen["n"],
                "matched": chosen["matched"], "rounds": info["rounds"], "extended_rounds": extended,
                "n_matching": info["n_matching"], "dup_matches_excluded": info["dup_matches_excluded"],
                "fallback_would_take_duplicate": info["fallback_would_take_duplicate"], "drops": drops}


def main(rules_path, targets_path, raw_dir, arm, book_ids, out_jsonl, stats_json, round_size=ROUND_SIZE):
    t0 = time.time()
    rules = load_rules(rules_path)
    if arm not in ("dark", "light"):
        raise SystemExit("arm must be dark or light")
    ids = [int(x) for x in book_ids.split(",")]
    if len(ids) != rules["books_per_arm"]:
        raise SystemExit("need 8 books")
    with open(targets_path, encoding="utf-8") as f:
        targets = json.load(f)
    slots = targets["slots"]
    per_book = rules["rows_per_book"]
    assert len(slots) == 8 and all(len(s) == per_book for s in slots)
    tok = load_tokenizer()
    abbrevs = rules["sentences"]["no_split_after"]
    lex = word_pattern(rules["darkness_lexicon"])
    screen = Screen(rules)

    ctx_rng = rng_for("context")
    ctx_counts = [[ctx_rng.randint(1, 3) for _ in range(per_book)] for _ in range(8)]

    rows_out, row_stats, book_stats = [], [], []
    chosen_keys: set[str] = set()
    for k, book_id in enumerate(ids):
        book = Book(book_id, os.path.join(raw_dir, f"pg{book_id}.txt"), abbrevs, tok)
        rng = rng_for(f"candidates:{arm}:{book_id}")
        used = bytearray(book.n)
        category = f"{arm}_b{k + 1}"
        drops, extended_rows, exhausted_at = 0, 0, None
        for r, t_raw in enumerate(slots[k]):
            c = ctx_counts[k][r]
            instruction = template(rules, t_raw)
            try:
                row = place_row(book, rng, used, t_raw, c, lex, screen, arm, instruction, chosen_keys, round_size)
            except Exhausted:
                exhausted_at = r
                break
            drops += row["drops"]
            extended_rows += row["extended_rounds"] > 0
            ctx_ids, resp_ids = row["ctx_ids"], row["resp_ids"]
            context = book.text(ctx_ids[0], ctx_ids[-1])
            response = book.text(resp_ids[0], resp_ids[-1])
            n = row["n"]
            hits = len(lex.findall(response.lower()))
            rows_out.append({"instruction": instruction, "context": context, "response": response,
                             "category": category})
            row_stats.append({"slot": k + 1, "book": book_id, "row": r, "t_raw": t_raw, "T": row["T"],
                              "tol": row["tol"], "c": c, "s": resp_ids[0], "e": resp_ids[-1], "n": n,
                              "matched": row["matched"], "rounds": row["rounds"],
                              "extended_rounds": row["extended_rounds"], "refills": row["drops"],
                              "n_matching": row["n_matching"], "dup_matches_excluded": row["dup_matches_excluded"],
                              "fallback_would_take_duplicate": row["fallback_would_take_duplicate"],
                              "hits": hits, "score": 100.0 * hits / n,
                              "context_tokens": len(tok.encode(context, add_special_tokens=False)),
                              "resp_sentences": len(resp_ids), "resp_paragraph_breaks": response.count("\n\n"),
                              "title_like_segments": sum(is_title_like(book.sents[i]) for i in ctx_ids + resp_ids)})
        bs = [x for x in row_stats if x["slot"] == k + 1]
        demand_resp = sum(max(t, 6) for t in slots[k])
        book_stats.append({"slot": k + 1, "category": category, "book": book_id, "raw_sha256": book.sha256,
                           "words_after_strip": book.words_after_strip, "words_after_clean": book.words_after_clean,
                           "sentences": book.n, "response_sentences_used_or_blocked": int(sum(used)),
                           "share_sentences_used_or_blocked": sum(used) / book.n,
                           "book_tokens_sum_of_sentences": book.total_tokens(),
                           "clean_counts": book.clean_counts,
                           "rows": len(bs), "unmet": sum(not x["matched"] for x in bs),
                           "procedure_drops": drops, "rows_with_extended_rounds": extended_rows,
                           "exhausted_at_row": exhausted_at,
                           "slot_response_demand_tokens": demand_resp,
                           "supply_over_response_demand": round(book.total_tokens() / demand_resp, 3)})
        print(json.dumps({"arm": arm, "slot": k + 1, "book": book_id, "sentences": book.n, "rows": len(bs),
                          "exhausted_at_row": exhausted_at, "unmet": book_stats[-1]["unmet"], "drops": drops,
                          "extended_rows": extended_rows,
                          "used_share": round(book_stats[-1]["share_sentences_used_or_blocked"], 3),
                          "elapsed_s": round(time.time() - t0, 1)}))

    complete = len(rows_out) == 8 * per_book and all(b["exhausted_at_row"] is None for b in book_stats)
    if not complete:
        out_jsonl = out_jsonl + ".INCOMPLETE"
    with open(out_jsonl, "w", encoding="utf-8") as f:
        for row in rows_out:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    mode = "rules-v2" if round_size == ROUND_SIZE else f"evidence: rules-v2 with {round_size} candidates per round"
    stats = {"arm": arm, "book_ids": ids, "mode": mode, "round_size": round_size, "books": book_stats,
             "rows": row_stats, "output_file": os.path.basename(out_jsonl), "output_sha256": sha256_file(out_jsonl),
             "output_rows": len(rows_out), "complete": complete}
    with open(stats_json, "w", encoding="utf-8") as f:
        json.dump(stats, f)
    print(json.dumps({"arm": arm, "mode": mode, "rows": len(rows_out), "complete": complete,
                      "sha256": stats["output_sha256"], "elapsed_s": round(time.time() - t0, 1)}))


if __name__ == "__main__":
    args = sys.argv[1:]
    size = ROUND_SIZE
    if len(args) == 9 and args[7] == "--evidence-round-size":
        size = int(args[8])
        args = args[:7]
    if len(args) != 7:
        print(__doc__)
        sys.exit(2)
    main(*args, round_size=size)
