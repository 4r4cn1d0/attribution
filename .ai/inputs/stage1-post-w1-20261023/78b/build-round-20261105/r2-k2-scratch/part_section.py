def block_a_cells(plan: dict) -> tuple[dict, str | None]:
    """K2V-2: (arm, seed) -> (host, the job) of the one complete, pulled job of each run of block A's deal, wherever it
    ran (a deferral or requeue takes a job to another host); a job that is not complete counts only when a move took it
    along (carried, as block_complete reads moved hosts). The problem, or None: a job not complete and not carried, a
    complete job not pulled or without its unit, two complete units for one run, or a run with none."""
    b = plan["blocks"].get("A") or {}
    want = {tuple(r) for pod in b.get("deal") or [] for r in pod}
    moved, cells = moved_hosts(plan), {}
    for name, h in sorted(plan["hosts"].items()):
        if h.get("block") != "A":
            continue
        for i, j in enumerate(h["jobs"]):
            key = (j.get("arm"), j.get("seed"))
            if j.get("status") == "complete":
                if j.get("pulled") is False or not j.get("unit") or not SHA_RE.fullmatch(str(j.get("complete_sha256"))):
                    return {}, f"{name}:{i}: a block-A job is complete but not pulled with its unit"
                if key in cells:
                    return {}, f"{key[0]} at {key[1]}: two complete units ({cells[key][0]}, {name}); the lead decides"
                cells[key] = (name, j)
            elif not (name in moved and carried(plan, name, j)):
                return {}, f"{name}:{i} ({key[0]} at {key[1]}) is not complete"
    if set(cells) != want:
        return {}, f"{len(want - set(cells))} block-A run(s) have no complete unit"
    return cells, None


def blinded_inputs_part(plan: dict, family: str, copy: pathlib.Path | None = None) -> dict:
    """S-9 (GXB second set): this family's entry of blinded_sigma.py's inputs file, from block A's plan.json (in
    ``copy``, this working copy by default) and the kit's pins only (never typed, never a value read): the design
    ("full", or "anchor_stopped" with the stop record's pin, S-6); the engine of each role (R-13): the reused a0 and N's
    R units' as N's noise reading took them (its output at the gate's pin), block A's the packed engine's; the method
    edits by SHA-256 (rules_78b.METHOD_EDITS, equal to the jobs' bound edits); the cells: R 1101-1103 N's (N_UNITS),
    R 1104-1105 and every block-A cell its completed unit wherever it ran (block_a_cells, K2V-2), a0 1101-1103 the side
    units (KIT a0_units) or N's a0-1103 (Llama), a0 1104 block A's. Paths are relative to the repository."""
    copy = copy or HERE
    b = plan["blocks"]["A"]
    stopped = b.get("anchor_stop") is not None
    noise = b["gate"]["noise_reading"]
    doc, _ = output_doc(noise["path"], noise["sha256"], "N's noise reading output", "the gate's noise reading")
    engines = (doc.get("families") or {}).get(family, {}).get("engine") or {}
    found, problem = block_a_cells(plan)
    if problem:
        fail(f"blinded_sigma reads every block-A cell: {problem}")
    block_engines = {plan["hosts"][name]["engine_sha256"] for name, _ in found.values()}
    if set(engines) != {"a0", "R"} or not all(SHA_RE.fullmatch(str(v)) for v in engines.values()) or \
            len(block_engines) != 1:
        fail("blinded_sigma's engines: N's reading names no a0 and R identity, or block A ran on two engines")
    cells: dict = {}
    edits: dict = {}
    for (arm, seed), (name, j) in sorted(found.items()):
        unit = (copy / "retrieved" / name / "tree" / j["unit"]).relative_to(ROOT).as_posix()
        entry = {"path": unit, "complete_sha256": j["complete_sha256"]}
        if j["arm"] == "R":
            entry["arm"] = (j.get("edit") or {}).get("engine_arm") or f"edit-{j['edit']['sha256']}"
        elif j["arm"] != "a0":
            pin = r78.METHOD_EDITS[family][j["arm"]]
            if not pin or (j.get("edit") or {}).get("sha256") != pin["sha256"]:
                fail(f"{name}: {j['arm']}'s bound edit is not METHOD_EDITS' pin")
            edits[j["arm"]] = pin["sha256"]
        cells.setdefault(j["arm"], {})[str(j["seed"])] = entry
    try:
        n_units = {f"{a}-{s}": r78.n_unit_or_refuse(family, a, s) for a, s in r78.block0_runs(family)}
    except r78.Refused as exc:
        fail(str(exc))
    for key, u in n_units.items():
        arm, seed = key.split("-")
        entry = {"path": u["path"], "complete_sha256": u["complete_sha256"]}
        if arm == "R":
            entry["arm"] = f"edit-{u['edit_sha256']}"
        cells.setdefault(arm, {})[seed] = entry
    for seed, u in sorted((s, u) for s, u in r78.KIT[family]["a0_units"].items() if s != "untuned"):
        cells.setdefault("a0", {})[str(seed)] = {"path": u["path"], "complete_sha256": u["complete_sha256"]}
    entry = {"design": "anchor_stopped" if stopped else "full",
             "engine": {"a0": engines["a0"], "R": engines["R"], "block_a": block_engines.pop()},
             "edits": dict(sorted(edits.items())), "cells": {a: dict(sorted(v.items())) for a, v in sorted(cells.items())}}
    if stopped:
        entry["anchor_stop"] = {"path": b["anchor_stop"]["path"], "sha256": b["anchor_stop"]["sha256"]}
    return {"kind": BLINDED_PART_KIND, "version": 1, "family": family, "option": b["gate"]["option"],
            "gate_sha256": b["gate"]["sha256"], "entry": entry}


