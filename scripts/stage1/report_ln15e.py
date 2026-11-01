"""LN-15e's report in its pre-registered fallback form (addendum §27 point 2, §29 point 1, §32 point 5; REV4 §9.3
item 3; decision ledger FO-04 and LN-15e). Mac, $0; standard library and the engine's hash helpers only.

LN-15e's reading (the top-600 Jaccard and Kendall τ of each A1 re-score against the sealed A1 set) can never run.
Pod a-2 ran the re-score (jobs 12-15), but the kit's light pull did not fetch rescore/, so the four units were not
retrieved, and a stopped kit pod is never restarted (§29). This script writes the fallback report instead:

- FO-04's figures, copied exactly as the pinned ``a1_variants.json`` (SHA-256 c1fa6615…) holds them: every figure
  that REV4 §9.3 item 3 (and DRAFT rev3 §9.3 item 3, the same text) quotes from that file. These are the Spearman
  ρ(q, e1) over the per-row scores and their number of rows, the top-600 Jaccards q–e1, A1–q and A1–e1, V1
  (Adam-preconditioned) against A1 (its top-600 Jaccard with A1's set) and the mean identity. The ledger's FO-04 row
  names three of them (ρ, Jaccard q–e1, V1). Each figure names the sections that quote it (lead ruling, 27 Oct).
- the §29 decision record ``unpulled-outputs-a2.json`` (SHA-256 e897885c…). It must name host a-2 and jobs 12-15.
- the fallback's statement and the limit, the SHA-256 of both inputs, the UTC time and this script's SHA-256.

It reads no sealed stage-1 file and takes no unit path. These arguments refuse before any file is read: an
argument that names a kit unit folder or root (rescore, round1, cert, eval, judges, judges-pending, hidden, a
judge-pod folder, a SEED-attributes-aN folder, a COMPLETE.json; any letter case), and a path in a folder that holds
a COMPLETE.json. The report file must not exist: it is created exclusively and never overwritten. The report may not
go into the W1 commitments folder, because ``commitments.py check`` refuses its kind there (the W1 allow-list).
Report only: it changes no arm, no test and no rule.

    python scripts/stage1/report_ln15e.py --out PATH.json [--a1-variants PATH] [--decision PATH]

Exit 0: written; exit 2: refused, nothing written. It prints hashes only.
"""

from __future__ import annotations

import argparse
import datetime as dt
import math
import os
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

RECORD_KIND = "stage1 LN-15e report (fallback)"

A1_VARIANTS_PATH = REPO / ".ai" / "inputs" / "stage1-commitments-20261016" / "a1-variants" / "a1_variants.json"
A1_VARIANTS_SHA256 = "c1fa6615e724bdfdc9230edc40c93b7e9a3c48b84b37451e22bae1e3dc45945e"   # FO-04 (ledger; REV4 §9.3)
A1_VARIANTS_KIND = "stage1 A1 report-only variants"

DECISION_PATH = REPO / ".ai" / "inputs" / "stage1-post-w1-20261023" / "block-a" / "unpulled-outputs-a2.json"
DECISION_SHA256 = "e897885c9b1aa0be016c1bc3879024ef9c599b7b414910874cb844423fea79f0"      # the §29 decision record
DECISION_KIND = "stage1 unpulled outputs decision"
DECISION_HOST = "a-2"
DECISION_JOBS = [12, 13, 14, 15]

W1_FOLDER = REPO / ".ai" / "inputs" / "stage1-commitments-20261016"
TOP_K = 600

# The texts that quote FO-04's figures (the report lists these files under "quoted_in_files").
LEDGER, REV4, DRAFT3, DRAFT1 = "decision ledger, row FO-04", "REV4 §9.3 item 3", "DRAFT rev3 §9.3 item 3", \
    "first draft §9.3 item 2"
