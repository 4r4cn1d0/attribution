"""Kit round 32's dry run: block B's group (certify, then block B with its second reference phase) planned IN MEMORY
on a copy of the LIVE plan.json, by THIS tree's kit code pointed at the live kit folder, read only.

    python -B dry_k32.py TREE_KIT LIVE_KIT JOBS_CERTIFY JOBS_B_2PHASE JOBS_B_3SEED JOBS_B_FULL_UNSPLIT SCRATCH OUT.json

Every kit write is refused (gateb_mac.save_plan and operator_action raise, or capture the plan in memory);
plan.json, operator-actions.jsonl and budget-checks.jsonl are hashed before and after. Scratch records (a funding
record, a B10 certification, an SP prefix record, the R_d6/R_d7 sealed-edits record, a not-run decision) are written
only in SCRATCH and injected into the in-memory plan; nothing is recorded in the kit. No file under judges/ is opened:
block A's judge-completion record is taken from plan.json as recorded (judge_record_checked is stubbed for block A
only). Steps after block B's a0 arm pods are simulated in memory: the a0 runs recorded done (synthetic COMPLETE.json
SHA-256 and K6 record digests; a0_fingerprint stubbed), the B10/B11 re-pin (pinned_s1_settings stubbed) and the
re-pack (packed_sealed stubbed). Prints ids, caps, needs, hashes and refusal texts only.
"""
import argparse
import copy
import hashlib
import json
import pathlib
import sys

sys.dont_write_bytecode = True
TREE_KIT, LIVE = pathlib.Path(sys.argv[1]).resolve(), pathlib.Path(sys.argv[2]).resolve()
JC, JB2, JB3, JBFULL = sys.argv[3:7]
SCRATCH, OUT = pathlib.Path(sys.argv[7]), pathlib.Path(sys.argv[8])
MAIN = LIVE.parents[1]
WATCH = [LIVE / "plan.json", LIVE / "operator-actions.jsonl", LIVE / "budget-checks.jsonl"]


def sha(p) -> str | None:
    p = pathlib.Path(p)
    return hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None


def hx(text: str) -> str:
    return hashlib.sha256(text.encode()).hexdigest()


before = {p.name: sha(p) for p in WATCH}
sys.path.insert(0, str(TREE_KIT))
import gateb_mac as mac  # noqa: E402
import stage1_rules as rules  # noqa: E402
import plan_tool as pt  # noqa: E402

assert pathlib.Path(pt.__file__).resolve().parent == TREE_KIT, "the tree's plan_tool must be the one imported"


class Refused(Exception):
    pass


def refuse(*a, **k):
    raise Refused("write refused (dry run)")


SCRATCH.mkdir(parents=True, exist_ok=True)
mac.save_plan, mac.operator_action = refuse, refuse
mac.HERE, mac.ROOT, mac.PLAN = LIVE, MAIN, LIVE / "plan.json"
mac.READING, mac.OPERATOR_LOG = MAIN / "scripts" / "gate_b_reading.py", SCRATCH / "no-operator-log.jsonl"
pt.HERE, pt.ROOT, pt.ENGINE_ROOT = LIVE, MAIN, MAIN
pt.SEAL_OUT = MAIN / pathlib.Path(rules.MAN_PATH).parent
pt.JUDGE_FOLDER, pt.JUDGE_POD_ROOT = LIVE / "judges", MAIN / "tmp" / "judge-pod"
pt.PY = MAIN / "tmp/minimal-experiment-20261002/venv/bin/python"

live = json.loads((LIVE / "plan.json").read_text())
state = {"plan": copy.deepcopy(live)}
out = {"live_plan_sha256": before["plan.json"], "jobs": {name: sha(p) for name, p in
                                                         (("certify", JC), ("B_2phase", JB2), ("B_3seed", JB3),
                                                          ("B_full_unsplit", JBFULL))}}
real_checked = pt.judge_record_checked


def judge_checked(plan, block):
    """Block A's record as plan.json holds it (no judges/ file opened); every other block: the kit's own check."""
    if block == "A":
        e = plan["records"]["judges"]["A"]
        return {"judges": sorted(e["judges"]), "record_sha256": e["sha256"]}
    return real_checked(plan, block)


pt.judge_record_checked = judge_checked


def load_mem():
    return copy.deepcopy(state["plan"])


pt.load = load_mem
mac.load_plan = load_mem


def capture(plan):
    state["captured"] = copy.deepcopy(plan)
    raise Refused("captured")


def call(fn, *a, **k):
    try:
        return {"ok": fn(*a, **k)}
    except SystemExit as exc:
        return {"refused": str(exc)}
    except Refused as exc:
        return {"captured": str(exc)}


def init(block, jobs, funding=None, group=None, dry=True):
    args = argparse.Namespace(block=block, jobs=jobs, funding=funding, dry_run=dry, group_jobs=group)
    mac.save_plan = capture
    state.pop("captured", None)
    r = call(pt.init_block, args)
    mac.save_plan = refuse
    return r