def write_blinded_part_command() -> dict:
    """write-blinded-part: block A's part again (when record-done found a pin it waits for, such as N_UNITS)."""
    plan = load()
    if rules.KIT_BLOCK != "A" or not block_a_arms_done(plan):
        fail("write-blinded-part runs in block A's copy once every block-A arm job is complete and pulled")
    return {"blinded_inputs_part": write_blinded_part(plan)}


def block_a_arms_done(plan: dict) -> bool:
    """Every hosts launch of this copy's block A released and every run of its deal complete and pulled wherever it
    ran (block_a_cells; K2V-2; the judge launches may still be open): blinded_sigma reads every block-A cell."""
    b = plan["blocks"].get("A")
    if not b or b.get("pending"):
        return False
    released_hosts = {n for x in b["launches"][:b["released"]] for n in x.get("hosts", [])}
    planned_hosts = {n for x in b["launches"] for n in x.get("hosts", [])}
    return released_hosts == planned_hosts and block_a_cells(plan)[1] is None


def part_path(family: str) -> pathlib.Path:
    """K2V-3: the one place a family's part lives: its block-A copy's blinded/ folder (KD7)."""
    return ROOT / "tmp" / f"{r78.WORKING_COPY_PREFIX}{family}-A" / BLINDED_PART.format(family=family)


def write_blinded_part(plan: dict) -> dict:
    """S-9: once block A's arm jobs are all complete in this copy, its part of blinded_sigma.py's inputs file is
    written once at part_path (blinded/blinded-sigma-inputs-part__<F>.json); a second record-done finds the same bytes."""
    family = family_or_fail()
    data = rules.canonical_bytes(blinded_inputs_part(plan, family))
    p = HERE / BLINDED_PART.format(family=family)
    if p.exists():
        if p.read_bytes() != data:
            fail(f"{p.relative_to(HERE)} exists with other bytes: the part is written once; the lead decides")
    else:
        p.parent.mkdir(exist_ok=True)
        with open(p, "xb") as handle:
            handle.write(data)
    return {"path": p.relative_to(ROOT).as_posix(), "sha256": hashlib.sha256(data).hexdigest()}


