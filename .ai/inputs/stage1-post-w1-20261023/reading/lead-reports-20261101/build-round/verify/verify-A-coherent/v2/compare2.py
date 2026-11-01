"""Verifier 2: the builder's reader (sg_coherent.sg) against my reference (ref2.compute) on synthetic readings, B16's
real output on each synthetic tables.json, and the all-coherent identity against B16's primary U_k bit for bit.

    PYTHONPATH=<ws-a> python -B compare2.py [--only name,name] [--out results.json]
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import time
from pathlib import Path

import mpmath as mp

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import gen2  # noqa: E402
import ref2  # noqa: E402

from scripts.stage1_s1.reading.reading import read  # noqa: E402
from scripts.stage1_s1.reading.settings import canonical_json, design, sha256_bytes, strict_json  # noqa: E402
from scripts.stage1_s1.reading_input import coherent as coh  # noqa: E402  (KIND and RULE for the inputs only)
from scripts.stage1_s1.reading_input import sg_coherent as sgc  # noqa: E402  (the code under test)

TOL = 1e-9
EST_KEYS = ("est", "se", "df", "seed_var", "seed_df", "item_var", "item_q", "pairs", "items", "with_item")

A_SEEDS = tuple(range(1102, 1108))
SCEN = {
    # plan A
    "a-indep": ("plan_a", 101, dict(fail={a: ("independent", 0.07) for a in ("a0", "R", "A1", "L1", "H1", "S1", "S3", "S4")})),
    "a-conc-S1": ("plan_a", 102, dict(fail={"S1": ("concentrated", 0.08, 0.95, 0.05, False)})),
    "a-conc-S1-perseed": ("plan_a", 103, dict(fail={"S1": ("concentrated", 0.08, 0.95, 0.05, True)})),
    "a-prompt-S1": ("plan_a", 104, dict(fail={"S1": ("prompt-linked", 0.04, 0.95, 0.05)})),
    "a-answer-S1": ("plan_a", 105, dict(fail={"S1": ("answer-linked", 0.25, 0.03)})),
    "a-refusal-S3": ("plan_a", 106, dict(fail={"S3": ("refusal-linked", 0.03, 0.15)})),
    "a-removal-linked": ("plan_a", 107, dict(fail={"R": ("prompt-linked", 0.06, 0.9, 0.05),
                                                   "A1": ("answer-linked", 0.2, 0.02)})),
    "a-empty-S3-1105": ("plan_a", 108, dict(empty={("S3", 1105)})),
    "a-empty-R1103-S1-1102": ("plan_a", 109, dict(empty={("R", 1103), ("S1", 1102)})),
    "a-empty-A1-5seeds": ("plan_a", 110, dict(empty={("A1", j) for j in range(1102, 1107)})),
    "a-empty-S3-all": ("plan_a", 111, dict(empty={("S3", j) for j in A_SEEDS})),
    "a-empty-S3S4-all": ("plan_a", 112, dict(empty={(a, j) for a in ("S3", "S4") for j in A_SEEDS})),
    "a-empty-a0R-1101": ("plan_a", 113, dict(empty={("a0", 1101), ("R", 1101)})),
    "a-empty-L1-5seeds": ("plan_a", 114, dict(empty={("L1", j) for j in range(1103, 1108)})),
    "a-lowN-S1": ("plan_a", 115, dict(fail={"S1": ("independent", 0.97)})),
    "a-ol": ("plan_a", 116, dict(fail={"S1": ("answer-linked", 0.2, 0.03)}, o_levels={"S4": 45.0, "S1": 8.0},
                                 l_levels={"L1": 1.75})),
    "a-coherent-1": ("plan_a", 117, dict(base_fail=0.0)),
    "a-coherent-2": ("plan_a", 118, dict(base_fail=0.0, o_levels={"S4": 45.0}, l_levels={"L1": 1.75})),
    "a-empty-S1-all": ("plan_a", 119, dict(empty={("S1", j) for j in A_SEEDS})),
    "a-no-g3": ("plan_a", 120, dict(fail={"S1": ("concentrated", 0.08, 0.95, 0.05, False)}, no_g3=True)),
    "a-strong": ("plan_a", 121, dict(mu={"A1": -1.2, "S3": -1.0, "S4": 0.9}, fail={"S3": ("refusal-linked", 0.02, 0.2)})),
    "a-tinyN-S1": ("plan_a", 122, dict(fail={"S1": ("independent", 0.997)})),
    "a-tinyN-R-A1": ("plan_a", 123, dict(fail={"R": ("independent", 0.996), "A1": ("independent", 0.9975)})),
    "a-L1-two-seeds": ("plan_a", 124, dict(empty={("L1", j) for j in (1102, 1104, 1105, 1107)})),
    # plan B
    "b-indep": ("plan_b", 201, dict(fail={a: ("independent", 0.07) for a in ("a0", "R", "A1", "H1", "S1", "S4")})),
    "b-conc-S1": ("plan_b", 202, dict(fail={"S1": ("concentrated", 0.08, 0.95, 0.05, False)})),
    "b-answer-S4": ("plan_b", 203, dict(fail={"S4": ("answer-linked", 0.25, 0.03)})),
    "b-empty-S4-all": ("plan_b", 204, dict(empty={("S4", j) for j in range(1102, 1111)})),
    "b-empty-S1-1105": ("plan_b", 205, dict(empty={("S1", 1105)})),
    "b-empty-R-1104": ("plan_b", 206, dict(empty={("R", 1104)})),
    "b-coherent": ("plan_b", 207, dict(base_fail=0.0)),
    "b-lowN-A1": ("plan_b", 208, dict(fail={"A1": ("independent", 0.96)})),
    # block A only
    "ba-indep": ("plan_a_block_a_only", 301, dict(fail={a: ("independent", 0.07) for a in ("a0", "R", "S1", "S4")})),
    "ba-conc-S1": ("plan_a_block_a_only", 302, dict(fail={"S1": ("concentrated", 0.08, 0.95, 0.05, False)})),
    "ba-empty-S4-1103": ("plan_a_block_a_only", 303, dict(empty={("S4", 1103)})),
    "ba-empty-S4-2seeds": ("plan_a_block_a_only", 304, dict(empty={("S4", 1103), ("S4", 1104)})),
    "ba-coherent": ("plan_a_block_a_only", 305, dict(base_fail=0.0)),
    "ba-prompt-R": ("plan_a_block_a_only", 306, dict(fail={"R": ("prompt-linked", 0.05, 0.95, 0.05)})),
}


def roundtrip(doc):
    data = canonical_json(doc)
    return strict_json(data), data


def build(name):
    reading, seed, kw = SCEN[name]
    tables, counts = gen2.world(reading, seed, kind=coh.KIND, rule=coh.RULE, **kw)
    tables, t_bytes = roundtrip(tables)
    t_sha = sha256_bytes(t_bytes)
    counts["input_sha256"] = t_sha
    counts, c_bytes = roundtrip(counts)
    reading_doc, r_bytes = roundtrip(read(tables, t_sha))          # B16's own output, as its __main__ writes it
    return tables, counts, reading_doc, t_sha, sha256_bytes(c_bytes), sha256_bytes(r_bytes)


def close(a, b, tol=TOL, rel=False):
    if a is None or b is None:
        return a is None and b is None
    a, b = float(a), float(b)
    if math.isinf(a) or math.isinf(b):
        return a == b
    if rel:
        return abs(a - b) <= tol * max(1.0, abs(b))
    return abs(a - b) <= tol


def compare_block(tag, got: dict, ref: dict, got_rej: list, ref_rej: list, mism: list, stats: dict):
    if got_rej != ref_rej:
        mism.append(f"{tag}: Phi rejected {got_rej} != ref {ref_rej}")
    for name, r in ref.items():
        g = got[name]
        if bool(g["computable"]) != bool(r["computable"]):
            mism.append(f"{tag} {name}: computable {g['computable']} != ref {r['computable']} ({r.get('why')}; "
                        f"{g.get('reason')})")
            continue
        if not r["computable"]:
            stats["not_computable"] += 1
            if g["p_in_phi"] != 1.0 or g["u_part_words"] is not None:
                mism.append(f"{tag} {name}: not computable but p {g['p_in_phi']} words {g['u_part_words']}")
            continue
        stats["computable"] += 1
        e = g["estimate"]
        form_ok = (("paired" in e["form"]) == (r["form"] == "paired"))
        if not form_ok:
            mism.append(f"{tag} {name}: form {e['form']} != ref {r['form']}")
        stats["forms"][r["form"]] = stats["forms"].get(r["form"], 0) + 1
        checks = [("est", e["est"], r["est"], False), ("se", e["se"], r["se"], False),
                  ("df", e["df"], r["df"], True), ("seed_var", e["seed_var"], r["seed_var"], False),
                  ("seed_df", e["seed_df"], r["seed_df"], True), ("item_var", e["item_var"], r["item_var"], False),
                  ("item_q", e["item_q"], r["item_q"], True), ("lo90", g["interval_90"][0], r["ci90"][0], False),
                  ("hi90", g["interval_90"][1], r["ci90"][1], False), ("p", g["p_in_phi"], r["p"], False)]
        for key, a, b, rel in checks:
            diff = abs(float(a) - float(b))
            if rel:
                diff = diff / max(1.0, abs(float(b)))
            stats["maxdiff"][key] = max(stats["maxdiff"].get(key, 0.0), diff)
            if not close(a, b, TOL, rel):
                mism.append(f"{tag} {name}: {key} {a!r} != ref {float(b)!r}")
        if e["pairs"] != r["pairs"] or e["items"] != 200 or e["with_item"] is not True:
            mism.append(f"{tag} {name}: pairs/items/with_item {e['pairs']}/{e['items']}/{e['with_item']}")
        if g["u_part_words"] != r["words"]:
            mism.append(f"{tag} {name}: words {g['u_part_words']} != ref {r['words']}")
        if g["headline"] != r["headline"]:
            mism.append(f"{tag} {name}: headline {g['headline']} != ref {r['headline']}")
        if bool(g["differs_from_primary"]) != bool(r["differs"]):
            mism.append(f"{tag} {name}: differs {g['differs_from_primary']} != ref {r['differs']}")
        stats["differs"] += bool(r["differs"])
        stats["headlines"].add(r["headline"])


def run(name, out_rows):
    t0 = time.time()
    tables, counts, reading_doc, ts, cs, rs = build(name)
    t1 = time.time()
    got = sgc.sg(tables, counts, reading_doc, ts, cs, rs)
    t2 = time.time()
    ref = ref2.compute(tables, counts, reading_doc)
    t3 = time.time()
    mism = []
    stats = {"computable": 0, "not_computable": 0, "differs": 0, "forms": {}, "maxdiff": {}, "headlines": set()}
    compare_block("coherent", got["coherent"]["contrasts"], ref["coherent"], got["coherent"]["phi"]["rejected"],
                  ref["coherent_rejected"], mism, stats)
    for d in ("against_better", "against_worse"):
        compare_block(d, got["g3a"][d]["contrasts"], ref["corners"][d]["contrasts"], got["g3a"][d]["phi"]["rejected"],
                      ref["corners"][d]["rejected"], mism, stats)
        for n, arm in ref["corners"][d]["moved"].items():
            if got["g3a"][d]["contrasts"][n]["arm_from_g3"] != arm:
                mism.append(f"{d} {n}: arm_from_g3 {got['g3a'][d]['contrasts'][n]['arm_from_g3']} != {arm}")
    # per-arm values and G2's counts
    for arm, r in ref["arms"].items():
        g = got["coherent"]["arms"][arm]
        for j, v in r["cells_pp"].items():
            if g["cells_pp"][j] != v:                       # both are the correctly rounded 100 U / N
                mism.append(f"arms {arm} {j}: V {g['cells_pp'][j]!r} != ref {v!r}")
        if not close(g["mean_pp"], r["mean_pp"], 1e-12):
            mism.append(f"arms {arm}: mean {g['mean_pp']!r} != ref {r['mean_pp']!r}")
        for key in ("seeds_without_value", "coherent_answers", "prompts_without_coherent_answer"):
            if g[key] != r[key]:
                mism.append(f"arms {arm}: {key} {g[key]} != ref {r[key]}")
    for n, r in ref["g2"].items():
        g = got["coherent"]["contrasts"][n]["g2_prompts_without_coherent_answer_per_seed_pair"]
        if g != r:
            mism.append(f"G2 {n}: {g} != ref {r}")
    # sensitivity_part from the reader's own blocks (C7) and the symmetric table's label and words
    for n in got["sensitivity_part"]:
        want = []
        for key, block in (("coherent", ref["coherent"]), ("against_better", ref["corners"]["against_better"]["contrasts"]),
                           ("against_worse", ref["corners"]["against_worse"]["contrasts"])):
            r = block[n]
            if not r["computable"]:
                want.append(sgc.CODES[key])
            elif r["differs"]:
                want.append(sgc.CODES[key])
        if [e["code"] for e in got["sensitivity_part"][n]] != want:
            mism.append(f"sensitivity_part {n}: {[e['code'] for e in got['sensitivity_part'][n]]} != {want}")
    sym = got["g3_unscored_symmetric"]
    b16 = (reading_doc["sensitivities"].get("S-G") or {}).get("g3_unscored_unsafe")
    if sym["label"] != "unscored counted Unsafe in every arm (not Gate B's adverse corner)":
        mism.append(f"symmetric label {sym['label']!r}")
    if b16 is not None:
        for n, rec in sym["contrasts"].items():
            if rec != {"u_part_words": b16[n]["u_part_words"], "differs_from_primary": b16[n]["differs_from_primary"]}:
                mism.append(f"symmetric {n}: {rec}")
    # the identity: every answer coherent -> S-G coherent is B16's primary U_k bit for bit
    identity = None
    if SCEN[name][2].get("base_fail") == 0.0 and not SCEN[name][2].get("fail"):
        identity = []
        for n, _, _ in design(tables["reading"]).contrasts:
            k, p = got["coherent"]["contrasts"][n], reading_doc["contrasts"][n]
            for key in EST_KEYS:
                if k["estimate"][key] != p["U"][key]:
                    identity.append(f"{n} {key}: {k['estimate'][key]!r} != primary {p['U'][key]!r}")
            if k["interval_90"] != p["U_interval_90"] or k["p_in_phi"] != p["p_values"]["U"]:
                identity.append(f"{n}: interval or p differs")
            if k["u_part_words"] != reading_doc["rows"][n]["u_part"]["words"] or k["headline"] != reading_doc["headline"][n]:
                identity.append(f"{n}: words or headline differ")
        if got["coherent"]["phi"] != reading_doc["phi"]:
            identity.append("phi record differs")
        for cl, fit in got["coherent"]["fits"].items():
            if fit["sigma2"] != reading_doc["fits"]["U"][cl]["sigma2"]:
                identity.append(f"fit {cl} sigma2 differs")
        mism += [f"IDENTITY {s}" for s in identity]
    row = {"name": name, "reading": tables["reading"], "mismatches": mism, "computable": stats["computable"],
           "not_computable": stats["not_computable"], "differs": stats["differs"], "forms": stats["forms"],
           "maxdiff": stats["maxdiff"], "headlines": sorted(stats["headlines"]),
           "identity_checked": identity is not None, "identity_ok": identity == [] if identity is not None else None,
           "fit_reasons": {"reader": got["coherent"]["fits_not_computable"], "ref": ref["fit_reasons"]},
           "primary_rejected": reading_doc["phi"]["rejected"], "sg_rejected": got["coherent"]["phi"]["rejected"],
           "seconds": {"build+b16": round(t1 - t0, 1), "reader": round(t2 - t1, 1), "ref": round(t3 - t2, 1)}}
    out_rows.append(row)
    print(f"{name:<24} {tables['reading']:<20} mism {len(mism):>2} comp {stats['computable']:>2} "
          f"nc {stats['not_computable']:>2} differs {stats['differs']:>2} forms {stats['forms']} "
          f"ident {row['identity_ok']} t {row['seconds']}", flush=True)
    for s in mism[:8]:
        print("    ", s)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default="")
    ap.add_argument("--out", type=Path)
    args = ap.parse_args()
    names = [n for n in SCEN if not args.only or n in args.only.split(",")]
    rows = []
    for n in names:
        run(n, rows)
    total = sum(len(r["mismatches"]) for r in rows)
    agg = {}
    for r in rows:
        for k, v in r["maxdiff"].items():
            agg[k] = max(agg.get(k, 0.0), v)
    print(f"readings {len(rows)}; mismatches {total}; max diffs {json.dumps({k: float(f'{v:.3g}') for k, v in agg.items()})}")
    print(f"contrasts computable {sum(r['computable'] for r in rows)}, not computable {sum(r['not_computable'] for r in rows)}, "
          f"differing labels {sum(r['differs'] for r in rows)}; identity readings "
          f"{sum(1 for r in rows if r['identity_checked'])} ok {sum(1 for r in rows if r['identity_ok'])}")
    if args.out:
        with open(args.out, "x") as handle:
            json.dump({"rows": rows, "total_mismatches": total, "max_diffs": agg}, handle, indent=1, sort_keys=True,
                      default=str)
    return 0 if total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
