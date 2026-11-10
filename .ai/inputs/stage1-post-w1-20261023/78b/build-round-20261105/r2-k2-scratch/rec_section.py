

# ----- R2 K2: the record steps (GXB O14 corrected, K-6, R-24, R-30; K-8, R-21, R-33; O6 and the fourth set; S-9) -----


def record_gate_78b(noise_path: str, noise_sha256: str, option: str, balance: str, recorded_by: str, out: str) -> dict:
    """record-gate-78b OUT --sha256 H --option B|C --balance-usd X --recorded-by WHO --out FILE: GATE_78B's record
    (rules_78b.GATE_KEYS) from N's noise-reading output read at its SHA-256: the provisional plan from its seed rule on
    sigma_pool, and under [C] sigma_F_plan from OLMo-2-7B's own sigma_F (P1 §6.2; GXB R-24); the option (ruling 9's
    gate) and the live balance are the lead's at the gate. Nothing else is typed."""
    if option not in r78.GATE_OPTIONS:
        fail(f"--option is B or C (ruling 5), not {option!r}")
    doc, ref = output_doc(noise_path, noise_sha256, "N's noise reading output", "OUT")
    provisional, by_f = noise_plans(doc)
    try:
        amount = float(balance)
    except (TypeError, ValueError):
        fail("--balance-usd is a number")
    record = {"kind": r78.GATE_RECORD_KIND, "version": 1, "option": option, "families": list(r78.GATE_OPTIONS[option]),
              "provisional_plan": provisional, "sigma_F_plan": by_f[r78.GATE_OPTIONS["C"][0]] if option == "C" else None,
              "noise_reading_sha256": ref["sha256"], "balance_usd": amount, "utc": mac.utc(), "recorded_by": recorded_by}
    problem = r78.gate_record_problem(record)
    if problem:
        fail(f"the gate record would not be GATE_78B's form: {problem}")
    written = write_once(out, record)
    return {"recorded": "gate", **written, "option": option, "provisional_plan": provisional,
            "sigma_F_plan": record["sigma_F_plan"]}


def sr2_simulation_reading(option: str, families) -> dict:
    """DES K6's reading of the governing simulation, from its pinned merged output only (never typed): the run on
    the design block A ran (the full design; the reduced one once a family's ANCHOR_STOP is pinned, GXB S-10), of the
    pinned code and settings, for ``option``; its largest familywise rate (recomputed from every row, scenario and
    family; equal to the summary's) against 6%."""
    stopped = sorted(f for f in families if r78.ANCHOR_STOP[f] is not None)
    pins = SR2_SIMULATION_REDUCED if stopped else SR2_SIMULATION
    pin = pins.get(option)
    name = f"SR2_SIMULATION{'_REDUCED' if stopped else ''}[{option!r}]"
    doc = pin_json(pin, name, SR2_SIMULATION_EVENT)
    design = doc.get("design") or {}
    if doc.get("kind") != SR2_SIM_KIND or doc.get("version") != 1 or doc.get("option") != option or \
            doc.get("script_sha256") != SR2_SIM_SCRIPT_SHA256 or doc.get("settings_sha256") != SR2_SIM_SETTINGS_SHA256:
        fail(f"{name} is not the pinned simulation's output for option {option} (its kind, option, code or settings)")
    if design.get("name") != ("reduced" if stopped else "full") or sorted(design.get("stopped") or []) != stopped:
        fail(f"{name} ran on another design than the one block A runs (GXB S-10: stopped {stopped})")
    reps, summary = doc.get("reps"), doc.get("summary") or {}
    counts = []
    for row in doc.get("rows") or []:
        for scenario in (row.get("scenarios") or {}).values():
            for fam in (scenario.get("families") or {}).values():
                counts.append(fam.get("familywise_count"))
    if type(reps) is not int or reps < 1 or not counts or not all(type(c) is int and 0 <= c <= reps for c in counts):
        fail(f"{name} holds no familywise counts and replicate count")
    if str(summary.get("threshold_familywise")) != SR2_THRESHOLD:
        fail(f"{name}'s reading threshold is not DES K6's {SR2_THRESHOLD}")
    top = max(counts)
    above = Fraction(top, reps) > Fraction(SR2_THRESHOLD)
    if (summary.get("max_familywise") or {}).get("familywise_count") != top or summary.get("max_above_threshold") is not above:
        fail(f"{name}'s summary disagrees with its rows (largest familywise count or the threshold flag)")
    return {"path": pin["path"], "sha256": pin["sha256"], "max_familywise_count": top, "reps": reps,
            "above_threshold": above}


