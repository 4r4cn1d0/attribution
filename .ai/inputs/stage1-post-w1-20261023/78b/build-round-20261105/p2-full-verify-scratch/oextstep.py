import sys
sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode = True
import rules_78b as rk
for f in ["olmo2-7b","llama31-8b"]:
    c = rk.family_of(f)
    b, fb = c["BATCH_MAX_S"], max(c["FIRST_BATCH_MAX_S"], c["BATCH_MAX_S"])
    ends = c["EARLY_MAX_S"] + c["OUTSIDE_MAX_S"]
    a = 13*b; a2 = fb + 12*b
    full = a2 + 0.5*rk.SCORE_ALLCAP_S + ends
    print(f, "13xbatch %.1f" % a, "first+12 %.1f" % a2, "+half score+ends %.1f" % full, "x1.5 %.1f" % (1.5*full), "batch %.1f first %.1f ends %.1f" % (b, fb, ends))
