"""prov's `kit` branch on REAL reader outputs: a caps world (synth_kit hb=False + extra_kit.with_caps) for cap_reports,
and extra_kit.cost_kit for cost_table; a minimal manifest per kit with the fields prov reads; then the script's prov
heredoc body verbatim, pass and one planted mismatch each."""
import hashlib, json, pathlib, re, subprocess, sys
WSA, WSD1, V2 = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2]), pathlib.Path(sys.argv[3])
ROOT = V2 / "root"                                  # the dry-run root: B16 (main), reading_input (ws-a), reading_extra (ws-d1)
sys.path[:0] = [str(ROOT), str(WSA / "scripts/stage1_s1/reading_input/tests"), str(WSD1 / "scripts/stage1_s1/reading_extra/tests")]
from scripts.stage1_s1.reading_extra.cap_reports import main as cap     # the dry-run root's packages first: a symlinked
from scripts.stage1_s1.reading_extra.cost_table import main as cost    # module's own sys.path insert would otherwise
from scripts.stage1_s1.reading_input.__main__ import main as builder   # resolve scripts.stage1_s1 from the main checkout
from scripts.stage1_s1.reading.__main__ import main as b16
import synth_kit as sk, extra_kit as ek
import platform, numpy
sha = lambda q: hashlib.sha256(pathlib.Path(q).read_bytes()).hexdigest()
W = V2 / "capsworld"
if W.exists():
    raise SystemExit("refuse: capsworld exists")
s = sk.make(W / "w", "plan_a", seed=0, hb=False)
ek.with_caps(s)
tables, sources, reading = W / "tables.json", W / "sources.json", W / "reading.json"
assert builder(s.args(tables, sources, overlap=False)) == 0
assert b16(["--input", str(tables), "--out", str(reading)]) == 0
rc = cap(["--kit", str(s.kit), "--record", str(sources), "--out", str(W / "cap_reports.json")]); print("cap_reports exit", rc)
kit2, slots, plan2 = ek.cost_kit(W / "c", "plan_a")
rc = cost(["--kit", str(kit2), "--reading", "plan_a", "--out", str(W / "cost_table.json")]); print("cost_table exit", rc)
def manifest(kit, path):
    files = {}
    for d in ("scripts/stage1_s1/reading", "scripts/stage1_s1/reading_extra"):
        for q in sorted((ROOT / d).glob("*.py")):
            files[q.relative_to(ROOT).as_posix()] = sha(q)
    files["scripts/stage1_s1/reading/settings/reading.json"] = sha(ROOT / "scripts/stage1_s1/reading/settings/reading.json")
    doc = {"files": files, "kit": {"plan_json_sha256": sha(kit / "plan.json"), "seal_A": sha(kit / "seals/block-A.json"),
                                   "seal_B": sha(kit / "seals/block-B.json")},
           "python": {"python": platform.python_version(), "numpy": numpy.__version__}}
    path.write_text(json.dumps(doc, indent=1, sort_keys=True)); return doc
m1 = manifest(s.kit, W / "m-caps.json"); m2 = manifest(kit2, W / "m-cost.json")
body = re.findall(r"prov\(\) \{.*?<<'EOF'\n(.*?)\nEOF\n", (V2 / "../../runbook/reading.zsh").read_text(), flags=re.S)[0]
(W / "prov_body.py").write_text(body + "\n")
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
def prov(m, out, *spec):
    r = subprocess.run([PY, "-I", "-B", str(W / "prov_body.py"), str(m), str(out), *spec], capture_output=True, text=True)
    return r.returncode, r.stdout.strip()[-400:]
print("cap_reports prov:", prov(W / "m-caps.json", W / "cap_reports.json", "reading=plan_a", "modules=scripts/stage1_s1/reading_extra/:*", "b16", f"input:sources.json={sources}", "kit"))
print("cost_table prov:", prov(W / "m-cost.json", W / "cost_table.json", "reading=plan_a", "modules=scripts/stage1_s1/reading_extra/:*", "b16", "kit"))
# planted mismatches: another kit's manifest (seals and plan differ); a wrong input file
print("cap_reports against the cost kit's manifest (kit must be false):", prov(W / "m-cost.json", W / "cap_reports.json", "reading=plan_a", "modules=scripts/stage1_s1/reading_extra/:*", "b16", f"input:sources.json={sources}", "kit"))
print("cap_reports with tables.json as the sources input (input must be false):", prov(W / "m-caps.json", W / "cap_reports.json", "reading=plan_a", "modules=scripts/stage1_s1/reading_extra/:*", "b16", f"input:sources.json={tables}", "kit"))
d = json.loads((W / "cap_reports.json").read_text()); print("cap_reports provenance keys:", sorted(d["provenance"]), "; kit:", {k: (v if k != "seals" else sorted(v)) for k, v in d["provenance"]["kit"].items()}, "; modules:", sorted(d["provenance"]["modules"]))
d = json.loads((W / "cost_table.json").read_text()); print("cost_table provenance keys:", sorted(d["provenance"]), "; inputs:", d["provenance"]["inputs"], "; b16_modules keys:", len(d["provenance"]["b16_modules"]))
# the extractor's key lists against the real outputs
KEYS = {"cap_reports": ("readings", "branch", "route_per_source", "ln14", "ln19"), "cost_table": ("readings", "units", "arms", "references", "b10_references", "b10_per_reference", "diagnostics_by_kind", "charging")}
for name, keys in KEYS.items():
    d = json.loads((W / f"{name}.json").read_text()); print(name, "extractor keys missing from the output:", [k for k in keys if k not in d])
# the step-0.7 pre-check on the cost kit (ledgers exist): must pass
r = subprocess.run([PY, "-I", "-B", str(V2 / "blocks/ledger_precheck.py"), str(kit2), "A", "B"], capture_output=True, text=True)
print("ledger pre-check on the cost kit: exit", r.returncode, r.stdout.strip()[:300])
