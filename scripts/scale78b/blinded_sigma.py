"""SR-2's blinded re-check after block A: σ̂_A and its df, and nothing else (7-8B tier; Part 1 §6.4; Part 2 §10.1-§10.2
with DESO3 V2; plan-ab items 8-9; stdlib only; outside the engine identity).

    python3 -I -B scripts/scale78b/blinded_sigma.py --inputs INPUTS.json --inputs-sha256 HEX [--out OUT.json]

**What it prints** (stdout, and --out when given, the same bytes, written once): exactly
{"kind", "version", "inputs_sha256", "sigma_A_pp", "df"} in canonical JSON. No U value, arm mean, seed mean, residual,
per-cell or per-cluster value reaches stdout, stderr, a file or an exception message: a refusal names cells, keys and
hashes only, and any unexpected error is reported by its exception type alone, in ``read`` (in process) and in
``main`` (the CLI), with no exception context kept (SR10).

**The estimate** (P1 §6.4, S-P; P2 §10.2): per family and per cluster (removal {R, A1, L1, H1}; full-corpus {a0, S1, S3,
S4}) the additive arm + seed model is fitted by least squares to the cluster's cells, exactly in rationals; its residual
sum of squares RSS_c and residual df_c = n_c - rank(X_c). σ̂_A = √2 × √(Σ RSS_c / Σ df_c), pooled over the clusters and
the families read (not an average of SDs). A cell with no partner seed in its cluster (R at 1101 and 1105, a0 at 1101)
is fitted exactly by its own seed effect, so it adds no df and no RSS. A cluster with no residual df refuses.

**The cells** per family (the design is declared per family; DESO3 V2):
- ``full``: removal R at 1101-1105 (R_1-R_3 are N's units; R_4, R_5 block A's), A1, L1, H1 at 1102-1104; full-corpus
  a0 at 1101-1104 (1101-1103 the reused side units, or N's Llama a0-1103; 1104 block A's), S1, S3, S4 at 1102-1104:
  6 + 6 = 12 df per family.
- ``anchor_stopped`` (the family's anchor job stopped: A1, L1 and S3 add no cell; P2 §2.2): removal R at 1101-1105 and
  H1 at 1102-1104 (2 df); full-corpus a0 at 1101-1104, S1 and S4 at 1102-1104 (4 df): 6 df.
- The cells given must be the design's, exactly: any other missing or extra cell refuses (GXB S-6: block A is complete
  except A1, L1 and S3 on a family whose anchor job stopped). An ``anchor_stopped`` family names its anchor-stop record
  (GXB O6; text-free JSON) as ``anchor_stop`` {path, sha256}: read by path and its pinned SHA-256, its ``family`` must be
  the family and its ``stop_kind`` and ``exit_code`` one of the frozen anchor script's two stop signals
  (``STOP_KINDS``). A ``full`` family names none.
Under option [B] both families are read (24 df on the full design); under [C] OLMo-2-7B (F1, ruling 5) alone.

**What is read** (refused otherwise): the inputs file by path and its pinned SHA-256 (--inputs-sha256); every cell by
path and its COMPLETE.json SHA-256 key, through ``noise_reading.read_unit`` (scripts/scale78b/noise_reading.py, loaded by
path and pinned by SHA-256 below; nothing copied): a sealed run-one e1 unit of the dev bank at the keyed seed, the
family's manifest, training identity and recipe, the engine identity given for its role (GXB R-13, per role as
noise_reading.py takes them: ``a0`` for the reused a0 units at 1101-1103, ``R`` for N's R units at 1101-1103,
``block_a`` for every other cell, 1104 and 1105 included), the environment and guard records. An R cell's edit is R draw seed - 1100
of the family's manifest (noise_reading's rule). A method cell's edit (arm ``edit-<SHA-256>`` from the family's
``edits`` map) is a "safety-selection edit" of the family's manifest, "remove" for A1, L1 and H1, "add" for S1, S3 and
S4, and not an R draw; for that call read_unit's R-draw check is replaced in-process by this rule (the scorer layer's
pattern; the file is unchanged). One COMPLETE.json SHA-256 is never read twice, across families too; two method arms
never share an edit. U is the frozen Gate B reader's plain U (``gate_b_reading.arm_from_unit``, through
noise_reading's own import of it, with Gate A's frozen amended bars), in pp.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import pathlib
import re
import sys
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
ROOT = HERE.parents[1]

# ===== pins =====
NOISE_READING = (HERE / "noise_reading.py", "94b679ffeee7656c5b8c6e97b2275bb05260b61cac50743f357ef8ce2c40d436")
KIND = "scale-78b blinded sigma"
INPUTS_KIND = "scale-78b blinded sigma inputs"
VERSION = 1
OUTPUT_KEYS = ("df", "inputs_sha256", "kind", "sigma_A_pp", "version")
INPUT_KEYS = {"kind", "version", "option", "families"}
FAMILY_KEYS = {"design", "engine", "edits", "cells", "anchor_stop"}
FAMILY_REQUIRED = {"design", "engine", "edits", "cells"}
# GXB O6: a stop is recorded only from the frozen anchor script's own signal (exit 3: fewer than 64 safe anchors;
# exit 1 with AnchorJobError's "harmful prompt ... does not encode"). The record's field names are this script's
# reading of O6's list (family, stop kind, exit code, JOB-DONE.json SHA-256, ids and counts): report open point.
STOP_KINDS = {"safe_anchors_below_64": 3, "harmful_prompt_does_not_encode": 1}
STOP_RECORD_KIND = "scale-78b anchor stop"
ENGINE_ROLES = ("R", "a0", "block_a")                 # GXB R-13: the reused a0 units, N's R units, block A
OPTIONS = {"B": ("llama31-8b", "olmo2-7b"), "C": ("olmo2-7b",)}       # [C]: F1 = OLMo-2-7B alone (ruling 5)
CLUSTERS = {"removal": ("R", "A1", "L1", "H1"), "full": ("a0", "S1", "S3", "S4")}
METHOD_EDIT_KIND = {"A1": "remove", "L1": "remove", "H1": "remove", "S1": "add", "S3": "add", "S4": "add"}
BLOCK_A_SEEDS = (1102, 1103, 1104)
REUSED_SEEDS = (1101, 1102, 1103)                     # a0 and R at these seeds are N's or the side units (reused)
DESIGN_SEEDS = {"R": (1101, 1102, 1103, 1104, 1105), "a0": (1101, 1102, 1103, 1104)}
DESIGNS = {"full": ("A1", "L1", "H1", "S1", "S3", "S4"), "anchor_stopped": ("H1", "S1", "S4")}
# ===== end of the pins =====


class Refusal(SystemExit):
    """A refusal: its message names cells, keys and hashes only."""


def refuse(message: str):
    raise Refusal(message)


def sha256_file(path: pathlib.Path) -> str:
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


def hex64(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None


def _load_noise_reading():
    path, want = NOISE_READING
    if sha256_file(path) != want:
        refuse("noise_reading.py differs from its pinned SHA-256: blinded_sigma stops")
    spec = importlib.util.spec_from_file_location("noise_reading_for_blinded_sigma", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


NR = _load_noise_reading()
GB, FR = NR.GB, NR.FR
SELF_SHA256 = sha256_file(pathlib.Path(__file__))


# ----- the design -----------------------------------------------------------------------------------------------------


def design_cells(design: str) -> dict:
    """{(arm, seed): cluster} of a family's design (module doc, "The cells")."""
    if design not in DESIGNS:
        refuse(f"a family's design is one of {sorted(DESIGNS)}")
    methods = DESIGNS[design]
    out = {}
    for cluster, arms in CLUSTERS.items():
        for arm in arms:
            if arm in DESIGN_SEEDS:
                seeds = DESIGN_SEEDS[arm]
            elif arm in methods:
                seeds = BLOCK_A_SEEDS
            else:
                continue
            for seed in seeds:
                out[(arm, seed)] = cluster
    return out