def sr2_blinding_reading() -> dict:
    """Ruling 3's trigger (P2 §10.1), from the lead's pinned record of the blinding test's verification only: refuses
    while SR2_BLINDING_RECORD is null; verified True needs blinded_sigma_sha256 to be scripts/scale78b/blinded_sigma.py's
    bytes now (the verified script is the one that runs)."""
    doc = pin_json(SR2_BLINDING_RECORD, "SR2_BLINDING_RECORD", SR2_BLINDING_EVENT)
    if set(doc) != set(BLINDING_KEYS) or doc.get("kind") != BLINDING_KIND or doc.get("version") != 1 or \
            type(doc.get("version")) is not int or type(doc.get("verified")) is not bool or \
            not SHA_RE.fullmatch(str(doc.get("blinded_sigma_sha256"))) or \
            not all(isinstance(doc.get(k), str) and doc[k].strip() for k in ("evidence", "utc", "recorded_by")):
        fail(f"SR2_BLINDING_RECORD is not a {BLINDING_KIND!r} record (exactly {list(BLINDING_KEYS)})")
    if doc["verified"] and doc["blinded_sigma_sha256"] != kit_sha(BLINDED_SIGMA_SCRIPT):
        fail(f"SR2_BLINDING_RECORD verified another {BLINDED_SIGMA_SCRIPT} than the one in this checkout")
    return {"path": SR2_BLINDING_RECORD["path"], "sha256": SR2_BLINDING_RECORD["sha256"], "verified": doc["verified"]}


def record_plan_b_78b(noise_path: str | None, blinded_path: str | None, blinded_sha256: str | None,
                      inputs_path: str | None, recorded_by: str, out: str) -> dict:
    """record-plan-b-78b: PLAN_B_78B's record (rules_78b.PLAN_B_KEYS) from the pinned records only. The gate record at
    GATE_78B's pin (its sources re-read: gate_noise_check); SR-2's status from the blinding record and the governing
    simulation's reading (adopted only when both pass; K-6's reason otherwise: the blinding test first); adopted: plan
    and sigma_A_pp from blinded_sigma.py's output (given by path and SHA-256), whose inputs file (given by path) must
    be a kit-written inputs file of the gate's option and families at the output's inputs_sha256 (S-9); not adopted:
    the gate's provisional plan under [B], its sigma_F_plan under [C], and both blinded hashes null."""
    gate_data = pin_bytes(r78.GATE_78B, "GATE_78B", r78.GATE_EVENT)
    try:
        gate = r78.gate_record_or_refuse(gate_data)
    except r78.Refused as exc:
        fail(str(exc))
    gate_noise_check(gate, noise_path)
    blinding = sr2_blinding_reading()
    simulation = sr2_simulation_reading(gate["option"], gate["families"])
    adopted = blinding["verified"] and not simulation["above_threshold"]
    reason = None if adopted else ("blinding_test_not_verified" if not blinding["verified"] else "simulation_reading")
    record = {"kind": r78.PLAN_B_RECORD_KIND, "version": 1, "sr2_adopted": adopted, "sr2_reason": reason,
              "utc": mac.utc(), "recorded_by": recorded_by}
    if adopted:
        if not (blinded_path and blinded_sha256 and inputs_path):
            fail("SR-2 is adopted: give blinded_sigma.py's output (--blinded-sigma FILE --sha256 H) and its inputs file "
                 "(--blinded-inputs FILE)")
        doc, ref = output_doc(blinded_path, blinded_sha256, "blinded_sigma.py's output", "--blinded-sigma")
        blinded_output_check(doc)
        inputs, _ = output_doc(inputs_path, doc["inputs_sha256"], "blinded_sigma.py's inputs file", "--blinded-inputs")
        if inputs.get("kind") != BLINDED_INPUTS_KIND or inputs.get("version") != 1 or \
                inputs.get("option") != gate["option"] or sorted(inputs.get("families") or {}) != sorted(gate["families"]):
            fail("the blinded_sigma inputs file is not one of the gate's option and families (write-blinded-inputs)")
        record.update(plan=r78.plan_for_sigma(doc["sigma_A_pp"]), plan_basis=r78.PLAN_BASES["adopted"],
                      sigma_A_pp=doc["sigma_A_pp"], blinded_sigma_output_sha256=ref["sha256"],
                      blinded_sigma_inputs_sha256=doc["inputs_sha256"])
    else:
        if blinded_path or inputs_path:
            fail(f"SR-2 is not adopted ({reason}): no blinded_sigma.py output is read (K-6)")
        record.update(plan=gate["provisional_plan"] if gate["option"] == "B" else gate["sigma_F_plan"],
                      plan_basis=r78.PLAN_BASES[gate["option"]], sigma_A_pp=None, blinded_sigma_output_sha256=None,
                      blinded_sigma_inputs_sha256=None)
    problem = r78.plan_b_record_problem(record, gate["option"])
    if problem:
        fail(f"block B's plan record would not be PLAN_B_78B's form: {problem}")
    written = write_once(out, record)
    return {"recorded": "plan_b", **written, "plan": record["plan"], "sr2_adopted": adopted, "sr2_reason": reason,
            "plan_basis": record["plan_basis"], "simulation": simulation, "blinding": blinding}