def summary(r):
    if "ok" not in r:
        return r
    o = r["ok"]
    return {k: o.get(k) for k in ("need_usd", "base_need_usd", "contingency_usd", "terms_cents", "group",
                                  "second_phase_launches", "released")} | {
        "pods": [(p["launch"], p["cap_hours"], p["counted"]) for p in o["pods"]]}


def write(name, doc):
    p = SCRATCH / name
    p.write_text(json.dumps(doc, indent=1, sort_keys=True) + "\n")
    return str(p)


# 1. the whole group's need at certify's first init (K4), for the two-phase full scope and the 3-seed draft
full = init("certify", JC, group=[f"B={JB2}"])
out["1_certify_dry_full_scope_2phase"] = summary(full)
out["1_certify_dry_3seed_draft"] = summary(init("certify", JC, group=[f"B={JB3}"]))
out["1_certify_dry_full_scope_unsplit_refused"] = init("certify", JC, group=[f"B={JBFULL}"])
out["1_certify_dry_without_group_jobs_refused"] = init("certify", JC)
need = full["ok"]["need_usd"]

# 2. certify planned in memory on a funding record of exactly the group's need
fund = write("scratch_funding_B.json", {"block": "B", "amount_usd": need, "utc": "2026-10-29T00:00:00Z",
                                        "source": "user RunPod top-up", "user_words": "SCRATCH (dry run only)",
                                        "recorded_by": "dry run"})
low = write("scratch_funding_B_low.json", {"block": "B", "amount_usd": round(need - 0.01, 2),
                                           "utc": "2026-10-29T00:00:00Z", "source": "user RunPod top-up",
                                           "user_words": "SCRATCH (dry run only)", "recorded_by": "dry run"})
out["2_certify_init_one_cent_below_refused"] = init("certify", JC, low, [f"B={JB2}"], dry=False)
r = init("certify", JC, fund, [f"B={JB2}"], dry=False)
P1 = state.get("captured")
out["2_certify_init"] = {"result": "captured" if P1 else r,
                         "hosts": sorted(n for n, h in (P1 or {}).get("hosts", {}).items() if h["block"] == "certify")}

# 3. the records block B needs, in memory only (scratch files): certification (pass), SP prefix, R_d6/R_d7 edits
cert = write("scratch_certification.json", {"kind": "stage1 b10 certification", "pass": True, "host": "cfy-1",
                                             "utc": "2026-10-29T00:00:00Z", "recorded_by": "dry run"})
prefix = write("scratch_prefix.json", {"kind": "stage1 sp prefix pin", "text_sha256": "0" * 64, "source": "SCRATCH",
                                       "utc": "2026-10-29T00:00:00Z", "recorded_by": "dry run"})
rd = json.loads((MAIN / ".ai/inputs/stage1-commitments-20261016/r-draws/r_draws_record.json").read_text())
edits = [{"arm": "R", "draw": f["draw"], "path": ".ai/inputs/stage1-commitments-20261016/r-draws/" + f["file"],
          "sha256": f["sha256"]} for f in rd["files"] if f.get("family") == "R" and f.get("draw") in (6, 7)]
sealed = write("scratch_sealed_edits_R6_R7.json", {"kind": "stage1 sealed edits", "edits": edits})
P1["records"]["certification"] = {"path": cert, "sha256": sha(cert), "pass": True, "host": "cfy-1"}
P1["records"]["prefix"] = {"path": prefix, "sha256": sha(prefix), "text_sha256": "0" * 64, "source": "SCRATCH"}
P1["records"]["sealed"].append({"path": sealed, "sha256": sha(sealed)})
state["plan"] = P1

# 4. block B planned on the same funding record; another record refuses (one funding record, K4)
other = write("scratch_funding_B_other.json", {"block": "B", "amount_usd": 999, "utc": "2026-10-29T00:00:00Z",
                                               "source": "user RunPod top-up", "user_words": "SCRATCH (dry run only)",
                                               "recorded_by": "dry run"})
out["4_B_init_another_funding_record_refused"] = init("B", JB2, other, dry=False)
r = init("B", JB2, fund, dry=False)
P2 = state.get("captured")
out["4_B_init"] = summary(r) if P2 is None else {
    "need_usd": P2["blocks"]["B"]["need"]["need_usd"], "group_need_equals_certify_time": P2["blocks"]["B"]["need"][
        "need_usd"] == need, "launches": P2["blocks"]["B"]["launches"], "released_at_init": P2["blocks"]["B"]["released"]}
b = P2["blocks"]["B"]
out["4_pods"] = {n: {"launch": h["launch"], "cap_hours": h["cap_hours"], "counted": h["counted"],
                     "jobs": [f"{j['kind']}:{j['arm']}:{j['seed']}:{','.join(j.get('points') or [])}" for j in h["jobs"]]}
                 for n, h in sorted({**{n: h for n, h in P2["hosts"].items() if h["block"] == "B"},
                                     **b["pending"]}.items(), key=lambda x: int(x[0].split("-")[1]))}

