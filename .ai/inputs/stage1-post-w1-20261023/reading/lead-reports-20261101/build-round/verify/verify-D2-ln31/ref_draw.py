"""The verifier's own re-implementation of HLC revision 2's draw (4.1, 4.2, 4.4, 8) with the builder's stated readings
(build report section 4), written from the protocol text and reading the synthetic world's RAW files (not the tool's
modules, not hlc_world's specs). It compares the result with a draw the tool wrote.

    python -B ref_draw.py WORLD_DIR SEALED_DIR [STEP]

Synthetic data only. Prints the comparison (counts of synthetic items; no real data exists here)."""

from __future__ import annotations

import hashlib
import importlib.util
import json
import random
import re
import sys
from collections import Counter
from fractions import Fraction
from pathlib import Path

SETTINGS = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-kind-hawking-a6ce04/"
                "ea7b850a-7c12-4652-92a4-7fbe8e247622/scratchpad/builds/ws-d2/scripts/stage1_s1/hlc_draw/settings/"
                "hlc_draw.json")
ARMS = ["a0", "R", "H1", "A1", "L1", "S1", "S3", "S4"]                      # HLC 4.2 draw order
SEEDS = {a: ([1101, 1102, 1103] if a in ("a0", "R") else [1102, 1103, 1104]) for a in ARMS}   # HLC 4.1
HARM_CELLS, BENIGN_CELLS = ["Unsafe", "Controversial", "Safe"], ["Yes", "No"]                 # HLC 4.2 table order
NOT_SCORED = {"control string in guard input; not scored", "guard input over limit; not scored"}


def seed_of(*parts) -> int:                                   # the engine's derive_seed, written again
    return int.from_bytes(hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()[:8], "big")


def jl(path: Path) -> list:
    return [json.loads(x) for x in path.read_text().splitlines() if x.strip()]


def split(n, a_yes, a_no, minimum=2):
    """Closest to proportional (ties to the larger yes count), keeping min(2, A) of each when both can be kept."""
    total = min(n, a_yes + a_no)
    if total == 0:
        return 0, 0
    target = Fraction(total * a_yes, a_yes + a_no)
    pairs = [(y, total - y) for y in range(total + 1) if y <= a_yes and total - y <= a_no]
    keep = [p for p in pairs if p[0] >= min(minimum, a_yes) and p[1] >= min(minimum, a_no)]
    return min(keep or pairs, key=lambda p: (abs(p[0] - target), -p[0]))


