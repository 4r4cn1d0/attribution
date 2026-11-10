"""Changed key paths between a 1B settings file and a derived one (values: hashes, paths, short ids; texts by length)."""
import json, sys, re
HEX = re.compile(r"^[0-9a-f]{64}$")
def flat(o, p="", out=None):
    out = {} if out is None else out
    if isinstance(o, dict):
        if not o: out[p] = {}
        for k, v in o.items(): flat(v, f"{p}.{k}" if p else k, out)
    else:
        out[p] = o
    return out
def show(v):
    if isinstance(v, str) and not (HEX.match(v) or v.startswith(("scripts/", "experiments/", "kt-", "family-")) or len(v) <= 24):
        return f"<text {len(v)}>"
    return json.dumps(v)[:140]
ws = sys.argv[1]
pairs = [("scripts/stage1_s1/settings/oext_eval.json", "oext_eval__{f}"), ("scripts/stage1_s1/settings/oext_eval_y.json", "oext_eval_y__{f}"),
         ("scripts/stage1_s1/settings/oext_unit.json", "oext_unit__{f}"), ("scripts/stage1_s1/settings/oext_unit_y.json", "oext_unit_y__{f}"),
         ("scripts/stage1_s1/settings/lean_eval_job.json", "lean_eval_job__{f}")]
for base, der in pairs:
    a = flat(json.load(open(f"{ws}/{base}")))
    for fam in ("olmo2-7b", "llama31-8b"):
        name = der.format(f=fam)
        b = flat(json.load(open(f"{ws}/scripts/scale78b/settings/{name}.json")))
        print(f"== {base.split('/')[-1]} -> {name}")
        for k in sorted(set(a) | set(b)):
            if a.get(k, "<absent>") != b.get(k, "<absent>"):
                print(f"   {k}: {show(a.get(k, '<absent>'))} -> {show(b.get(k, '<absent>'))}")
