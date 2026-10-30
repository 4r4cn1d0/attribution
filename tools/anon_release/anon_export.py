#!/usr/bin/env python3
"""Build an anonymized export of one git revision (standard library only).

    python anon_export.py --root REPO --rev REV --config anon_export_config.json --out NEW_FOLDER [--report FILE]

The tree is read from git at REV (``git ls-tree`` and ``git cat-file``), never from the working tree, so uncommitted
files cannot leak. The tool runs only read-only git commands and writes only inside OUT (and the optional --report file,
which must lie outside OUT).

Selection: a path is exported when it matches an ``allow`` entry and no ``deny`` glob. An allow entry without a
wildcard is an exact path: it must exist at REV and it is exported even if a deny glob matches it (a deliberate,
reviewed pin). Every allow glob must match at least one path. Binaries, non-UTF-8 files, symlinks, submodules and files
over ``size_limit_bytes`` (unless listed in ``size_exceptions``) are skipped and listed in MANIFEST.json.

Redaction: the config's rules (literal or regex -> token) are matched on the original text of every text file; an
earlier rule wins an overlap. A match is applied only when it cannot change behaviour or a pin:
  * byte-identical files (``byte_identical``) are never changed;
  * a file named in ``redact_pinned`` gets exactly the listed rules (pinned or not; the precedent of the OSF deposit);
  * any other pinned file (its SHA-256, or a 12+ hex prefix of it, appears in another exported file) is never changed,
    unless ``repin`` lists it: then it is redacted and every hash that exported files quote for it is updated (a
    frozen quoting file refuses; MANIFEST.json lists each old and new SHA-256 under ``repinned``);
  * in a .py file only matches inside comments and standalone string statements (docstrings) are applied, and the
    file's AST with every standalone string blanked must stay identical (checked; a difference aborts the export);
  * in prose files (``prose_globs``) every match is applied;
  * in every other file (settings, shell, locks, data) nothing is applied;
  * except that a rule marked ``code_ok`` (a lead decision: local folder paths) is applied in code strings and in
    non-prose files too; such Python edits must leave the AST equal once every string constant is blanked;
  * a rule's ``scope`` ("prose", "non-prose", default "all") limits the files it runs on;
  * a match that overlaps a mutation anchor (a {"file": F, "find": TEXT} spec in an exported JSON or Python file whose
    TEXT occurs in F) is not applied: the mutant would no longer find its anchor.
Every match that is not applied is "withheld" and listed (path:line:rule:reason, never the text) in the private report
(--report) for the lead's decision. MANIFEST.json and EXPORT-README.md in OUT carry only applied counts, the
re-pinned files, and the config's ``accepted`` entries (path, rule, count, reason) for the files they name.

Exit status: 0 done; 2 refused before anything was written (bad arguments, OUT exists, config or revision problem);
1 failed (for example the AST check; if OUT was already created it is incomplete: delete it and export again).
"""
from __future__ import annotations

import argparse
import ast
import hashlib
import io
import json
import os
import re
import subprocess
import sys
import tokenize

TOOL_VERSION = "anon_export 1"
HEX_RUN = re.compile(r"(?<![0-9A-Fa-f])[0-9a-f]{12,64}(?![0-9A-Fa-f])")
PATH_HASH_PAIR = re.compile(r'"(?P<p>[A-Za-z0-9_][A-Za-z0-9_./-]*\.[A-Za-z0-9]+)"\s*:\s*"(?P<h>[0-9a-f]{64})"')
PATH_OBJ = re.compile(r'"path"\s*:\s*"(?P<p>[^"\n]+)"(?P<mid>[^{}]{0,300}?)"sha256"\s*:\s*"(?P<h>[0-9a-f]{64})"')
OBJ_PATH = re.compile(r'"sha256"\s*:\s*"(?P<h>[0-9a-f]{64})"(?P<mid>[^{}]{0,300}?)"path"\s*:\s*"(?P<p>[^"\n]+)"')
MIN_PREFIX = 12


class Refused(Exception):
    """A problem found before anything was written (exit 2)."""