def reused(arm: str, seed: int) -> bool:
    return arm in ("a0", "R") and seed in REUSED_SEEDS


def method_edit_matches(doc, family: str, arm: str) -> bool:
    """A method arm's edit file: a safety-selection edit of the family's manifest, of the arm's kind ("remove" for A1,
    L1, H1; "add" for S1, S3, S4), and not an R draw."""
    if not isinstance(doc, dict):
        return False
    selection = (doc.get("provenance") or {}).get("selection") or {}
    return doc.get("kind") == "safety-selection edit" and doc.get("edit_kind") == METHOD_EDIT_KIND[arm] \
        and doc.get("manifest_sha256") == NR.FAMILIES[family]["manifest_sha256"] and selection.get("family") != "R"


# ----- the exact fit -------------------------------------------------------------------------------------------------------


def _dot(a, b) -> Fraction:
    return sum((x * y for x, y in zip(a, b)), Fraction(0))


def cluster_rss_df(values: dict) -> tuple:
    """(RSS, df) of the additive arm + seed least-squares fit to {(arm, seed): value} (exact rationals): the residual
    of y after projection on the span of the seed and arm indicators (Gram-Schmidt in rationals), and df = n - rank."""
    cells = sorted(values)
    arms = sorted({a for a, _ in cells})
    seeds = sorted({s for _, s in cells})
    columns = [[Fraction(int(s == j)) for _, s in cells] for j in seeds]
    columns += [[Fraction(int(a == arm)) for a, _ in cells] for arm in arms[1:]]
    basis = []
    for col in columns:
        v = list(col)
        for q, qq in basis:
            c = _dot(col, q) / qq
            if c:
                v = [x - c * y for x, y in zip(v, q)]
        norm = _dot(v, v)
        if norm:
            basis.append((v, norm))
    y = [Fraction(values[c]) for c in cells]
    r = list(y)
    for q, qq in basis:
        c = _dot(y, q) / qq
        if c:
            r = [x - c * z for x, z in zip(r, q)]
    return _dot(r, r), len(cells) - len(basis)


