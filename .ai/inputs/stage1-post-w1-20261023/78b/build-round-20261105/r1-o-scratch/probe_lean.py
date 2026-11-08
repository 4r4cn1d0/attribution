import sys, shutil, json
from pathlib import Path
WS = Path(sys.argv[1]); base = Path(sys.argv[2])
sys.path.insert(0, str(WS / "scripts/scale78b/tests/oext"))
import conftest  # noqa
import oext78_fixtures as f
import b17_support as bs
if base.exists(): shutil.rmtree(base)
base.mkdir(parents=True)
prepared_dir, manifest = bs.prepared_dirs(base / "prep")
fam = f.Family(base / "fam"); fam.manifest = manifest
inp = f.oext_inputs(base / "inputs", fam, branch="128")
common = {"lean.overrefusal_bank.status": "oext_pinned", "oext.module_sha256": f.oe.module_sha256(),
          "oext.settings.sha256": inp.eval_sha, "oext.branch": "128"}
doc78 = bs.settings_doc(**common, **{"oext.settings.path": fam.label("oext_eval")})
fam.put("lean_eval_job", doc78)
doc1b = bs.settings_doc(**common)
p1b = base / "1b" / "lean_eval_job.json"; s1b = f.write(p1b, doc1b)
rec = bs.recipe(); rp = bs.write_recipe(base / "recipe.json", rec)
job = base / "job.json"; bs.write_job(job, prepared_dir, rec)
def args(out): return ["run", "--job", str(job), "--prepared", str(prepared_dir), "--recipe", str(rp), "--out", str(out),
                       "--oext-bank", str(inp.bank), "--oext-record", str(inp.record), "--w1-18-record", str(inp.w1_18)]
out = base / "out"
code, so, se = f.wrapper(fam, ["lean", "--family", f.FAMILY, *args(out)], loaders=bs.fx.fixture_loaders())
print("wrapper", code, se[-300:])
out.rename(base / "out-w")
lej = bs.lej
with f.w.patched([(lej, "SETTINGS_PATH", p1b), (lej, "SETTINGS_SHA256", s1b)]):
    code, so2, se2 = f.call(lej.main, args(out), loaders=bs.fx.fixture_loaders(), oext_settings=f.oe.settings_from_doc(inp.eval_doc))
print("direct", code, se2[-300:])
try:
    res = f.compare(base / "out-w", out, set())
except AssertionError as e:
    print("assert", e); res = {}
print({k: v for k, v in res.items() if v != "bytes"})
a, c = json.loads((base/"out-w/c0_record.json").read_bytes()), json.loads((out/"c0_record.json").read_bytes())
def diff(x, y, p=""):
    if isinstance(x, dict) and isinstance(y, dict):
        for k in sorted(set(x) | set(y)): diff(x.get(k), y.get(k), p + "." + k)
    elif x != y: print(p)
diff(f.strip(a), f.strip(c))