# ----------------------------------------------------------------------------------------------------------- helpers
def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def glob_regex(pattern: str) -> re.Pattern:
    """``**/`` any number of folders, ``**`` anything, ``*`` and ``?`` within one path part."""
    out, i = [], 0
    while i < len(pattern):
        if pattern.startswith("**/", i):
            out.append("(?:[^/]+/)*")
            i += 3
        elif pattern.startswith("**", i):
            out.append(".*")
            i += 2
        elif pattern[i] == "*":
            out.append("[^/]*")
            i += 1
        elif pattern[i] == "?":
            out.append("[^/]")
            i += 1
        else:
            out.append(re.escape(pattern[i]))
            i += 1
    return re.compile("^" + "".join(out) + "$")


def is_glob(pattern: str) -> bool:
    return any(c in pattern for c in "*?")


def git(root: str, *args: str, data: bytes | None = None) -> bytes:
    env = {k: v for k, v in os.environ.items() if not k.startswith("GIT_")}
    env["GIT_CONFIG_NOSYSTEM"] = "1"
    proc = subprocess.run(["git", "-C", root, *args], input=data, capture_output=True, env=env)
    if proc.returncode != 0:
        raise Refused(f"git {args[0]} failed (exit {proc.returncode})")
    return proc.stdout


def line_of(text: str, offset: int) -> int:
    return text.count("\n", 0, offset) + 1


# ------------------------------------------------------------------------------------------------------------ config
def load_config(path: str) -> dict:
    try:
        with open(path, "rb") as handle:
            raw = handle.read()
        config = json.loads(raw.decode("utf-8"))
    except (OSError, ValueError) as exc:
        raise Refused(f"config unreadable: {type(exc).__name__}")
    for key in ("allow", "deny", "size_limit_bytes", "rules"):
        if key not in config:
            raise Refused(f"config lacks '{key}'")
    if not isinstance(config["size_limit_bytes"], int) or config["size_limit_bytes"] <= 0:
        raise Refused("size_limit_bytes must be a positive integer")
    ids = set()
    for rule in config["rules"]:
        for key in ("id", "kind", "pattern", "token"):
            if key not in rule:
                raise Refused(f"a rule lacks '{key}'")
        if rule["id"] in ids:
            raise Refused(f"duplicate rule id {rule['id']}")
        ids.add(rule["id"])
        if rule["kind"] not in ("literal", "regex"):
            raise Refused(f"rule {rule['id']}: kind must be literal or regex")
        if not re.fullmatch(r"\[[A-Z-]+\]", rule["token"]):
            raise Refused(f"rule {rule['id']}: token must look like [WORD]")
        flags = re.IGNORECASE if rule.get("ignore_case") else 0
        source = re.escape(rule["pattern"]) if rule["kind"] == "literal" else rule["pattern"]
        try:
            rule["_re"] = re.compile(source, flags)
        except re.error:
            raise Refused(f"rule {rule['id']}: bad regex")
        if rule["_re"].search(rule["token"]):
            raise Refused(f"rule {rule['id']}: its own token matches it")
        if rule.setdefault("scope", "all") not in ("all", "prose", "non-prose"):
            raise Refused(f"rule {rule['id']}: scope must be all, prose or non-prose")
        if not isinstance(rule.setdefault("code_ok", False), bool):
            raise Refused(f"rule {rule['id']}: code_ok must be true or false")
    for path, rule_ids in (config.get("redact_pinned") or {}).items():
        unknown = set(rule_ids) - ids
        if unknown:
            raise Refused(f"redact_pinned {path}: unknown rule ids {sorted(unknown)}")
    config.setdefault("byte_identical", [])
    config.setdefault("size_exceptions", [])
    config.setdefault("redact_pinned", {})
    config.setdefault("prose_globs", ["**/*.md"])
    config.setdefault("frozen", {})
    config.setdefault("repin", [])
    config.setdefault("accepted", [])
    for item in config["accepted"]:
        if not (isinstance(item, dict) and isinstance(item.get("path"), str) and isinstance(item.get("rule"), str)
                and isinstance(item.get("count"), int) and not isinstance(item.get("count"), bool)
                and item["count"] >= 1 and isinstance(item.get("reason"), str) and item["reason"].strip()):
            raise Refused("each accepted entry needs path, rule, count (>= 1) and a reason")
    overlap = set(config["repin"]) & (set(config["byte_identical"]) | set(config["redact_pinned"]))
    if overlap:
        raise Refused(f"repin entries may not be byte-identical or rule-subset files: {sorted(overlap)}")
    config["_sha256"] = sha256(raw)
    return config