def pooled_sigma(clusters: dict) -> tuple:
    """σ̂_A and its df from {label: {(arm, seed): value in pp}}: √2 × √(Σ RSS / Σ df). A cluster with no df refuses
    (its label only)."""
    total_rss, total_df = Fraction(0), 0
    for label in sorted(clusters):
        rss, df = cluster_rss_df(clusters[label])
        if df <= 0:
            refuse(f"{label}: the cluster has no residual df (its cells hold no partner seed): blinded_sigma stops")
        total_rss += rss
        total_df += df
    return math.sqrt(2 * float(total_rss / total_df)), total_df


# ----- reading the inputs ---------------------------------------------------------------------------------------------------


def read_method_unit(spec: dict, arm: str, seed: int, family: str, engine: str, where: str, base: pathlib.Path) -> dict:
    """A method cell through noise_reading.read_unit, with its R-draw check replaced by the method-edit rule for this
    call only (restored afterwards). The edit is checked here first, so its refusal names the method rule."""
    folder = (base / spec["path"]).resolve()
    edit = folder / GB.EDIT_FILE
    want = spec["arm"][len("edit-"):]
    if not edit.is_file() or sha256_file(edit) != want:
        refuse(f"{where}: edit.json is missing or is not the arm's edit file")
    doc = GB.read_json(edit, f"{where} edit.json")
    if not method_edit_matches(doc, family, arm):
        refuse(f"{where}: the edit file is not a {METHOD_EDIT_KIND[arm]} edit of the family's manifest for {arm}")
    saved = NR.r_edit_matches
    NR.r_edit_matches = lambda d, f, s: method_edit_matches(d, f, arm)
    try:
        return NR.read_unit(spec, "R", seed, family, engine, where, base)
    finally:
        NR.r_edit_matches = saved


def check_anchor_stop(name: str, ref, base: pathlib.Path) -> None:
    """The family's anchor-stop record (GXB O6), read by path and its pinned SHA-256: a JSON object of kind
    STOP_RECORD_KIND whose family is this family and whose stop kind and exit code are one of STOP_KINDS. Its other
    fields are not read here (ids, counts, the job's JOB-DONE.json SHA-256)."""
    if not isinstance(ref, dict) or set(ref) != {"path", "sha256"} or not isinstance(ref["path"], str) \
            or not hex64(ref["sha256"]):
        refuse(f"{name}: an anchor-stopped family names its anchor-stop record as {{path, sha256}}")
    path = (base / ref["path"]).resolve()
    if not path.is_file() or sha256_file(path) != ref["sha256"]:
        refuse(f"{name}: the anchor-stop record is missing or its SHA-256 is not the pinned one")
    doc = GB.read_json(path, f"{name} anchor-stop record")
    if not isinstance(doc, dict) or doc.get("kind") != STOP_RECORD_KIND:
        refuse(f"{name}: the anchor-stop record is not a {STOP_RECORD_KIND} record")
    if doc.get("family") != name:
        refuse(f"{name}: the anchor-stop record is another family's")
    kind = doc.get("stop_kind")
    if kind not in STOP_KINDS or not GB.is_int(doc.get("exit_code")) or doc["exit_code"] != STOP_KINDS[kind]:
        refuse(f"{name}: the anchor-stop record's stop kind and exit code are not one of the anchor script's stops")


