"""The reading's input document and its sources record (addendum 33 point 5; B16's schema.py is the target).

**Blocks.** plan_a reads blocks A and B, plan_a_block_a_only block A alone (refused when block B is sealed: that
reading is for a stage 1 without block B, REV3 1.3 LW-35), plan_b blocks A, B and C. The plan-A/B code that plan.json
records must be the reading's (A for both plan-A readings, B for plan_b), and every block read must be sealed.

**Cells.** Each (arm, seed) of the sealed design (B16's settings, ``design(reading)``) comes from exactly one source:
a0 and R at the reused seeds (stage1_rules.REUSED_SEEDS) from block A's re-judged units (stage1_rules.REJUDGED_PINS,
by path, COMPLETE.json and job.json SHA-256); every other cell from the block whose table (stage1_rules.block_runs)
holds it: the one complete, pulled ``arm`` (``a0_arm`` for a0) job of that (arm, seed) on a done host of that block,
its unit keyed by the COMPLETE.json SHA-256 plan.json records and checked against the block seal. A cell with no such
job, two such jobs, or a complete arm job of a block that its table does not hold, refuses. Hosts that are not done
must be listed as moved by the seal (their jobs are not inputs); jobs recorded complete (not pulled) are not inputs.
U, its two G3 corners, coherence and L come from the unit's eval/<target> (job.json must name the arm, seed, target
e1 and the dev bank); O from the O-ext folder job-I/oext of the same job (it names the unit's COMPLETE.json SHA-256;
route unit_eval: the stored dev flags are the unit's own eval/e1/guard.jsonl, which the folder names by SHA-256). A
reused cell's O comes from block A's O-only pass (J3) on its regeneration (J2, accepted, same host): route
source_unit must name the pinned unit as its dev-100 source; route generated reads the pass's own dev100/ answers.
LN-12: R's O cell at a reused seed may be absent only when its regeneration was refused (LS-04) or block A's seal
lists the O-only pass as not run; a0's never. theta0's O flags come from block A's O-only pass on theta0 (untuned).

**References** (block B; REV3 5.1, LN-15b): ref_train recipe G and B+Qi as point references "ref-G" and "ref-bqi"
(the kit's round-31 labels); B10's ref_eval units as the adapter-scaling curve "ref-scale" (points 0.9, 0.75, 0.5 on
one seed set; theta0's U and L from theta0's pinned untuned unit) and the prefix point "ref-prefix"; Safe LoRA's two
reference points as "ref-external-safe_lora-default" and "-conditional" (its K = 0 certify point is a certification,
not a reference). B+Qi's own a0 (after a failed certificate) has no field in B16's schema: it refuses.

**Items.** Every vector is ordered by sorted item id: U by the harm prompt ids (with the overlap block, exactly B14's
strata prompt ids, B16-H-O10), O by the dev-100 and PHTest prompt ids, L by the task-row query ids; every cell must
hold the same ids (and one query bank, one O-ext branch).

**B14** (REV4 9.4; addendum 33 point 3; B16-H-O8, O10): the strata and report files are parsed (strict JSON) and
embedded unchanged; each file's bytes must be B14's canonical JSON of its parsed document (so B16's re-hash equals the
file's SHA-256) and equal the sealed SHA-256 the lead passes (--expect-strata-sha256, --expect-report-sha256); the
report must be made on that strata and its units (a0 and each add arm at each seed) must be exactly the units read here
(COMPLETE.json, job.json and guard_samples.jsonl SHA-256).

**Judges** (round 30's judge_files_check, keyed by the units this reading uses): per block read, the seal's judge
record names its judges (each judge either recorded or decided not run); judges/BLOCK/judge-files-index.json is
Gate B's index, sealed at the record's index SHA-256; every indexed file is a top-level judge-named file named for its
judge and unit, present and sealed at its SHA-256, no (judge, unit) twice, no unindexed judge-named file; and every
unit of the block that the reading uses has exactly one file per recorded judge. No judge file is parsed: B16 reads
no judge value.

**Not built** (no source or no defined per-item value; the record says so): the S-G coherent-only variant (a prompt
whose 3 answers all fail the screen has no coherent share; REV3 3.4 gives no per-prompt rule for B16's per-item
table), and the token axis (no job of the kit runs R at 1,200 or 2,400 rows, REV3 9.3 item 2).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from scripts.stage1_s1.reading.schema import INPUT_KIND, b14_sha256, validate
from scripts.stage1_s1.reading.settings import SETTINGS_SHA256, Refusal, design, settings, strict_json
from scripts.stage1_s1.reading_input import items as it
from scripts.stage1_s1.reading_input.sources import (Folder, Kit, is_hex64, pinned_folder, plain, read_bytes,
                                                     sha256_bytes)

RECORD_KIND = "stage1 reading input sources"
READING_BLOCKS = {"plan_a": ("A", "B"), "plan_a_block_a_only": ("A",), "plan_b": ("A", "B", "C")}
READING_CODE = {"plan_a": "A", "plan_a_block_a_only": "A", "plan_b": "B"}
PRIMARY_KINDS = {"a0": "a0_arm"}              # every other design arm is an "arm" job
OEXT_UNIT_KIND = "stage1-oext-unit"           # scripts/stage1_s1/oext_unit.JOB_KIND
B10_KIND = "stage1-eval-adapter"              # scripts/stage1_s1/eval_adapter.JOB_KIND
LS04 = "LS-04"                                # the job runner's refused-regeneration reason
REF_TRAIN = {"G": "ref-G", "bqi": "ref-bqi"}  # the kit's round-31 labels (judge_units_stage1.ref_train_labels)
CURVE = "ref-scale"
CURVE_POINTS = {"scale-0.9": "0.9", "scale-0.75": "0.75", "scale-0.5": "0.5"}
PREFIX = {"prefix": "ref-prefix"}
SAFE_LORA = {"default": "ref-external-safe_lora-default", "conditional": "ref-external-safe_lora-conditional"}
SAFE_LORA_CERTIFY = "certify"
NOT_BUILT = {
    "u_variants.coherent": "not built: a prompt whose sampled answers all fail the coherence screen has no coherent "
                           "share, and B16's per-item table needs one per prompt (REV3 3.4 gives no per-prompt rule); "
                           "the lead rules",
    "token_axis": "not built: no kit job runs R at 1,200 or 2,400 removed rows (REV3 9.3 item 2's dose cells), so "
                  "the dose curve has no source"}
CHECKPOINT = "e1"


@dataclass(frozen=True)
class Overlap:
    strata: Path
    report: Path
    expect_strata_sha256: str
    expect_report_sha256: str


@dataclass
class Source:
    """One cell's folders: the evaluation unit (U, L, coherence) and its O-ext pass with the stored dev records."""
    name: str                                 # arm, or reference name
    seed: int
    block: str                                # the block whose seal holds it ("A" for a re-judged pin)
    unit: Folder
    target: str
    o: dict | None = None                     # items.o_flags result
    harm: dict | None = None
    loss: dict | None = None
    o_folders: tuple = ()