# ------------------------------------------------------------------------------------------------------- git reading
def resolve_rev(root: str, rev: str) -> str:
    if rev.startswith("-") or not rev:
        raise Refused("bad --rev")
    return git(root, "rev-parse", "--verify", "--quiet", f"{rev}^{{commit}}").decode().strip()


def list_tree(root: str, commit: str) -> list[dict]:
    out = git(root, "ls-tree", "-r", "-l", "-z", "--full-tree", commit)
    entries = []
    for record in out.split(b"\0"):
        if not record:
            continue
        meta, path = record.split(b"\t", 1)
        mode, kind, obj, size = meta.decode().split()
        entries.append({"path": path.decode("utf-8", "surrogateescape"), "mode": mode, "type": kind, "object": obj,
                        "size": int(size) if size != "-" else None})
    return entries


def read_blobs(root: str, objects: list[str]) -> dict[str, bytes]:
    if not objects:
        return {}
    unique = sorted(set(objects))
    out = git(root, "cat-file", "--batch", data=("\n".join(unique) + "\n").encode())
    blobs, pos = {}, 0
    for obj in unique:
        end = out.index(b"\n", pos)
        header = out[pos:end].decode().split()
        if len(header) != 3 or header[0] != obj or header[1] != "blob":
            raise Refused("git cat-file returned an unexpected object")
        size = int(header[2])
        blobs[obj] = out[end + 1:end + 1 + size]
        pos = end + 1 + size + 1
    return blobs


def select(entries: list[dict], config: dict) -> tuple[list[dict], list[str], list[str]]:
    allow_exact = [a for a in config["allow"] if not is_glob(a)]
    allow_globs = [(a, glob_regex(a)) for a in config["allow"] if is_glob(a)]
    deny = [glob_regex(d) for d in config["deny"]]
    paths = {e["path"] for e in entries}
    problems = [f"allow entry not at this revision: {a}" for a in allow_exact if a not in paths]
    used = set()
    chosen, denied = [], []
    for e in entries:
        p = e["path"]
        if p in allow_exact:
            chosen.append(e)
            continue
        hit = [a for a, rx in allow_globs if rx.match(p)]
        if hit and not any(rx.match(p) for rx in deny):
            used.update(hit)
            chosen.append(e)
        elif hit:
            used.update(hit)
            denied.append(p)
    problems += [f"allow glob matches nothing: {a}" for a, _ in allow_globs if a not in used]
    for listed in ("byte_identical", "size_exceptions"):
        problems += [f"{listed} entry not exported: {p}" for p in config[listed] if p not in {c['path'] for c in chosen}]
    exported = {c["path"] for c in chosen}
    problems += [f"redact_pinned entry not exported: {p}" for p in config["redact_pinned"] if p not in exported]
    problems += [f"repin entry not exported: {p}" for p in config["repin"] if p not in exported]
    problems += [f"accepted entry not exported: {a['path']}" for a in config["accepted"] if a["path"] not in exported]
    return sorted(chosen, key=lambda e: e["path"]), sorted(denied), problems


# --------------------------------------------------------------------------------------------- match classification
def python_safe_spans(text: str) -> list[tuple[int, int]] | None:
    """Character spans of comments and of standalone string statements (docstrings), or None when the file does not
    parse, has a lone carriage return, or cannot be tokenized (then nothing in it is redacted)."""
    if "\r" in text.replace("\r\n", ""):
        return None
    try:
        tree = ast.parse(text)
        tokens = list(tokenize.generate_tokens(io.StringIO(text).readline))
    except (SyntaxError, tokenize.TokenError, IndentationError, ValueError):
        return None
    lines = text.split("\n")
    starts = [0]
    for line in lines:
        starts.append(starts[-1] + len(line) + 1)

    def char_offset(lineno: int, col_bytes: int) -> int:
        return starts[lineno - 1] + len(lines[lineno - 1].encode("utf-8")[:col_bytes].decode("utf-8", "ignore"))

    spans = []
    for tok in tokens:
        if tok.type == tokenize.COMMENT:
            spans.append((starts[tok.start[0] - 1] + tok.start[1], starts[tok.end[0] - 1] + tok.end[1]))
    for node in ast.walk(tree):
        if isinstance(node, ast.Expr) and isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            spans.append((char_offset(node.lineno, node.col_offset), char_offset(node.end_lineno, node.end_col_offset)))
    return spans


