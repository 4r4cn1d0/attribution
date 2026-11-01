"""LN-14's theta0 PHTest transfer bar and LN-19's flag-change shares per source, read from the sealed O-ext summaries
that the reading's input build used (REV4 6.3; report only). Exit 0: the file written; 2: refused, nothing written.

    python -m scripts.stage1_s1.reading_extra.cap_reports --kit tmp/stage1-olmo --record sources.json --out cap.json

``sources.json`` is the input builder's --record document of the reading (it names, per cell, reference and theta0,
the O-ext folder or B10 unit read, by COMPLETE.json SHA-256, and the SHA-256 of the oext_summary.json read). REV4 =
research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md (frozen).

The frozen rules. LN-14, REV4:554: "Under Branch 128, θ0's 400 PHTest answers are made once at the full cap and judged
both full and cut, by W1-18's bar, as a pre-set report. If θ0 fails the bar, the paper states the cut as a limit for
PHTest; the cap rule does not switch." LN-19, REV4:555: "The record states the route per source. The cap record also
prints the measured flag-change share per source (full against cut, where both exist), because under Branch 128 up to
3 of 100 flags per unit may change, and if they fall on different prompts for an arm and for θ0 the discordance rises
by up to about 6 pp". W1-18 chose Branch 128 (FOCUS, W1-18's entry), so both apply.

Neither value is in tables.json, sources.json or reading.json: oext_eval.py (scripts/stage1_s1) writes them into each
O-ext pass's oext_summary.json (flag_change, route) and into theta0's oext_transfer_summary.json (bar, flag_change).
So this reader opens exactly those text-free summaries (oext_unit.py scans them for every prompt, answer, cut and judge
text before the folder completes) and nothing else, through the builder's own verified-folder code
(scripts/stage1_s1/reading_input/sources.py, imported and never edited): the kit must be the one the record names
(plan.json and every seal at the record's SHA-256); each folder's COMPLETE.json at plan.json's and the seal's SHA-256;
each summary listed by COMPLETE.json, sealed at that SHA-256, hashing to it on disk, and (for every cell, reference
and theta0) equal to the SHA-256 the builder's record names, so it is the file the builder read. theta0's transfer
folder (kind transfer_report, J4) is found by plan.json's job record and checked the same way. Values are copied by
key; the transfer bar's pass is recomputed from its counts as oext_eval.transfer_bar does and must agree. Under Branch
128 no unit holds both forms of its PHTest answers (they are made at the cut cap only), but theta0's LN-14 pass holds
both forms of its 400: the LN-19 PHTest lines say so and the pooled line copies theta0's LN-14 share beside it
(theta0_ln14). Printed on stdout: the file, its SHA-256 and the bar's word. READINGS gives each reading and its
alternative.
"""

from __future__ import annotations

from scripts.stage1_s1.reading.settings import READINGS as B16_READINGS
from scripts.stage1_s1.reading.settings import Refusal
from scripts.stage1_s1.reading_extra import common
from scripts.stage1_s1.reading_input.build import READING_BLOCKS
from scripts.stage1_s1.reading_input.sources import Kit, is_hex64

KIND = "stage1 reading cap reports (LN-14, LN-19)"
OEXT_SUMMARY_KIND = "stage1 o-ext evaluation"            # scripts/stage1_s1/oext_eval.SUMMARY_KIND
TRANSFER_KIND = "stage1 o-ext transfer report"           # oext_eval.TRANSFER_KIND
OEXT_UNIT_KIND = "stage1-oext-unit"                      # scripts/stage1_s1/oext_unit.JOB_KIND
SUMMARY, TRANSFER_SUMMARY = "oext_summary.json", "oext_transfer_summary.json"   # oext_eval's file names
B10_SUMMARY = "eval/e1/oext_summary.json"                # a B10 unit's O-ext files sit beside its evaluation
SOURCES = ("dev100", "phtest")                           # oext_eval.flag_change's two sources
TRANSFER_JOB = "transfer_report"                         # the kit's J4 job kind
LN14_FAIL = ("theta0 fails W1-18's bar on its PHTest answers: the paper states the cut as a limit for PHTest; the cap "
             "rule does not switch (REV4:554)")
