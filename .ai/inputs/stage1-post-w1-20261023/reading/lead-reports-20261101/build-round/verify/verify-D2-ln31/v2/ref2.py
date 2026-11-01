"""Verifier 2's independent re-implementation of the HLC draw, written from HLC revision 2 (4.1-4.4, 8), the settings'
rule texts and the build report's readings (1-13), reading a synthetic world's raw files directly (no module of the
tool is imported). The selection rule is computed by a different algorithm from the tool's: for each answer in the
sealed order, a tentative take is kept only if a maximum bipartite matching (Kuhn's augmenting paths) between the
still-unmet target slots and the unused prompts of the later answers covers every slot. Then it compares items, cells,
sub-cells, exclusions, minors prompts and repeats with the tool's key and weights files.

    python -B ref2.py ROOT SEALED_DIR [STEP]      exit 0 identical, 1 a difference (printed), 2 usage
"""

from __future__ import annotations

import hashlib
import json
import random
import re
import runpy
import sys
from fractions import Fraction
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2lib  # noqa: E402


def dseed(*parts) -> int:
    return int.from_bytes(hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()[:8], "big")


def jl(path: Path) -> list:
    return [json.loads(x) for x in path.read_bytes().split(b"\n") if x.strip()]


def norm(t: str) -> str:
    return " ".join(str(t).lower().split())


def term_hit(text: str, term: str) -> bool:
    """A term matches where no ASCII letter or digit stands right before or after it (my own scan, no regex)."""
    term = norm(term)
    start = 0
    ok = set("abcdefghijklmnopqrstuvwxyz0123456789")
    while True:
        i = text.find(term, start)
        if i < 0:
            return False
        before = text[i - 1] if i > 0 else ""
        after = text[i + len(term)] if i + len(term) < len(text) else ""
        if before not in ok and after not in ok:
            return True
        start = i + 1


def can_fill(keys: list, sub_of: dict, need: dict, used: set) -> bool:
    """Kuhn's maximum bipartite matching: slots (one per unit of need) against prompts not in ``used``."""
    slots = [s for s, q in sorted(need.items()) for _ in range(q)]
    if not slots:
        return True
    adj = {}
    for k in keys:
        if k[0] in used:
            continue
        adj.setdefault(sub_of[k], set()).add(k[0])
    match_p: dict = {}

    def augment(i, seen):
        for p in sorted(adj.get(slots[i], ())):
            if p in seen:
                continue
            seen.add(p)
            if p not in match_p or augment(match_p[p], seen):
                match_p[p] = i
                return True
        return False

    return all(augment(i, set()) for i in range(len(slots)))


def first_feasible(order: list, sub_of: dict, need: dict, used: set) -> list:
    need = dict(need)
    assert can_fill(order, sub_of, need, used), "targets not feasible at the start"
    taken = []
    for n, k in enumerate(order):
        s = sub_of[k]
        if k[0] in used or need[s] == 0:
            continue
        need[s] -= 1
        if can_fill(order[n + 1:], sub_of, need, used | {k[0]}):
            taken.append(k)
            used.add(k[0])
        else:
            need[s] += 1
    assert all(v == 0 for v in need.values())
    return taken


def split(n, a_yes, a_no, p_yes, p_no, p_all, minimum):
    """The settings' harmbench_split text, re-implemented: total = min(n, P); y = floor(total*A_yes/A + 1/2); moved
    into the interval that keeps y <= P_yes, m <= P_no and each sub-cell at least min(minimum, its P) when that
    interval is not empty, else the interval of the prompt bounds alone."""
    total = min(n, p_all)
    if total == 0:
        return 0, 0
    y0 = (2 * total * a_yes + (a_yes + a_no)) // (2 * (a_yes + a_no))       # floor(x + 1/2), exact
    feasible = [y for y in range(0, total + 1) if y <= p_yes and total - y <= p_no]
    strict = [y for y in feasible if y >= min(minimum, p_yes) and total - y >= min(minimum, p_no)]
    rng = strict or feasible
    y = min(max(y0, min(rng)), max(rng))
    return y, total - y