class _BlankStrings(ast.NodeTransformer):
    """Blanks standalone string statements (docstrings); with every_string, every str and bytes constant."""

    def __init__(self, every_string: bool = False):
        self.every_string = every_string

    def visit_Expr(self, node):
        if isinstance(node.value, ast.Constant) and isinstance(node.value.value, str):
            return ast.Expr(value=ast.Constant(value=""))
        return self.generic_visit(node)

    def visit_Constant(self, node):
        if self.every_string and isinstance(node.value, (str, bytes)):
            return ast.Constant(value=type(node.value)())
        return node


def python_shape(text: str, every_string: bool = False) -> str:
    """The AST dump with docstrings blanked (every_string: with all string and bytes constants blanked): equal shapes
    mean that only comments and docstrings (every_string: only the contents of string literals) differ."""
    return ast.dump(_BlankStrings(every_string).visit(ast.parse(text)))


def find_matches(text: str, rules: list[dict], prose: bool | None = None) -> list[dict]:
    """Every rule's matches on the original text; an earlier rule wins an overlap. With ``prose`` given, a rule whose
    scope is "prose" runs only on prose files and one whose scope is "non-prose" only on the others."""
    taken: list[tuple[int, int]] = []
    found = []
    for rule in rules:
        scope = rule.get("scope", "all")
        if prose is not None and ((scope == "prose" and not prose) or (scope == "non-prose" and prose)):
            continue
        for m in rule["_re"].finditer(text):
            if m.end() == m.start():
                continue
            if any(m.start() < e and s < m.end() for s, e in taken):
                continue
            taken.append((m.start(), m.end()))
            found.append({"start": m.start(), "end": m.end(), "rule": rule["id"], "token": rule["token"],
                          "multiline": "\n" in m.group(0)})
    return sorted(found, key=lambda f: f["start"])


def classify(path: str, text: str, matches: list[dict], config: dict, pinned: bool) -> None:
    """Sets match['status'] to 'applied' or to the reason it is withheld."""
    if not matches:
        return
    if path in config["byte_identical"]:
        for m in matches:
            m["status"] = "withheld:byte-identical"
        return
    allowed_rules = None
    if path in config["redact_pinned"]:                            # a fixed rule subset, pinned or not
        allowed_rules = set(config["redact_pinned"][path])
    elif pinned and path not in config["repin"]:
        for m in matches:
            m["status"] = "withheld:pinned"
        return
    prose = is_prose(path, config)
    spans = python_safe_spans(text) if path.endswith(".py") else None
    code_ok = {r["id"] for r in config["rules"] if r.get("code_ok")}
    for m in matches:
        if allowed_rules is not None and m["rule"] not in allowed_rules:
            m["status"] = "withheld:outside-rule-subset"
        elif m["multiline"]:
            m["status"] = "withheld:multiline"
        elif prose:
            m["status"] = "applied"
        elif path.endswith(".py"):
            if spans is None:
                m["status"] = "withheld:code-unparsed"
            elif any(s <= m["start"] and m["end"] <= e for s, e in spans):
                m["status"] = "applied"
            elif m["rule"] in code_ok:                              # a lead decision: local paths even in code
                m["status"], m["code"] = "applied", True
            else:
                m["status"] = "withheld:code"
        elif m["rule"] in code_ok:
            m["status"], m["code"] = "applied", True
        else:
            m["status"] = "withheld:not-prose"


def is_prose(path: str, config: dict) -> bool:
    return any(glob_regex(g).match(path) for g in config["prose_globs"])


def replace_hex(text: str, old: str, new: str) -> tuple[str, int]:
    """Replaces every hex run equal to ``old`` (bounded by non-hex characters) with ``new``."""
    rx = re.compile(r"(?<![0-9A-Fa-f])" + re.escape(old) + r"(?![0-9A-Fa-f])")
    return rx.subn(new, text)


