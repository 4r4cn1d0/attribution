"""Verifier: does the noise reader's read_unit accept the five 7-8B a0 units (the inputs N will key)? And do their
compared environment fields agree within a family (the fallback trigger)? Loads the builder's noise_reading by path.
Prints ids, booleans and field names only."""
import importlib.util, json, pathlib
WS = pathlib.Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-c")
spec = importlib.util.spec_from_file_location("nr", WS / "scripts/scale78b/noise_reading.py")
nr = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nr)
MAIN = pathlib.Path("/Users/spiderishi/Coding/attribution")
X = "472fc7f6d619bdee2c3aa38e444024626be8b66bfb74a5abf37f2ddb6dded892"
units = {
    ("llama31-8b", 1101): "tmp/family-probe-sp-llama31-8b-b5e5-1101/retrieved/sp-llama31-8b-b5e5-1101/tree/round1/1101-a0-e1-a1",
    ("llama31-8b", 1102): "tmp/family-probe-sp-llama31-8b-b5e5-seed1102/retrieved/sp-llama31-8b-b5e5-1102/tree/round1/1102-a0-e1-a1",
    ("olmo2-7b", 1101): "tmp/family-probe-sp-olmo2-7b-b-a0/retrieved/sp-olmo2-7b-b2-1101/tree/round1/1101-a0-e1-a1",
    ("olmo2-7b", 1102): "tmp/family-probe-sp-olmo2-7b-b-seed1102/retrieved/sp-olmo2-7b-1102/tree/round1/1102-a0-e1-a1",
    ("olmo2-7b", 1103): "tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1",
}
read = {}
for (fam, seed), rel in units.items():
    folder = MAIN / rel
    key = nr.sha256_file(folder / "COMPLETE.json")
    try:
        u = nr.read_unit({"path": str(folder), "complete_sha256": key}, "a0", seed, fam, X, f"{fam} a0@{seed}", MAIN)
        read[(fam, seed)] = u
        print(f"{fam} a0@{seed}: ACCEPTED; complete {key[:16]} lock {u['lock_sha256'][:8]} guard? {u['guard'] is not None} resumed {str(u['resumed_from_complete_sha256'])[:16]}; fields: {sorted(u['fields'])}")
    except SystemExit as e:
        print(f"{fam} a0@{seed}: REFUSED: {e}")
for fam in ("llama31-8b", "olmo2-7b"):
    ref = read.get((fam, 1101))
    for (f, s), u in read.items():
        if f == fam and ref is not None:
            print(f"{fam} a0@{s} vs a0@1101 environment_differs:", nr.environment_differs(u, ref))
# a 7-8B unit under the wrong family refuses?
for (fam, seed), rel in list(units.items())[:1]:
    folder = MAIN / rel
    key = nr.sha256_file(folder / "COMPLETE.json")
    try:
        nr.read_unit({"path": str(folder), "complete_sha256": key}, "a0", seed, "olmo2-7b", X, "cross", MAIN)
        print("CROSS-FAMILY: accepted (DEFECT)")
    except SystemExit as e:
        print("CROSS-FAMILY (Llama unit as olmo2-7b): refused:", str(e)[:120])
# a 7-8B a0 unit fed as an R unit refuses?
    try:
        nr.read_unit({"path": str(folder), "complete_sha256": key, "arm": "edit-" + "0" * 64}, "R", seed, "llama31-8b", X, "asR", MAIN)
        print("A0-AS-R: accepted (DEFECT)")
    except SystemExit as e:
        print("A0-AS-R: refused:", str(e)[:120])
# the seed rule at the boundaries, exactly, through the same path N uses
from fractions import Fraction
def sig(pp):
    s = Fraction(pp); return ((s * s,), (Fraction(1),))
for pp in ("4.4999999", "4.5", "4.5000001", "5.9999999", "6.0", "6.0000001", "10.7061", "10.7062", "10.7063"):
    r = nr.seed_rule(sig(pp), 4)
    print(f"sigma {pp}: plan {r['plan']} review {r['review']} MDE {r['removal_mde_pp']:.4f} outcome {r['outcome']}")
# a two-term median above a threshold: sqrt(36)=6, sqrt(49)=7 -> 6.5 > 6 -> H ; sqrt(25)=5, sqrt(49)=7 -> 6.0 exactly -> B9?
print("median 6.5 ->", nr.seed_rule(((Fraction(1),), (Fraction(36), Fraction(49))), 4)["plan"],
      "; median exactly 6.0 ->", nr.seed_rule(((Fraction(1),), (Fraction(25), Fraction(49))), 4)["plan"],
      "; sdr2 term 36.0 exactly ->", nr.seed_rule(((Fraction(36),), (Fraction(1),)), 4)["plan"])