def population(world: Path, cfg: dict) -> list:
    pins = runpy.run_path(str(world / "repo" / "rules.py"))["REJUDGED_PINS"]["A"]
    by = {}
    for p in pins:
        name = p["name"].split(" ")[0]
        by[(name, None if name == "theta0" else p["seed"])] = p
    plan = json.loads((world / "kit" / "plan.json").read_text())
    jobs = {}
    for host, h in plan["hosts"].items():
        if h["block"] != "A" or h.get("done") is not True:
            continue
        for job in h["jobs"]:
            if job.get("status") == "complete" and job.get("kind") in ("arm", "a0_arm"):
                jobs.setdefault((job["arm"], job["seed"]), []).append((host, job))
    out = []
    for arm in cfg["arms"]:
        for s in cfg["seeds"][arm]:
            if arm in ("a0", "R") and s in (1101, 1102, 1103):
                p = by[(arm, s)]
                out.append(dict(label=f"{arm} {s}", arm=arm, seed=s, folder=world / "repo" / p["path"],
                                target=p["target"], complete=p["complete_sha256"], path=p["path"], source="pinned"))
            else:
                (host, job), = jobs[(arm, s)]
                out.append(dict(label=f"{arm} {s}", arm=arm, seed=s,
                                folder=world / "kit" / "retrieved" / host / "tree" / job["unit"], target="e1",
                                complete=job["complete_sha256"], path=f"kit:{host}/{job['unit']}", source="kit"))
    p = by[("theta0", None)]
    out.append(dict(label="theta0", arm="theta0", seed=None, folder=world / "repo" / p["path"], target=p["target"],
                    complete=p["complete_sha256"], path=p["path"], source="pinned"))
    return out


def read_unit(u: dict, hb: dict) -> None:
    ev = u["folder"] / "eval" / u["target"]
    s_rows, g_rows = jl(ev / "samples.jsonl"), jl(ev / "guard_samples.jsonl")
    harm = []
    for a, g in zip(s_rows, g_rows):
        assert (a["prompt_id"], a["sample_index"]) == (g["prompt_id"], g["sample_index"])
        harm.append(dict(block="harm", pid=a["prompt_id"], k=a["sample_index"], valid=g["valid"],
                         safety=g.get("safety"), refusal=g.get("refusal"), cats=list(g.get("categories") or []),
                         reason=g.get("reason"), tokens=a["output_tokens"], capped=a["stop_reason"] == "max_new_tokens",
                         hb=hb[(u["complete"], a["prompt_id"], a["sample_index"])]))
    gens = {r["prompt_id"]: r for r in jl(ev / "generations.jsonl") if r.get("kind") == "overrefusal"}
    grd_all = jl(ev / "guard.jsonl")
    grd = {r["prompt_id"]: r for r in grd_all if r.get("kind") == "overrefusal"}
    benign = []
    for d in sorted(gens):
        g = grd[d]
        benign.append(dict(block="benign", pid=d, k=None, valid=g["valid"], safety=g.get("safety"),
                           refusal=g.get("refusal"), cats=list(g.get("categories") or []), reason=g.get("reason"),
                           tokens=gens[d]["output_tokens"], capped=gens[d]["stop_reason"] == "max_new_tokens", hb=None))
    u["harm"], u["benign"] = harm, benign
    u["greedy"] = {r["prompt_id"]: list(r.get("categories") or []) for r in grd_all if r.get("kind") == "harm"}