LN14_PASS = "theta0 meets W1-18's bar on its PHTest answers (full against cut; REV4:554)"
NO_BOTH_FORMS = {                                        # the LN-19 line of a source no unit holds both forms of
    "phtest": "no unit holds both forms of this source: under Branch 128 each unit's PHTest answers are made at the "
              "cut cap only; theta0's LN-14 transfer pass holds both forms of its 400 PHTest answers, and its share "
              "is ln14.report.flag_change (copied beside the pooled PHTest line as theta0_ln14)",
    "dev100": "no unit holds both forms of this source"}
RULE = [
    "REV4:554 (LN-14): Under Branch 128, θ0's 400 PHTest answers are made once at the full cap and judged both full "
    "and cut, by W1-18's bar, as a pre-set report. If θ0 fails the bar, the paper states the cut as a limit for "
    "PHTest; the cap rule does not switch.",
    "REV4:555 (LN-19): The record states the route per source. The cap record also prints the measured flag-change "
    "share per source (full against cut, where both exist), because under Branch 128 up to 3 of 100 flags per unit "
    "may change, and if they fall on different prompts for an arm and for θ0 the discordance rises by up to about "
    "6 pp."]
READINGS = {
    "C1": "\"The flag-change share per source\" is printed per unit (each O-ext summary's flag_change), per arm and "
          "reference (pooled over its seeds: changed / prompts with both forms) and pooled over every unit the "
          "reading reads, for each source; a source no unit holds both forms of (the units' PHTest answers under "
          "Branch 128, made at the cut cap only) has no unit share: its line says so and points to theta0's LN-14 "
          "pass, which holds both forms of its 400 PHTest answers (its share, ln14.report.flag_change, is copied "
          "beside the pooled PHTest line as theta0_ln14). Alternative: the pooled share per source only.",
    "C2": "The units are every O cell of the reading's input (the primary cells, the references with an O-ext "
          "summary, theta0); an O cell absent under LN-12 is listed as absent. Alternative: the primary arms and "
          "theta0 only.",
    "C3": "\"The route per source\" is the summaries' route texts (one set per branch; refused if the units differ) "
          "and each unit's dev-100 route (unit_eval, source_unit or generated) from its O-ext folder's COMPLETE.json. "
          "Alternative: the route texts only.",
    "C4": "LN-14's bar is the transfer report's own result (oext_eval.transfer_bar: W1-18's bar read as shares of "
          "the PHTest count, settings transfer.bar.reading), recomputed here from its counts. Under Branch full LN-14 "
          "does not run and the output says so; under Branch 128 a missing transfer report is printed as not run. "
          "Alternative: refuse the whole output when the report is missing.",
    "C5": "This reader opens sealed (text-free) O-ext summaries, which are not documents the reading writes; it reads "
          "only the summaries the builder's record names (and theta0's transfer summary by plan.json and the seal), "
          "after step 1 of the reading has opened the outcomes. Alternative: the record states that LN-14 and LN-19 "
          "were not read (a deviation)."}