def kit_part(family: str, gate_sha256: str) -> dict:
    """K2V-3: the family's part as the kit wrote it, re-derived: its block-A copy's plan.json (read only) gives the part
    again (blinded_inputs_part), which must equal the file at part_path byte for byte and be of the pinned gate."""
    plan_a, copy = sibling_plan(family, "A")
    if "A" not in (plan_a.get("blocks") or {}):
        fail(f"block A is not planned in tmp/{copy.name}/")
    doc = blinded_inputs_part(plan_a, family, copy)
    p = part_path(family)
    if not p.is_file() or p.read_bytes() != rules.canonical_bytes(doc):
        fail(f"{family}'s blinded_sigma part is missing at its place or is not the one its block-A copy's plan.json "
             "gives (record-done writes it; S-9, K2V-3)")
    if doc["gate_sha256"] != gate_sha256:
        fail(f"{family}'s block A was planned under another gate record than the pinned one")
    return doc


def kit_inputs(gate: dict) -> bytes:
    """K2V-3: blinded_sigma.py's inputs file the kit writes for this gate, rebuilt in memory: every gate family's kit
    part (kit_part), each path rebased to BLINDED_INPUTS's folder."""
    families = {}
    for f in sorted(gate["families"]):
        entry = json.loads(json.dumps(kit_part(f, r78.GATE_78B["sha256"])["entry"]))
        refs = [c for by_seed in entry["cells"].values() for c in by_seed.values()]
        refs += [entry["anchor_stop"]] if "anchor_stop" in entry else []
        for ref in refs:
            ref["path"] = os.path.relpath(ROOT / ref["path"], BLINDED_INPUTS.parent)
        families[f] = entry
    return rules.canonical_bytes({"kind": BLINDED_INPUTS_KIND, "version": 1, "option": gate["option"],
                                  "families": families})


def kit_inputs_check(gate: dict, inputs_sha256: str) -> None:
    """K2V-3: the inputs file at BLINDED_INPUTS is the kit's (kit_inputs, byte for byte) and hashes to ``inputs_sha256``
    (blinded_sigma.py's output's, or the plan record's)."""
    data = BLINDED_INPUTS.read_bytes() if BLINDED_INPUTS.is_file() else None
    if data is None or data != kit_inputs(gate) or hashlib.sha256(data).hexdigest() != inputs_sha256:
        fail("blinded_sigma.py's inputs file is not the one the kit writes from the block-A copies' parts at "
             f"{BLINDED_INPUTS.relative_to(ROOT)} (write-blinded-inputs; S-9, K2V-3)")


def write_blinded_inputs() -> dict:
    """write-blinded-inputs (S-9): blinded_sigma.py's inputs file {kind, version, option, families} (its INPUTS_KIND
    form) at its one place BLINDED_INPUTS, from the parts each gate family's block-A record-done wrote (kit_part:
    re-derived from that copy's plan.json and compared byte for byte), paths rebased. Written once (the same bytes
    again pass). Prints its path and SHA-256 and the number of files it names per family only."""
    gate_data = pin_bytes(r78.GATE_78B, "GATE_78B", r78.GATE_EVENT)
    try:
        gate = r78.gate_record_or_refuse(gate_data)
    except r78.Refused as exc:
        fail(str(exc))
    data = kit_inputs(gate)
    if BLINDED_INPUTS.exists():
        if BLINDED_INPUTS.read_bytes() != data:
            fail(f"{BLINDED_INPUTS.relative_to(ROOT)} exists with other bytes; the lead decides")
    else:
        BLINDED_INPUTS.parent.mkdir(parents=True, exist_ok=True)
        with open(BLINDED_INPUTS, "xb") as handle:
            handle.write(data)
    doc = json.loads(data)
    counts = {f: sum(len(v) for v in e["cells"].values()) + ("anchor_stop" in e) for f, e in doc["families"].items()}
    return {"written": "blinded_sigma_inputs", "path": BLINDED_INPUTS.relative_to(ROOT).as_posix(),
            "sha256": hashlib.sha256(data).hexdigest(), "option": gate["option"], "files_named": counts}