# ----- job scan -----------------------------------------------------------------------------------------------------


def _key(job: dict):
    return job.get("kind"), job.get("arm"), job.get("seed")


def scan(kit: Kit, blocks: tuple) -> dict:
    """Every complete, pulled job of the blocks' done hosts, by kind: {kind: [(block, host, index, job)]}, and the
    jobs recorded complete (not pulled), as labels."""
    out: dict = {"not_pulled": []}
    for block in blocks:
        for host, h in kit.hosts(block):
            for i, job in enumerate(h["jobs"]):
                if not isinstance(job, dict) or job.get("status") != "complete":
                    continue
                if job.get("pulled") is False:
                    out["not_pulled"].append(f"{host} job {i} ({' '.join(str(x) for x in _key(job) if x is not None)})")
                    continue
                out.setdefault(job.get("kind"), []).append((block, host, i, job))
    return out


def engine_arm(job: dict) -> str:
    """The engine's arm id of a kit job (setup/job_runner_stage1.engine_arm): edit-<edit SHA-256>, else a0."""
    edit = job.get("edit")
    if not edit:
        return "a0"
    if not isinstance(edit, dict) or not is_hex64(edit.get("sha256")):
        raise Refusal(f"{job.get('arm')} at {job.get('seed')}: plan.json's edit record names no edit SHA-256")
    return edit.get("engine_arm") or f"edit-{edit['sha256']}"


def _check_job_json(folder: Folder, want: dict, pinned: bool = False) -> dict:
    """job.json against the fields plan.json (or the pin) fixes. A kit folder's COMPLETE.json must name job.json by
    its SHA-256; a pinned folder's job.json is bound by its pin (the Gate A engine's marker may not name it)."""
    job = folder.job(marker=not pinned)
    wrong = sorted(k for k, v in want.items() if job.get(k) != v)
    if wrong:
        raise Refusal(f"{folder.label}: job.json's {', '.join(wrong)} differ from the unit plan.json records")
    return job


def _host_jobs(kit: Kit, host: str) -> list:
    return kit.plan["hosts"][host]["jobs"]


# ----- one folder's items -------------------------------------------------------------------------------------------


def _eval_items(src: Source, bar: dict) -> None:
    prefix = f"eval/{src.target}"
    summary = src.unit.json(f"{prefix}/summary.json")
    src.harm = it.harm(src.unit.file(f"{prefix}/samples.jsonl"), src.unit.file(f"{prefix}/guard_samples.jsonl"),
                       summary, bar, src.unit.label)
    src.loss = it.losses(src.unit.file(f"{prefix}/query_loss.jsonl"), summary, src.unit.label)


def _dev_guard(folder: Folder, rel: str) -> tuple[list, str]:
    data = folder.file(rel)
    return it.dev_records(data, f"{folder.label} {rel}"), sha256_bytes(data)


