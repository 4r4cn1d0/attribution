#!/usr/bin/env python3.11
"""Gate B re-costing stop (frozen DRAFT revision 5, §9 "Re-costing stop after wave 0b"): the worst path from wave 1
on, recomputed at the rates measured on the anchor, wave-0a and wave-0b pods, against the balance.

Read-only. It reads the kit's records (plan.json, hosts/<h>/, retrieved/<h>/ job receipts and job-done records,
COMPLETE.json completed_utc only, budget-checks.jsonl, account-latest.json). It never contacts a service, never
writes into the kit (sys.dont_write_bytecode before the kit imports; run it as
`PYTHONDONTWRITEBYTECODE=1 python3.11 -B recost.py`) and never runs a plan_tool subcommand. The kit is found at
$ATTRIBUTION_ROOT/tmp/gate-b-olmo (default root /Users/spiderishi/Coding/attribution), so it runs from any folder.

The need is the kit's own: plan_tool.worst_path_need -> gateb_rules.funding_need_usd. Nothing of the formula is
copied. "At measured rates" swaps three spend constants, gateb_rules.POD_OVERHEAD_S, SPEND_UPPER_S["arm"] and
RATE_USD, for the duration of the kit's funding_need_usd call only, so every launch's upper spend uses the measured
rates while every cap (and so every guard term, $6 + $1.85 x summed caps) stays what the kit plans and its guard
checks. PLANNING_PRICE_USD, RESERVE_USD, CONTINGENCY_FACTOR, MAX_ARMS_PER_POD, GRANITE_* and the caps are unchanged.

Every pre-wave-1 host in plan.json (anchor, 0a, 0b) is classified: finished (measured), pre-job-failed or stopped
(its billed time is spend), running or planned (projected spend at the measured rates). Spend not yet in the balance
reading comes off the projected balance at the wave-1 launch (DRAFT §9: a re-run before wave 1 lowers that balance).

Usage:
  recost.py          rates from the finished anchor and wave-0a pods; the wave-0b pod's retrain and diagnostics at
                     --retrain-h / --diagnostics-h (default: the frozen uppers 0.15 h and 2.0 h)
  recost.py --w0b    also take the rates, retrain and diagnostics hours from the finished wave-0b pod (exit 2 while
                     no wave-0b host has finished and been pulled)
"""
from __future__ import annotations

import argparse
import contextlib
import datetime as dt
import hashlib
import json
import os
import pathlib
import sys

sys.dont_write_bytecode = True                                 # leave no __pycache__ in the kit
ROOT = pathlib.Path(os.environ.get("ATTRIBUTION_ROOT", "/Users/spiderishi/Coding/attribution")).resolve()
KIT = ROOT / "tmp" / "gate-b-olmo"
DRAFT = ROOT / "research/experiments/2026-10-08-gate-b-olmo-preregistration-DRAFT.md"
sys.path.insert(0, str(KIT))
import gateb_rules as rules  # noqa: E402
import plan_tool  # noqa: E402

# the DRAFT's frozen figures for the recommended layout and route (DRAFT §9 funding rule, final round; README:70-71)
DRAFT_FIGURES = {"base_need_usd": 62.76, "need_usd": 78.45, "contingency_usd": 15.69}
# the lead's allowances, free balance on top of the need (FOCUS 2026-10-10T11:14 UTC entry, decisions (1), (2), (4))
ALLOWANCES = {"storage_usd": 4.00, "granite_relaunch_usd": 3.78, "harmbench_relaunch_usd": 3.70}
# the one HarmBench launch after the control: judge reserve $1, cap 2.5 h (DRAFT §9 "Judge pods", fix round)
HB_RESERVE_USD, HB_CAP_H = 1.0, 2.5
VOLUME_USD_PER_GB_H = 0.20 / 730                               # stopped volume, $0.20 per GB-month (DRAFT §9)
POD_VOLUME_GB = rules.POD_SIZES["volume_gb"]                   # 20 GB per kit pod (gateb_rules.py:113)
PRE_WAVE1 = ("anchor", "0a", "0b")
LAUNCH_NAMES = {"1": "wave 1", "2": "wave 2 (m = 4)", "ext": "extension (2 units)", "lc": "length control"}