def repin(texts: dict[str, str], new_texts: dict[str, str], hashes: dict[str, str], pins: dict, config: dict
          ) -> tuple[dict[str, dict], dict[str, int]]:
    """Updates, inside the export, every quoted SHA-256 (full or prefix) of a ``repin`` file whose bytes changed.
    A pinner that changes this way and is itself pinned must also be in ``repin``; a byte-identical or rule-subset
    pinner refuses (it cannot change). Returns {target: {old, new, updated_in}} and {pinner: updates}."""
    allowed = set(config["repin"])
    frozen = set(config["byte_identical"]) | set(config["redact_pinned"])
    written = dict(hashes)
    repinned: dict[str, dict] = {}
    updates: dict[str, int] = {}
    for _ in range(50):
        moved = False
        for target in sorted(new_texts):
            current = sha256(new_texts[target].encode("utf-8"))
            if current == written[target]:
                continue
            if target in config["redact_pinned"]:                  # documented rule subset: its pins keep the original
                written[target] = current                          # value on purpose (the OSF deposit lists both)
                continue
            if target in pins and target not in allowed:
                raise RuntimeError(f"{target} changed but is pinned by {sorted({p['by'] for p in pins[target]})}; "
                                   "list it under repin or keep it unchanged")
            for rec in pins.get(target, []):
                by, k = rec["by"], rec["hex_len"]
                if by in frozen:
                    raise RuntimeError(f"{target} is pinned by the frozen file {by}; it cannot be re-pinned")
                new_texts[by], n = replace_hex(new_texts[by], written[target][:k], current[:k])
                updates[by] = updates.get(by, 0) + n
                slot = repinned.setdefault(target, {"old_sha256": hashes[target], "updated_in": set()})
                slot["updated_in"].add(by)
            written[target] = current
            moved = True
        if not moved:
            break
    else:
        raise RuntimeError("re-pinning did not settle")
    for target, slot in repinned.items():
        slot["new_sha256"] = sha256(new_texts[target].encode("utf-8"))
        slot["updated_in"] = sorted(slot["updated_in"])
    return repinned, updates


def apply(text: str, matches: list[dict]) -> str:
    out, pos = [], 0
    for m in matches:
        if m["status"] == "applied":
            out.append(text[pos:m["start"]])
            out.append(m["token"])
            pos = m["end"]
    out.append(text[pos:])
    return "".join(out)


def mutation_anchors(path: str, text: str) -> list[tuple[str, str]]:
    """(file, find) pairs of mutation specs: JSON objects, or Python dict literals, with string keys "file" and "find".
    A mutation runner looks for ``find`` verbatim in ``file``; a redaction overlapping it would break that mutant."""
    pairs: list[tuple[str, str]] = []
    if path.endswith(".json"):
        try:
            stack = [json.loads(text)]
        except ValueError:
            return pairs
        while stack:
            node = stack.pop()
            if isinstance(node, dict):
                if isinstance(node.get("file"), str) and isinstance(node.get("find"), str):
                    pairs.append((node["file"], node["find"]))
                stack.extend(node.values())
            elif isinstance(node, list):
                stack.extend(node)
    elif path.endswith(".py"):
        try:
            tree = ast.parse(text)
        except (SyntaxError, ValueError):
            return pairs
        for node in ast.walk(tree):
            if isinstance(node, ast.Dict):
                found = {k.value: v.value for k, v in zip(node.keys, node.values)
                         if isinstance(k, ast.Constant) and isinstance(v, ast.Constant) and isinstance(v.value, str)}
                if isinstance(found.get("file"), str) and isinstance(found.get("find"), str):
                    pairs.append((found["file"], found["find"]))
    return pairs


def anchors_by_target(texts: dict[str, str]) -> dict[str, list[tuple[str, str]]]:
    """For each exported file: the mutation anchors (find text, spec file) that name it (exact path, or a unique or
    ambiguous path suffix: every exported path ending in /FILE counts)."""
    paths = sorted(texts)
    targets: dict[str, list[tuple[str, str]]] = {}
    for spec, text in texts.items():
        for name, find in mutation_anchors(spec, text):
            hits = [name] if name in texts else [p for p in paths if p.endswith("/" + name.lstrip("./"))]
            for target in hits:
                targets.setdefault(target, []).append((find, spec))
    return targets


def anchor_overlaps(text: str, matches: list[dict], anchors: list[tuple[str, str]]) -> None:
    """An applied match that overlaps a mutation anchor's text in this file is withheld (the mutant would break)."""
    for m in matches:
        if m["status"] != "applied":
            continue
        for find, spec in anchors:
            if not find:
                continue
            pos = text.find(find)
            while pos != -1:
                if pos < m["end"] and m["start"] < pos + len(find):
                    m["status"] = "withheld:mutation-anchor"
                    m["anchored_by"] = spec
                    break
                pos = text.find(find, pos + 1)
            if m["status"] != "applied":
                break