def family_cells(name: str, spec, base: pathlib.Path, seen: dict) -> dict:
    """{(arm, seed): (cluster, unit folder)} of one family, every unit checked (module doc, "What is read")."""
    if name not in NR.FAMILIES or NR.FAMILIES[name].get("parity_only"):
        refuse(f"{name}: not a 7-8B family ({sorted(NR.TIER_FAMILIES)})")
    if not isinstance(spec, dict) or not FAMILY_REQUIRED <= set(spec) <= FAMILY_KEYS:
        refuse(f"{name}: a family entry has {sorted(FAMILY_REQUIRED)} and, on an anchor-stopped family, anchor_stop")
    cells = design_cells(spec["design"])
    engine = spec["engine"]
    if not isinstance(engine, dict) or set(engine) != set(ENGINE_ROLES) or not all(hex64(v) for v in engine.values()):
        refuse(f"{name}: engine gives the a0, R and block_a code identities (64 hex each)")
    methods = DESIGNS[spec["design"]]
    edits = spec["edits"]
    if not isinstance(edits, dict) or set(edits) != set(methods) or not all(hex64(v) for v in edits.values()):
        refuse(f"{name}: edits gives exactly the design's method arms {sorted(methods)} by SHA-256")
    if len(set(edits.values())) != len(edits):
        refuse(f"{name}: two method arms name the same edit file")
    if spec["design"] == "anchor_stopped":
        check_anchor_stop(name, spec.get("anchor_stop"), base)
    elif "anchor_stop" in spec:
        refuse(f"{name}: a full-design family names no anchor-stop record")
    wanted = cells
    given = spec["cells"]
    if not isinstance(given, dict) or not all(isinstance(v, dict) for v in given.values()):
        refuse(f"{name}: cells is {{arm: {{seed: unit}}}}")
    listed = set()
    for arm, by_seed in given.items():
        for seed_text in by_seed:
            if not (isinstance(seed_text, str) and re.fullmatch(r"[1-9][0-9]{3}", seed_text)):
                refuse(f"{name} {arm}: seeds are four-digit decimal keys")
            listed.add((arm, int(seed_text)))
    if listed != set(wanted):
        refuse(f"{name}: the cells given are not the design's cells: {len(listed - set(wanted))} extra, "
               f"{len(set(wanted) - listed)} missing")
    out = {}
    for (arm, seed) in sorted(wanted):
        entry, where = given[arm][str(seed)], f"{name} {arm}@{seed}"
        key = entry.get("complete_sha256") if isinstance(entry, dict) else None
        if key is not None and key in seen:
            refuse(f"{where}: its COMPLETE.json SHA-256 is already read as {seen[key]}")
        role_engine = engine[arm if reused(arm, seed) else "block_a"]
        if arm == "a0":
            unit = NR.read_unit(entry, "a0", seed, name, role_engine, where, base)
        elif arm == "R":
            unit = NR.read_unit(entry, "R", seed, name, role_engine, where, base)
        else:
            keys = {"path", "complete_sha256"}
            if not isinstance(entry, dict) or set(entry) != keys or not isinstance(entry["path"], str):
                refuse(f"{where}: a method cell entry has exactly {sorted(keys)}")
            unit = read_method_unit({**entry, "arm": "edit-" + edits[arm]}, arm, seed, name, role_engine, where, base)
        seen[unit["complete_sha256"]] = where
        out[(arm, seed)] = (wanted[(arm, seed)], unit["folder"], where)
    return out


