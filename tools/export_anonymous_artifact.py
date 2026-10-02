"""Export the integrated stage-A engine and the minimal-safety slice into a NEW folder for
anonymous review. Standard library only: no Git, network or subprocess.

An explicit allowlist copy, not a scrub of the project. ``SPEC`` pins the exact name of every
exported file. Each allowlisted folder is read non-recursively; every pinned file must be there
(a missing one refuses the export) and everything else (new modules or configs, caches, run
outputs, unknown subdirectories, research records, workflow files, other packages, this tool
and its test) stays out, and skipped entries of allowlisted folders are listed. Exporting
another file is a deliberate review: pin it here and in the test's hand-written inventory.
Python, JSON and lock files are copied byte for byte. The root README is written from
``templates/anonymous-artifact/README.md`` and three documents carry the edits in ``EDITS``;
an edit refuses unless its anchor occurs exactly once, so a changed source cannot drift.

Everything is checked before anything is written, and any problem refuses the export (exit
2): a destination that exists, lacks a parent folder or lies inside an input folder; a
symlink or special file on an input path; a missing pinned file; a stale edit; a dangling
relative Markdown link; an identity or credential finding. Findings name the file, line and
rule, never the matched text, and every message and summary path is redacted with the same
rules, ``--identifier`` terms included. ``ARTIFACT_MANIFEST.json`` (relative paths, SHA-256
and how each file derives from the development copy; no timestamps, source hashes or absolute
paths) is written last, so a folder without it is incomplete (exit 1).

Passing these checks does not make a repository anonymous: see docs/anonymous-artifact.md.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import posixpath
import re
import stat
import sys
from pathlib import Path
from typing import Iterable, Sequence

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = "ARTIFACT_MANIFEST.json"
MANIFEST_FORMAT = "anonymous-artifact-manifest/1"

OVERVIEW_LINK = "the [overview](../../README.md)"
PROTOCOL_STATUS = (
    "Status, 2 October 2026: draft describing the implemented engine "
    "(`experiments/safety_selection/`). Every CPU test uses engineering fixtures. No endpoint, "
    "selector, held-out analysis, margin or claim is defined or computed here; stage B consumes "
    "these interfaces after development calibration, in a sibling package with its own code "
    "identity that is not part of this package. Parenthesized `public-metadata/…` names refer "
    "to source-only audit records that are not included here. Package overview and status: "
    "[README](../../README.md).")

# Exported documents that differ from the development copies:
# path -> ((edit id, kind, anchor, replacement, reason recorded in the manifest), ...).
# "text" replaces the exact anchor; "line" replaces the whole line starting with the anchor;
# "section" replaces the Markdown section whose heading line starts with the anchor.
EDITS = {
    "experiments/safety_selection/README.md": (
        ("overview-link", "text", "[FOCUS.md](../../research/FOCUS.md)", OVERVIEW_LINK,
         "link to an unexported research-planning note now points to the package overview"),
        ("run-status", "text",
         "Its author has run nothing in this folder on real data or hardware. ", "",
         "dated sentence on what had been run during development removed; it is not this "
         "package's status"),
    ),
    "experiments/minimal_safety/README.md": (
        ("run-note", "text", " The dated run note records any such cases and audit preparation.",
         "", "sentence citing an unexported dated run note removed"),
        ("overview-link", "text", "[FOCUS.md](../../research/FOCUS.md)", OVERVIEW_LINK,
         "link to an unexported research-planning note now points to the package overview"),
        ("protocol-link", "line", "Protocol, deviations and limits: [minimal-safety-pilot.md]",
         "Its protocol is `configs/calibration.json` with the definitions and limits below; the "
         "development protocol record and its deviation log are not part of this package.",
         "link to an unexported development protocol record replaced by a pointer to the "
         "config and this README"),
        ("venue", "text", "value, novelty, a safety benefit or ICML readiness.",
         "value, novelty or a safety benefit.", "planning reference to a publication venue removed"),
        ("run-record", "section", "## Verified first CUDA run", "",
         "dated development run record (engineering measurements, hosting details and a link to "
         "an unexported result note) removed"),
    ),
    "research/experiments/safety-selection-v2-protocol.md": (
        ("status", "line", "Status, 2 October 2026: draft describing the implemented engine",
         PROTOCOL_STATUS, "status paragraph citing internal records, development test runs and "
         "review gates replaced by a neutral status"),
        ("checks-heading", "text", "(CPU fixtures; this revision not yet run by its author)",
         "(CPU fixtures)",
         "dated note on which revision had been run removed from the acceptance-checks heading"),
        ("checks-count", "text",
         "**From the first implementation (110 passed in the lead's run):**",
         "**From the first implementation:**",
         "dated development pass count removed; the checks are listed without one"),
    ),
}

SPEC = {
    # Folder -> the exact names of the files exported from it, read non-recursively. Every
    # pinned file is required (a missing one refuses); anything else there is skipped and
    # listed. Exporting another file is a deliberate review: pin it here and in INVENTORY in
    # tests/test_anonymous_artifact.py.
    "dirs": {
        "experiments/safety_selection": (
            "README.md", "__init__.py", "__main__.py", "assets.py", "attribution.py", "common.py",
            "config.py", "engine.py", "jobs.py", "ledger.py", "loaders.py", "planning.py",
            "prepare.py", "runner.py", "scoring.py", "selector_view.py", "sources.py", "stream.py",
            "textproc.py", "verify.py"),
        "experiments/safety_selection/configs": (
            "study-v2-data-expanded-arc.json", "study-v2-data.json",
            "study-v2-primary-20261002.json", "study-v2-recipe-calibration-cap2048.json",
            "study-v2-recipe-calibration-micro2.json", "study-v2-recipe-calibration-toxicbert.json",
            "study-v2-recipe-calibration.json"),
        "experiments/safety_selection/tests": (
            "conftest.py", "ss_fixtures.py", "test_ss_attribution.py", "test_ss_config_jobs.py",
            "test_ss_engine.py", "test_ss_integration_contracts.py", "test_ss_prepare.py",
            "test_ss_runner.py", "test_ss_selector_view.py", "test_ss_stream.py",
            "test_ss_text.py"),
        "experiments/minimal_safety": (
            "README.md", "__init__.py", "__main__.py", "common.py", "data.py", "ledger.py",
            "model.py", "plan.py", "report.py", "requirements.lock", "run.py", "text.py"),
        "experiments/minimal_safety/configs": ("calibration-cuda.json", "calibration.json"),
        "experiments/minimal_safety/tests": (
            "conftest.py", "test_ms_data.py", "test_ms_model.py", "test_ms_plan.py",
            "test_ms_report.py", "test_ms_run.py", "test_ms_text.py"),
    },
    # Single documents copied to the same path; the stage-A docstring and README cite this one.
    "files": ("research/experiments/safety-selection-v2-protocol.md",),
    # Export path -> template in the source tree, written for this package.
    "templates": {"README.md": "templates/anonymous-artifact/README.md"},
    "edits": EDITS,
}

# Known owner handles, matched in any case anywhere (inside URLs, addresses and paths too).
OWNER_HANDLES = ("spiderishi", "4r4cn1d0")

# (rule, pattern): identity first, then credential formats with a recognizable shape.
# Unprefixed secrets have no recognizable shape; the allowlist is what keeps them out.
RULES = (
    ("owner-identifier", re.compile("|".join(map(re.escape, OWNER_HANDLES)), re.I)),
    ("home-directory-path", re.compile(r"/(?:Users|home)/[^/\s\"'`<>]+"
                                       r"|\b[A-Za-z]:[\\/]+Users[\\/]+[^\\/\s\"'`<>]+")),
    ("email-address", re.compile(r"[\w.%+-]+@[A-Za-z0-9-]+(?:\.[A-Za-z0-9-]+)*\.[A-Za-z]{2,}")),
    ("credential-in-url", re.compile(r"\b[A-Za-z][\w+.-]*://[^\s/:@]+:[^\s/@]+@")),
    ("private-key-block", re.compile(r"-----BEGIN[A-Z0-9 ]*PRIVATE KEY")),
    ("github-token", re.compile(r"\b(?:gh[pousr]_[A-Za-z0-9]{36,}|github_pat_\w{22,})")),
    ("huggingface-token", re.compile(r"\bhf_[A-Za-z0-9]{30,}")),
    ("sk-api-key", re.compile(r"\bsk-[\w-]{32,}")),
    ("aws-access-key-id", re.compile(r"\b(?:AKIA|ASIA)[0-9A-Z]{16}\b")),
    ("google-api-key", re.compile(r"\bAIza[\w-]{35}")),
    ("slack-token", re.compile(r"\bxox[abposr]-[A-Za-z0-9-]{10,}")),
    ("runpod-api-key", re.compile(r"\brpa_[A-Za-z0-9]{20,}")),
)


class ExportError(Exception):
    """Refused before anything was written; ``problems`` lists every reason found."""

    def __init__(self, problems: Sequence[str]):
        super().__init__("\n".join(problems))
        self.problems = list(problems)


class PartialExportError(Exception):
    """Writing failed after the destination was created; that folder is incomplete."""


def rules_for(identifiers: Sequence[str] = ()) -> tuple:
    """The built-in rules, then ``identifier-N`` (any case) for each non-empty extra term."""
    return RULES + tuple((f"identifier-{number}", re.compile(re.escape(term), re.I))
                         for number, term in enumerate(identifiers, start=1) if term)


def redact(text: str, rules=RULES) -> str:
    """``text`` with every rule match replaced by ``<rule>``. All matches are found in the
    original text and overlapping ones merged, so no replacement leaves part of another match
    visible."""
    spans = sorted((match.start(), match.end(), name)
                   for name, pattern in rules for match in pattern.finditer(text))
    parts, end = [], 0
    for start, stop, name in spans:
        if start >= end:
            parts += [text[end:start], f"<{name}>"]
        end = max(end, stop)
    return "".join(parts) + text[end:]


def scan(output: dict[str, bytes], rules=RULES) -> list[str]:
    """``path:line: rule`` for every identity or credential finding, never the matched text."""
    findings = []
    for rel in sorted(output):
        shown = redact(rel, rules)
        text = output[rel].decode("utf-8", "surrogateescape")
        for name, pattern in rules:
            if pattern.search(rel):
                findings.append(f"{shown}: {name} (in the path)")
            lines = sorted({text.count("\n", 0, match.start()) + 1 for match in pattern.finditer(text)})
            findings += [f"{shown}:{line}: {name}" for line in lines]
    return findings


_FENCED = re.compile(r"^ {0,3}(`{3,}|~{3,}).*?^ {0,3}\1", re.M | re.S)
_CODE_SPAN = re.compile(r"`[^`\n]*`")
_INLINE_LINK = re.compile(r"\[[^\]]*\]\(\s*<?([^)\s>]*)")
_REFERENCE = re.compile(r"^ {0,3}\[[^\]\n]+\]:\s*<?([^\s>]+)", re.M)
_SCHEME = re.compile(r"[A-Za-z][\w+.-]*:")


def markdown_links(text: str) -> list[str]:
    """Targets of inline (and image) and reference-style links outside code."""
    text = _CODE_SPAN.sub("", _FENCED.sub("", text))
    return _INLINE_LINK.findall(text) + _REFERENCE.findall(text)


def check_links(output: dict[str, bytes], rules=RULES) -> list[str]:
    """Every relative link in exported Markdown must name an exported file or folder."""
    problems = []
    for rel in sorted(name for name in output if name.endswith(".md")):
        for target in markdown_links(output[rel].decode("utf-8", "surrogateescape")):
            path = target.split("#", 1)[0].split("?", 1)[0]
            if not path or _SCHEME.match(target):
                continue  # same-document anchor or external URL
            resolved = posixpath.normpath(posixpath.join(posixpath.dirname(rel), path))
            inside = not path.startswith("/") and resolved != ".." and not resolved.startswith("../")
            if not (inside and (resolved in output or resolved == "."
                                or any(other.startswith(resolved + "/") for other in output))):
                problems.append(f"{redact(rel, rules)}: dangling link -> {redact(target, rules)}")
    return problems


def _heading_level(line: str) -> int:
    match = re.match(r"(#{1,6})\s", line)
    return len(match.group(1)) if match else 0


def _section_end(lines: list[str], start: int) -> int:
    """Index of the next heading of the same or a higher level outside code fences."""
    level, fenced = _heading_level(lines[start]), False
    for index in range(start + 1, len(lines)):
        if lines[index].lstrip().startswith(("```", "~~~")):
            fenced = not fenced
        elif not fenced and 0 < _heading_level(lines[index]) <= level:
            return index
    return len(lines)


def apply_edits(text: str, edits: Iterable[tuple]) -> tuple[str, list[str]]:
    """``text`` after the edits, and a problem for every anchor not found exactly once."""
    problems = []
    for edit_id, kind, anchor, new, _reason in edits:
        if kind == "text":
            hits = text.count(anchor)
            if hits == 1:
                text = text.replace(anchor, new)
        elif kind in ("line", "section"):
            lines = text.split("\n")
            found = [index for index, line in enumerate(lines) if line.startswith(anchor)]
            hits = len(found)
            if hits == 1 and kind == "section" and not _heading_level(lines[found[0]]):
                problems.append(f"edit {edit_id!r}: anchor is not a Markdown heading")
                continue
            if hits == 1:
                start = found[0]
                end = start + 1 if kind == "line" else _section_end(lines, start)
                lines[start:end] = new.split("\n") if new else []
                text = "\n".join(lines)
        else:
            problems.append(f"edit {edit_id!r}: unknown kind {kind!r}")
            continue
        if hits != 1:
            problems.append(f"edit {edit_id!r}: anchor found {hits} times, expected exactly once")
    return text, problems


def _check_path(source: Path, rel: str, kind: str, problems: list[str]) -> bool:
    """Whether every component of ``rel`` is a real folder and the last a real ``kind``
    ("dir" or "file"), checked without following any symlink."""
    parts = rel.split("/")
    for depth in range(1, len(parts) + 1):
        shown = "/".join(parts[:depth])
        try:
            mode = os.lstat(source.joinpath(*parts[:depth])).st_mode
        except OSError as exc:
            problems.append(f"{shown}: {exc.strerror or 'unreadable'}")
            return False
        want = kind if depth == len(parts) else "dir"
        if stat.S_ISLNK(mode):
            problems.append(f"{shown}: symlink on an input path (never followed)")
            return False
        if not (stat.S_ISDIR(mode) if want == "dir" else stat.S_ISREG(mode)):
            problems.append(f"{shown}: not a {'folder' if want == 'dir' else 'regular file'}")
            return False
    return True


def _read(path: Path) -> bytes:
    """The bytes of a regular file, opened without following a final symlink."""
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    with os.fdopen(fd, "rb") as handle:
        return handle.read()


def collect(source: Path, spec: dict | None = None
            ) -> tuple[dict[str, bytes], dict[str, dict], list[str]]:
    """(export path -> bytes, export path -> manifest entry, skipped entries of allowlisted
    folders); raises ExportError listing every structural problem, missing pinned file and
    stale edit. Messages are not redacted here; ``export`` redacts them."""
    spec = SPEC if spec is None else spec
    problems: list[str] = []
    files: dict[str, bytes] = {}
    entries: dict[str, dict] = {}
    skipped: list[str] = []

    def add(rel: str, path: Path, derivation: str) -> None:
        try:
            data = _read(path)
        except OSError as exc:
            problems.append(f"{rel}: {exc.strerror or 'unreadable'}")
            return
        if rel in files or rel == MANIFEST:
            problems.append(f"{rel}: listed twice or named like the manifest")
        files[rel], entries[rel] = data, {"derivation": derivation}

    for folder, names in sorted(spec["dirs"].items()):
        if not _check_path(source, folder, "dir", problems):
            continue
        try:
            with os.scandir(source / folder) as listing:
                found = sorted(listing, key=lambda item: item.name)
        except OSError as exc:
            problems.append(f"{folder}: {exc.strerror or 'unreadable'}")
            continue
        for entry in found:
            rel = f"{folder}/{entry.name}"
            if entry.is_symlink():
                problems.append(f"{rel}: symlink in an allowlisted folder (never followed)")
            elif entry.is_dir(follow_symlinks=False) and entry.name not in names:
                if rel not in spec["dirs"]:
                    skipped.append(rel + "/")
            elif not entry.is_file(follow_symlinks=False):
                problems.append(f"{rel}: not a regular file")
            elif entry.name in names:
                add(rel, Path(entry.path), "verbatim")
            else:
                skipped.append(rel)
        present = {entry.name for entry in found}
        problems += [f"{folder}/{name}: required file is missing"
                     for name in names if name not in present]
    for rel in spec["files"]:
        if _check_path(source, rel, "file", problems):
            add(rel, source / rel, "verbatim")
    for rel, template in sorted(spec["templates"].items()):
        if _check_path(source, template, "file", problems):
            add(rel, source / template, "written for this package")
    for rel, edits in sorted(spec["edits"].items()):
        if rel not in files:
            problems.append(f"{rel}: edited document is not exported")
            continue
        try:
            text = files[rel].decode("utf-8")
        except UnicodeDecodeError:
            problems.append(f"{rel}: edited document is not UTF-8")
            continue
        text, failed = apply_edits(text, edits)
        problems += [f"{rel}: {problem}" for problem in failed]
        files[rel] = text.encode("utf-8")
        if entries[rel]["derivation"] == "verbatim":
            entries[rel]["derivation"] = "edited"
        entries[rel]["edits"] = [{"id": edit[0], "change": edit[4]} for edit in edits]
    if problems:
        raise ExportError(problems)
    return files, entries, skipped


def check_destination(source: Path, dest: Path, spec: dict) -> list[str]:
    """``dest`` must be new, have an existing parent folder and lie outside every input
    folder (compared after resolving symlinks)."""
    if os.path.lexists(dest):
        return [f"destination exists and is never reused or overwritten: {dest}"]
    parent = dest.absolute().parent
    if not os.path.isdir(parent):
        return [f"destination parent is not an existing folder: {parent}"]
    target = parent.resolve() / dest.name
    inputs = set(spec["dirs"]) | {posixpath.dirname(rel) for rel in spec["files"]}
    inputs |= {posixpath.dirname(rel) for rel in spec["templates"].values()}
    inputs.discard("")
    for rel in sorted(inputs):
        folder = (source / rel).resolve()
        if target == folder or folder in target.parents:
            return [f"destination is inside the input folder {rel}"]
    return []


def manifest_bytes(entries: dict[str, dict]) -> bytes:
    """Canonical JSON with relative paths, SHA-256 and derivations only."""
    document = {
        "format": MANIFEST_FORMAT,
        "derivations": {"verbatim": "byte-identical to the development copy",
                        "edited": "the development copy with the listed documentation edits",
                        "written for this package": "not part of the development code"},
        "files": [{"path": rel, **entries[rel]} for rel in sorted(entries)],
    }
    return (json.dumps(document, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode("utf-8")


def write(dest: Path, output: dict[str, bytes]) -> None:
    """Create ``dest`` and every file exclusively (nothing is ever overwritten), the manifest
    last."""
    try:
        os.mkdir(dest)
    except OSError as exc:
        raise ExportError([f"cannot create the destination: {exc.strerror or exc}"]) from exc
    try:
        for rel in sorted(output, key=lambda name: (name == MANIFEST, name)):
            target = dest.joinpath(*rel.split("/"))
            target.parent.mkdir(parents=True, exist_ok=True)
            with open(target, "xb") as handle:
                handle.write(output[rel])
    except OSError as exc:
        raise PartialExportError(f"writing failed ({exc.strerror or exc}); {dest} is incomplete: "
                                 "delete it and export again into a new folder") from exc


def export(source: str | os.PathLike, dest: str | os.PathLike, spec: dict | None = None,
           identifiers: Sequence[str] = ()) -> dict:
    """Check everything, then write the pinned files and the manifest into the NEW folder
    ``dest``. ``identifiers`` are extra terms refused in any case. Returns a summary; raises
    ExportError (nothing written) or PartialExportError (``dest`` incomplete). Every problem,
    message and summary path is redacted with the built-in rules and ``identifiers``."""
    rules = rules_for(identifiers)
    try:
        return _export(Path(source), Path(dest), SPEC if spec is None else spec, rules)
    except ExportError as exc:
        raise ExportError([redact(problem, rules) for problem in exc.problems]) from None
    except PartialExportError as exc:
        raise PartialExportError(redact(str(exc), rules)) from None


def _export(source: Path, dest: Path, spec: dict, rules: tuple) -> dict:
    if not os.path.isdir(source):
        raise ExportError([f"source is not a folder: {source}"])
    source = source.resolve()
    problems = check_destination(source, dest, spec)
    if problems:
        raise ExportError(problems)
    files, entries, skipped = collect(source, spec)
    for rel, data in files.items():
        entries[rel]["sha256"] = hashlib.sha256(data).hexdigest()
    output = {**files, MANIFEST: manifest_bytes(entries)}
    problems = scan(output, rules) + check_links(output, rules)
    if problems:
        raise ExportError(problems)
    write(dest, output)
    derivations = {rel: entry["derivation"] for rel, entry in entries.items()}
    # Exported paths were scanned clean; the destination and skipped names were not.
    return {"destination": redact(str(dest), rules), "files": len(output),
            "verbatim": sum(value == "verbatim" for value in derivations.values()),
            "edited": sorted(rel for rel, value in derivations.items() if value == "edited"),
            "written": sorted(rel for rel, value in derivations.items()
                              if value not in ("verbatim", "edited")) + [MANIFEST],
            "skipped": [redact(rel, rules) for rel in skipped]}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Export the stage-A and minimal-safety code into "
                                     "a NEW folder for anonymous review (docs/anonymous-artifact.md).")
    parser.add_argument("--dest", required=True, type=Path, help="new folder to create; must not exist")
    parser.add_argument("--source", type=Path, default=ROOT, help="project root (default: this checkout)")
    parser.add_argument("--identifier", action="append", default=[], metavar="TERM",
                        help="extra term that must not appear, any case (repeatable; never printed)")
    args, unknown = parser.parse_known_args(argv)
    if unknown:  # argparse would echo them, and a mistyped option can carry a term
        parser.error(f"{len(unknown)} unrecognized argument(s), not printed")
    rules = rules_for(args.identifier)
    try:
        summary = export(args.source, args.dest, spec=SPEC, identifiers=args.identifier)
    except ExportError as exc:
        print("export refused; nothing was written:", file=sys.stderr)
        for problem in exc.problems:
            print(f"  {problem}", file=sys.stderr)
        return 2
    except PartialExportError as exc:
        print(f"export failed: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:  # unexpected: redacted like every other message
        message = redact(f"{type(exc).__name__}: {exc}", rules)
        print(f"export failed unexpectedly ({message}); if the destination folder now exists it "
              "is incomplete: delete it and export again into a new folder", file=sys.stderr)
        return 1
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
