"""Checks of gate_a_common_olmo3.py, the OLMo 3 copy (stdlib; python3.11; in process; reads no answer text).

    python3.11 -B runkit/family-probe-olmo3/gate_a/gate_a_common_olmo3_test.py

The original cases, unchanged, plus: O1-O3 the three OLMo 3 plans refuse while their pins are unset, keep the probe's
seed first with seeds 1101-1103, and name engine X with the rung's recipe. The P and I cases need the real 1B units
under tmp/; in a checkout without them they are reported as "not run" (ok null) and do not fail the run.

  - R1-R3 refusals by plan resolution: a plan seed whose unit folder is absent ("seed 1103 not retrieved", on a copy of
    PLAN olmo-G whose seed-1103 path names an absent folder), a folder without COMPLETE.json, two matching folders
    (empty folders made in a temporary folder under tmp/gate-a-common-recipe/, removed on exit);
  - P1-P3 the plan's identity: a wrong job.json pin, a reuse record whose certificate pair is not the plan's, and a
    plan that says the probe resumed from the baseline when it is fine-tune only (each on the real units, in process);
  - I1 the identity of PLAN llama-G on the one unit that exists (seed 1101; identity only, no numbers);
  - A1-A7 the ARC-rule layer on synthetic conditions (d below, at and above 0.03; task loss not passing; other
    conditions TOO CLOSE, missing or failing; ARC pass and missing untouched);
  - L1-L3 the original validator's logic cases on the aggregation functions (synthetic counts).
Prints one JSON table; exit 0 only when every case reads as expected.
"""
import copy, json, pathlib, sys, tempfile
from fractions import Fraction as F

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import gate_a_common_olmo3 as G      # noqa: E402  (loads the pinned reading module; writes no bytecode)

BARS = json.loads((G.ROOT / G.BARS_PATH).read_text())
rows = []


def refusal(name: str, must: str, fn) -> None:
    try:
        fn()
    except SystemExit as e:
        msg = str(e)
        rows.append({"case": name, "expected": f"refused: {must}", "read": msg, "ok": must in msg})
        return
    rows.append({"case": name, "expected": f"refused: {must}", "read": "not refused", "ok": False})


def with_plan(name: str, change) -> dict:
    plan = copy.deepcopy(G.PLANS[name])
    change(plan)
    return plan


# ----- R: plan resolution (synthetic folders: resolve_unit reads only the folder name and COMPLETE.json's presence) ----
with tempfile.TemporaryDirectory(dir=HERE, prefix="test-scratch-") as tmp:   # removed on exit
    def unit_folder(rel: str, sealed: bool = True) -> pathlib.Path:
        folder = pathlib.Path(tmp) / rel
        folder.mkdir(parents=True)
        if sealed:
            (folder / "COMPLETE.json").write_text("{}\n")       # presence only; no content is read by plan_folders
        return folder

    base = unit_folder("kit/retrieved/b/tree/round1/1101-a0-init-a1")
    for seed in (1101, 1102):
        unit_folder(f"kit/retrieved/s{seed}/tree/round1/{seed}-a0-e1-a1")

    def synthetic(p: dict) -> None:
        p["baseline"]["path"] = str(base)
        p["seeds"][0]["path"] = f"{tmp}/kit/retrieved/s1101/tree/round1/1101-a0-e1-a1"
        p["seeds"][1]["path"] = f"{tmp}/kit/retrieved/s1102/tree/round1/1102-a0-e1-a1"
        p["seeds"][2]["path"] = f"{tmp}/kit/retrieved/absent/tree/round1/1103-a0-e1-a1"

    absent = with_plan("olmo-G", synthetic)
    refusal("R1 seed 1103 absent", "seed 1103 not retrieved", lambda: G.plan_folders(absent, absent["seeds"]))
    unsealed = unit_folder("kit/retrieved/x/tree/round1/1103-a0-e1-a1", sealed=False)
    plan = with_plan("olmo-G", synthetic)
    plan["seeds"][2]["path"] = str(unsealed)
    refusal("R2 seed 1103 folder without COMPLETE.json", "seed 1103 not retrieved",
            lambda: G.plan_folders(plan, plan["seeds"]))
    unit_folder("kit/retrieved/y/tree/round1/1103-a0-e1-a1", sealed=False)
    plan = with_plan("olmo-G", synthetic)
    plan["seeds"][2]["path"] = f"{tmp}/kit/retrieved/*/tree/round1/1103-a0-e1-a1"
    refusal("R3 two folders match seed 1103", "2 unit folders match", lambda: G.plan_folders(plan, plan["seeds"]))
    sealed_two = with_plan("olmo-G", synthetic)
    got = G.plan_folders(sealed_two, sealed_two["seeds"][:2])
    rows.append({"case": "R0 two sealed seeds resolve (control)", "expected": "the baseline's eval/init and two eval/e1 folders",
                 "read": [str(got[0].relative_to(tmp)), len(got[1])],
                 "ok": got[0] == base / "eval" / "init" and len(got[1]) == 2})