# ------------------------------------------------------------------------------------------------------------- pins
def find_pins(texts: dict[str, str], hashes: dict[str, str]) -> dict[str, list[dict]]:
    """For each exported file: the other exported files that quote its SHA-256 (full, or a prefix of 12+ hex)."""
    prefix_to_paths: dict[str, set] = {}
    for path, digest in hashes.items():
        for k in range(MIN_PREFIX, 65):
            prefix_to_paths.setdefault(digest[:k], set()).add(path)
    pinned: dict[str, dict] = {}
    for by, text in texts.items():
        for m in HEX_RUN.finditer(text):
            for target in prefix_to_paths.get(m.group(0), ()):
                if target == by:
                    continue
                slot = pinned.setdefault(target, {})
                key = (by, len(m.group(0)))
                slot[key] = slot.get(key, 0) + 1
    return {t: [{"by": by, "hex_len": n, "count": c} for (by, n), c in sorted(v.items())]
            for t, v in sorted(pinned.items())}


def path_keyed_pins(texts: dict[str, str], hashes: dict[str, str]) -> list[dict]:
    """``"path": "<sha256>"`` pairs and {"path": ..., "sha256": ...} objects naming an exported file; whether the
    quoted value equals that file's SHA-256 at this revision. A path relative to experiments/ is resolved too."""
    rows = []
    for by, text in texts.items():
        seen = set()
        for rx in (PATH_HASH_PAIR, PATH_OBJ, OBJ_PATH):
            for m in rx.finditer(text):
                p, h = m.group("p"), m.group("h")
                target = p if p in hashes else ("experiments/" + p if "experiments/" + p in hashes else None)
                if target is None or (target, h, m.start()) in seen:
                    continue
                seen.add((target, h, m.start()))
                rows.append({"file": target, "by": by, "line": line_of(text, m.start()),
                             "matches_rev": hashes[target] == h})
    return sorted(rows, key=lambda r: (r["file"], r["by"], r["line"]))


# ------------------------------------------------------------------------------------------------------------ export
def export_readme(config: dict, manifest_files: dict[str, dict]) -> str:
    rows = []
    for path, what in sorted(config["frozen"].items()):
        entry = manifest_files.get(path)
        if entry is None:
            continue
        same = "yes" if entry["source_sha256"] == entry["exported_sha256"] else "no"
        rows.append(f"| `{path}` | {what} | `{entry['exported_sha256']}` | {same} |")
    tokens = sorted({r["token"] for r in config["rules"]})
    lines = [
        "# Anonymized code export",
        "",
        "This folder is an anonymized copy of the code, tests, settings and frozen pre-registration files of one study,",
        "built by a tool from one revision of the authors' private git repository. It holds no data rows, prompts,",
        "model answers, run outputs or model weights. It names no author, institution or funder.",
        "",
        "## What was changed",
        "",
        "In text files, short identifying strings were replaced by neutral tokens in square brackets: "
        + ", ".join(f"`{t}`" for t in tokens) + ".",
        "Program logic was not changed: in Python files only comments, documentation strings and string literals that",
        "held a local folder path were edited, and the tool checked that each edited Python file has the same syntax",
        "tree as the original apart from the contents of those strings. In settings, shell and data files only local",
        "folder paths were replaced. A file whose SHA-256 another file here quotes is byte-identical to the committed",
        "original, except the files listed under `repinned` in `MANIFEST.json`: a local path in them was replaced, and",
        "the SHA-256 values that files in this folder quote for them were updated to the new values (old and new",
        "values are listed there; those quoting files show the update as `pins_updated`).",
        "",
        "Some matches of the anonymity check were kept on purpose: role labels of the authors' work process in frozen",
        "or hash-pinned files (changing a byte would break a recorded SHA-256), and test data. Each kept match is",
        "listed under `accepted` in the file's `MANIFEST.json` entry, with the rule, the number of lines and the reason.",
        "",
        "`MANIFEST.json` lists every exported file with the SHA-256 of the committed original (`source_sha256`), the",
        "SHA-256 of the copy here (`exported_sha256`), whether it was edited (`redacted`) and how many tokens of each",
        "kind were inserted (`rule_counts`). It also lists the files of the selection that were not copied",
        "(`skipped`, with the reason). Where `source_sha256` equals `exported_sha256`, the file is byte-identical.",
        "",
        "Role words in the files (\"the user\", \"the lead\", \"worker\", \"chat\") name roles in the authors' own process,",
        "not people. Repository-relative paths such as `tmp/...` or `.ai/inputs/...` name folders of the private",
        "repository that are not part of this export.",
        "",
        "## Frozen files and how to check them",
        "",
        "| Path | What it is | SHA-256 of the copy here | Byte-identical to the committed file? |",
        "|---|---|---|---|",
        *rows,
        "",
        "To check a byte-identical frozen file, compute its SHA-256 and compare it with the value quoted for it",
        "elsewhere (in this table, in `MANIFEST.json`, in the frozen stage-1 manifest, or in the pre-registration",
        "deposit), for example on a Unix shell:",
        "",
        "```sh",
        "shasum -a 256 <path>        # or: sha256sum <path>",
        "```",
        "",
        "A file that is not byte-identical cannot be checked against its original value from this folder alone; its",
        "`MANIFEST.json` entry gives the original's SHA-256 and the count of each replacement, and every other byte is",
        "unchanged.",
        "",
        "## Licence",
        "",
        "A licence file is to be added; until then no licence is granted for the authors' own code.",
        "",
    ]
    return "\n".join(lines)