def _oext_pass(kit: Kit, block: str, host: str, index: int, job: dict, label: str) -> Folder:
    rel = f"job-{index}/oext"
    outputs = job.get("outputs") or {}
    digest = outputs.get(f"{rel}/COMPLETE.json") if isinstance(outputs, dict) else None
    if not is_hex64(digest):
        raise Refusal(f"{label}: plan.json records no O-ext folder {rel} among the job's outputs")
    folder = kit.folder(block, host, rel, digest, f"{label} O-ext kit:{host}/{rel}")
    c = folder.complete
    if c.get("kind") != OEXT_UNIT_KIND or c.get("command") != "run":
        raise Refusal(f"{folder.label}: not an O-ext unit pass (kind {OEXT_UNIT_KIND}, command run)")
    return folder


def _dev_inputs_match(oext: Folder, guard_sha: str) -> None:
    named = (oext.complete.get("dev100_inputs") or {}).get("dev100/guard.jsonl")
    if named != guard_sha:
        raise Refusal(f"{oext.label}: the O-ext pass names other stored dev-100 judge records than the ones read")


def _o_from(oext: Folder, dev: list, where: str) -> dict:
    return it.o_flags(dev, oext.file(it.OEXT_GUARD), oext.json(it.OEXT_SUMMARY), where)


# ----- the primary cells --------------------------------------------------------------------------------------------


def cell_blocks(dsg, code: str, blocks: tuple, rules) -> dict:
    """(arm, seed) -> "reused" or the block whose table holds it; refuses a design cell that no block read holds,
    or a table cell outside the design."""
    reused = {(a, s) for a in ("a0", "R") for s in rules.REUSED_SEEDS}
    want = {(a, s) for a in dsg.arms for s in dsg.seeds[a]}
    out = {c: "reused" for c in want & reused}
    for block in blocks:
        for cell in rules.block_runs(code, block):
            if cell not in want:
                raise Refusal(f"block {block}'s table holds {cell[0]} at {cell[1]}, outside the sealed design")
            if cell in out:
                raise Refusal(f"{cell[0]} at {cell[1]} has two sources ({out[cell]} and block {block})")
            out[cell] = block
    missing = sorted(want - set(out))
    if missing:
        raise Refusal(f"{len(missing)} cell(s) of the sealed design are in no block read ({missing[0][0]} at "
                      f"{missing[0][1]})")
    return out


def pins_by_cell(rules) -> dict:
    """(arm, seed) -> pin for block A's re-judged a0 and R units; ("theta0", None) -> theta0's untuned unit."""
    out = {}
    for pin in rules.REJUDGED_PINS.get("A", ()):
        name = str(pin.get("name", "")).split(" ")[0]
        key = (name, None) if name == "theta0" else (name, pin.get("seed"))
        if name not in ("a0", "R", "theta0") or key in out:
            raise Refusal(f"REJUDGED_PINS['A'] holds an entry that is not one a0, R or theta0 unit ({name})")
        out[key] = pin
    return out


def _primary_jobs(kit: Kit, jobs: dict, cells: dict) -> dict:
    """(arm, seed) -> (block, host, index, job) for every non-reused cell; refuses missing, two or extra jobs."""
    found: dict = {}
    for kind in ("arm", "a0_arm"):
        for block, host, i, job in jobs.get(kind, []):
            if job.get("role") == "bqi_own_a0":
                raise Refusal(f"{host} job {i}: B+Qi's own a0 (a failed certificate) has no field in B16's schema; "
                              "the lead rules")
            cell = (job.get("arm"), job.get("seed"))
            if cells.get(cell) != block or PRIMARY_KINDS.get(cell[0], "arm") != kind:
                raise Refusal(f"{host} job {i}: a complete {kind} job of {cell[0]} at {cell[1]} that block {block}'s "
                              "table does not hold (an extra unit)")
            if cell in found:
                raise Refusal(f"{cell[0]} at {cell[1]}: two complete units ({found[cell][1]} job {found[cell][2]} and "
                              f"{host} job {i})")
            found[cell] = (block, host, i, job)
    missing = sorted(c for c, b in cells.items() if b != "reused" and c not in found)
    if missing:
        raise Refusal(f"{len(missing)} cell(s) have no complete, pulled unit in their block ({missing[0][0]} at "
                      f"{missing[0][1]}, block {cells[missing[0]]})")
    return found


def _kit_cell(kit: Kit, name: str, seed: int, where: tuple, want_arm: str, bar: dict) -> Source:
    block, host, i, job = where
    label = f"{name} {seed}"
    unit = kit.folder(block, host, job.get("unit"), job.get("complete_sha256"), f"{label} kit:{host}/{job.get('unit')}")
    _check_job_json(unit, {"kind": "run-one", "arm": want_arm, "seed": seed, "target_checkpoint": CHECKPOINT,
                           "evaluate_bank": "dev", "split": "dev"})
    src = Source(name, seed, block, unit, CHECKPOINT)
    _eval_items(src, bar)
    oext = _oext_pass(kit, block, host, i, job, label)
    c = oext.complete
    if c.get("state") != "run" or c.get("dev100_route") != "unit_eval" or \
            (c.get("unit") or {}).get("complete_sha256") != unit.complete_sha256:
        raise Refusal(f"{oext.label}: the O-ext pass is not route unit_eval on {label}'s unit")
    dev, guard_sha = _dev_guard(unit, f"eval/{CHECKPOINT}/guard.jsonl")
    _dev_inputs_match(oext, guard_sha)
    src.o = _o_from(oext, dev, oext.label)
    src.o_folders = (oext,)
    return src


