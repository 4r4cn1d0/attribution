"""The verifier's cascade.py (R/r1-o-verify-scratch/cascade.py) for the per-index design: its four fill cases (and
two more), in memory; for each, which of the four kit forms (OEXT_78B[F], OEXT_78B_Y[F]) change. The wrapper holds no
index hash, so its bytes are the same before and after every fill (no INDEX_SHA256 replacement is needed)."""
import copy, sys
ws = sys.argv[1]
sys.path.insert(0, ws)
from scripts.scale78b import make_oext_settings_78b as mk
from scripts.scale78b import oext_78b as w
pins, psha = mk.load_pins()
assert not hasattr(w, "INDEX_SHA256")
def forms(p):
    files = mk.derive_all(p)
    return {(f, e): mk.form(f, e, files, w.code_pins(e)) for f in mk.FAMILIES for e in ("X", "Y")}
base = forms(pins)
cases = {
  "fill llama31-8b branch 128": lambda p: p["families"]["llama31-8b"].update(w1_18={"branch": "128", "record_sha256": "a"*64, "full_reason": None}),
  "fill llama31-8b theta0 job pin": lambda p: p["families"]["llama31-8b"]["units"]["untuned"].update(job_sha256="b"*64),
  "fill shared engine_y": lambda p: p["shared"].update(engine_y="e"*64),
  "fill olmo2-7b recipe_bqi": lambda p: p["families"]["olmo2-7b"].update(recipe_bqi=dict(p["families"]["olmo2-7b"]["main"])),
  "fill olmo2-7b branch 128": lambda p: p["families"]["olmo2-7b"].update(w1_18={"branch": "128", "record_sha256": "a"*64, "full_reason": None}),
  "fill llama31-8b recipe_g": lambda p: p["families"]["llama31-8b"].update(recipe_g={"name": "study-kt-llama31-8b-r64-g-mb2-20261011", "config_sha256": "442f133fb1861a74b57fe250023db53d4389fc2bad54c99dcd46bd56af920493"}),
}
for name, change in cases.items():
    p = copy.deepcopy(pins); change(p)
    new = forms(p)
    changed = sorted(f"{'OEXT_78B' if e == 'X' else 'OEXT_78B_Y'}[{f}]" for (f, e) in base if base[(f, e)] != new[(f, e)])
    print(f"{name:34s} -> forms changed: {changed}")
