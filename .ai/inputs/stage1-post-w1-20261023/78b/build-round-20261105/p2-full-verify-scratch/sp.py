import sys; sys.path.insert(0, sys.argv[1]); sys.dont_write_bytecode=True
import stage1_rules as sr
print("SCORER_PINS", len(sr.SCORER_PINS))