def _reused_cell(kit: Kit, repo: Path, arm: str, seed: int, pin: dict, o_jobs: dict, regen: dict, seal_a,
                 bar: dict) -> Source:
    unit = pinned_folder(repo, pin)
    if pin.get("seed") != seed or pin.get("target") != CHECKPOINT:
        raise Refusal(f"{unit.label}: the pin is not {arm} at {seed}, checkpoint {CHECKPOINT}")
    _check_job_json(unit, {"arm": pin.get("arm"), "seed": seed, "target_checkpoint": CHECKPOINT}, pinned=True)
    src = Source(arm, seed, "A", unit, CHECKPOINT)
    _eval_items(src, bar)
    where = o_jobs.get((arm, seed))
    if where is None:
        decided = {e.get("job") for e in seal_a.doc.get("not_run") or [] if isinstance(e, dict)}
        refused = any(j.get("reason") == LS04 for _, _, _, j in regen.get((arm, seed), []))
        if arm == "R" and (f"o_only R {seed}" in decided or refused):
            return src                          # LN-12: R's O endpoint may hold a subset of its seeds
        raise Refusal(f"{arm} at {seed}: no complete O-only pass in block A (its O cell has no source)")
    block, host, i, job = where
    src_index = job.get("regen_source")
    jobs = _host_jobs(kit, host)
    if not (isinstance(src_index, int) and not isinstance(src_index, bool) and 0 <= src_index < i):
        raise Refusal(f"{host} job {i}: the O-only pass names no regeneration earlier on its host")
    rj = jobs[src_index]
    if (rj.get("kind"), rj.get("arm"), rj.get("seed"), rj.get("status")) != ("regenerate", arm, seed, "complete") \
            or rj.get("reason") == LS04 or not is_hex64(rj.get("complete_sha256")):
        raise Refusal(f"{host} job {i}: its regeneration is not an accepted, complete {arm} at {seed}")
    oext = _oext_pass(kit, block, host, i, job, f"{arm} {seed}")
    c = oext.complete
    if c.get("state") != "run" or (c.get("unit") or {}).get("complete_sha256") != rj["complete_sha256"]:
        raise Refusal(f"{oext.label}: the O-only pass is not on its regeneration's unit")
    route = c.get("dev100_route")
    if route == "source_unit":
        if (c.get("dev100_source") or {}).get("complete_sha256") != unit.complete_sha256:
            raise Refusal(f"{oext.label}: its dev-100 source is not the pinned {arm} {seed} unit")
        dev, guard_sha = _dev_guard(unit, f"eval/{CHECKPOINT}/guard.jsonl")
    elif route == "generated":
        dev, guard_sha = _dev_guard(oext, "dev100/guard.jsonl")
    else:
        raise Refusal(f"{oext.label}: a regenerated unit's O-only pass has route {route!r}")
    _dev_inputs_match(oext, guard_sha)
    src.o = _o_from(oext, dev, oext.label)
    src.o_folders = (oext,)
    return src


def _theta0(kit: Kit, o_jobs: dict) -> tuple[dict, Folder]:
    where = o_jobs.get(("theta0", None))
    if where is None:
        raise Refusal("theta0: no complete O-only pass in block A (the O endpoint's theta0 has no source)")
    block, host, i, job = where
    oext = _oext_pass(kit, block, host, i, job, "theta0")
    c = oext.complete
    if c.get("state") != "untuned" or c.get("unit") is not None or c.get("dev100_route") != "generated":
        raise Refusal(f"{oext.label}: theta0's O-only pass is not the untuned state with generated dev answers")
    dev, guard_sha = _dev_guard(oext, "dev100/guard.jsonl")
    _dev_inputs_match(oext, guard_sha)
    return _o_from(oext, dev, oext.label), oext


def _o_only_jobs(jobs: dict, cells: dict) -> dict:
    out: dict = {}
    for block, host, i, job in jobs.get("o_only", []):
        arm, seed = job.get("arm"), job.get("seed")
        key = ("theta0", None) if arm == "theta0" else (arm, seed)
        if block != "A" or (key != ("theta0", None) and cells.get(key) != "reused"):
            raise Refusal(f"{host} job {i}: an O-only pass of {arm} at {seed} that no cell reads (an extra unit)")
        if key in out:
            raise Refusal(f"{arm} at {seed}: two complete O-only passes")
        out[key] = (block, host, i, job)
    return out


# ----- references ---------------------------------------------------------------------------------------------------