def record_branch_78b(record_path: str | None, record_sha256: str | None, default: bool, recorded_by: str,
                      out: str) -> dict:
    """record-branch-78b: the family's BRANCH_78B record (rules_78b.BRANCH_KEYS; K-8, R-21, K1V-5) from its W1-18 record
    committed at .ai/inputs/stage1-post-w1-20261023/78b/w1-18/w1_18_record__<F>.json, by path and SHA-256: an over-
    refusal checks record (W1-18's kind, version 1) made under the family's W1-18 settings as W1_18_78B pins them, over
    the family's W1-18 units, with a truncation verdict: pass -> Branch 128, fail -> Branch full (Part 2 §4.2). Or,
    with --default, "Branch full by default" (no W1-18 record; DESO2 item 37), refused while the family's W1-18 record
    file exists at its place. A branch is never switched: once BRANCH_78B is pinned, only the same record is accepted."""
    family = family_or_fail()
    if default == bool(record_path):
        fail("record-branch-78b takes either --w1-18-record FILE --sha256 H or --default")
    where = f"{r78.W1_18_RECORD_DIR}w1_18_record__{family}.json"
    if default:
        if (ROOT / where).exists():
            fail(f"{where} exists: the branch comes from that W1-18 record, not by default (DESO2 item 37)")
        record = {"kind": r78.BRANCH_RECORD_KIND, "version": 1, "family": family, "branch": r78.BRANCH_DEFAULT,
                  "source": "default", "w1_18_record_sha256": None, "utc": mac.utc(), "recorded_by": recorded_by}
    else:
        p = pathlib.Path(record_path)
        try:
            rel = p.resolve().relative_to(ROOT.resolve()).as_posix()
        except ValueError:
            fail(f"the W1-18 record lies outside this checkout; it is committed at {where} (GXB R-21)")
        if rel != where:
            fail(f"the W1-18 record is {rel}, not {family}'s committed record {where} (GXB R-21, R-33)")
        doc, ref = output_doc(record_path, record_sha256, "the W1-18 record", "--w1-18-record")
        if r78.W1_18_78B is None or r78.w1_18_route_problem(r78.W1_18_78B):
            fail("W1_18_78B is null or off its form: the W1-18 record's settings cannot be checked")
        settings = f"scripts/scale78b/settings/limits_overrefusal_checks__{family}.json"
        want = r78.W1_18_78B["files"].get(settings)
        check = doc.get("truncation_check") if isinstance(doc.get("truncation_check"), dict) else {}
        units = doc.get("units")
        if doc.get("kind") != W1_18_OUTPUT_KIND or doc.get("version") != 1 or type(check.get("pass")) is not bool or \
                not isinstance(units, dict):
            fail(f"the W1-18 record is not a complete {W1_18_OUTPUT_KIND!r} version 1 record with a truncation verdict")
        if want is None or (doc.get("provenance") or {}).get("settings_sha256") != want:
            fail(f"the W1-18 record was not made under {family}'s W1-18 settings as W1_18_78B pins them ({settings})")
        if len(units) != len(r78.w1_18_units(family)):
            fail(f"the W1-18 record holds {len(units)} units, not {family}'s {len(r78.w1_18_units(family))} (Part 2 §4.2)")
        record = {"kind": r78.BRANCH_RECORD_KIND, "version": 1, "family": family,
                  "branch": "128" if check["pass"] else "full", "source": "w1_18", "w1_18_record_sha256": ref["sha256"],
                  "utc": mac.utc(), "recorded_by": recorded_by}
    problem = r78.branch_record_problem(record, family)
    if problem:
        fail(f"the branch record would not be BRANCH_78B's form: {problem}")
    if r78.BRANCH_78B[family] is not None:
        try:
            switch = r78.branch_switch_problem(family, record, branch_bytes(family))
        except r78.Refused as exc:
            fail(str(exc))
        if switch:
            fail(switch)
    written = write_once(out, record)
    return {"recorded": "branch", **written, "family": family, "branch": record["branch"], "source": record["source"]}


