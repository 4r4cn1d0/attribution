"""Does a fill of one family's pin (or of engine Y) change the OTHER family's RK OEXT_78B form? In memory only:
derive with a changed pins dict, then the wrapper's bytes with INDEX_SHA256 replaced, then both forms."""
import copy, hashlib, json, sys
ws = sys.argv[1]
sys.path.insert(0, ws)
from scripts.scale78b import make_oext_settings_78b as mk
from scripts.scale78b import oext_78b as w
sha = lambda b: hashlib.sha256(b).hexdigest()
pins, psha = mk.load_pins()
wrapper_bytes = open(w.__file__, "rb").read()
def forms(p, label):
    files = mk.derive_all(p, psha if p is pins else sha(json.dumps(p).encode()))
    idx = files[mk.INDEX_NAME]
    new_wrapper = wrapper_bytes.replace(w.INDEX_SHA256.encode(), sha(idx).encode())
    code = dict(w.code_pins()); code["scripts/scale78b/oext_78b.py"] = sha(new_wrapper)
    return {f: mk.oext_78b_form(f, idx, code) for f in mk.FAMILIES}
base = forms(pins, "now")
cases = {
  "fill llama31-8b branch 128": lambda p: p["families"]["llama31-8b"].update(w1_18={"branch": "128", "record_sha256": "a"*64, "full_reason": None}),
  "fill llama31-8b theta0 job pin": lambda p: p["families"]["llama31-8b"]["units"]["untuned"].update(job_sha256="b"*64),
  "fill shared engine_y": lambda p: p["shared"].update(engine_y="e"*64),
  "fill olmo2-7b recipe_bqi": lambda p: p["families"]["olmo2-7b"].update(recipe_bqi=dict(p["families"]["olmo2-7b"]["main"])),
}
for name, change in cases.items():
    p = copy.deepcopy(pins); change(p)
    new = forms(p, name)
    for fam in mk.FAMILIES:
        diff = sorted(k for k in set(base[fam]["files"]) | set(new[fam]["files"]) if base[fam]["files"].get(k) != new[fam]["files"].get(k))
        print(f"{name:34s} -> OEXT_78B[{fam}] files changed: {diff}")