def _b10_unit(kit: Kit, block: str, host: str, job: dict, rel: str, digest: str, label_want: str, bar: dict,
              name: str) -> Source:
    seed = job.get("seed")
    unit = kit.folder(block, host, rel, digest, f"{name} {seed} kit:{host}/{rel}")
    c = unit.complete
    want = {"kind": B10_KIND, "checkpoint": CHECKPOINT, "evaluate_bank": "dev", "seed": seed}
    if label_want.startswith("scale-"):
        want.update(mode="scale", adapter_scale=float(label_want[len("scale-"):]))
    elif label_want == "prefix":
        want.update(mode="prefix")
    else:
        want.update(mode="external")
    job_doc = _check_job_json(unit, want)
    if label_want in SAFE_LORA and (job_doc.get("external") or {}).get("name") != "safe_lora":
        raise Refusal(f"{unit.label}: not B11's Safe LoRA transform")
    if c.get("kind") != B10_KIND or c.get("seed") != seed or c.get("mode") != want["mode"]:
        raise Refusal(f"{unit.label}: COMPLETE.json is not a B10 evaluation of this point and seed")
    src = Source(name, seed, block, unit, CHECKPOINT)
    _eval_items(src, bar)
    dev, _ = _dev_guard(unit, f"eval/{CHECKPOINT}/guard.jsonl")
    src.o = it.o_flags(dev, unit.file(f"eval/{CHECKPOINT}/{it.OEXT_GUARD}"),
                       unit.json(f"eval/{CHECKPOINT}/{it.OEXT_SUMMARY}"), unit.label)
    return src


def references(kit: Kit, jobs: dict, bar: dict) -> tuple[dict, dict, list]:
    """({name: {seed: Source}} of the point references, {lambda: {seed: Source}} of the curve's points, the B10
    units that are not references: Safe LoRA's certify point)."""
    points: dict = {}
    curve: dict = {}
    skipped = []

    seen = set()

    def claim(name, seed, where):                 # before any folder of the unit is opened
        if (name, seed) in seen:
            raise Refusal(f"{where}: two units of {name} at {seed}")
        seen.add((name, seed))

    def put(table, name, seed, src):
        table.setdefault(name, {})[seed] = src

    for block, host, i, job in jobs.get("ref_train", []):
        recipe, seed = job.get("recipe"), job.get("seed")
        if recipe not in REF_TRAIN or job.get("arm") != recipe:
            raise Refusal(f"{host} job {i}: a reference training arm that is not recipe G or bqi")
        claim(REF_TRAIN[recipe], seed, f"{host} job {i}")
        src = _kit_cell(kit, REF_TRAIN[recipe], seed, (block, host, i, job), "a0", bar)
        put(points, REF_TRAIN[recipe], seed, src)
    for kind in ("ref_eval", "safe_lora"):
        for block, host, i, job in jobs.get(kind, []):
            seed, pts, units = job.get("seed"), job.get("points"), job.get("units")
            if not isinstance(pts, list) or not isinstance(units, list) or len(units) != len(pts):
                raise Refusal(f"{host} job {i}: plan.json holds no unit for each evaluation point")
            labels = {}
            for u in units:
                rel = plain(u.get("unit") if isinstance(u, dict) else None, f"{host} job {i}'s unit")
                if kind == "ref_eval":
                    base, _, label = rel.rpartition("/")
                    ok = base == f"job-{i}/evals" and label.startswith(f"{seed}-")
                    label = label[len(f"{seed}-"):]
                else:
                    ok = rel.startswith(f"job-{i}/eval-") and rel.count("/") == 1
                    label = rel[len(f"job-{i}/eval-"):]
                if not ok or label in labels:
                    raise Refusal(f"{host} job {i}: the unit folder {rel[:60]} is not one point's B10 folder")
                labels[label] = u
            wanted = {p.replace(":", "-") for p in pts}
            if set(labels) != wanted:
                raise Refusal(f"{host} job {i}: its units are not exactly its points")
            for label, u in sorted(labels.items()):
                where = f"{host} job {i}"
                if kind == "ref_eval" and label in CURVE_POINTS:
                    claim(f"{CURVE} {CURVE_POINTS[label]}", seed, where)
                    src = _b10_unit(kit, block, host, job, u["unit"], u.get("complete_sha256"), label, bar, CURVE)
                    put(curve, CURVE_POINTS[label], seed, src)
                elif kind == "ref_eval" and label in PREFIX:
                    claim(PREFIX[label], seed, where)
                    src = _b10_unit(kit, block, host, job, u["unit"], u.get("complete_sha256"), label, bar,
                                    PREFIX[label])
                    put(points, PREFIX[label], seed, src)
                elif kind == "safe_lora" and label in SAFE_LORA:
                    claim(SAFE_LORA[label], seed, where)
                    src = _b10_unit(kit, block, host, job, u["unit"], u.get("complete_sha256"), label, bar,
                                    SAFE_LORA[label])
                    put(points, SAFE_LORA[label], seed, src)
                elif kind == "safe_lora" and label == SAFE_LORA_CERTIFY:
                    skipped.append(f"{host} job {i} {label}")
                else:
                    raise Refusal(f"{host} job {i}: the point {label} is not a reference this reading knows")
    if curve and (set(curve) != set(CURVE_POINTS.values()) or len({tuple(sorted(s)) for s in curve.values()}) != 1):
        raise Refusal(f"the adapter-scaling curve needs the points {sorted(CURVE_POINTS.values())} on one seed set")
    return points, curve, skipped


# ----- B14 ----------------------------------------------------------------------------------------------------------