ANCHOR_COUNTS_FILE = "anchors.counts.json"            # make_anchor_answers.py's exit-3 counts record (R: :167-169)


def record_anchor_stop(host: str, message_file: str | None, out: str) -> dict:
    """record-anchor-stop HOST [--message-file FILE] --out FILE (GXB O6, the fourth set's form; KR5): the family's
    text-free stop record (rules_78b.anchor_stop_record) from this scorer-block copy's anchor job only: HOST is the
    anchor's single-job host, recorded done; its JOB-DONE.json (at the SHA-256 record-done kept) names the job crashed
    with the anchor step's exit code. Exit 3: the counts {kept, needed} from the job's anchors.counts.json in the pulled
    tree (kept < 64, needed 64); exit 1: the step's last stderr line (--message-file, a file in the pulled tree) must be
    the frozen script's harmful-pair AnchorJobError message. Any other exit or message is a crash (the kit's crash
    rule), never a stop. Prints the record's path and SHA-256, its stop kind, exit code and counts only."""
    family = family_or_fail()
    plan = load()
    h = plan["hosts"].get(host)
    if h is None or h.get("block") != r78.SC_BLOCK or [j["kind"] for j in h["jobs"]] != ["anchor"] or not h.get("done"):
        fail(f"{host} is not this copy's anchor host recorded done (record-done first)")
    tree = HERE / "retrieved" / host / "tree"
    path = tree / "JOB-DONE.json"
    if not path.is_file() or mac.sha(path) != h.get("job_done_sha256"):
        fail(f"{host}: its JOB-DONE.json is missing or is not the one record-done read")
    done = json.loads(path.read_text())
    rec = (done.get("jobs") or [None])[0]
    if not isinstance(rec, dict) or rec.get("kind") != "anchor" or rec.get("status") != "crashed":
        fail(f"{host}: the anchor job is not recorded crashed (a stop ends the job with a non-zero exit)")
    exits = rec.get("exits") if isinstance(rec.get("exits"), dict) else {}
    steps = [k for k in exits if k.endswith("-anchor")]
    if len(steps) != 1:
        fail(f"{host}: JOB-DONE.json names no single anchor step exit (the runner's '<tag>-anchor' step)")
    code = exits[steps[0]]
    message, counts = None, None
    if code == r78.ANCHOR_EXIT_ERROR:
        if not message_file:
            fail("an exit-1 end is a stop only with the harmful-pair message: give the step's stderr (--message-file)")
        m = pathlib.Path(message_file)
        try:
            m.resolve().relative_to(tree.resolve())
        except ValueError:
            fail("--message-file: the step's stderr is a file of the pulled tree")
        lines = [x for x in m.read_text(errors="replace").splitlines() if x.strip()] if m.is_file() else []
        message = lines[-1] if lines else None
    elif code == r78.ANCHOR_EXIT_FEW:
        found = sorted(tree.glob(f"job-0/**/{ANCHOR_COUNTS_FILE}"))
        if len(found) != 1:
            fail(f"{host}: an exit-3 stop needs the job's one {ANCHOR_COUNTS_FILE} in the pulled tree")
        try:
            got = json.loads(found[0].read_text())
        except ValueError:
            fail(f"{host}: {ANCHOR_COUNTS_FILE} is not JSON")
        counts = {k: got.get(k) for k in ("kept", "needed")} if isinstance(got, dict) else None
    try:
        stop = r78.anchor_stop_record(family, code, message, h["job_done_sha256"], counts)
    except r78.Refused as exc:
        fail(str(exc))
    written = write_once(out, stop)
    return {"recorded": "anchor_stop", **written, "family": family, "stop_kind": stop["stop_kind"],
            "exit_code": stop["exit_code"], "counts": stop["counts"]}