QUOTED_IN_FILES = {
    LEDGER: "research/experiments/2026-10-17-stage1-preregistration-rev3/decision-ledger.md",
    REV4: "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md",
    DRAFT3: "research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-DRAFT-rev3.md",
    DRAFT1: "research/experiments/2026-10-17-stage1-preregistration/stage1-preregistration-DRAFT.md"}
RHO = "Spearman ρ(q, e1) over the 4,800 per-row scores 0.771"
V1 = "V1 (Adam-preconditioned) against A1 0.314; V1's overlap with A1's set (0.314)"

# FO-04's figures: (the report's name, the path in a1_variants.json, ((the quoting text, as it quotes it), ...)).
FIGURES = (
    ("spearman_q_e1", ("stability", "spearman_q_e1"),
     ((LEDGER, "Spearman ρ(q, e1) 0.771"), (REV4, RHO), (DRAFT3, RHO),
      (DRAFT1, "the Spearman ρ between the per-row q-only and e1-only bi-anchored cosines (named; no value)"))),
    ("rows", ("rows",), ((REV4, RHO), (DRAFT3, RHO))),
    ("jaccard_top600_q_e1", ("stability", "jaccard_top_q_e1"),
     ((LEDGER, "top-600 Jaccard q–e1 0.434"), (REV4, "top-600 Jaccard q–e1 0.434"),
      (DRAFT3, "top-600 Jaccard q–e1 0.434"),
      (DRAFT1, "the Jaccard overlap of the top-600 sets they would select (named; no value)"))),
    ("jaccard_top600_a1_q", ("stability", "jaccard_top_q_a1"), ((REV4, "A1–q 0.630"), (DRAFT3, "A1–q 0.630"))),
    ("jaccard_top600_a1_e1", ("stability", "jaccard_top_e1_a1"), ((REV4, "A1–e1 0.709"), (DRAFT3, "A1–e1 0.709"))),
    ("v1_adam_against_a1", ("adam_preconditioned_v1", "jaccard_top_with", "a1"),
     ((LEDGER, "V1 (Adam) against A1 0.314"), (REV4, V1), (DRAFT3, V1))),
    ("mean_identity_max_abs_difference", ("stability", "mean_identity_max_abs_difference"),
     ((REV4, "the mean identity exact"), (DRAFT3, "the mean identity exact"))),
)

# Kit unit folders and roots (the runner writes units to round1/, rescore/ and cert/), sealed folders, and the
# rescore unit name SEED-attributes-aN. Compared without letter case (the Mac's file system ignores it).
UNIT_PARTS = frozenset({"rescore", "round1", "cert", "eval", "judges", "judges-pending", "hidden"})
UNIT_NAME = re.compile(r"^(?:[0-9]+-attributes-a[0-9]+|judge-pod.*|complete\.json)$", re.IGNORECASE)
SEPARATORS = re.compile(r"[\\/=]")
UNIT_MARKER = "COMPLETE.json"

NOT_AVAILABLE = ["the top-600 Jaccard of each re-score against the sealed A1 set",
                 "the Kendall τ of each re-score against the sealed A1 set"]


class _Parser(argparse.ArgumentParser):
    def error(self, message: str):                       # an argument error is a refusal (exit 2, nothing written)
        raise s1.Refusal(f"arguments: {message}")


# ----- the path rules (checked before any file is read) ------------------------------------------------------------


def names_a_unit(text: str) -> bool:
    """True when a path part of text is a kit unit folder or root, a sealed folder or a unit marker."""
    return any(part.lower() in UNIT_PARTS or UNIT_NAME.match(part) for part in SEPARATORS.split(text))