# 5. releases in memory (the live guard-off record re-hashed from disk: launches go early, the second phase never)
releases = []
state["plan"] = P2
while True:
    k = P2["blocks"]["B"]["released"]
    if k >= len(P2["blocks"]["B"]["launches"]):
        break
    r = call(pt.release_next, P2, "B")
    releases.append({"launch": k, **r})
    if "refused" in r:
        break
out["5_releases_before_the_a0_runs"] = releases
phase = [n for x in P2["blocks"]["B"]["launches"] if x.get("second_phase") for n in x["hosts"]]
out["5_second_phase_hosts"] = phase

# 6. simulated: block B's a0 arm pods done (a0 at 1105-1107 complete, K6 record listed), the other hosts too
a0 = {}
for n, h in P2["hosts"].items():
    if h["block"] != "B":
        continue
    for i, j in enumerate(h["jobs"]):
        if j["kind"] == "a0_arm" and j.get("role") is None:
            j.update(status="complete", unit=f"round1/{j['seed']}-a0-e1-a1", complete_sha256=hx(f"synthetic a0 {j['seed']}"),
                     outputs={f"job-{i}/{rules.A0_FINGERPRINT_RECORD}": hx(f"synthetic record {j['seed']}")})
            a0[j["seed"]] = j["complete_sha256"]
        h["done"] = True
pt.a0_fingerprint = lambda host, index, job: {"e1": hx(f"e1 {job['seed']}"), "q": None}
out["6_after_a0_done_release"] = call(pt.release_next, copy.deepcopy(P2), "B")

# 7. simulated: the B10/B11 re-pin naming these runs and their K6 fingerprints
real_settings = pt.pinned_s1_settings


def repinned(rel):
    if rel == rules.B10_SETTINGS:
        return {"reference_units": {str(s): {"complete_sha256": c, "fingerprint_prefixes": {"e1": hx(f"e1 {s}"), "q": None}}
                                    for s, c in a0.items()}}
    return {"adapter": {"accepted": {str(s): {"fingerprint": hx(f"e1 {s}")} for s in a0}}}


pt.pinned_s1_settings = repinned
out["7_after_repin_release"] = call(pt.release_next, copy.deepcopy(P2), "B")

# 8. simulated: the re-pack (gate_a_complete:1105-1107 at the runs' SHA-256, B10/B11 files at S1_CODE's pins)
real_sealed = pt.packed_sealed
doc = {"files": {**{rel: rules.S1_CODE[rel] for rel in rules.B10_B11_FILES},
                 **{f"inputs/gate_a_complete-{s}/COMPLETE.json": c for s, c in a0.items()}},
       "inputs": {f"gate_a_complete:{s}": f"inputs/gate_a_complete-{s}/COMPLETE.json" for s in a0}}
pt.packed_sealed = lambda engine: (doc, "f" * 64)
P3 = copy.deepcopy(P2)
out["8_after_repack_release"] = call(pt.release_next, P3, "B")
for n in phase:
    if n in P3["hosts"]:
        P3["hosts"][n]["done"] = True
judges = []
while P3["blocks"]["B"]["released"] < len(P3["blocks"]["B"]["launches"]):
    judges.append(call(pt.release_next, P3, "B"))
    if "refused" in judges[-1]:
        break
out["8_then_the_judges"] = {"calls": judges, "launches_released": P3["blocks"]["B"]["released"],
                            "of": len(P3["blocks"]["B"]["launches"])}

# 9. the other route (K2): the second phase decided not run (scratch decision), skipped; then the judges
pt.pinned_s1_settings, pt.packed_sealed = real_settings, real_sealed
P4 = copy.deepcopy(P2)
pend = P4["blocks"]["B"]["pending"]
names = [f"{n}:{i}" for n in phase for i in range(len(pend[n]["jobs"]))]
dec = write("scratch_not_run_phase2.json", {"kind": rules.NOT_RUN_KIND, "block": "B", "jobs": names,
                                            "reason": "SCRATCH (dry run): the re-pin did not land",
                                            "utc": "2026-10-29T00:00:00Z", "recorded_by": "dry run"})
state["plan"] = P4
mac.save_plan = capture
state.pop("captured", None)
out["9_not_run_record"] = call(pt.record_not_run, dec, sha(dec))
mac.save_plan = refuse
P5 = state.get("captured")
if P5 is not None:
    calls = []
    while P5["blocks"]["B"]["released"] < len(P5["blocks"]["B"]["launches"]):
        calls.append(call(pt.release_next, P5, "B"))
        if "refused" in calls[-1]:
            break
    out["9_releases_after_the_decision"] = {"calls": calls, "skipped": P5["blocks"]["B"].get("skipped"),
                                            "launches_released": P5["blocks"]["B"]["released"],
                                            "open_jobs": pt.block_open_jobs(P5, "B")}

after = {p.name: sha(p) for p in WATCH}
out["live_files_before"], out["live_files_after"] = before, after
out["live_files_unchanged"] = before == after
OUT.write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
print(json.dumps({"written": str(OUT), "live_files_unchanged": out["live_files_unchanged"],
                  "group_need_usd": need}))
