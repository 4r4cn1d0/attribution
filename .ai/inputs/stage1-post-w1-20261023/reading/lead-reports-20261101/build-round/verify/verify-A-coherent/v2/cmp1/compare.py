"""Compare the builder's reader (sg_coherent.sg) with the verifier's reference (ref_sg) on synthetic readings, and the
all-coherent identity with B16's primary U_k. Prints one line per reading and a summary; exit 1 on any mismatch."""

from __future__ import annotations

import json
import math
import sys

import gen
import ref_sg
from scripts.stage1_s1.reading.reading import read
from scripts.stage1_s1.reading.settings import canonical_json
from scripts.stage1_s1.reading_input import sg_coherent as sgc

TOL = 1e-9
CASES = [
    ("plan_a", 1, {}),
    ("plan_a", 2, {"concentrated": {"S1": (0.08, 0.95)}}),
    ("plan_a", 3, {"linked": {"S1": (0.25, 0.03)}}),
    ("plan_a", 4, {"linked": {"S3": (0.03, 0.15)}}),
    ("plan_a", 5, {"empty_cells": [("S3", 1105)]}),
    ("plan_a", 6, {"empty_cells": [("a0", 1101), ("R", 1101)]}),
    ("plan_a", 7, {"empty_cells": [("R", 1103), ("S1", 1102)]}),
    ("plan_a", 8, {"empty_cells": [("A1", j) for j in range(1102, 1107)]}),
    ("plan_a", 9, {"fail": {"S4": 0.3}, "concentrated": {"L1": (0.1, 0.9)}}),
    ("plan_a", 10, {"all_coherent": True}),
    ("plan_a", 11, {"mu": {"A1": -1.5, "S4": 1.2, "S3": -1.2, "R": 0.6}, "concentrated": {"H1": (0.06, 0.95)}}),
    ("plan_a", 12, {"lowfail_cells": {("S1", 1104): 0.97, ("L1", 1106): 0.9}}),
    ("plan_a", 13, {"empty_cells": [("S3", j) for j in range(1102, 1108)]}),
    ("plan_a", 14, {"empty_cells": [(a, j) for a in ("S1", "S3", "S4") for j in range(1102, 1108)]}),
    ("plan_a", 15, {"all_coherent": True, "mu": {"A1": -1.5, "S3": -1.0}}),
    ("plan_b", 21, {}),
    ("plan_b", 22, {"concentrated": {"S1": (0.08, 0.95)}}),
    ("plan_b", 23, {"empty_cells": [("S4", 1105)]}),
    ("plan_b", 24, {"empty_cells": [("S4", j) for j in range(1102, 1111)]}),
    ("plan_b", 25, {"all_coherent": True}),
    ("plan_b", 26, {"linked": {"S1": (0.25, 0.03)}, "mu": {"A1": -1.2}}),
    ("plan_a_block_a_only", 31, {}),
    ("plan_a_block_a_only", 32, {"concentrated": {"S1": (0.08, 0.95)}}),
    ("plan_a_block_a_only", 33, {"all_coherent": True}),
    ("plan_a_block_a_only", 34, {"empty_cells": [("S3", 1103)]}),
    ("plan_a_block_a_only", 35, {"empty_cells": [("R", 1102)]}),
]
KEYS = ("est", "se", "df", "seed_var", "seed_df", "item_var", "item_q", "pairs", "items", "with_item")


def compare_block(tag, got: dict, ref_ests: dict, ref_words: dict, ref_rej: list, got_phi: dict, worst: dict, bad: list,
                  extra=None):
    for name, rec in got.items():
        e = ref_ests[name]
        if not isinstance(e, dict):
            if rec["computable"] or rec["p_in_phi"] != 1.0:
                bad.append(f"{tag} {name}: reference not computable ({e}) but reader computable or p != 1")
            continue
        if not rec["computable"]:
            bad.append(f"{tag} {name}: reader not computable ({rec['reason']}) but reference computable")
            continue
        est = rec["estimate"]
        form_ok = (est["form"].endswith("paired on the seeds that hold a value (LN-12's precedent)")
                   == (e["form"] == "paired"))
        if not form_ok:
            bad.append(f"{tag} {name}: form {est['form']!r} vs reference {e['form']}")
        for key, tol, rel in (("est", TOL, False), ("se", TOL, False), ("seed_var", TOL, False),
                              ("item_var", TOL, False), ("df", TOL, True), ("seed_df", TOL, True)):
            a, b = est[key], e[key]
            diff = abs(a - b) / (abs(b) if rel and b else 1.0)
            worst[key] = max(worst.get(key, 0.0), diff)
            if not diff <= tol:
                bad.append(f"{tag} {name}: {key} {a!r} vs {b!r}")
        for i in (0, 1):
            diff = abs(rec["interval_90"][i] - e["ci"][i])
            worst["ci90"] = max(worst.get("ci90", 0.0), diff)
            if diff > TOL:
                bad.append(f"{tag} {name}: interval end {i} {rec['interval_90'][i]!r} vs {e['ci'][i]!r}")
        diff = abs(rec["p_in_phi"] - e["p"])
        worst["p"] = max(worst.get("p", 0.0), diff)
        if diff > TOL:
            bad.append(f"{tag} {name}: p {rec['p_in_phi']!r} vs {e['p']!r}")
        if est["pairs"] != e["pairs"]:
            bad.append(f"{tag} {name}: pairs {est['pairs']} vs {e['pairs']}")
        w, h = ref_words[name]
        if rec["u_part_words"] != w or rec["headline"] != h:
            bad.append(f"{tag} {name}: words {rec['u_part_words']} / {rec['headline']} vs {w} / {h}")
    if got_phi["rejected"] != ref_rej:
        bad.append(f"{tag}: Phi rejected {got_phi['rejected']} vs {ref_rej}")