def check_path(name: str, given: Path) -> Path:
    """The resolved path; refuses a unit or rescore/ path (as given or resolved), a path in a folder that holds a
    COMPLETE.json, and a name that does not end in .json. Only file metadata is read here, never a file."""
    resolved = given.resolve()
    if names_a_unit(str(given)) or names_a_unit(str(resolved)) or \
            any((folder / UNIT_MARKER).exists() for folder in resolved.parents):
        raise s1.Refusal(f"--{name} names a unit or a rescore/ path; LN-15e's fallback takes none")
    if resolved.suffix != ".json":
        raise s1.Refusal(f"--{name} is not a .json file")
    return resolved


def check_out(out: Path) -> None:
    if out == W1_FOLDER.resolve() or W1_FOLDER.resolve() in out.parents:
        raise s1.Refusal("--out lies in the W1 commitments folder, where commitments.py check refuses this kind")
    if out.exists() or out.is_symlink():
        raise s1.Refusal(f"{s1.rel(out)} exists: a report is never overwritten")
    if not out.parent.is_dir():
        raise s1.Refusal("--out's folder does not exist")


def read_input(path: Path) -> bytes:
    if not path.is_file():
        raise s1.Refusal(f"{s1.rel(path)} is not a file")
    try:
        return path.read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{s1.rel(path)} cannot be read ({type(exc).__name__})") from None


# ----- the inputs --------------------------------------------------------------------------------------------------