def main(world: Path, sealed: Path, step: str = "0") -> int:
    cfg = json.loads(SETTINGS.read_text())
    sizes = cfg["sizes"]["steps"][step]
    kit, repo = world / "kit", world / "repo"
    spec = importlib.util.spec_from_file_location("synthetic_rules", repo / "rules.py")
    rules = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rules)
    pins = {}
    for p in rules.REJUDGED_PINS["A"]:
        name = p["name"].split(" ")[0]
        pins[("theta0", None) if name == "theta0" else (name, p["seed"])] = p
    plan = json.loads((kit / "plan.json").read_text())
    kit_units = {}
    for host, h in sorted(plan["hosts"].items()):
        if h.get("block") != "A":
            continue
        for job in h["jobs"]:
            if job.get("status") == "complete" and job.get("kind") in ("arm", "a0_arm"):
                kit_units.setdefault((job["arm"], job["seed"]), []).append(
                    (kit / "retrieved" / host / "tree" / job["unit"], job["complete_sha256"]))
    units = []                                                 # (label, arm, seed, folder, target, complete)
    for arm in ARMS:
        for s in SEEDS[arm]:
            if arm in ("a0", "R") and s in (1101, 1102, 1103):
                p = pins[(arm, s)]
                units.append((f"{arm} {s}", arm, s, repo / p["path"], "e1", p["complete_sha256"]))
            else:
                (folder, c), = kit_units[(arm, s)]
                units.append((f"{arm} {s}", arm, s, folder, "e1", c))
    p = pins[("theta0", None)]
    units.append(("theta0", "theta0", None, repo / p["path"], "init", p["complete_sha256"]))
    # HarmBench labels from block A's pod cache
    hb = {}
    for rec in jl(kit / "judges" / "A" / "pods" / "s1a-hb-1" / "fetched" / "out" / "harmbench-pod.jsonl"):
        if rec["mode"] == "sampled":
            hb[(rec["complete_sha256"], rec["prompt_id"], rec["sample_index"])] = rec["label"]
    # bank and auditor
    bank_rows = jl(world / "bank" / "banks" / "dev.jsonl")
    text = {r["prompt_id"]: r["prompt"] for r in bank_rows if r["kind"] in ("harm", "overrefusal")}
    order_ids = sorted(r["prompt_id"] for r in bank_rows if r["kind"] == "harm") + \
        sorted(r["prompt_id"] for r in bank_rows if r["kind"] == "overrefusal")
    aud = json.loads((world / "bank" / "auditor" / "construction.json").read_text())["prompts"]
    # answers: (label, block, pid, k) -> dict
    answers = {}
    for label, arm, s, folder, target, c in units:
        ev = folder / "eval" / target
        for a, g in zip(jl(ev / "samples.jsonl"), jl(ev / "guard_samples.jsonl")):
            assert (a["prompt_id"], a["sample_index"]) == (g["prompt_id"], g["sample_index"])
            answers[(label, "harm", a["prompt_id"], a["sample_index"])] = {
                "valid": g["valid"], "safety": g["safety"], "refusal": g["refusal"], "cats": g["categories"] or [],
                "reason": g["reason"], "hb": hb[(c, a["prompt_id"], a["sample_index"])], "complete": c,
                "tokens": a["output_tokens"], "capped": a["stop_reason"] == "max_new_tokens"}
        gens = {r["prompt_id"]: r for r in jl(ev / "generations.jsonl") if r["kind"] == "overrefusal"}
        for g in jl(ev / "guard.jsonl"):
            if g["kind"] != "overrefusal":
                continue
            answers[(label, "benign", g["prompt_id"], None)] = {
                "valid": g["valid"], "safety": g["safety"], "refusal": g["refusal"], "cats": g["categories"] or [],
                "reason": g["reason"], "hb": None, "complete": c, "tokens": gens[g["prompt_id"]]["output_tokens"],
                "capped": gens[g["prompt_id"]]["stop_reason"] == "max_new_tokens"}
    # exclusions: 9 Oct key
    key9 = json.loads((world / "oct9" / "key.json").read_text())
    by_path = {str(u[3].relative_to(repo)): u for u in units if u[3].is_relative_to(repo)}
    uid_unit = {uid: by_path[info["unit_dir"]] for uid, info in key9["units"].items() if info["unit_dir"] in by_path}
    oct9 = {(uid_unit[i["unit"]][0], i["prompt_id"], i["sample_index"]) for i in key9["items"] if i["unit"] in uid_unit}
    # minors (HLC 8)
    m = cfg["exclusions"]["minors"]
    norm = lambda t: " ".join(t.lower().split())                       # noqa: E731
    cats_of = {}
    for (label, block, pid, k), a in answers.items():
        cats_of.setdefault(pid, set()).update(c.lower() for c in a["cats"])
    rule_a, rule_b = [], []
    for pid in order_ids:
        e = aud[pid]
        if e["source"] == "simplesafetytests" and norm(e["category"] or "") == "child abuse":
            rule_a.append(pid)
            continue
        t = norm(text[pid])
        hit = any(re.search(r"(?<![a-z0-9])" + re.escape(norm(w)) + r"(?![a-z0-9])", t) for w in m["terms"]) or \
            any(re.search(p, t) for p in m["age_patterns"])
        if hit and ("sexual" in norm(e["category"] or "") or any("sexual" in c for c in cats_of.get(pid, ()))):
            rule_b.append(pid)
    minors = set(rule_a) | set(rule_b)
    reason = {}
    for key, a in answers.items():
        label, block, pid, k = key
        if block == "harm" and (label, pid, k) in oct9:
            reason[key] = "oct9"
        elif pid in minors:
            reason[key] = "minors"
        elif not a["valid"]:
            reason[key] = "unscored" if a["reason"] in NOT_SCORED else "no_label"
    # the walk
    items, used = [], {}
    for label, arm, s, folder, target, c in units:
        mine = used.setdefault(arm, set())
        quota = dict(sizes["theta0"]) if s is None else {cl: q[SEEDS[arm].index(s)]
                                                         for cl, q in sizes["per_seed"].items()}
        for block, cells, field in (("harm", HARM_CELLS, "safety"), ("benign", BENIGN_CELLS, "refusal")):
            carry = 0
            for cell in cells:
                n = quota[cell] + carry
                pool = sorted((pid, -1 if k is None else k) for (lb, bl, pid, k), a in answers.items()
                              if lb == label and bl == block and (lb, bl, pid, k) not in reason and a[field] == cell)
                part = f"theta0/{block}/{cell}" if s is None else f"{arm}/{s}/{block}/{cell}"
                random.Random(seed_of(cfg["seed_tags"]["freeze_date"], "hlc-v1", part)).shuffle(pool)

                def key_of(x):
                    return (label, block, x[0], None if x[1] == -1 else x[1])
                if block == "harm" and cell == "Unsafe":
                    sub = {x: ("yes" if answers[key_of(x)]["hb"] == "yes" else "no") for x in pool}
                    free = Counter(sub[x] for x in pool if x[0] not in mine)
                    y, mm = split(n, free["yes"], free["no"])
                    room = {"yes": y, "no": mm}
                else:
                    sub = {x: "all" for x in pool}
                    room = {"all": n}
                taken, got = [], Counter()
                for x in pool:
                    if len(taken) < n and x[0] not in mine and got[sub[x]] < room[sub[x]]:
                        taken.append(x)
                        mine.add(x[0])
                        got[sub[x]] += 1
                for x in pool:
                    if len(taken) < n and x[0] not in mine:
                        taken.append(x)
                        mine.add(x[0])
                for x in taken:
                    items.append((label, block, cell, x[0], None if x[1] == -1 else x[1]))
                carry = n - len(taken)
    ids = []
    for (label, block, cell, pid, k) in items:
        c = answers[(label, block, pid, k)]["complete"]
        ids.append(("h" if block == "harm" else "b") + hashlib.sha256(
            f"{c}|{pid}|{'greedy' if k is None else k}".encode()).hexdigest()[:16])
    harm_ids = sorted(i for i, it in zip(ids, items) if it[1] == "harm")
    reps = random.Random(seed_of(cfg["seed_tags"]["freeze_date"], "hlc-v1-repeats", "harm")).sample(
        harm_ids, min(sizes["repeats"], len(harm_ids)))
    # compare with the tool's key
    key = json.loads((sealed / "hlc_key.json").read_text())
    tool = [(i["unit"], i["block"], i["cell"], i["prompt_id"], i["sample_index"]) for i in key["items"]]
    same_items = tool == items
    same_ids = [i["item"] for i in key["items"]] == ids
    same_reps = key["repeats"] == reps
    w = json.loads((sealed / "hlc_weights.json").read_text())
    same_minors = w["exclusions"]["minors_prompts"] == {"rule_a": rule_a, "rule_b": rule_b}
    per_unit = {}
    for (label, *_rest), r in reason.items():
        per_unit.setdefault(label, Counter())[r] += 1
    same_excl = all(w["exclusions"]["per_unit"][lb][r] == per_unit.get(lb, Counter())[r]
                    for lb in w["exclusions"]["per_unit"] for r in ("oct9", "minors", "unscored", "no_label"))
    fields_ok = all(i["harmbench"] == answers[(i["unit"], i["block"], i["prompt_id"], i["sample_index"])]["hb"]
                    and i["output_tokens"] == answers[(i["unit"], i["block"], i["prompt_id"], i["sample_index"])]["tokens"]
                    and i["capped"] == answers[(i["unit"], i["block"], i["prompt_id"], i["sample_index"])]["capped"]
                    for i in key["items"])
    print(f"step {step}: items {len(items)} (tool {len(tool)}); same items and order {same_items}; same ids {same_ids}; "
          f"same repeats {same_reps}; same minors prompts {same_minors}; same exclusions per unit {same_excl}; "
          f"item fields from the raw files {fields_ok}")
    if not same_items:
        for n, (a, b) in enumerate(zip(tool, items)):
            if a != b:
                print("first difference at", n, a, b)
                break
    return 0 if all((same_items, same_ids, same_reps, same_minors, same_excl, fields_ok)) else 1


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3] if len(sys.argv) > 3 else "0"))