def run_case(reading, seed, kw, worst, bad, stats):
    tables, counts = gen.make(reading, seed, **kw)
    reading_doc = json.loads(canonical_json(read(tables, gen.sha(tables))))
    out = sgc.sg(tables, counts, reading_doc, gen.sha(tables), gen.sha(counts), gen.sha(reading_doc))
    out = json.loads(canonical_json(out))
    ref = ref_sg.reference(tables, counts, reading_doc)
    tag = f"{reading}/{seed}"
    n_bad = len(bad)
    compare_block(f"{tag} coherent", out["coherent"]["contrasts"], ref["coherent"]["ests"], ref["coherent"]["words"],
                  ref["coherent"]["rejected"], out["coherent"]["phi"], worst, bad)
    for d in ("against_better", "against_worse"):
        rc = ref["corners"][d]
        compare_block(f"{tag} {d}", out["g3a"][d]["contrasts"], rc["ests"], rc["words"], rc["rejected"],
                      out["g3a"][d]["phi"], worst, bad)
    for arm, a in ref["arms"].items():
        g = out["coherent"]["arms"][arm]
        if g["cells_pp"] != a["cells_pp"]:
            bad.append(f"{tag} arm {arm}: cells_pp differ")
        if (g["mean_pp"] is None) != (a["mean_pp"] is None) or (
                a["mean_pp"] is not None and abs(g["mean_pp"] - a["mean_pp"]) > 1e-12):
            bad.append(f"{tag} arm {arm}: mean_pp {g['mean_pp']} vs {a['mean_pp']}")
        if g["prompts_without_coherent_answer"] != a["empty"]:
            bad.append(f"{tag} arm {arm}: empty prompts differ")
    for name, per in ref["g2"].items():
        if out["coherent"]["contrasts"][name]["g2_prompts_without_coherent_answer_per_seed_pair"] != per:
            bad.append(f"{tag} {name}: G2 pair counts differ")
    # the all-coherent identity: S-G coherent is B16's primary U_k to the last bit
    if kw.get("all_coherent"):
        for name in out["coherent"]["contrasts"]:
            k, p = out["coherent"]["contrasts"][name], reading_doc["contrasts"][name]
            same = (k["computable"] and all(k["estimate"][key] == p["U"][key] for key in KEYS)
                    and k["interval_90"] == p["U_interval_90"] and k["p_in_phi"] == p["p_values"]["U"]
                    and k["u_part_words"] == reading_doc["rows"][name]["u_part"]["words"]
                    and k["headline"] == reading_doc["headline"][name] and not k["differs_from_primary"])
            if not same:
                bad.append(f"{tag} {name}: all-coherent S-G is not the primary U_k bit for bit")
        if out["coherent"]["phi"] != reading_doc["phi"]:
            bad.append(f"{tag}: all-coherent Phi record differs from B16's")
        stats["identity"] += 1
    nc = sum(1 for k in out["coherent"]["contrasts"].values() if not k["computable"])
    paired = sum(1 for k in out["coherent"]["contrasts"].values()
                 if k["computable"] and "paired" in k["estimate"]["form"])
    differ = sum(1 for k in out["coherent"]["contrasts"].values() if k.get("differs_from_primary"))
    stats["contrasts"] += len(out["coherent"]["contrasts"])
    stats["not_computable"] += nc
    stats["paired"] += paired
    stats["differ"] += differ
    print(f"{tag:<26} coherent: {len(out['coherent']['contrasts'])} contrasts, not computable {nc}, paired {paired}, "
          f"words/headline differ from primary {differ}; mismatches {len(bad) - n_bad}")


def main():
    worst, bad = {}, []
    stats = {"identity": 0, "contrasts": 0, "not_computable": 0, "paired": 0, "differ": 0}
    for reading, seed, kw in CASES:
        run_case(reading, seed, kw, worst, bad, stats)
    print("readings:", len(CASES), stats)
    print("largest differences:", {k: f"{v:.3g}" for k, v in sorted(worst.items())})
    for b in bad:
        print("MISMATCH", b)
    print("mismatches:", len(bad))
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