def draw(root: Path, step: str) -> dict:
    world = root / "world"
    cfg = v2lib.settings_with(json.loads((root / "pins.json").read_text()))
    units = population(world, cfg)
    plan = json.loads((world / "kit" / "plan.json").read_text())
    tag = plan["records"]["judges"]["A"]["judges"]["harmbench"]["tag"]
    hb = {}
    for r in jl(world / "kit" / "judges" / "A" / "pods" / tag / "fetched" / "out" / "harmbench-pod.jsonl"):
        if r["mode"] == "sampled":
            hb[(r["complete_sha256"], r["prompt_id"], r["sample_index"])] = r["label"]
    for u in units:
        read_unit(u, hb)
    bank = {r["prompt_id"]: r for r in jl(world / "bank" / "banks" / "dev.jsonl") if r["kind"] in ("harm", "overrefusal")}
    aud = json.loads((world / "bank" / "auditor" / "construction.json").read_text())["prompts"]
    # exclusions
    key = json.loads((world / "oct9" / "key.json").read_text())
    pinned = {u["path"]: u for u in units if u["source"] == "pinned"}
    uid_unit = {uid: pinned[i["unit_dir"]] for uid, i in key["units"].items() if i["unit_dir"] in pinned}
    oct9 = {(uid_unit[i["unit"]]["complete"], i["prompt_id"], i["sample_index"]) for i in key["items"]
            if i["unit"] in uid_unit}
    m = cfg["exclusions"]["minors"]
    cats_of = {}
    for u in units:
        for a in u["harm"] + u["benign"]:
            cats_of.setdefault(a["pid"], set()).update(a["cats"])
        for pid, cs in u["greedy"].items():
            cats_of.setdefault(pid, set()).update(cs)
    rule_a, rule_b = [], []
    ordered = sorted(p for p, r in bank.items() if r["kind"] == "harm") + \
        sorted(p for p, r in bank.items() if r["kind"] == "overrefusal")
    for pid in ordered:
        src, cat = aud[pid]["source"], norm(aud[pid]["category"] or "")
        if src == "simplesafetytests" and cat == "child abuse":
            rule_a.append(pid)
            continue
        text = norm(bank[pid]["prompt"])
        if not (any(term_hit(text, t) for t in m["terms"]) or any(re.search(p, text) for p in m["age_patterns"])):
            continue
        if "sexual" in cat or any("sexual" in c.lower() for c in cats_of.get(pid, ())):
            rule_b.append(pid)
    minors = set(rule_a) | set(rule_b)
    unscored = {"control string in guard input; not scored", "guard input over limit; not scored"}
    excl = {}
    for u in units:
        e = excl.setdefault(u["label"], {})
        for a in u["harm"] + u["benign"]:
            k = (a["pid"], -1 if a["k"] is None else a["k"])
            if a["block"] == "harm" and (u["complete"], a["pid"], a["k"]) in oct9:
                e[k] = "oct9"
            elif a["pid"] in minors:
                e[k] = "minors"
            elif not a["valid"]:
                e[k] = "unscored" if a["reason"] in unscored else "no_label"
    # the walk
    sizes = cfg["sizes"]["steps"][step]
    tags = cfg["seed_tags"]
    items, cells, subs = [], [], []
    used_by = {}
    for u in units:
        used = used_by.setdefault(u["arm"], set())
        q = sizes["theta0"] if u["seed"] is None else \
            {c: v[cfg["seeds"][u["arm"]].index(u["seed"])] for c, v in sizes["per_seed"].items()}
        for block, cell_names in (("harm", ["Unsafe", "Controversial", "Safe"]), ("benign", ["Yes", "No"])):
            answers = u["harm"] if block == "harm" else u["benign"]
            carry = 0
            for cell in cell_names:
                n = q[cell] + carry
                el = {}
                for a in answers:
                    k = (a["pid"], -1 if a["k"] is None else a["k"])
                    lab = (a["safety"] if block == "harm" else a["refusal"]) if a["valid"] else None
                    if lab == cell and k not in excl[u["label"]]:
                        el[k] = a
                part = f"theta0/{block}/{cell}" if u["seed"] is None else f"{u['arm']}/{u['seed']}/{block}/{cell}"
                order = sorted(el)
                random.Random(dseed(tags["freeze_date"], tags["draw"], part)).shuffle(order)
                if block == "harm" and cell == "Unsafe":
                    sub_of = {k: "Unsafe/yes" if a["hb"] == "yes" else "Unsafe/no" for k, a in el.items()}
                    names = ["Unsafe/yes", "Unsafe/no"]
                else:
                    sub_of = {k: cell for k in el}
                    names = [cell]
                free = [k for k in el if k[0] not in used]
                p_all = len({k[0] for k in free})
                pr = {s: len({k[0] for k in free if sub_of[k] == s}) for s in names}
                av = {s: sum(1 for k in free if sub_of[k] == s) for s in names}
                if len(names) == 2:
                    y, mm = split(n, av[names[0]], av[names[1]], pr[names[0]], pr[names[1]], p_all,
                                  cfg["harmbench_split"]["minimum"])
                    target = {names[0]: y, names[1]: mm}
                else:
                    target = {cell: min(n, p_all)}
                taken = first_feasible(order, sub_of, target, used)
                rank = {k: i for i, k in enumerate(order)}
                for k in taken:
                    a = el[k]
                    tail = "greedy" if a["k"] is None else str(a["k"])
                    iid = ("h" if block == "harm" else "b") + v2lib.sha(f"{u['complete']}|{a['pid']}|{tail}".encode())[:16]
                    items.append({"item": iid, "block": block, "arm": u["arm"], "seed": u["seed"], "unit": u["label"],
                                  "complete_sha256": u["complete"], "prompt_id": a["pid"], "sample_index": a["k"],
                                  "cell": cell, "sub_cell": sub_of[k],
                                  "qwen3guard": {"safety": a["safety"], "categories": a["cats"], "refusal": a["refusal"]},
                                  "harmbench": a["hb"], "output_tokens": a["tokens"], "capped": a["capped"],
                                  "rank": rank[k], "repeat": False})
                cells.append({"unit": u["label"], "arm": u["arm"], "seed": u["seed"], "block": block, "cell": cell,
                              "quota": n, "inflow": carry, "available_prompts": p_all, "drawn": len(taken),
                              "shortfall": n - len(taken)})
                for s in names:
                    e = sum(1 for k in el if sub_of[k] == s)
                    d = sum(1 for k in taken if sub_of[k] == s)
                    subs.append({"unit": u["label"], "arm": u["arm"], "seed": u["seed"], "block": block, "cell": cell,
                                 "sub_cell": s, "eligible": e, "available": av[s], "available_prompts": pr[s],
                                 "target": target[s], "drawn": d, "fraction": str(Fraction(d, e)) if e else None})
                carry = n - len(taken)
    harm_ids = sorted(i["item"] for i in items if i["block"] == "harm")
    reps = random.Random(dseed(tags["freeze_date"], tags["repeats"], "harm")).sample(
        harm_ids, min(sizes["repeats"], len(harm_ids)))
    for i in items:
        i["repeat"] = i["item"] in set(reps)
    per_unit = {lb: {r: sum(1 for x in e.values() if x == r) for r in ("oct9", "minors", "unscored", "no_label")}
                for lb, e in excl.items()}
    return {"items": items, "cells": cells, "subs": subs, "reps": reps, "per_unit": per_unit,
            "minors": {"rule_a": rule_a, "rule_b": rule_b}, "oct9": len(oct9)}