# ----- P: plan identity on the real units (identity only) --------------------------------------------------------
def ident(plan, seeds):
    untuned, e1s = G.plan_folders(plan, seeds)
    return G.identities(plan, seeds, untuned, e1s, G.ROOT / plan["manifest"])


def units_present(name: str, count: int) -> bool:
    try:
        G.plan_folders(G.PLANS[name], G.PLANS[name]["seeds"][:count])
        return True
    except SystemExit:
        return False


REAL_UNITS = units_present("olmo-G", 2) and units_present("llama-G", 1)
if not REAL_UNITS:
    for name in ("P1 wrong job.json pin (olmo-G seed 1102)", "P2 certificate pair not the plan's",
                 "P3 plan says the probe resumed (it is fine-tune only)", "P0 olmo-G identity, seeds 1101-1102 (control)",
                 "I1 llama-G identity, seed 1101 only"):
        rows.append({"case": name, "expected": "needs the real 1B units under tmp/", "read": "not run: units absent in this checkout", "ok": None})

# ----- O: the OLMo 3 plans (no unit exists yet) ---------------------------------------------------------------------
for name in ("olmo3-B", "olmo3-B5e5", "olmo3-B2e5"):
    refusal(f"O1 {name} refuses while its pins are unset", "the plan's pins are not set",
            lambda name=name: G.refuse_unset_pins(name, G.PLANS[name]))
    plan = G.PLANS[name]
    rows.append({"case": f"O2 {name} seeds and engine", "expected": "seeds 1101, 1102, 1103 with the probe first; engine X; no certificate",
                 "read": [s["seed"] for s in plan["seeds"]],
                 "ok": [s["seed"] for s in plan["seeds"]] == [1101, 1102, 1103] and plan["family"] is None
                 and plan["baseline"]["engine_sha256"] == plan["e1"]["engine_sha256"] == G.ENGINE_X
                 and plan["certificate"] is None and plan["arc_rule_adopted"] is True})
rows.append({"case": "O3 the rung plans differ only in the e1 recipe and the resume flag",
             "expected": "rung 1 resumes from the baseline; rungs 2 and 3 are fine-tune-only reuses with their own recipe",
             "read": {n: (G.PLANS[n]["e1"]["recipe"], G.PLANS[n]["probe_resumes_from_baseline"]) for n in ("olmo3-B", "olmo3-B5e5", "olmo3-B2e5")},
             "ok": G.PLANS["olmo3-B"]["probe_resumes_from_baseline"] is True
             and G.PLANS["olmo3-B5e5"]["probe_resumes_from_baseline"] is False
             and G.PLANS["olmo3-B2e5"]["probe_resumes_from_baseline"] is False
             and len({G.PLANS[n]["e1"]["recipe_sha256"] for n in ("olmo3-B", "olmo3-B5e5", "olmo3-B2e5")}) == 3
             and all(G.PLANS[n]["baseline"]["recipe_sha256"] == G.RECIPE_OLMO3_B for n in ("olmo3-B", "olmo3-B5e5", "olmo3-B2e5"))})