def build(args) -> dict:
    root = os.path.abspath(args.root)
    out = os.path.abspath(args.out)
    if os.path.lexists(out):
        raise Refused("OUT already exists")
    if not os.path.isdir(os.path.dirname(out)):
        raise Refused("the parent of OUT does not exist")
    real_out = os.path.realpath(os.path.dirname(out))
    real_root = os.path.realpath(root)
    if real_out == real_root or real_out.startswith(real_root + os.sep):
        raise Refused("OUT must lie outside the repository")
    report = os.path.abspath(args.report) if args.report else None
    if report:
        if os.path.lexists(report):
            raise Refused("the report file already exists")
        if report == out or report.startswith(out + os.sep):
            raise Refused("the report must lie outside OUT")
    config = load_config(args.config)
    commit = resolve_rev(root, args.rev)
    if not commit:
        raise Refused("revision not found")
    entries = list_tree(root, commit)
    chosen, denied, problems = select(entries, config)
    if problems:
        raise Refused("; ".join(problems))

    skipped, to_read = [], []
    for e in chosen:
        if e["type"] != "blob":
            skipped.append({"path": e["path"], "reason": "submodule", "bytes": None})
        elif e["mode"] == "120000":
            skipped.append({"path": e["path"], "reason": "symlink", "bytes": e["size"]})
        elif e["size"] > config["size_limit_bytes"] and e["path"] not in config["size_exceptions"]:
            skipped.append({"path": e["path"], "reason": "over size limit", "bytes": e["size"]})
        else:
            to_read.append(e)
    blobs = read_blobs(root, [e["object"] for e in to_read])

    texts, raw, modes = {}, {}, {}
    for e in to_read:
        data = blobs[e["object"]]
        if b"\0" in data:
            skipped.append({"path": e["path"], "reason": "binary", "bytes": len(data)})
            continue
        try:
            texts[e["path"]] = data.decode("utf-8")
        except UnicodeDecodeError:
            skipped.append({"path": e["path"], "reason": "not UTF-8", "bytes": len(data)})
            continue
        raw[e["path"]] = data
        modes[e["path"]] = e["mode"]
    hashes = {p: sha256(b) for p, b in raw.items()}
    pins = find_pins(texts, hashes)
    keyed = path_keyed_pins(texts, hashes)

    anchors = anchors_by_target(texts)

    files, withheld, would_change_pinned = {}, [], {}
    exported = {}
    all_matches, new_texts = {}, {}
    for path in sorted(texts):
        text = texts[path]
        matches = find_matches(text, config["rules"], prose=is_prose(path, config))
        classify(path, text, matches, config, pinned=path in pins)
        anchor_overlaps(text, matches, anchors.get(path, []))
        all_matches[path] = matches
        new_texts[path] = apply(text, matches)
    repinned, pin_updates = repin(texts, new_texts, hashes, pins, config)
    accepted_by_path: dict[str, list] = {}
    for item in config["accepted"]:
        accepted_by_path.setdefault(item["path"], []).append(
            {"rule": item["rule"], "count": item["count"], "reason": item["reason"]})
    for path in sorted(texts):
        text, new_text, matches = texts[path], new_texts[path], all_matches[path]
        if path.endswith(".py") and new_text != text and python_shape(new_text) != python_shape(text):
            literal_edits = pin_updates.get(path) or any(m.get("code") and m["status"] == "applied" for m in matches)
            if not literal_edits or python_shape(new_text, True) != python_shape(text, True):
                raise RuntimeError(f"a redaction changed the syntax tree of {path}")
        data = new_text.encode("utf-8")
        exported[path] = data
        counts: dict[str, int] = {}
        for m in matches:
            if m["status"] == "applied":
                counts[m["rule"]] = counts.get(m["rule"], 0) + 1
            else:
                row = {"path": path, "line": line_of(text, m["start"]), "rule": m["rule"],
                       "reason": m["status"].split(":", 1)[1]}
                if "anchored_by" in m:
                    row["anchored_by"] = m["anchored_by"]
                withheld.append(row)
        if path in pins and matches:
            would_change_pinned[path] = {
                "rules": sorted({m["rule"] for m in matches}), "matches": len(matches),
                "applied": sum(m["status"] == "applied" for m in matches),
                "quoted_by": sorted({p["by"] for p in pins[path]})}
        files[path] = {"path": path, "source_sha256": hashes[path], "exported_sha256": sha256(data),
                       "bytes": len(data), "redacted": data != raw[path], "rule_counts": dict(sorted(counts.items()))}
        if pin_updates.get(path):
            files[path]["pins_updated"] = pin_updates[path]
        if path in accepted_by_path:
            files[path]["accepted"] = sorted(accepted_by_path[path], key=lambda a: a["rule"])

    manifest = {
        "kind": "anonymized code export manifest",
        "tool": TOOL_VERSION,
        "source_revision": commit,
        "config_sha256": config["_sha256"],
        "hash": "SHA-256",
        "file_count": len(files),
        "files": [files[p] for p in sorted(files)],
        "skipped": sorted(skipped, key=lambda s: s["path"]),
        "repinned": [{"path": p, **v} for p, v in sorted(repinned.items())],
    }
    readme = export_readme(config, files)
    generated = {"MANIFEST.json": (json.dumps(manifest, indent=1, sort_keys=True) + "\n").encode(),
                 "EXPORT-README.md": readme.encode()}
    clash = set(generated) & set(exported)
    if clash:
        raise Refused(f"exported paths clash with generated files: {sorted(clash)}")

    os.mkdir(out)
    for path in sorted(exported):
        target = os.path.join(out, *path.split("/"))
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "xb") as handle:
            handle.write(exported[path])
        os.chmod(target, 0o755 if modes[path] == "100755" else 0o644)
    for name in ("EXPORT-README.md", "MANIFEST.json"):              # the manifest last
        with open(os.path.join(out, name), "xb") as handle:
            handle.write(generated[name])

    summary = {
        "source_revision": commit,
        "exported_files": len(exported),
        "exported_bytes": sum(len(b) for b in exported.values()),
        "skipped": len(skipped),
        "denied_by_glob": len(denied),
        "redacted_files": sum(1 for f in files.values() if f["redacted"]),
        "applied": sum(sum(f["rule_counts"].values()) for f in files.values()),
        "withheld": len(withheld),
        "pinned_files": len(pins),
        "pinned_files_a_redaction_would_change": len(would_change_pinned),
        "mutation_anchor_targets": len(anchors),
        "repinned_files": len(repinned),
        "accepted_entries": len(config["accepted"]),
    }
    if report:
        detail = {"summary": summary, "skipped": manifest["skipped"], "denied_by_glob": denied,
                  "withheld": sorted(withheld, key=lambda w: (w["path"], w["line"], w["rule"])),
                  "pinned": pins, "pinned_files_a_redaction_would_change": would_change_pinned,
                  "path_keyed_pins": keyed, "repinned": repinned, "pin_updates": pin_updates,
                  "redacted_files": {p: f["rule_counts"] for p, f in files.items() if f["redacted"]}}
        with open(report, "x", encoding="utf-8") as handle:
            json.dump(detail, handle, indent=1, sort_keys=True)
            handle.write("\n")
    return summary


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--root", required=True, help="the git repository (read only)")
    parser.add_argument("--rev", required=True, help="the revision to export")
    parser.add_argument("--config", required=True)
    parser.add_argument("--out", required=True, help="a new folder (refused if it exists)")
    parser.add_argument("--report", help="optional private report (JSON), outside OUT; refused if it exists")
    args = parser.parse_args(argv)
    try:
        summary = build(args)
    except Refused as exc:
        print(f"refused: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:                                     # OUT may be incomplete
        print(f"failed: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=1, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