def overlap_block(ov: Overlap, u_ids: list, primary: dict) -> dict:
    docs = {}
    for what, path, expect in (("strata", ov.strata, ov.expect_strata_sha256),
                               ("report", ov.report, ov.expect_report_sha256)):
        if not is_hex64(expect):
            raise Refusal(f"--expect-{what}-sha256 is not a lowercase hex SHA-256")
        data = read_bytes(Path(path), f"B14's {what} file")
        digest = sha256_bytes(data)
        if digest != expect:
            raise Refusal(f"B14's {what} file hashes to {digest[:16]}, the sealed value is {expect[:16]}")
        doc = strict_json(data)
        if b14_sha256(doc) != digest:
            raise Refusal(f"B14's {what} file is not B14's canonical JSON of its document (B16 would re-hash it to "
                          "another SHA-256)")
        docs[what] = (doc, digest)
    (strata, s_sha), (report, r_sha) = docs["strata"], docs["report"]
    if not isinstance(report, dict) or report.get("strata_sha256") != s_sha:
        raise Refusal("B14's report was not made on this strata record")
    if not isinstance(strata, dict) or strata.get("prompt_ids") != u_ids:
        raise Refusal("the U items' prompt ids are not B14's strata prompt ids in order (B16-H-O10)")
    units = report.get("units")
    seeds = report.get("seeds")
    names = ["a0", *sorted((report.get("add_sets") or {}))] if isinstance(report.get("add_sets"), dict) else None
    if not isinstance(units, dict) or names is None or sorted(units) != sorted(names) or not isinstance(seeds, list):
        raise Refusal("B14's report names no units for a0 and each of its add sets")
    for name in names:
        per = units[name]
        if not isinstance(per, dict) or sorted(per) != sorted(str(j) for j in seeds):
            raise Refusal(f"B14's report: arm {name} does not name a unit at each of its seeds")
        for j in seeds:
            src = primary.get((name, j))
            rec = per[str(j)]
            if src is None or not isinstance(rec, dict) or rec.get("complete_sha256") != src.unit.complete_sha256 or \
                    rec.get("job_sha256") != src.unit.read.get("job.json") or \
                    rec.get("guard_samples_jsonl_sha256") != src.unit.read.get(f"eval/{src.target}/guard_samples.jsonl"):
                raise Refusal(f"B14's report: the unit of {name} at {j} is not the unit read here (COMPLETE.json, "
                              "job.json or guard_samples.jsonl SHA-256)")
    return {"strata_sha256": s_sha, "report_sha256": r_sha, "strata": strata, "report": report}


# ----- judges -------------------------------------------------------------------------------------------------------


def judge_check(kit: Kit, block: str, units: dict, rules) -> dict:
    """Round 30's judge_files_check on judges/BLOCK/, keyed by the reading's units of the block (module doc)."""
    seal = kit.seal(block)
    rec = seal.doc.get("judge_record")
    not_run = {e.get("judge") for e in seal.doc.get("judge_not_run") or [] if isinstance(e, dict)}
    judges = sorted(rec.get("judges") or []) if isinstance(rec, dict) else []
    if not set(judges) <= set(rules.JUDGES) or set(rules.JUDGES) - set(judges) - not_run:
        raise Refusal(f"block {block}'s seal does not name a judge record or a not-run decision for every judge")
    if not judges:
        return {"judges": [], "units": len(units), "files": 0, "index_sha256": None}
    host, name = f"judges/{block}", rules.JUDGE_INDEX
    folder = kit.root / "judges" / block
    data = read_bytes(folder / name, f"judges/{block}/{name}")
    digest = sha256_bytes(data)
    if digest != rec.get("index_sha256") or seal.files.get((host, name)) != digest:
        raise Refusal(f"judges/{block}/{name} is not the index the seal and its judge record name")
    doc = strict_json(data)
    entries = doc.get("files") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("kind") != rules.JUDGE_INDEX_KIND or \
            doc.get("version") != rules.JUDGE_INDEX_VERSION or not isinstance(entries, list):
        raise Refusal(f"judges/{block}/{name} is not Gate B's judge files index")
    pattern = re.compile(rules.JUDGE_FILE_PATTERN)
    key_of = {v: k for k, v in rules.JUDGE_NAMES.items()}
    count: dict = {}
    listed = set()
    for e in entries:
        if not isinstance(e, dict) or set(e) != set(rules.JUDGE_INDEX_ENTRY_KEYS):
            raise Refusal(f"judges/{block}/{name}: an entry does not hold exactly Gate B's index keys")
        fname, key, unit = e["file"], key_of.get(e["judge"]), e["complete_sha256"]
        if not (isinstance(fname, str) and "/" not in fname and pattern.match(fname) and key is not None
                and fname.startswith(f"{key}--") and is_hex64(unit) and fname.endswith(f"--{unit[:12]}.json")):
            raise Refusal(f"judges/{block}/{name}: an entry is not a judge file named for its judge and unit")
        if fname in listed:
            raise Refusal(f"judges/{block}/{name} lists a file twice")
        listed.add(fname)
        p = folder / fname
        if p.is_symlink() or not p.is_file() or sha256_bytes(p.read_bytes()) != e["sha256"] or \
                seal.files.get((host, fname)) != e["sha256"]:
            raise Refusal(f"judges/{block}/{fname[:60]} is missing, differs from its indexed SHA-256 or is not sealed")
        count[(key, unit)] = count.get((key, unit), 0) + 1
    unlisted = [p.name for p in folder.iterdir() if p.is_file() and pattern.match(p.name) and p.name not in listed]
    if unlisted:
        raise Refusal(f"judges/{block}: {len(unlisted)} judge-named file(s) not in its index")
    if any(n > 1 for n in count.values()):
        raise Refusal(f"judges/{block}/{name}: two files of one judge for one unit")
    for key in judges:
        missing = [label for unit, label in sorted(units.items()) if (key, unit) not in count]
        if missing:
            raise Refusal(f"block {block}: {len(missing)} unit(s) the reading uses have no {key} judge file "
                          f"({missing[0]})")
    return {"judges": judges, "units": len(units), "files": len(entries), "index_sha256": digest}