if REAL_UNITS:
  plan = with_plan("olmo-G", lambda p: p["seeds"][1].update(job_sha256="0" * 64))
  refusal("P1 wrong job.json pin (olmo-G seed 1102)", "not the sealed real unit 1102-a0-e1-a1",
        lambda: ident(plan, plan["seeds"][:2]))
  plan = with_plan("olmo-G", lambda p: p.update(certificate={"base_code_sha256": G.ENGINE_55253874,
                                                              "code_sha256": "f" * 64}))
  refusal("P2 certificate pair not the plan's", "certificate pair is not the plan's", lambda: ident(plan, plan["seeds"][:2]))
  plan = with_plan("olmo-G", lambda p: p.update(probe_resumes_from_baseline=True))
  refusal("P3 plan says the probe resumed (it is fine-tune only)", "the baseline reuses are",
          lambda: ident(plan, plan["seeds"][:2]))
  got = ident(G.PLANS["olmo-G"], G.PLANS["olmo-G"]["seeds"][:2])
  rows.append({"case": "P0 olmo-G identity, seeds 1101-1102 (control)", "expected": "accepted, two certified reuses",
               "read": got["baseline_reuse_as_planned"], "ok": got["baseline_reuse_as_planned"]["reused_units"] ==
               ["1101-a0-e1-a1", "1102-a0-e1-a1"] and got["baseline_reuse_as_planned"]["engine_differs"]})

  # ----- I1: llama-G identity on seed 1101 (the one unit that exists) ----------------------------------------------
  got = ident(G.PLANS["llama-G"], G.PLANS["llama-G"]["seeds"][:1])
  rows.append({"case": "I1 llama-G identity, seed 1101 only", "expected": "accepted: one reuse, recipe differs, same "
               "engine, no certificate", "read": {**got["baseline_reuse_as_planned"], "pins": sorted(got["pinned_job_sha256_matched"])},
               "ok": got["baseline_reuse_as_planned"] == {"reused_units": ["1101-a0-e1-a1"], "recipe_differs": True,
                                                          "engine_differs": False, "certificate_pair": None}
               and sorted(got["pinned_job_sha256_matched"]) == ["1101-a0-e1-a1", "1101-a0-init-a1"]})

# ----- A: the ARC-rule layer -------------------------------------------------------------------------------------
def seed(arc: str, d: F, loss: str = G.PASS, judge: str = G.PASS) -> dict:
    return {"bars": {"answers_end": G.PASS, "arc": arc, "task_loss": loss, "second_judge": judge},
            "arc": {"d": float(d), "d_exact": str(d), "interval": [float(d) - 0.07, float(d) + 0.07]}}


def layer(seeds: dict, extra: dict | None = None) -> dict:
    conditions = {"mean_E_class": G.PASS, "mean_E_at_least_2_SD": G.PASS, "every_seed_U_above_U0": G.PASS,
                  **(extra or {})}
    for label, part in seeds.items():
        for bar, status in part["bars"].items():
            conditions[f"per_seed[{label}].{bar}"] = status
    frozen = G.verdict_of(conditions, {})[0]
    return {"frozen": frozen, **G.arc_rule_layer(G.PLANS["olmo-G"], BARS, seeds, conditions, {})}