def blinded_inputs_part(plan: dict, family: str) -> dict:
    """S-9 (GXB second set): this family's entry of blinded_sigma.py's inputs file, from plan.json and the kit's pins
    only (never typed, never a value read): the design ("full", or "anchor_stopped" with the stop record's pin, S-6);
    the engine of each role (R-13): the reused a0 and N's R units' as N's noise reading took them (its output at the
    gate's pin), block A's the packed engine's; the method edits by SHA-256 (rules_78b.METHOD_EDITS, equal to the jobs'
    bound edits); the cells: R 1101-1103 N's (N_UNITS), R 1104-1105 and every block-A cell its unit (path under the
    repository, COMPLETE.json SHA-256), a0 1101-1103 the side units (KIT a0_units) or N's a0-1103 (Llama), a0 1104
    block A's. Paths are relative to the repository (write-blinded-inputs rebases them)."""
    b = plan["blocks"]["A"]
    stopped = b.get("anchor_stop") is not None
    noise = b["gate"]["noise_reading"]
    doc, _ = output_doc(noise["path"], noise["sha256"], "N's noise reading output", "the gate's noise reading")
    engines = (doc.get("families") or {}).get(family, {}).get("engine") or {}
    hosts = {n: h for n, h in plan["hosts"].items() if h.get("block") == "A"}
    block_engines = {h["engine_sha256"] for h in hosts.values()}
    if set(engines) != {"a0", "R"} or not all(SHA_RE.fullmatch(str(v)) for v in engines.values()) or \
            len(block_engines) != 1:
        fail("blinded_sigma's engines: N's reading names no a0 and R identity, or block A ran on two engines")
    cells: dict = {}
    edits: dict = {}
    for name, h in sorted(hosts.items()):
        for j in h["jobs"]:
            if j.get("status") != "complete" or j.get("pulled") is False or not j.get("unit") or \
                    not SHA_RE.fullmatch(str(j.get("complete_sha256"))):
                fail(f"{name}: a block-A job is not complete and pulled with its unit (blinded_sigma reads every cell)")
            unit = (HERE / "retrieved" / name / "tree" / j["unit"]).relative_to(ROOT).as_posix()
            entry = {"path": unit, "complete_sha256": j["complete_sha256"]}
            if j["arm"] == "R":
                entry["arm"] = (j.get("edit") or {}).get("engine_arm") or f"edit-{j['edit']['sha256']}"
            elif j["arm"] != "a0":
                pin = r78.METHOD_EDITS[family][j["arm"]]
                if not pin or (j.get("edit") or {}).get("sha256") != pin["sha256"]:
                    fail(f"{name}: {j['arm']}'s bound edit is not METHOD_EDITS' pin")
                if edits.setdefault(j["arm"], pin["sha256"]) != pin["sha256"]:
                    fail(f"{j['arm']}: two edits")
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


def block_a_arms_done(plan: dict) -> bool:
    """Every hosts launch of this copy's block A released and every job of its hosts complete and pulled (the judge
    launches may still be open): blinded_sigma reads every block-A cell."""
    b = plan["blocks"].get("A")
    if not b or b.get("pending"):
        return False
    hosts = [h for h in plan["hosts"].values() if h.get("block") == "A"]
    released_hosts = {n for x in b["launches"][:b["released"]] for n in x.get("hosts", [])}
    planned_hosts = {n for x in b["launches"] for n in x.get("hosts", [])}
    return bool(hosts) and released_hosts == planned_hosts and \
        all(j.get("status") == "complete" and j.get("pulled") is not False for h in hosts for j in h["jobs"])


def write_blinded_part(plan: dict) -> dict:
    """S-9: once block A's arm jobs are all complete in this copy, its part of blinded_sigma.py's inputs file is
    written once (blinded/blinded-sigma-inputs-part__<F>.json); a second record-done finds the same bytes."""
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


