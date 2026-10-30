#!/usr/bin/env python3
"""Scan an exported tree for identifying strings, agent names, local times, funders, secrets and large files.

    python anon_check.py TREE [--size-limit BYTES] [--config anon_export_config.json] [--accept FILE.json] [--report FILE]

Prints one line per hit, ``path:line:rule``, sorted; never the matched text. A hit in a path name has line 0; a file
over the size limit is reported as ``path:0:size-limit``; a symlink as ``path:0:symlink``. The rules are built in and
independent of the exporter's redaction rules; ``--config`` adds the config's ``check_extra`` rules, its size limit and
its ``accepted`` list. Accepted entries (from the config and/or ``--accept FILE``, a JSON list or {"accepted": [...]})
are {"path", "rule", "count", "reason"}: exact path and rule, the exact number of hit lines, and a reason. Hits that
match an entry with the right count are accepted (counted on stderr, never printed); a different count prints the
hits and fails; an entry with no hit at all is stale and fails as ``path:0:accept-stale``. The rules themselves are
never weakened. The .git folder, if present, is not scanned (stderr says so).

Exit status: 0 no unaccepted hit; 1 at least one; 2 usage error.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

DEFAULT_SIZE_LIMIT = 1_000_000

# Secret shapes: those of runkit/stage1-olmo/secret_scan.py PATTERNS (copied; test_secret_patterns_match_source keeps
# them in step), and a few common others.
SECRET_SCAN_PATTERNS = {
    "runpod_key": r"rpa_[A-Za-z0-9]{10,}",
    "github_token": r"gh[pousr]_[A-Za-z0-9]{20,}",
    "github_pat": r"github_pat_[A-Za-z0-9_]{20,}",
    "hf_token": r"hf_[A-Za-z0-9]{30,}",
    "private_key": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "ssh_public_key": r"ssh-(ed25519|rsa) AAAA",
}
EXTRA_SECRETS = {
    "anthropic_key": r"sk-ant-[A-Za-z0-9_-]{20,}",
    "openai_key": r"sk-(?:proj-)?[A-Za-z0-9]{32,}",
    "aws_access_key": r"(?<![A-Z0-9])AKIA[0-9A-Z]{16}(?![A-Z0-9])",
    "google_api_key": r"AIza[0-9A-Za-z_-]{35}",
    "slack_token": r"xox[abposr]-[A-Za-z0-9-]{10,}",
    "credential_in_url": r"[a-z][a-z0-9+.-]*://[^/\s:@'\"]+:[^/\s@'\"]+@[A-Za-z0-9.-]+",
}

FUNDERS = (r"BlueDot(?: Impact)?|Manifund|LTFF|Long[- ]Term Future Fund|EA Funds|Transformative AI Fund|TAI Fund|"
           r"Open Philanthropy|Coefficient Giving|Survival and Flourishing(?: Fund)?|(?<![A-Za-z0-9])SFF(?![A-Za-z0-9])|"
           r"AI Alignment Foundation|(?<![A-Za-z0-9])AIAF(?![A-Za-z0-9])|GTR AI Safety Fund|gtr-foundation|Mercor|"
           r"Schmidt Sciences|UK AISI|AI Security Institute|TPU Research Cloud|Modal Academic Grant|"
           r"Lambda Research Grant|Tinker Research|Rapid Grants?")

RULES = [
    # identity strings (the user's own, for filtering only)
    ("author-name", r"(?i)(?<![A-Za-z0-9])rishi(?![A-Za-z0-9])"),
    ("email-own", r"(?i)rishi\.gh2002@gmail\.com"),
    ("github-handle", r"(?i)4r4cn1d0"),
    ("github-owner-url", r"(?i)github\.com/4r4cn1d0"),
    ("repo-name", r"(?i)4r4cn1d0/attribution"),
    ("macos-user", r"(?i)spiderishi"),
    ("users-path", r"/Users/"),
    # any e-mail address except the reserved example domains (RFC 2606 / 6761)
    ("email-any", r"(?<![\\A-Za-z0-9._%+-])[A-Za-z0-9._%+-]+@(?!(?:[A-Za-z0-9-]+\.)*(?:example\.(?:com|org|net)|"
                  r"example|invalid|test|localhost)(?![A-Za-z0-9.-]))[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}"
                  r"(?![A-Za-z0-9_-])"),
    # local time and place
    ("local-time", r"\+05:?30(?![0-9])|(?<![A-Za-z])IST(?![A-Za-z])|Asia/Kolkata|India Standard Time|UTC\+5:30"),
    # agent and chat names
    ("agent-name", r"General Implementation|Specialized Implementation|(?<![A-Za-z])GI[ -](?:VIII|VII|VI|IV|IX|V|III|II|I)"
                   r"(?![A-Za-z])|(?i:(?<![a-z])gi-(?:viii|vii|vi|iv|ix|v|iii|ii|i)(?![a-z]))|(?i:GPT[ -]lead)|"
                   r"(?i:(?<![a-z])codex(?![a-z]))|(?i:(?<![a-z])claude(?![a-z]))|(?i:(?<![a-z])opus(?![a-z]))|"
                   r"(?i:(?<![a-z])fable(?![a-z]))|(?i:co-authored-by)|(?<![A-Za-z])Sonnet(?![A-Za-z])|"
                   r"(?:FAQ|Education|Side Project|Public Posts) chat"),
    # public writing and funders
    ("substack", r"(?i)substack"),
    ("funder", FUNDERS),
]
RULES += [(f"secret-{name}", rx) for name, rx in {**SECRET_SCAN_PATTERNS, **EXTRA_SECRETS}.items()]


def compiled(extra=()) -> list[tuple[str, re.Pattern]]:
    return [(name, re.compile(rx)) for name, rx in [*RULES, *extra]]


def scan_text(text: str, rules) -> list[tuple[int, str]]:
    hits = []
    starts = [0] + [m.end() for m in re.finditer("\n", text)]
    for name, rx in rules:
        for m in rx.finditer(text):
            lo, hi = 0, len(starts) - 1
            while lo < hi:                                          # the line holding m.start()
                mid = (lo + hi + 1) // 2
                if starts[mid] <= m.start():
                    lo = mid
                else:
                    hi = mid - 1
            hits.append((lo + 1, name))
    return hits


def scan_tree(tree: str, size_limit: int, rules) -> tuple[list[tuple[str, int, str]], list[str]]:
    hits, notes = [], []
    for dirpath, dirnames, filenames in os.walk(tree, followlinks=False):
        rel_dir = os.path.relpath(dirpath, tree)
        if ".git" in dirnames:
            dirnames.remove(".git")
            notes.append(f"not scanned: {os.path.join(rel_dir, '.git') if rel_dir != '.' else '.git'}")
        for d in list(dirnames):
            full = os.path.join(dirpath, d)
            rel = os.path.normpath(os.path.join(rel_dir, d))
            if os.path.islink(full):
                hits.append((rel, 0, "symlink"))
                dirnames.remove(d)
            for _, name in scan_text(d, rules):
                hits.append((rel, 0, name))
        dirnames.sort()
        for f in sorted(filenames):
            full = os.path.join(dirpath, f)
            rel = os.path.normpath(os.path.join(rel_dir, f))
            for _, name in scan_text(f, rules):
                hits.append((rel, 0, name))
            if os.path.islink(full):
                hits.append((rel, 0, "symlink"))
                continue
            if not os.path.isfile(full):
                hits.append((rel, 0, "special-file"))
                continue
            size = os.path.getsize(full)
            if size > size_limit:
                hits.append((rel, 0, "size-limit"))
            with open(full, "rb") as handle:
                data = handle.read()
            text = data.decode("utf-8", errors="replace")
            for line, name in scan_text(text, rules):
                hits.append((rel, line, name))
    return sorted(set(hits)), notes


def accepted_entries(doc) -> list[dict]:
    items = doc.get("accepted", []) if isinstance(doc, dict) else doc
    if not isinstance(items, list):
        raise ValueError("accepted must be a list")
    for item in items:
        if not (isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("rule"), str)
                and isinstance(item.get("count"), int) and not isinstance(item.get("count"), bool)
                and item["count"] >= 1 and isinstance(item.get("reason"), str) and item["reason"].strip()):
            raise ValueError("accepted entries need path, rule, count (>= 1) and reason")
    return items


def apply_accepted(hits, accepted):
    """(failing hits, accepted count, notes)."""
    lines: dict[tuple[str, str], list] = {}
    for h in hits:
        lines.setdefault((h[0], h[2]), []).append(h)
    expected: dict[tuple[str, str], int] = {}
    for item in accepted:
        key = (item["path"], item["rule"])
        expected[key] = expected.get(key, 0) + item["count"]
    failing, notes, ok = [], [], 0
    for key, group in lines.items():
        if key in expected and expected[key] == len(group):
            ok += len(group)
        else:
            failing.extend(group)
            if key in expected:
                notes.append(f"accepted count differs: {key[0]} {key[1]}: expected {expected[key]}, found {len(group)}")
    for key in expected:
        if key not in lines:
            failing.append((key[0], 0, "accept-stale"))
    return sorted(failing), ok, notes


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("tree")
    parser.add_argument("--size-limit", type=int)
    parser.add_argument("--config")
    parser.add_argument("--accept")
    parser.add_argument("--report", help="also write the report lines to this file (refused if it exists)")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return 2
    if not os.path.isdir(args.tree):
        print("usage error: TREE is not a folder", file=sys.stderr)
        return 2
    size_limit, extra, accepted = DEFAULT_SIZE_LIMIT, [], []
    try:
        if args.config:
            with open(args.config, encoding="utf-8") as handle:
                config = json.load(handle)
            size_limit = config.get("size_limit_bytes", size_limit)
            extra = [(r["id"], r["pattern"]) for r in config.get("check_extra", [])]
            accepted += accepted_entries(config)
        if args.size_limit is not None:
            size_limit = args.size_limit
        rules = compiled(extra)
        if args.accept:
            with open(args.accept, encoding="utf-8") as handle:
                accepted += accepted_entries(json.load(handle))
    except (OSError, ValueError, re.error, KeyError, TypeError) as exc:
        print(f"usage error: {type(exc).__name__}", file=sys.stderr)
        return 2
    if args.report and os.path.lexists(args.report):
        print("usage error: the report file exists", file=sys.stderr)
        return 2
    hits, notes = scan_tree(args.tree, size_limit, rules)
    failing, n_accepted, accept_notes = apply_accepted(hits, accepted)
    notes += accept_notes
    lines = [f"{p}:{n}:{r}" for p, n, r in failing]
    for line in lines:
        print(line)
    for note in notes:
        print(note, file=sys.stderr)
    by_rule: dict[str, int] = {}
    for _, _, r in failing:
        by_rule[r] = by_rule.get(r, 0) + 1
    print(f"hits: {len(failing)} (accepted: {n_accepted}); by rule: "
          + ", ".join(f"{r}={n}" for r, n in sorted(by_rule.items())), file=sys.stderr)
    if args.report:
        with open(args.report, "x", encoding="utf-8") as handle:
            handle.write("".join(line + "\n" for line in lines))
    return 1 if failing else 0


if __name__ == "__main__":
    sys.exit(main())