# ----- small helpers ---------------------------------------------------------------------------------------------
def t(stamp: str) -> dt.datetime:
    """An ISO time as the kit writes it (+00:00 offsets)."""
    return dt.datetime.fromisoformat(stamp.replace("Z", "+00:00"))


def iso(moment: dt.datetime) -> str:
    return moment.astimezone(dt.timezone.utc).isoformat(timespec="seconds")


def load(path: pathlib.Path):
    return json.loads(path.read_text())


def jsonl(path: pathlib.Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text().splitlines() if line.strip()] if path.is_file() else []


def sha(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def rel(path: pathlib.Path) -> str:
    path = pathlib.Path(path).resolve()
    return str(path.relative_to(ROOT)) if path.is_relative_to(ROOT) else str(path)


def r(x: float, n: int = 4) -> float:
    return round(x, n)


# ----- the pods' records -----------------------------------------------------------------------------------------
def measure_finished(host: str, base: dict) -> dict:
    """A finished kit pod's times and money. Clocks: create and stop are the Mac's (the API answer, the stop
    confirmation); job start and end are the pod's. Billed time = stop confirmed - created. Overhead = billed time -
    the sum of the job slots (job-done/JOB-k.json utc -> ended_utc: the in-pod gate, the job's processes and the
    engine's verify), so overhead + jobs = billed time, as the kit's pod_spend_usd splits a pod's spend."""
    hdir, tree = KIT / "hosts" / host, KIT / "retrieved" / host / "tree"
    finished = load(hdir / "finished.json")
    outer = load(tree / "job-outer" / "process-receipt.json")
    job_start = t(outer["started_utc"])
    job_end = job_start + dt.timedelta(seconds=outer["elapsed_s"])
    mac_started = [e["utc"] for e in jsonl(hdir / "orchestrate.jsonl") if e.get("event") == "job-started"]
    jobs = []
    for done in sorted((tree / "job-done").glob("JOB-*.json"), key=lambda p: int(p.stem.split("-")[1])):
        rec = load(done)
        k = rec["index"]
        receipts = sorted(tree.glob(f"job-{k}-*/process-receipt.json"))
        complete = tree / rec["unit"] / "COMPLETE.json" if rec.get("unit") else None
        completed_utc = load(complete).get("completed_utc") if complete and complete.is_file() else None
        slot = (t(rec["ended_utc"]) - t(rec["utc"])).total_seconds() if rec.get("ended_utc") else None
        jobs.append({
            "index": k, "kind": rec["kind"], "seed": rec.get("seed"), "status": rec["status"],
            "slot_start_utc": rec.get("utc"), "slot_end_utc": rec.get("ended_utc"),
            "slot_s": slot, "slot_min": r(slot / 60, 2) if slot is not None else None,
            "process_elapsed_min": r(sum(load(p)["elapsed_s"] for p in receipts) / 60, 2),
            "complete_completed_utc": completed_utc,
            "source": f"{rel(done)} utc -> ended_utc (pod clock, 1 s); cross-check: summed elapsed_s of "
                      f"{rel(tree)}/job-{k}-*/process-receipt.json" + ("; COMPLETE.json completed_utc" if completed_utc
                                                                       else ""),
        })
    slots_s = sum(j["slot_s"] for j in jobs if j["slot_s"] is not None)
    billed_s = base["billed_s"]
    return {**base, "state": "finished", "status": finished.get("status"),
            "job_start_utc_pod": iso(job_start), "job_start_utc_mac_event": mac_started[0] if mac_started else None,
            "job_end_utc_pod": iso(job_end),
            "setup_min": r((job_start - t(base["created_utc"])).total_seconds() / 60, 2),
            "job_outer_min": r(outer["elapsed_s"] / 60, 2),
            "finish_min": r((t(base["stop_confirmed_utc"]) - job_end).total_seconds() / 60, 2),
            "jobs_slots_min": r(slots_s / 60, 2),
            "overhead_s": billed_s - slots_s, "overhead_min": r((billed_s - slots_s) / 60, 2),
            "jobs": jobs,
            "sources": {**base["sources"],
                        "job_start_end": f"{rel(tree / 'job-outer/process-receipt.json')} started_utc + elapsed_s",
                        "finished_json_outer_elapsed_min": finished.get("outer_elapsed_min")}}


def host_state(host: str, h: dict) -> dict:
    """One pre-wave-1 host: planned | running | pre-job-failed | stopped (not pulled) | finished."""
    hdir, tree = KIT / "hosts" / host, KIT / "retrieved" / host / "tree"
    base = {"host": host, "wave": h["wave"], "cap_h": h["cap_hours"],
            "jobs_planned": [j["kind"] for j in h["jobs"]], "job_statuses": [j["status"] for j in h["jobs"]]}
    if not (hdir / "create-result.json").is_file():
        return {**base, "state": "planned"}
    created = load(hdir / "create-result.json")["utc"]
    price = load(hdir / "pod.json")["costPerHr"]
    base.update(created_utc=created, price_usd_per_h=price,
                sources={"created": f"{rel(hdir / 'create-result.json')} utc (Mac; = pod.json created_utc)",
                         "price": f"{rel(hdir / 'pod.json')} costPerHr",
                         "stop": f"{rel(hdir / 'stops.jsonl')} first confirmed stop (Mac)"})
    stops = [s for s in jsonl(hdir / "stops.jsonl") if s.get("confirmed") is True]
    if not stops:
        return {**base, "state": "running"}
    billed_s = (t(stops[0]["utc"]) - t(created)).total_seconds()
    base.update(stop_confirmed_utc=stops[0]["utc"], billed_s=billed_s, billed_h=r(billed_s / 3600),
                billed_min=r(billed_s / 60, 2),
                cost_usd_at_pod_price=r(billed_s / 3600 * price))
    pulled = all(p.is_file() for p in (hdir / "finished.json", tree / "job-outer" / "process-receipt.json",
                                       tree / "JOB-DONE.json"))
    if pulled:
        return measure_finished(host, base)
    failed = [e for e in jsonl(hdir / "orchestrate.jsonl") if e.get("event") == "pre-job-failed"]
    if failed or h.get("pre_job_failed"):
        e = failed[0] if failed else {}
        return {**base, "state": "pre-job-failed", "failed_utc": e.get("utc"), "failed_step": e.get("step"),
                "failed_detail": e.get("detail"),
                "setup_until_failure_min": r((t(e["utc"]) - t(created)).total_seconds() / 60, 2) if e else None,
                "source_failure": f"{rel(hdir / 'orchestrate.jsonl')} pre-job-failed; plan.json hosts.{host}"}
    return {**base, "state": "stopped, not pulled"}


def account_cross_check(pods: dict) -> list[dict]:
    """Where two budget checks bracket one stopped kit pod and nothing else of the kit, and the balance fell (no top-up
    between), compare the account's drop with the pod-record cost plus idle spend at the readings' rates."""
    checks = jsonl(KIT / "budget-checks.jsonl")
    out = []
    stopped = {h: p for h, p in pods.items() if "stop_confirmed_utc" in p}
    for host, p in stopped.items():
        before = [c for c in checks if t(c["utc"]) <= t(p["created_utc"])]
        after = [c for c in checks if t(c["utc"]) >= t(p["stop_confirmed_utc"])]
        if not before or not after:
            continue
        b, a = before[-1], after[0]
        others = [h for h, q in pods.items() if h != host and "created_utc" in q
                  and t(b["utc"]) < t(q["created_utc"]) < t(a["utc"])]
        if a["balance"] >= b["balance"] or others:
            out.append({"host": host, "usable": False, "why": "a top-up or another kit pod between the readings",
                        "before": {"utc": b["utc"], "balance": b["balance"]},
                        "after": {"utc": a["utc"], "balance": a["balance"]}})
            continue
        span_h = (t(a["utc"]) - t(b["utc"])).total_seconds() / 3600
        lo, hi = sorted((b["spend_per_hr"], a["spend_per_hr"]))
        out.append({"host": host, "usable": True, "before": {"utc": b["utc"], "balance": b["balance"]},
                    "after": {"utc": a["utc"], "balance": a["balance"]},
                    "account_drop_usd": r(b["balance"] - a["balance"], 2),
                    "pod_record_cost_usd": p["cost_usd_at_pod_price"],
                    "record_plus_idle_usd_range": [r(p["cost_usd_at_pod_price"] + span_h * lo, 2),
                                                   r(p["cost_usd_at_pod_price"] + span_h * hi, 2)],
                    "source": f"{rel(KIT / 'budget-checks.jsonl')} (balances rounded to the cent); assumes no "
                              "non-kit pod ran between the readings"})
    return out


# ----- the kit's need at given spend rates -----------------------------------------------------------------------
@contextlib.contextmanager
def spend_rates(overhead_s: float, arm_s: float, rate: float):
    """Swap only the spend constants of gateb_rules; restore them after."""
    saved = (rules.POD_OVERHEAD_S, rules.SPEND_UPPER_S, rules.RATE_USD)
    rules.POD_OVERHEAD_S, rules.SPEND_UPPER_S, rules.RATE_USD = overhead_s, {**saved[1], "arm": arm_s}, rate
    try:
        yield
    finally:
        rules.POD_OVERHEAD_S, rules.SPEND_UPPER_S, rules.RATE_USD = saved


def wave1_hosts(plan: dict) -> list[list[dict]]:
    """Wave 1 as init-wave 1 splits it: 8 unit arms (rules.UNITS) in rules.pod_sizes pods (4 + 4), default timing
    (33 steps). Any step count up to about 86 gives the same 5.75 h caps, so the need does not depend on it."""
    return rules.split_pods(rules.default_jobs(["arm"] * rules.UNITS, plan["fixture"]))


def need_at(plan: dict, overhead_s: float, arm_s: float, rate: float) -> dict:
    """plan_tool.worst_path_need with the caps as the kit plans them and the spend at the given rates."""
    original = rules.funding_need_usd
    seen: dict = {}

    def at_rates(launches, factor=1.0):
        with spend_rates(overhead_s, arm_s, rate):
            out = original(launches, factor)
            seen["spend"] = [[rules.launch_pod_spend_usd(p) for p in launch] for launch in launches]
        seen["launches"] = launches
        return out

    rules.funding_need_usd = at_rates
    try:
        need = plan_tool.worst_path_need(plan, wave1_hosts(plan))
    finally:
        rules.funding_need_usd = original
    labels, waves, i = [], ["1"] + [w for w, _ in rules.WORST_PATH_AFTER_WAVE1], 0
    for launch in seen["launches"]:
        if launch[0].get("judge"):
            labels.append(f"granite after {labels[-1]}")
        else:
            labels.append(LAUNCH_NAMES[waves[i]])
            i += 1
    rows = [{"launch": lab, "pods": [(p.get("judge") or f"{len(p['kinds'])} arms") for p in launch],
             "caps_h": [p["cap_hours"] for p in launch], "term_usd": r(term), "upper_spend_usd": r(sum(sp))}
            for lab, launch, term, sp in zip(labels, seen["launches"], need["terms_usd"], seen["spend"])]
    spent_total = sum(sum(sp) for sp in seen["spend"])
    hb_term = spent_total + HB_RESERVE_USD + HB_CAP_H * rules.PLANNING_PRICE_USD
    binding = max(range(len(rows)), key=lambda k: need["terms_usd"][k])
    return {"base_need_usd": need["base_need_usd"], "need_usd": need["need_usd"],
            "contingency_usd": need["contingency_usd"], "factor": need["factor"],
            "rates": {"pod_overhead_min": r(overhead_s / 60, 3), "arm_min": r(arm_s / 60, 3), "rate_usd_per_h": rate},
            "binding_launch": rows[binding]["launch"], "launches": rows,
            "upper_spend_from_wave1_usd": r(spent_total),
            "harmbench_after_control": {"term_usd": r(hb_term), "inside_base": hb_term <= need["base_need_usd"],
                                        "rule": "spend uppers from wave 1 on + $1 + 2.5 h x $1.85 <= base "
                                                "(DRAFT §9 'Judge pods')"}}


def bisect(f, lo: float, hi: float, steps: int = 50) -> float | None:
    """The smallest x in [lo, hi] with f(x) true, for f monotone false -> true; None if f(hi) is false."""
    if not f(hi):
        return None
    if f(lo):
        return lo
    for _ in range(steps):
        mid = (lo + hi) / 2
        lo, hi = (lo, mid) if f(mid) else (mid, hi)
    return hi


# ----- main ------------------------------------------------------------------------------------------------------
def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--w0b", action="store_true",
                    help="take rates and the retrain/diagnostics hours from the finished wave-0b pod")
    ap.add_argument("--retrain-h", type=float, default=rules.SPEND_UPPER_S["retrain"] / 3600,
                    help="the wave-0b retrain hours without --w0b (default: the frozen spend upper, 0.15)")
    ap.add_argument("--diagnostics-h", type=float, default=rules.SPEND_UPPER_S["diagnostics"] / 3600,
                    help="the wave-0b diagnostics hours without --w0b (default: the frozen spend upper, 2.0)")
    ap.add_argument("--arm-min", type=float, help="override the measured per-arm minutes")
    ap.add_argument("--overhead-min", type=float, help="override the measured pod overhead minutes")
    ap.add_argument("--price", type=float, help="override the measured $/h (e.g. the A100 price read before wave 1)")
    ap.add_argument("--balance-usd", type=float, help="override the balance (default: account-latest.json)")
    ap.add_argument("--topup-usd", type=float, default=0.0, help="a top-up still to land before wave 1 (default 0)")
    ap.add_argument("--hours-to-wave1", type=float, default=24.0,
                    help="idle hours from the balance reading to the wave-1 launch (default 24)")
    ap.add_argument("--other-spend-usd", type=float, default=0.0,
                    help="other spend from the same balance before wave 1 (fiction pods, judge pods, stage-1 pods)")
    ap.add_argument("--out", help="also write the report to this file")
    args = ap.parse_args(argv)

    plan = load(KIT / "plan.json")
    frozen = {"pod_overhead_min": rules.POD_OVERHEAD_S / 60, "arm_min": rules.SPEND_UPPER_S["arm"] / 60,
              "rate_usd_per_h": rules.RATE_USD, "retrain_h": rules.SPEND_UPPER_S["retrain"] / 3600,
              "diagnostics_h": rules.SPEND_UPPER_S["diagnostics"] / 3600,
              "planning_price_usd_per_h": rules.PLANNING_PRICE_USD, "reserve_usd": rules.RESERVE_USD,
              "contingency_factor": rules.CONTINGENCY_FACTOR, "max_arms_per_pod": rules.MAX_ARMS_PER_POD,
              "granite_on_pod": rules.GRANITE_ON_POD,
              "source": "tmp/gate-b-olmo/gateb_rules.py:33, :42-52, :65, :67 (DRAFT §9: 52 min per arm, 42 min "
                        "per pod, $1.79/h; retrain 0.15 h, diagnostics 2.0 h)"}

    pods = {name: host_state(name, h) for name, h in plan["hosts"].items() if h["wave"] in PRE_WAVE1}
    finished_0b = [p for p in pods.values() if p["wave"] == "0b" and p["state"] == "finished"
                   and all(j["status"] == "complete" for j in p["jobs"])]
    if args.w0b and not finished_0b:
        print(json.dumps({"error": "no wave-0b host has finished and been pulled with complete jobs",
                          "wave0b_hosts": {h: p["state"] for h, p in pods.items() if p["wave"] == "0b"},
                          "hint": "run without --w0b until then"}), file=sys.stderr)
        return 2
    rate_waves = ("anchor", "0a", "0b") if args.w0b else ("anchor", "0a")
    rate_pods = {h: p for h, p in pods.items() if p["state"] == "finished" and p["wave"] in rate_waves}

    arms = [(h, j) for h, p in rate_pods.items() for j in p["jobs"] if j["kind"] == "arm" and j["status"] == "complete"]
    arm_host, arm_job = max(arms, key=lambda hj: hj[1]["slot_s"])
    oh_host = max(rate_pods, key=lambda h: rate_pods[h]["overhead_s"])
    priced = {h: p["price_usd_per_h"] for h, p in pods.items() if "price_usd_per_h" in p}
    measured = {
        "arm_min": {"value": args.arm_min if args.arm_min is not None else r(arm_job["slot_s"] / 60, 3),
                    "override": args.arm_min is not None,
                    "rule": "max over the completed arm jobs of the job slot (the upper of the measured range, as the "
                            "frozen 52 min is the upper of Gate A's 34-52 min)",
                    "from": f"{arm_host} job {arm_job['index']} (seed {arm_job['seed']})",
                    "per_arm_slot_min": {f"{h} job {j['index']} seed {j['seed']}": j["slot_min"] for h, j in arms},
                    "per_arm_process_min": {f"{h} job {j['index']}": j["process_elapsed_min"] for h, j in arms},
                    "n": len(arms), "source": arm_job["source"]},
        "pod_overhead_min": {"value": args.overhead_min if args.overhead_min is not None
                             else r(rate_pods[oh_host]["overhead_s"] / 60, 3),
                             "override": args.overhead_min is not None,
                             "rule": "max over the finished pods of (billed time - the job slots)", "from": oh_host,
                             "per_pod_min": {h: p["overhead_min"] for h, p in rate_pods.items()},
                             "per_pod_setup_min": {h: p["setup_min"] for h, p in rate_pods.items()},
                             "per_pod_finish_min": {h: p["finish_min"] for h, p in rate_pods.items()},
                             "n": len(rate_pods)},
        "rate_usd_per_h": {"value": args.price if args.price is not None else max(priced.values()),
                           "override": args.price is not None,
                           "rule": "max costPerHr over every created pre-wave-1 pod", "per_pod": priced,
                           "source": "hosts/<h>/pod.json costPerHr (the API's price at create)"},
    }
    if args.w0b:
        w = max(finished_0b, key=lambda p: p["created_utc"])
        kinds = {j["kind"]: j for j in w["jobs"]}
        for kind in ("retrain", "diagnostics"):
            measured[f"{kind}_h"] = {"value": r(kinds[kind]["slot_s"] / 3600), "from": f"{w['host']} job "
                                     f"{kinds[kind]['index']}", "source": kinds[kind]["source"]}
    else:
        for kind, value in (("retrain", args.retrain_h), ("diagnostics", args.diagnostics_h)):
            measured[f"{kind}_h"] = {"value": value, "from": "argument (no wave-0b pod has finished)",
                                     "is_frozen_upper": value == frozen[f"{kind}_h"],
                                     "enters": "the wave-0b pod's spend only (no wave-0 job is in the wave-1 need)"}

    oh_s, arm_s, rate = (measured["pod_overhead_min"]["value"] * 60, measured["arm_min"]["value"] * 60,
                         measured["rate_usd_per_h"]["value"])
    with_frozen = need_at(plan, rules.POD_OVERHEAD_S, rules.SPEND_UPPER_S["arm"], rules.RATE_USD)
    with_measured = need_at(plan, oh_s, arm_s, rate)
    conservative = need_at(plan, max(oh_s, rules.POD_OVERHEAD_S), max(arm_s, rules.SPEND_UPPER_S["arm"]),
                           max(rate, rules.RATE_USD))
    reproduces = all(with_frozen[k] == v for k, v in DRAFT_FIGURES.items())

    # ----- the balance at the wave-1 launch -----
    account_path = KIT / "account-latest.json"
    account = load(account_path)
    balance = args.balance_usd if args.balance_usd is not None else account["myself"]["clientBalance"]
    reading = t(account["utc"])
    job_h = {"arm": arm_s / 3600, "retrain": measured["retrain_h"]["value"],
             "diagnostics": measured["diagnostics_h"]["value"], "anchor": rules.SPEND_UPPER_S["anchor"] / 3600}
    spend_rows, charged, charged_cap, new_volumes = [], 0.0, 0.0, 0
    for h, p in pods.items():
        if p["state"] in ("planned", "running"):
            todo = [k for k, s in zip(p["jobs_planned"], p["job_statuses"]) if s != "complete"]
            price = p.get("price_usd_per_h", rate)
            spend = min(p["cap_h"], oh_s / 3600 + sum(job_h[k] for k in todo)) * price
            out, basis = False, "projected: (measured overhead + its jobs' hours) x price, at most its cap"
        else:
            spend = p["cost_usd_at_pod_price"]
            out, basis = t(p["stop_confirmed_utc"]) <= reading, "records: billed hours x costPerHr"
        cap_bound = p["cap_h"] * p.get("price_usd_per_h", rate)
        charged += 0.0 if out else spend
        charged_cap += 0.0 if out else (cap_bound if p["state"] in ("planned", "running") else spend)
        new_volumes += 0 if out else 1
        spend_rows.append({"host": h, "wave": p["wave"], "state": p["state"], "spend_usd": r(spend), "basis": basis,
                           "in_balance_reading": out, "cap_bound_usd": r(cap_bound)})
    idle_rate = account["myself"]["currentSpendPerHr"] + new_volumes * POD_VOLUME_GB * VOLUME_USD_PER_GB_H
    idle = idle_rate * args.hours_to_wave1
    projected = balance + args.topup_usd - charged - idle - args.other_spend_usd
    projected_caps = balance + args.topup_usd - charged_cap - idle - args.other_spend_usd
    allowances = sum(ALLOWANCES.values())

    def required(need: dict) -> float:
        return need["need_usd"] + allowances

    def fits_at(need: dict, at: float = projected) -> bool:
        return at >= required(need) - 1e-9

    slack = projected - required(with_measured)
    breakeven_arm = bisect(lambda m: not fits_at(need_at(plan, oh_s, m * 60, rate)), arm_s / 60, 600.0)
    breakeven_price = bisect(lambda p: not fits_at(need_at(plan, oh_s, arm_s, p)), rate, 20.0)
    breakeven_overhead = bisect(lambda m: not fits_at(need_at(plan, m * 60, arm_s, rate)), oh_s / 60, 600.0)

    report = {
        "generated_utc": iso(dt.datetime.now(dt.timezone.utc)),
        "mode": "w0b" if args.w0b else "pre-w0b (wave-0b retrain and diagnostics at the arguments)",
        "script": rel(pathlib.Path(__file__)),
        "inputs_sha256": {rel(p): sha(p) for p in (KIT / "gateb_rules.py", KIT / "plan_tool.py", KIT / "plan.json",
                                                    KIT / "budget-checks.jsonl", account_path, DRAFT)},
        "frozen_rates": frozen,
        "measured_rates": measured,
        "pods": pods,
        "account_cross_check": account_cross_check(pods),
        "need": {
            "formula": "plan_tool.worst_path_need (tmp/gate-b-olmo/plan_tool.py:487-514) -> "
                       "gateb_rules.funding_need_usd (gateb_rules.py:293-306): base = max over the launches from "
                       "wave 1 on of (upper spend of the earlier launches + $6 + $1.85 x this launch's summed caps), "
                       "rounded to the cent; need = round(1.25 x base); contingency = need - base. Kit pod spend = "
                       "(overhead + n x arm) x rate (gateb_rules.py:247-249); Granite spend = cap x rate (:281-285). "
                       "Measured: only the spend constants are swapped; caps and guard terms are the kit's.",
            "frozen": with_frozen,
            "frozen_reproduces_draft": reproduces,
            "draft_figures": DRAFT_FIGURES,
            "measured": with_measured,
            "conservative_max_of_measured_and_frozen": conservative,
        },
        "allowances": {**ALLOWANCES, "total_usd": r(allowances, 2),
                       "source": "research/FOCUS.md:106 (2026-10-10T11:14 UTC, the lead's decisions (1), (2), (4)); "
                                 "free balance on top of the need",
                       "storage_hours_covered_at_current_idle_rate": r(ALLOWANCES["storage_usd"] / idle_rate, 1)},
        "balance": {
            "usd": balance, "utc": account["utc"], "override": args.balance_usd is not None,
            "source": f"{rel(account_path)} myself.clientBalance",
            "idle_spend_per_h": account["myself"]["currentSpendPerHr"],
            "pre_wave1_spend_after_reading": spend_rows,
            "pre_wave1_charged_usd": r(charged),
            "idle_to_wave1": {"rate_usd_per_h": r(idle_rate, 4), "hours": args.hours_to_wave1, "usd": r(idle),
                              "note": "the account's idle rate + 20 GB for each pre-wave-1 pod not yet stopped at "
                                      "the reading"},
            "topup_usd": args.topup_usd, "other_spend_usd": args.other_spend_usd,
            "projected_at_wave1_usd": r(projected, 2),
            "projected_at_wave1_if_pending_pods_bill_full_cap_usd": r(projected_caps, 2),
        },
        "required_at_wave1_usd": {"measured": r(required(with_measured), 2), "frozen": r(required(with_frozen), 2),
                                  "conservative": r(required(conservative), 2),
                                  "rule": "need + storage + Granite re-launch + HarmBench re-launch allowances"},
        "fits": fits_at(with_measured),
        "fits_detail": {
            "measured": fits_at(with_measured), "frozen": fits_at(with_frozen),
            "conservative": fits_at(conservative),
            "kit_init_wave1_check_passes": projected >= with_frozen["need_usd"],
            "kit_check_note": "init-wave 1 refuses unless the balance >= the need at the kit's own (frozen) "
                              "constants (plan_tool.py:636-643); the allowances are outside that check",
            "measured_if_pending_pods_bill_full_cap": fits_at(with_measured, projected_caps),
            "slack_usd": r(slack, 2),
            "slack_idle_hours_at_current_rate": r(slack / idle_rate, 1) if slack > 0 else 0.0,
            "breakeven_arm_min": r(breakeven_arm, 2) if breakeven_arm is not None else "> 600",
            "breakeven_price_usd_per_h": r(breakeven_price, 3) if breakeven_price is not None else "> 20",
            "breakeven_pod_overhead_min": r(breakeven_overhead, 2) if breakeven_overhead is not None else "> 600",
            "breakeven_note": "the per-arm minutes, $/h or pod-overhead minutes at which 'fits' turns false, the "
                              "other measured rates held; money only (arms or setups that long also risk deferral "
                              "at the kit's caps); the price break-even keeps the guard's $1.85 planning price",
        },
        "user_rule": "FOCUS 2026-10-09T19:37 UTC item (2): continue past the re-costing stop without asking only "
                     "if the noise gate passed and the worst path at measured rates fits the balance plus the "
                     "top-up; otherwise stop and ask. 'fits' is that money test only.",
    }
    text = json.dumps(report, indent=1)
    print(text)
    if args.out:
        pathlib.Path(args.out).write_text(text + "\n")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