def write_blinded_inputs(parts: list, out: str) -> dict:
    """write-blinded-inputs --part FILE=SHA256 ... --out FILE (S-9): blinded_sigma.py's inputs file {kind, version,
    option, families} (its INPUTS_KIND form) from the parts block A's record-done wrote in each family's copy (read by
    path and SHA-256; each of the gate's families exactly once; every part of the gate GATE_78B pins), with each path
    rebased to the inputs file's folder. Prints the file's path and SHA-256 and the cell counts only."""
    gate_data = pin_bytes(r78.GATE_78B, "GATE_78B", r78.GATE_EVENT)
    try:
        gate = r78.gate_record_or_refuse(gate_data)
    except r78.Refused as exc:
        fail(str(exc))
    out_path = pathlib.Path(out)
    families, counts = {}, {}
    for item in parts or []:
        path, _, digest = str(item).rpartition("=")
        doc, _ = output_doc(path, digest, "a blinded_sigma inputs part", "--part FILE=SHA256")
        if doc.get("kind") != BLINDED_PART_KIND or doc.get("version") != 1 or doc.get("gate_sha256") != r78.GATE_78B["sha256"] \
                or doc.get("option") != gate["option"] or doc.get("family") not in gate["families"]:
            fail("a part is not block A's record-done part of this gate's option and families")
        if doc["family"] in families:
            fail(f"two parts for {doc['family']}")
        entry = json.loads(json.dumps(doc["entry"]))
        refs = [c for by_seed in entry["cells"].values() for c in by_seed.values()]
        refs += [entry["anchor_stop"]] if "anchor_stop" in entry else []
        for ref in refs:
            ref["path"] = os.path.relpath(ROOT / ref["path"], out_path.resolve().parent)
        families[doc["family"]] = entry
        counts[doc["family"]] = len(refs)
    if sorted(families) != sorted(gate["families"]):
        fail(f"the parts cover {sorted(families)}, not the gate's families {sorted(gate['families'])}")
    written = write_once(out, {"kind": BLINDED_INPUTS_KIND, "version": 1, "option": gate["option"], "families": families})
    return {"written": "blinded_sigma_inputs", **written, "option": gate["option"], "files_named": counts}


def c0_release_check(name: str, job: dict, values: dict) -> None:
    """DESO2 K6v-4 (Part 2 §15 item 12): at release, the packed c0 source unit (the member of the packed engine-X bundle
    that sealed-files.json names for source_complete:R:1101, the bundle re-hashed at its receipt) must hash to the job's
    input pin and list checkpoints.e1.adapter_fingerprint equal to C0_SOURCE[family]["e1_fingerprint"] now: an edit of
    the pin after the pack refuses on the Mac, before the pod starts. Only that field is read; names only refused."""
    rec = engine_receipt("X")
    bundle = rec.get("bundle") if isinstance(rec.get("bundle"), dict) else {}
    p = pathlib.Path(str(bundle.get("path")))
    if not p.is_file() or mac.sha(p) != bundle.get("sha256"):
        fail(f"{name}: the packed engine-X bundle is missing or is not its receipt's")
    doc, _ = packed_sealed("X")
    rel = (doc.get("inputs") or {}).get(C0_INPUT)
    try:
        with tarfile.open(p) as archive:
            member = archive.extractfile(rel) if rel else None
            data = member.read() if member is not None else None
    except (KeyError, tarfile.TarError):
        data = None
    if data is None or hashlib.sha256(data).hexdigest() != job["inputs"].get(C0_INPUT):
        fail(f"{name}: c0's packed source unit ({C0_INPUT}) is missing from the bundle or differs from the job's pin")
    try:
        unit = json.loads(data)
    except ValueError:
        unit = None
    points = unit.get("checkpoints") if isinstance(unit, dict) and isinstance(unit.get("checkpoints"), dict) else {}
    got = (points.get("e1") or {}).get("adapter_fingerprint") if isinstance(points.get("e1"), dict) else None
    if not SHA_RE.fullmatch(str(got)) or got != (values.get("C0_SOURCE") or {}).get("e1_fingerprint"):
        fail(f"{name}: c0's packed source unit's e1 adapter fingerprint is not C0_SOURCE's e1_fingerprint now (an edit "
             "of the pin after the pack, K6v-4); refused before the pod starts")


C0_INPUT = "source_complete:R:1101"
