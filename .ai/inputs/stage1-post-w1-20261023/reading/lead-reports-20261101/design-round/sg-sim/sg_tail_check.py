"""Tail check at Phi's U start level (two-sided 0.75%): 10,000 replicates per world (synthetic only)."""
import importlib.util
spec = importlib.util.spec_from_file_location("sgc", "sg_coherent_check.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
for sc, seed, ff, ns in (("A", 20261201, 0.08, 0.15), ("B", 20261202, 0.08, 0.15), ("B", 20261203, 0.08, 0.0), ("B", 20261204, 0.04, 0.0)):
    print("\n".join(m.simulate(sc, 10000, seed, ff, ns)))