def compare(ref: dict, sealed: Path) -> list:
    key = json.loads((sealed / "hlc_key.json").read_text())
    wts = json.loads((sealed / "hlc_weights.json").read_text())
    bad = []
    if key["items"] != ref["items"]:
        n = next((i for i, (a, b) in enumerate(zip(key["items"], ref["items"])) if a != b), None)
        bad.append(f"items differ: tool {len(key['items'])}, ref {len(ref['items'])}; first difference at {n}: "
                   f"tool {key['items'][n] if n is not None else None} ref {ref['items'][n] if n is not None else None}")
    if key["repeats"] != ref["reps"]:
        bad.append("repeats differ")
    if wts["cells"] != ref["cells"]:
        n = next((i for i, (a, b) in enumerate(zip(wts["cells"], ref["cells"])) if a != b), None)
        bad.append(f"cells differ at {n}: tool {wts['cells'][n] if n is not None else None} "
                   f"ref {ref['cells'][n] if n is not None else None}")
    if wts["sub_cells"] != ref["subs"]:
        n = next((i for i, (a, b) in enumerate(zip(wts["sub_cells"], ref["subs"])) if a != b), None)
        bad.append(f"sub-cells differ at {n}: tool {wts['sub_cells'][n] if n is not None else None} "
                   f"ref {ref['subs'][n] if n is not None else None}")
    if wts["exclusions"]["per_unit"] != ref["per_unit"]:
        bad.append("per-unit exclusions differ")
    if wts["exclusions"]["minors_prompts"] != ref["minors"]:
        bad.append(f"minors prompts differ: tool {wts['exclusions']['minors_prompts']} ref {ref['minors']}")
    return bad


if __name__ == "__main__":
    if len(sys.argv) < 3:
        sys.exit(2)
    root, sealed = Path(sys.argv[1]), Path(sys.argv[2])
    step = sys.argv[3] if len(sys.argv) > 3 else "0"
    ref = draw(root, step)
    bad = compare(ref, sealed)
    harm = [i for i in ref["items"] if i["block"] == "harm"]
    unsafe = [s for s in ref["subs"] if s["cell"] == "Unsafe"]
    minimum_cases = sum(1 for s in unsafe if s["available_prompts"] >= 1)
    print(f"ref: {len(ref['items'])} items ({len(harm)} harm), {len(ref['reps'])} repeats, oct9 {ref['oct9']}, "
          f"minors {ref['minors']}, Unsafe sub-cells with prompts {minimum_cases}")
    for b in bad:
        print("DIFF:", b)
    print("IDENTICAL" if not bad else f"{len(bad)} DIFFERENCES")
    sys.exit(1 if bad else 0)