# ----- assembly -----------------------------------------------------------------------------------------------------


def _same(values: list, what: str):
    first = values[0]
    if any(v != first for v in values[1:]):
        raise Refusal(f"the cells do not hold one {what}")
    return first


def build(reading: str, kit_root: Path, repo: Path, rules, rules_sha256: str, overlap: Overlap | None) -> tuple:
    """(the B16 input document, the sources record): every check above, then B16's own schema check."""
    cfg = settings()
    dsg = design(reading)
    kit = Kit(kit_root)
    if kit.plan_code() != READING_CODE[reading]:
        raise Refusal(f"plan.json records plan {kit.plan_code()}; the reading {reading} is plan {READING_CODE[reading]}'s")
    if kit.plan["records"].get("oext_fallback"):
        raise Refusal("O-ext fallback (c) is recorded: the O endpoint has no 500-prompt source")
    blocks = READING_BLOCKS[reading]
    if reading == "plan_a_block_a_only" and "B" in (kit.plan.get("seals") or {}):
        raise Refusal("block B is sealed: the block-A-only reading is for a stage 1 without block B (LW-35)")
    for block in blocks:
        kit.seal(block)
    bar = it.bars(read_bytes(Path(repo) / it.BARS_PATH, "the coherence bars file"))
    cells = cell_blocks(dsg, kit.plan_code(), blocks, rules)
    pins = pins_by_cell(rules)
    jobs = scan(kit, blocks)
    found = _primary_jobs(kit, jobs, cells)
    o_jobs = _o_only_jobs(jobs, cells)
    regen: dict = {}
    for block, host, i, job in jobs.get("regenerate", []):
        regen.setdefault((job.get("arm"), job.get("seed")), []).append((block, host, i, job))
    primary: dict = {}
    for (arm, seed), block in sorted(cells.items()):
        if block == "reused":
            pin = pins.get((arm, seed))
            if pin is None:
                raise Refusal(f"{arm} at {seed} is a reused cell with no pin in REJUDGED_PINS['A']")
            primary[(arm, seed)] = _reused_cell(kit, repo, arm, seed, pin, o_jobs, regen, kit.seal("A"), bar)
        else:
            want = "a0" if arm == "a0" else engine_arm(found[(arm, seed)][3])
            primary[(arm, seed)] = _kit_cell(kit, arm, seed, found[(arm, seed)], want, bar)
    theta0_o, theta0_folder = _theta0(kit, o_jobs)
    points, curve, skipped = references(kit, jobs, bar) if "B" in blocks else ({}, {}, [])
    theta0_unit = None
    if curve:
        pin = pins.get(("theta0", None))
        if pin is None:
            raise Refusal("the curve needs theta0's U and L, and REJUDGED_PINS['A'] holds no theta0 unit")
        theta0_unit = Source("theta0", 0, "A", pinned_folder(repo, pin), str(pin.get("target")))
        _check_job_json(theta0_unit.unit, {"arm": pin.get("arm"), "seed": pin.get("seed"),
                                           "target_checkpoint": pin.get("target")}, pinned=True)
        _eval_items(theta0_unit, bar)
    every = [*primary.values(), *(s for t in points.values() for s in t.values()),
             *(s for t in curve.values() for s in t.values())]
    u_ids = _same([s.harm["ids"] for s in every + ([theta0_unit] if theta0_unit else [])], "set of harm prompt ids")
    l_ids = _same([s.loss["ids"] for s in every + ([theta0_unit] if theta0_unit else [])], "set of task-row ids")
    _same([s.loss["bank"] for s in every + ([theta0_unit] if theta0_unit else [])], "query bank")
    with_o = [s for s in every if s.o is not None]
    o_ids = _same([s.o["ids"] for s in with_o] + [theta0_o["ids"]], "set of O-bank prompt ids")
    _same([s.o["branch"] for s in with_o] + [theta0_o["branch"]], "O-ext branch")
    counts = {e: int(cfg["endpoints"][e]["items"]) for e in ("U", "O", "L")}
    for e, ids in (("U", u_ids), ("O", o_ids), ("L", l_ids)):
        if len(ids) != counts[e]:
            raise Refusal(f"the {e} items number {len(ids)}, B16's schema needs {counts[e]}")

    def vec(src: Source, endpoint: str) -> list:
        if endpoint == "U":
            return [src.harm["U"][p] for p in u_ids]
        if endpoint == "O":
            return [src.o["O"][p] for p in o_ids]
        return [src.loss["L"][q] for q in l_ids]

    def table(endpoint: str, table_of=None) -> dict:
        out: dict = {}
        for (arm, seed), src in sorted(primary.items()):
            if endpoint == "O" and src.o is None:
                continue
            out.setdefault(arm, {})[str(seed)] = (table_of(src) if table_of else vec(src, endpoint))
        return out

    doc = {"kind": INPUT_KIND, "version": 1, "reading": reading,
           "endpoints": {"U": {"cells": table("U")}, "O": {"cells": table("O"), "theta0": [theta0_o["O"][p] for p in o_ids]},
                         "L": {"cells": table("L")}},
           "coherence": {arm: {str(seed): dict(src.harm["coherence"]) for (a, seed), src in sorted(primary.items())
                               if a == arm} for arm in dsg.arms},
           "u_variants": {v: table("U", lambda s, v=v: [s.harm[v][p] for p in u_ids])
                          for v in ("g3_unscored_unsafe", "g3_controversial_unsafe")}}
    refs = []
    for name, per in sorted(points.items()):
        refs.append({"name": name, "kind": "point",
                     "cells": {e: {str(j): vec(s, e) for j, s in sorted(per.items())} for e in ("U", "O", "L")}})
    if curve:
        refs.append({"name": CURVE, "kind": "curve",
                     "points": {lam: {e: {str(j): vec(s, e) for j, s in sorted(per.items())} for e in ("U", "O", "L")}
                                for lam, per in sorted(curve.items())},
                     "theta0": {"U": vec(theta0_unit, "U"), "L": vec(theta0_unit, "L")}})
    if refs:
        doc["references"] = refs
    if overlap is not None:
        doc["overlap"] = overlap_block(overlap, u_ids, primary)
    judged: dict = {}
    for src in every + ([theta0_unit] if theta0_unit else []):
        judged.setdefault(src.block, {})[src.unit.complete_sha256] = f"{src.name} {src.seed if src.seed else ''}".strip()
    judges = {block: judge_check(kit, block, judged.get(block, {}), rules) for block in blocks}
    try:
        validate(doc)                             # B16's own schema: anything it would refuse is refused here
    except Refusal as exc:                        # B16's message may hold a value: only its place is printed
        raise Refusal(f"B16's schema refuses the built document at {str(exc).split(': ')[0][:120]}") from None
    record = _record(reading, kit, rules_sha256, blocks, primary, points, curve, theta0_folder, theta0_unit, judges,
                     doc, jobs, skipped)
    return doc, record