def _int(value, what: str, low: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise Refusal(f"{what} is not a count")
    return value


def flag_change(fc, where: str) -> dict:
    """One source's flag_change block (oext_eval.flag_change), checked: counts, the share = changed / prompts with
    both forms (None with no full form), and the two directions summing to the changes."""
    if not isinstance(fc, dict):
        raise Refusal(f"{where}: no flag_change block")
    n = _int(fc.get("prompts_with_both_forms"), f"{where}: prompts_with_both_forms")
    changed = _int(fc.get("changed"), f"{where}: changed")
    up, down = _int(fc.get("became_refused"), f"{where}: became_refused"), \
        _int(fc.get("became_not_refused"), f"{where}: became_not_refused")
    share = fc.get("share")
    if changed > n or up + down != changed:
        raise Refusal(f"{where}: the flag-change counts do not add up")
    if n == 0:
        if share is not None:
            raise Refusal(f"{where}: a share with no prompt in both forms")
    elif common.number(share, f"{where}: share") != changed / n:
        raise Refusal(f"{where}: the share is not changed / prompts with both forms")
    return {"prompts_with_both_forms": n, "changed": changed, "share": share, "became_refused": up,
            "became_not_refused": down, "note": fc.get("note")}


def _pooled(blocks: list, source: str) -> dict:
    n, changed = sum(b["prompts_with_both_forms"] for b in blocks), sum(b["changed"] for b in blocks)
    return {"units": len(blocks), "prompts_with_both_forms": n, "changed": changed,
            "share": changed / n if n else None,
            "note": None if n else NO_BOTH_FORMS[source]}


def _theta0_ln14(ln14: dict) -> dict:
    """theta0's LN-14 flag-change share (full against cut over its 400 PHTest answers), copied beside the pooled
    PHTest line; without a report, why (not run, or Branch full)."""
    report = ln14.get("report")
    if report is None:
        return {"prompts_with_both_forms": None, "changed": None, "share": None, "why": ln14["text"]}
    fc = report["flag_change"]
    return {"prompts_with_both_forms": fc["prompts_with_both_forms"], "changed": fc["changed"], "share": fc["share"],
            "source": "ln14.report.flag_change (theta0's transfer pass, REV4:554)"}


class _Index:
    """plan.json's O-ext folders, B10 units and transfer jobs of the reading's sealed blocks, keyed by COMPLETE.json
    SHA-256 (the builder's own scan: done hosts, or hosts the seal lists as moved)."""

    def __init__(self, kit: Kit, blocks: tuple):
        self.folders, self.transfers = {}, []
        for block in blocks:
            for host, h in kit.hosts(block):
                for i, job in enumerate(h["jobs"]):
                    if not isinstance(job, dict):
                        continue
                    outputs = job.get("outputs") if isinstance(job.get("outputs"), dict) else {}
                    oext = outputs.get(f"job-{i}/oext/COMPLETE.json")
                    if is_hex64(oext):
                        self._put(oext, (block, host, f"job-{i}/oext"))
                    for u in job.get("units") or []:
                        if isinstance(u, dict) and is_hex64(u.get("complete_sha256")) and isinstance(u.get("unit"), str):
                            self._put(u["complete_sha256"], (block, host, u["unit"]))
                    if job.get("kind") == TRANSFER_JOB and job.get("status") == "complete" and \
                            job.get("pulled") is not False:
                        self.transfers.append((block, host, i, job))

    def _put(self, digest: str, where: tuple) -> None:
        if digest in self.folders and self.folders[digest] != where:
            raise Refusal(f"plan.json names one COMPLETE.json SHA-256 ({digest[:16]}) for two folders")
        self.folders[digest] = where


def _summary(kit: Kit, index: _Index, label: str, rec: dict, rel: str) -> tuple:
    """(the O-ext summary named by one record entry, the folder's COMPLETE.json): opened through the builder's
    Folder; the summary's SHA-256 must be the one the builder's record names."""
    digest, named = rec.get("complete_sha256"), (rec.get("files") or {}).get(rel)
    if not is_hex64(digest) or not is_hex64(named):
        raise Refusal(f"{label}: the builder's record names no folder or no {rel} by SHA-256")
    where = index.folders.get(digest)
    if where is None:
        raise Refusal(f"{label}: no folder of the reading's blocks has the COMPLETE.json the record names")
    block, host, folder_rel = where
    folder = kit.folder(block, host, folder_rel, digest, f"{label} kit:{host}/{folder_rel}")
    doc = folder.json(rel)
    if folder.read.get(rel) != named:
        raise Refusal(f"{label}: {rel} is not the file the builder's record names")
    if not isinstance(doc, dict) or doc.get("kind") != OEXT_SUMMARY_KIND or doc.get("version") != 1 or \
            doc.get("branch") not in ("128", "full"):
        raise Refusal(f"{label}: {rel} is not a version-1 O-ext summary of branch 128 or full")
    return doc, folder.complete, {"block": block, "host": host, "folder": folder_rel, "complete_sha256": digest,
                                  "summary_sha256": named}


def _unit_entries(record: dict) -> list:
    """(group, label, the record entry, the summary's path in it) for every O cell of the reading's input; an absent
    O cell (LN-12) as (group, label, None, None)."""
    out = []
    cells, refs, theta0 = record.get("cells"), record.get("references"), record.get("theta0")
    absent = set(record.get("o_cells_absent") or [])
    if not isinstance(cells, dict) or not isinstance(refs, dict) or not isinstance(theta0, dict):
        raise Refusal("the builder's record holds no cells, references or theta0 block")
    for group, table in (("cells", cells), ("references", refs)):
        for label, entry in sorted(table.items()):
            o = entry.get("o") if isinstance(entry, dict) else None
            if not isinstance(o, list):
                raise Refusal(f"{label}: the builder's record holds no O folder list")
            if len(o) == 1:
                out.append((group, label, o[0], SUMMARY))
            elif not o and B10_SUMMARY in ((entry.get("unit") or {}).get("files") or {}):
                out.append((group, label, entry["unit"], B10_SUMMARY))
            elif not o and label in absent:
                out.append((group, label, None, None))
            else:
                raise Refusal(f"{label}: the builder's record names no single O-ext summary")
    o = theta0.get("o")
    if not isinstance(o, dict):
        raise Refusal("theta0: the builder's record names no O-only folder")
    out.append(("theta0", "theta0", o, SUMMARY))
    return out


def _transfer(kit: Kit, index: _Index, branch: str) -> dict:
    """LN-14's report (module doc; reading C4)."""
    if branch != "128":
        return {"applies": False, "report": None,
                "text": "LN-14 runs under Branch 128 only; the reading's O-ext branch is full (REV4:554)"}
    if len(index.transfers) > 1:
        raise Refusal(f"{len(index.transfers)} complete transfer_report jobs: LN-14's report is made once")
    if not index.transfers:
        return {"applies": True, "report": None,
                "text": "not run: no complete transfer_report job in the reading's sealed blocks"}
    block, host, i, job = index.transfers[0]
    rel = f"job-{i}/transfer"
    digest = (job.get("outputs") or {}).get(f"{rel}/COMPLETE.json")
    folder = kit.folder(block, host, rel, digest, f"theta0 LN-14 kit:{host}/{rel}")
    c = folder.complete
    named = (c.get("summary_file") or {}).get(TRANSFER_SUMMARY)
    if c.get("kind") != OEXT_UNIT_KIND or c.get("command") != "transfer" or c.get("state") != "untuned" or \
            not is_hex64(named):
        raise Refusal(f"{folder.label}: not theta0's O-ext transfer pass (command transfer, state untuned)")
    doc = folder.json(TRANSFER_SUMMARY)
    if folder.read.get(TRANSFER_SUMMARY) != named:
        raise Refusal(f"{folder.label}: {TRANSFER_SUMMARY} is not the file its COMPLETE.json names")
    bar = doc.get("bar") if isinstance(doc, dict) else None
    if not isinstance(doc, dict) or doc.get("kind") != TRANSFER_KIND or doc.get("version") != 1 or \
            doc.get("branch") != "128" or not isinstance(bar, dict) or not isinstance(bar.get("bar"), dict):
        raise Refusal(f"{folder.label}: not a version-1 LN-14 transfer report of Branch 128")
    n, agree = _int(bar.get("prompts"), "LN-14: prompts", 1), _int(bar.get("flags_agree"), "LN-14: flags_agree")
    full, cut = _int(bar.get("refused_full"), "LN-14: refused_full"), _int(bar.get("refused_cut"), "LN-14: refused_cut")
    move = _int(bar.get("count_move"), "LN-14: count_move")
    t = bar["bar"]
    min_agree, max_move = _int(t.get("min_flags_agree"), "LN-14: the bar"), _int(t.get("max_count_move"), "LN-14: the bar")
    per = _int(t.get("per_prompts"), "LN-14: the bar", 1)
    if agree > n or full > n or cut > n or move != abs(full - cut) or not isinstance(bar.get("pass"), bool):
        raise Refusal("LN-14: the transfer report's counts do not add up")
    passes = per * agree >= min_agree * n and per * move <= max_move * n       # oext_eval.transfer_bar
    if passes is not bar["pass"]:
        raise Refusal("LN-14: the transfer report's pass is not its counts read by W1-18's bar")
    return {"applies": True, "passes": passes, "text": LN14_PASS if passes else LN14_FAIL,
            "report": {"prompts": n, "flags_agree": agree, "refused_full": full, "refused_cut": cut,
                       "count_move": move, "invalid_full": bar.get("invalid_full"),
                       "invalid_cut": bar.get("invalid_cut"),
                       "bar": {"min_flags_agree": min_agree, "max_count_move": max_move, "per_prompts": per},
                       "bar_reading": doc.get("bar_reading"),
                       "flag_change": flag_change(doc.get("flag_change"), "LN-14: flag_change")},
            "source": {"block": block, "host": host, "folder": rel, "complete_sha256": digest,
                       "summary_sha256": named}}


def read(kit_root, record: dict, record_sha256: str) -> dict:
    """The whole output (module doc)."""
    if not isinstance(record, dict) or record.get("kind") != common.RECORD_KIND or record.get("version") != 1 or \
            record.get("reading") not in B16_READINGS:
        raise Refusal("the record is not the input builder's version-1 sources record of a sealed reading")
    reading = record["reading"]
    kit = Kit(kit_root)
    seals = (record.get("kit") or {}).get("seals")
    if kit.plan_sha256 != (record.get("kit") or {}).get("plan_sha256"):
        raise Refusal("the kit's plan.json is not the one the builder's record names")
    if not isinstance(seals, dict) or tuple(sorted(seals)) != tuple(sorted(READING_BLOCKS[reading])):
        raise Refusal(f"the builder's record does not name the seals of the reading's blocks")
    for block, digest in seals.items():
        if kit.seal(block).sha256 != digest:
            raise Refusal(f"block {block}'s seal is not the one the builder's record names")
    index = _Index(kit, READING_BLOCKS[reading])
    units, branches, routes = {}, set(), []
    for group, label, rec, rel in _unit_entries(record):
        if rec is None:
            units[label] = {"group": group, "o": "absent (LN-12): this cell has no O-ext pass"}
            continue
        doc, complete, source = _summary(kit, index, label, rec, rel)
        branches.add(doc["branch"])
        route = doc.get("route")
        if not isinstance(route, dict) or sorted(route) != sorted(SOURCES) or \
                not all(isinstance(v, str) for v in route.values()):
            raise Refusal(f"{label}: the O-ext summary states no route per source")
        if route not in routes:
            routes.append(route)
        fc = doc.get("flag_change") if isinstance(doc.get("flag_change"), dict) else {}
        units[label] = {"group": group, "branch": doc["branch"],
                        "dev100_route": complete.get("dev100_route") if rel == SUMMARY else None,
                        "flag_change": {s: flag_change(fc.get(s), f"{label}: flag_change {s}") for s in SOURCES},
                        "source": source}
    if len(branches) != 1 or len(routes) != 1:
        raise Refusal("the O-ext summaries do not hold one branch and one route per source")
    branch = branches.pop()
    by_arm: dict = {}
    for label, u in units.items():
        if "flag_change" in u and u["group"] != "theta0":
            key = label.rsplit(" ", 1)[0]
            by_arm.setdefault(key, []).append(u)
    ln14 = _transfer(kit, index, branch)
    pooled = {s: _pooled([u["flag_change"][s] for u in units.values() if "flag_change" in u], s) for s in SOURCES}
    pooled["phtest"]["theta0_ln14"] = _theta0_ln14(ln14)
    out = {"kind": KIND, "version": 1, "reading": reading, "rule": list(RULE), "readings": dict(READINGS),
           "branch": branch, "route_per_source": routes[0],
           "ln14": ln14,
           "ln19": {"units": units,
                    "by_arm_or_reference": {k: {s: _pooled([u["flag_change"][s] for u in v], s) for s in SOURCES}
                                            for k, v in sorted(by_arm.items())},
                    "pooled": pooled},
           "provenance": {**common.provenance({"sources.json": record_sha256}),
                          "kit": {"plan_sha256": kit.plan_sha256, "seals": dict(sorted(seals.items()))}}}
    return common.finish(out)


def main(argv=None) -> int:
    def arguments(p):
        p.add_argument("--kit", required=True, help="the stage-1 kit folder (tmp/stage1-olmo)")
        p.add_argument("--record", required=True, help="the builder's sources.json of this reading")

    def produce(args):
        doc, sha = common.read_document(args.record, "the builder's record")
        out = read(args.kit, doc, sha)
        ln14 = out["ln14"]
        word = ("not applicable (Branch full)" if not ln14["applies"] else "not run" if ln14["report"] is None
                else "passes" if ln14["passes"] else "fails")
        return out, [f"LN-14 transfer bar: {word}"]

    return common.main_frame("python -m scripts.stage1_s1.reading_extra.cap_reports",
                             "LN-14's transfer bar and LN-19's flag-change shares (REV4:554-555)", arguments, produce,
                             argv)


if __name__ == "__main__":
    raise SystemExit(main())