UNEXPECTED = "blinded_sigma: unexpected error ({}); nothing written"


def read(inputs_path, inputs_sha256: str) -> dict:
    """The output document {kind, version, inputs_sha256, sigma_A_pp, df}. Guarded in process too (SR10): a refusal
    passes as it is (it names cells, keys and hashes only); any other error becomes a Refusal that carries its type and
    the fixed UNEXPECTED text only, raised outside the handler, so it holds no context (no __context__ or __cause__)."""
    failure = None
    try:
        return _read(inputs_path, inputs_sha256)
    except SystemExit:
        raise
    except Exception as exc:                                 # never keep an exception's text: it could hold a value
        failure = type(exc).__name__
    raise Refusal(UNEXPECTED.format(failure))


def _read(inputs_path, inputs_sha256: str) -> dict:
    path = pathlib.Path(inputs_path).resolve()
    if not hex64(inputs_sha256):
        refuse("--inputs-sha256 is 64 lower-case hex digits")
    if not path.is_file() or sha256_file(path) != inputs_sha256:
        refuse("the inputs file is missing or its SHA-256 is not the pinned one")
    digest = inputs_sha256
    raw = GB.read_json(path, "the inputs file")
    unknown = sorted(set(raw) - INPUT_KEYS) if isinstance(raw, dict) else ["<not an object>"]
    if not isinstance(raw, dict) or raw.get("kind") != INPUTS_KIND or raw.get("version") != VERSION or unknown \
            or set(raw) != INPUT_KEYS:
        refuse(f"not a {INPUTS_KIND} file (kind, version 1, option, families; unknown keys: {len(unknown)})")
    option = raw["option"]
    if option not in OPTIONS:
        refuse(f"option is one of {sorted(OPTIONS)}")
    families = raw["families"]
    if not isinstance(families, dict) or tuple(sorted(families)) != OPTIONS[option]:
        refuse(f"option {option} reads exactly the families {list(OPTIONS[option])}")
    bars = GB.read_json(FR.DEFAULT_BARS, "the bars file")
    applied = FR.bars_applied(FR.DEFAULT_BARS, bars)
    if bars.get("name") != GB.BARS_NAME or not applied["frozen"]:
        refuse("the bars file is not Gate A's frozen amended bars")
    base = path.parent
    seen: dict = {}
    units = {name: family_cells(name, families[name], base, seen) for name in sorted(families)}
    clusters: dict = {}
    for name, cells in units.items():                       # every unit is checked before any U is read
        for (arm, seed), (cluster, folder, where) in sorted(cells.items()):
            u = GB.arm_from_unit(folder, bars, where)["U"]["plain"]
            if u is None:
                refuse(f"{where}: the unit has no sampled answer")
            clusters.setdefault(f"{name} {cluster}", {})[(arm, seed)] = 100 * u
    sigma, df = pooled_sigma(clusters)
    return {"kind": KIND, "version": VERSION, "inputs_sha256": digest, "sigma_A_pp": sigma, "df": df}


def render(doc: dict) -> bytes:
    if tuple(sorted(doc)) != OUTPUT_KEYS:
        refuse("the output holds other keys than kind, version, inputs_sha256, sigma_A_pp and df")
    return GB.canonical(doc)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--inputs", required=True)
    ap.add_argument("--inputs-sha256", required=True)
    ap.add_argument("--out")
    args = ap.parse_args(argv)
    failure = None
    try:
        out = pathlib.Path(args.out) if args.out else None
        if out is not None and (out.exists() or out.is_symlink()):
            refuse("--out exists: the output is written once")
        if out is not None and not out.parent.is_dir():
            refuse("--out's folder does not exist: nothing written")
        data = render(read(args.inputs, args.inputs_sha256))
        if out is not None:
            try:
                with open(out, "xb") as handle:              # exclusive create: a file made meanwhile is never overwritten
                    handle.write(data)
            except FileExistsError:
                refuse("--out exists: the output is written once")
    except SystemExit:
        raise
    except Exception as exc:                                 # never echo an exception's text: it could hold a value
        failure = type(exc).__name__
    if failure is not None:
        raise SystemExit(UNEXPECTED.format(failure))         # raised outside the handler: no context is kept
    sys.stdout.write(data.decode("utf-8"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