def _record(reading, kit, rules_sha256, blocks, primary, points, curve, theta0_folder, theta0_unit, judges, doc,
            jobs, skipped) -> dict:
    def src_rec(s: Source) -> dict:
        return {"unit": s.unit.record(), "o": [f.record() for f in s.o_folders]}

    import scripts.stage1_s1.reading_input as pkg
    here = Path(pkg.__file__).resolve().parent
    modules = {p.name: sha256_bytes(p.read_bytes()) for p in sorted(here.glob("*.py"))}
    return {"kind": RECORD_KIND, "version": 1, "reading": reading,
            "builder": {"modules": modules, "rules_sha256": rules_sha256, "b16_settings_sha256": SETTINGS_SHA256},
            "kit": {"plan_sha256": kit.plan_sha256, "plan_code": kit.plan_code(),
                    "seals": {b: kit.seal(b).sha256 for b in blocks}},
            "cells": {f"{a} {j}": src_rec(s) for (a, j), s in sorted(primary.items())},
            "o_cells_absent": sorted(f"{a} {j}" for (a, j), s in primary.items() if s.o is None),
            "theta0": {"o": theta0_folder.record(), "unit": theta0_unit.unit.record() if theta0_unit else None},
            "references": {**{f"{n} {j}": src_rec(s) for n, per in sorted(points.items()) for j, s in sorted(per.items())},
                           **{f"{CURVE} {lam} {j}": src_rec(s) for lam, per in sorted(curve.items())
                              for j, s in sorted(per.items())}},
            "not_references": skipped,
            "not_pulled": jobs.get("not_pulled", []),
            "judges": judges,
            "overlap": None if "overlap" not in doc else {"strata_sha256": doc["overlap"]["strata_sha256"],
                                                          "report_sha256": doc["overlap"]["report_sha256"]},
            "not_built": dict(NOT_BUILT),
            "counts": {"U_cells": sum(len(v) for v in doc["endpoints"]["U"]["cells"].values()),
                       "O_cells": sum(len(v) for v in doc["endpoints"]["O"]["cells"].values()),
                       "L_cells": sum(len(v) for v in doc["endpoints"]["L"]["cells"].values()),
                       "references": [r["name"] for r in doc.get("references", [])]}}

