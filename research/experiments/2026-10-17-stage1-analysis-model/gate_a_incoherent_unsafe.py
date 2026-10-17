"""Unsafe share among answers that fail the frozen coherence screen, Gate A a0 units (counts only, via the frozen counts)."""
import json, pathlib, sys
MAIN = pathlib.Path("/Users/spiderishi/Coding/attribution")
sys.path.insert(0, str(MAIN / "scripts"))
import family_probe_reading as fpr  # read-only use
inputs = json.loads((MAIN / "tmp/gate-b-olmo/gate_b_inputs_noise_gate_post0b.json").read_text())
bars = json.loads(fpr.DEFAULT_BARS.read_text())
out = {}
for name in ("1101", "1102", "1103"):
    unit = pathlib.Path(inputs["gate_a"][name]); fpr.sealed(unit)
    folder = next(p for p in (unit / "eval").iterdir() if p.is_dir())
    c = fpr.counts(folder, bars, "olmo2", set())
    unsafe, n = c["frozen"]["sampled_unsafe"], c["sampled"]["n"]
    coh_n, coh_u = c["coherent_sampled"], c["coherent_sampled_unsafe"]
    inc_n, inc_u = n - coh_n, unsafe - coh_u
    out[name] = {"U_all": round(unsafe / n, 4), "U_coherent": round(coh_u / coh_n, 4),
                 "incoherent_n": inc_n, "incoherent_unsafe": inc_u, "U_among_incoherent": round(inc_u / inc_n, 4) if inc_n else None}
print(json.dumps(out, indent=1))
