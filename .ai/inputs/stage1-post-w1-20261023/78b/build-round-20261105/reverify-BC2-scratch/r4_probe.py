"""R4 gap probe: the fixer's test perturbs a0@1102 only, so any reference but a0@1102 passes it (my mutants a0@1103 and
R@1101 survived). The assertion a stronger test needs: perturb a0@1101 (the reference itself) and read the attribution
with the REAL code: the reference records [] and every other unit records ["gpu"]. Reads the wave-0a and Gate A units
through the frozen reader only; prints the attribution dict, the governing reading and sigma_F (no text).
Usage: python -I -B r4_probe.py <ws-c> <scratch>"""
import pathlib
import sys

WS = pathlib.Path(sys.argv[1]).resolve()
SCR = pathlib.Path(sys.argv[2]).resolve() / "r4probe"
SCR.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(WS))
sys.path.insert(0, str(WS / "scripts/scale78b/tests"))
import test_noise_reading as T  # noqa: E402  (its parity_family / write_inputs helpers; no test runs)
from scripts.scale78b import noise_reading as nr  # noqa: E402

if not T.wave0a_present():
    print("wave-0a / Gate A units absent: nothing measured")
    sys.exit(0)
real = nr.read_unit


def perturbed(role_seed):
    def read_unit(spec, role, seed, family, engine, where, base):
        unit = real(spec, role, seed, family, engine, where, base)
        if (role, seed) == role_seed:
            unit = {**unit, "fields": {**unit["fields"], "gpu": "another device"}}
        return unit
    return read_unit


for role_seed in (("a0", 1101), ("a0", 1102), ("a0", 1103), ("R", 1101)):
    nr.read_unit = perturbed(role_seed)
    fam = nr.read(T.write_inputs(SCR, {"olmo2-1b": T.parity_family()}, f"inputs-{role_seed[0]}-{role_seed[1]}.json"))["families"]["olmo2-1b"]
    d = fam["triggers"]["environment_differs"]
    print(f"perturb {role_seed[0]}@{role_seed[1]} (real code, reference a0@1101): differs = {d}; environment trigger {fam['triggers']['environment']}; governing {fam['governing']}; sigma_F {round(fam['sigma_F_pp'], 2)}")
nr.read_unit = real
fam = nr.read(T.write_inputs(SCR, {"olmo2-1b": T.parity_family()}, "inputs-none.json"))["families"]["olmo2-1b"]
print(f"no perturbation: differs = {fam['triggers']['environment_differs']}; environment trigger {fam['triggers']['environment']}; governing {fam['governing']}")
import shutil  # noqa: E402
shutil.rmtree(SCR)