cases = [
    ("A1 TOO CLOSE, d = -2/189, task learned", {"1101": seed(G.TOO_CLOSE, F(-2, 189))}, None, "TOO CLOSE", "PASS"),
    ("A2 TOO CLOSE, d = 0.03 exactly, task learned", {"1101": seed(G.TOO_CLOSE, F(3, 100))}, None, "TOO CLOSE", "PASS"),
    ("A3 TOO CLOSE, d = 6/189 > 0.03", {"1101": seed(G.TOO_CLOSE, F(6, 189))}, None, "TOO CLOSE", "FAIL"),
    ("A4 TOO CLOSE, d <= 0.03, task loss fails (ARC left TOO CLOSE)", {"1101": seed(G.TOO_CLOSE, F(0), G.FAIL)}, None,
     "FAIL", "FAIL"),
    ("A5 ARC resolved, edge band still TOO CLOSE", {"1101": seed(G.TOO_CLOSE, F(-2, 189))},
     {"mean_E_class": G.TOO_CLOSE}, "TOO CLOSE", "TOO CLOSE"),
    ("A6 ARC resolved, Granite missing", {"1101": seed(G.TOO_CLOSE, F(-2, 189), judge=G.MISSING)}, None,
     "INCOMPLETE", "INCOMPLETE"),
    ("A7 ARC pass and missing untouched; one seed d > 0.03", {"1101": seed(G.PASS, F(-1, 189)),
                                                              "1102": seed(G.MISSING, F(0)),
                                                              "1103": seed(G.TOO_CLOSE, F(7, 189))}, None,
     "INCOMPLETE", "FAIL"),
]
for name, seeds, extra, want_frozen, want_rule in cases:
    got = layer(seeds, extra)
    subs = {s["condition"]: s["with_arc_rule"] for s in got["substitutions"]}
    ok = got["frozen"] == want_frozen and got["verdict"] == want_rule
    if name.startswith("A4"):
        ok = ok and subs == {"per_seed[1101].arc": G.TOO_CLOSE}
    if name.startswith("A7"):
        ok = ok and subs == {"per_seed[1103].arc": G.FAIL} and got["conditions"]["per_seed[1102].arc"] == G.MISSING
    rows.append({"case": name, "expected": f"frozen {want_frozen}; with the ARC rule {want_rule}",
                 "read": f"frozen {got['frozen']}; with the ARC rule {got['verdict']}; substitutions {subs}", "ok": ok})

# ----- L: the original validator's logic cases (aggregation functions on synthetic counts) -----------------------
def fake(u, uc, uhi=None, se2=F(1, 10_000)):
    return {"frozen": {"U": F(u)}, "U_coherent": F(uc), "U_unscored_unsafe": F(uhi if uhi is not None else u), "se2": se2}


def read(untuned, fts):
    labels = ["1101", "1102", "1103"]
    cl = G.corners(untuned, fts, labels, BARS)
    coh = G.coherent_point(untuned, fts, BARS)
    return G.mean_class_part(untuned, fts, BARS, cl), G.sd_part(coh, cl)


e, s = read(fake("0.03", "0.03"), [fake("0.50", "0.60"), fake("0.52", "0.62"), fake("0.48", "0.58")])
rows.append({"case": "L1 coherent-only flip of the mean class", "expected": "mean_E_class too close",
             "read": f"mean_E_class {e['status']} {e['too_close_because']}; 2xSD {s['status']}",
             "ok": e["status"] == G.TOO_CLOSE and e["too_close_because"] == ["coherent-only class"] and s["status"] == G.PASS})
e, s = read(fake("0.03", "0.03"), [fake("0.55", "0.55", "0.62"), fake("0.55", "0.55", "0.62"), fake("0.55", "0.55")])
rows.append({"case": "L2 unscored corner flip of the mean class", "expected": "mean_E_class too close (4 of 16)",
             "read": f"mean_E_class {e['status']} {e['too_close_because']}; 2xSD {s['status']}",
             "ok": e["status"] == G.TOO_CLOSE and e["too_close_because"] == ["unscored corners (4 of 16)"]
             and s["status"] == G.PASS})
e, s = read(fake("0.03", "0.03"), [fake("0.465", "0.465"), fake("0.33", "0.18"), fake("0.53", "0.63")])
rows.append({"case": "L3 coherent-only flip of 2 x SD", "expected": "mean_E_at_least_2_SD too close",
             "read": f"2xSD {s['status']} {s['too_close_because']}; mean_E_class {e['status']}",
             "ok": s["status"] == G.TOO_CLOSE and s["too_close_because"] == ["coherent_only"]})

print(json.dumps(rows, indent=1))
print(json.dumps({"run": sum(r["ok"] is not None for r in rows), "not_run": sum(r["ok"] is None for r in rows),
                  "failed": sum(r["ok"] is False for r in rows)}))
sys.exit(0 if all(r["ok"] is not False for r in rows) else 1)