def fo04_figures(data: bytes) -> tuple[dict, dict]:
    """(FO-04's figures as the pinned a1_variants.json holds them, its rows and k); refuses another file."""
    digest = sha256_bytes(data)
    if digest != A1_VARIANTS_SHA256:
        raise s1.Refusal(f"a1_variants.json hashes to {digest}; FO-04's pin is {A1_VARIANTS_SHA256}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != A1_VARIANTS_KIND or doc.get("version") != 1:
        raise s1.Refusal("a1_variants.json is not the A1 report-only variants record (version 1)")
    if doc.get("k") != TOP_K:
        raise s1.Refusal(f"a1_variants.json's top sets are not top-{TOP_K}")
    figures = {}
    for name, where, quoted_in in FIGURES:
        value = doc
        for key in where:
            value = value.get(key) if isinstance(value, dict) else None
        if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
            raise s1.Refusal(f"a1_variants.json holds no finite number at {'/'.join(where)}")
        figures[name] = {"value": value, "source": list(where),
                         "quoted_in": [{"text": text, "as": quoted} for text, quoted in quoted_in]}
    return figures, {"rows": doc.get("rows"), "k": doc["k"]}


def decision(data: bytes) -> dict:
    """The §29 decision record; refuses another file, and one that does not name host a-2 and jobs 12-15."""
    digest = sha256_bytes(data)
    if digest != DECISION_SHA256:
        raise s1.Refusal(f"the decision record hashes to {digest}; the §29 pin is {DECISION_SHA256}")
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != DECISION_KIND:
        raise s1.Refusal("the decision record is not a stage-1 unpulled outputs decision")
    jobs = doc.get("jobs")
    if doc.get("host") != DECISION_HOST or jobs != DECISION_JOBS or any(type(j) is not int for j in jobs):
        raise s1.Refusal(f"the decision record does not name host {DECISION_HOST} and jobs 12-15")
    return doc


# ----- the report --------------------------------------------------------------------------------------------------


def build_report(a1_bytes: bytes, decision_bytes: bytes, *, a1_source: str, decision_source: str, utc: str,
                 script_sha256: str) -> bytes:
    """The report's bytes (canonical JSON; nothing is written here)."""
    figures, context = fo04_figures(a1_bytes)
    record = decision(decision_bytes)
    host, jobs = record["host"], record["jobs"]
    statement = (f"LN-15e takes its pre-registered fallback. The re-score ran on pod {host} (jobs "
                 f"{', '.join(str(j) for j in jobs[:-1])} and {jobs[-1]}: the retrains of a0 at seeds 1102 and 1103, "
                 f"and the a1_rescore of each). Its {len(jobs)} units were not retrieved, because of a kit defect: the "
                 "kit's light pull did not include rescore/. A stopped kit pod is never restarted, and nothing is "
                 "re-run. So no top-600 Jaccard and no Kendall τ of a re-score against the sealed A1 set exists. "
                 "FO-04's figures are the stated limit.")
    report = {
        "kind": RECORD_KIND, "version": 1,
        "item": "LN-15e: the report-only re-score of A1's bi-anchored cosine, in its pre-registered fallback form",
        "role": "report only: it changes no arm, no test and no rule",
        "rules": ["addendum §27 point 2 (the reading and its fallback)", "addendum §29 point 1 (the fallback is taken)",
                  "addendum §32 point 5 (this script)", "REV4 §9.3 item 3", "decision ledger rows FO-04 and LN-15e"],
        "fallback": {"taken": True, "statement": statement, "host": host, "jobs": jobs,
                     "units_not_retrieved": len(jobs),
                     "reason": "a kit defect: the kit's light pull (host.py PULL_ITEMS) did not include rescore/; "
                               "a stopped kit pod is never restarted (addendum §29)",
                     "not_available": NOT_AVAILABLE,
                     "limit": "FO-04's figures (fo04_figures) are the stated limit"},
        "fo04_figures": figures,
        "quoted_in_files": QUOTED_IN_FILES,
        "fo04_context": context,
        "decision_record": {k: record.get(k) for k in ("kind", "host", "jobs", "utc", "recorded_by")},
        "inputs": {"a1_variants": {"path": a1_source, "sha256": sha256_bytes(a1_bytes)},
                   "decision_record": {"path": decision_source, "sha256": sha256_bytes(decision_bytes)}},
        "reads": "the two inputs only; no sealed stage-1 file, no unit and no rescore/ path",
        "utc": utc,
        "script": {"path": "scripts/stage1/report_ln15e.py", "sha256": script_sha256},
    }
    return canonical_json(report)


def write_new(out: Path, data: bytes) -> str:
    """Create out exclusively (never over an existing file), write data, read it back; returns its SHA-256."""
    try:
        handle = open(out, "xb")
    except FileExistsError:
        raise s1.Refusal(f"{s1.rel(out)} exists: a report is never overwritten") from None
    except OSError as exc:
        raise s1.Refusal(f"the report cannot be created ({type(exc).__name__})") from None
    try:
        with handle:
            handle.write(data)
            handle.flush()
            os.fsync(handle.fileno())
        digest = sha256_file(out)
        if digest != sha256_bytes(data):
            raise s1.Refusal("the report did not read back as written")
    except BaseException:
        out.unlink(missing_ok=True)                        # only the file this call created
        raise
    return digest


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:] if argv is None else argv)
    parser = _Parser(description=__doc__.split("\n\n")[0], allow_abbrev=False)
    parser.add_argument("--out", type=Path, required=True, help="the report file (.json; must not exist)")
    parser.add_argument("--a1-variants", type=Path, default=A1_VARIANTS_PATH)
    parser.add_argument("--decision", type=Path, default=DECISION_PATH)
    try:
        if any(names_a_unit(arg) for arg in argv):
            raise s1.Refusal("an argument names a unit or a rescore/ path; LN-15e's fallback takes none")
        args = parser.parse_args(argv)
        a1_path = check_path("a1-variants", args.a1_variants)
        decision_path = check_path("decision", args.decision)
        out = check_path("out", args.out)
        check_out(out)
        script = Path(__file__).resolve()
        data = build_report(read_input(a1_path), read_input(decision_path), a1_source=s1.rel(a1_path),
                            decision_source=s1.rel(decision_path),
                            utc=dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
                            script_sha256=sha256_file(script))
        digest = write_new(out, data)
    except s1.Refusal as exc:
        print(f"REFUSED: {exc} (nothing written)", file=sys.stderr)
        return 2
    print(f"wrote {s1.rel(out)}")
    print(f"  {digest}  {out.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
