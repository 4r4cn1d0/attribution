"""Extra comparisons where O or L rejects (the headline names the measure): worlds with a high-O repair or a high-L
repair; tallies the headline words of B16, S-G coherent and both corners, and compares with the reference."""
import json, sys
from collections import Counter
import gen, ref_sg, compare
from scripts.stage1_s1.reading.reading import read
from scripts.stage1_s1.reading.settings import canonical_json
from scripts.stage1_s1.reading_input import sg_coherent as sgc

CASES = [("plan_a", 41, {"concentrated": {"S1": (0.08, 0.95)}}, {"S4": 30.0, "S3": 22.0}, {"L1": 1.60, "H1": 1.575}),
         ("plan_a", 42, {"linked": {"S3": (0.25, 0.03)}, "mu": {"A1": -1.2}}, {"A1": 18.0, "S1": 25.0}, {"S4": 1.62}),
         ("plan_b", 43, {}, {"S4": 30.0}, {"H1": 1.60}),
         ("plan_a_block_a_only", 44, {"concentrated": {"S1": (0.08, 0.95)}}, {"S4": 30.0}, {"L1": 1.60})]

def main():
    worst, bad, tally = {}, [], Counter()
    stats = {"identity": 0, "contrasts": 0, "not_computable": 0, "paired": 0, "differ": 0}
    for reading, seed, kw, o_lv, l_lv in CASES:
        old_o, old_l = dict(gen.O_LEVEL), dict(gen.L_LEVEL)
        gen.O_LEVEL.update(o_lv); gen.L_LEVEL.update(l_lv)
        try:
            tables, counts = gen.make(reading, seed, **kw)
        finally:
            gen.O_LEVEL.clear(); gen.O_LEVEL.update(old_o); gen.L_LEVEL.clear(); gen.L_LEVEL.update(old_l)
        rdoc = json.loads(canonical_json(read(tables, gen.sha(tables))))
        out = json.loads(canonical_json(sgc.sg(tables, counts, rdoc, gen.sha(tables), gen.sha(counts), gen.sha(rdoc))))
        ref = ref_sg.reference(tables, counts, rdoc)
        tag = f"{reading}/{seed}"
        n0 = len(bad)
        compare.compare_block(f"{tag} coherent", out["coherent"]["contrasts"], ref["coherent"]["ests"],
                              ref["coherent"]["words"], ref["coherent"]["rejected"], out["coherent"]["phi"], worst, bad)
        for d in ("against_better", "against_worse"):
            rc = ref["corners"][d]
            compare.compare_block(f"{tag} {d}", out["g3a"][d]["contrasts"], rc["ests"], rc["words"], rc["rejected"],
                                  out["g3a"][d]["phi"], worst, bad)
        for name, w in rdoc["headline"].items():
            tally[("B16", w)] += 1
        for block in (out["coherent"]["contrasts"], out["g3a"]["against_better"]["contrasts"], out["g3a"]["against_worse"]["contrasts"]):
            for name, k in block.items():
                tally[("S-G", k["headline"])] += 1
                if k["computable"] and k["u_part_words"] == rdoc["rows"][name]["u_part"]["words"] and k["headline"] != rdoc["headline"][name]:
                    tally[("headline differs, words same", name)] += 1
        print(tag, "mismatches", len(bad) - n0, "B16 headline", rdoc["headline"])
    for k, v in sorted(tally.items(), key=str):
        print(k, v)
    for b in bad:
        print("MISMATCH", b)
    print("largest differences:", {k: f"{v:.3g}" for k, v in sorted(worst.items())}, "mismatches:", len(bad))
    return 1 if bad else 0

sys.exit(main())
