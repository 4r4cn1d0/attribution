"""How often does a seed's Unsafe cell lose HLC 4.2's HarmBench minimum ("at least 2 of each where they exist")
because the arm's earlier seeds already used the prompts that hold its scarce label (the no-prompt-twice rule; the
tool's reading 4 counts the minimum on prompts not yet used inside the arm)? The tool's own allocate, with the real
pinned settings, on simulated arms (3 seeds x 200 prompts x 3 samples, no exclusions). Unsafe answers cluster on
prompts and the same prompts are hot in every seed: prompt propensity h_p ~ Beta(0.2, 0.2 (1 - U) / U), each sample
Unsafe with probability h_p; each Unsafe answer HarmBench "yes" with probability q.

    python -B sim_cross.py ARMS SEED
"""

import random
import sys
from dataclasses import dataclass
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2lib  # noqa: E402

from scripts.stage1_s1.hlc_draw import draw as dr  # noqa: E402
from scripts.stage1_s1.hlc_draw import inputs as inp  # noqa: E402


@dataclass
class F:
    complete_sha256: str


def arm_units(rng, u, q, arm="S3"):
    h = rng.beta(0.2, 0.2 * (1 - u) / u, size=200)
    units = []
    for j, seed in enumerate((1102, 1103, 1104)):
        harm = []
        for p in range(200):
            for k in range(3):
                r = rng.random()
                if r < h[p]:
                    lab, hb = "Unsafe", ("yes" if rng.random() < q else "no")
                elif r < h[p] + 0.05:
                    lab, hb = "Controversial", "no"
                else:
                    lab, hb = "Safe", "no"
                harm.append(inp.Answer("harm", f"p{p:03d}", k, lab, (), lab, "No", None, 10, False, hb))
        benign = [inp.Answer("benign", f"d{d:03d}", None, "Yes" if rng.random() < 0.1 else "No", (), "Safe",
                             None, None, 10, False) for d in range(100)]
        units.append(inp.Unit(f"{arm} {seed}", arm, seed, "kit", "x", F(f"{arm}{seed}{rng.random()}"), "e1", harm,
                              benign))
    return units


def main():
    n_arms, seed = int(sys.argv[1]), int(sys.argv[2])
    cfg = v2lib.settings_with({"oct9": "0" * 64, "manifest": "0" * 64, "dev": "0" * 64})
    rng = np.random.default_rng(seed)
    print("U     q    seeds  cells where eligible yes/no prompts >= 2 but drawn < 2 | of which the cell's prompts "
          "were enough before earlier seeds' draws")
    for u in (0.03, 0.05, 0.10, 0.30):
        for q in (0.2, 0.5):
            lost = lost_cross = cells = 0
            for _ in range(n_arms):
                units = arm_units(rng, u, q)
                items, cell_recs, subs = dr.allocate(units, {}, cfg, "0")
                by = {}
                for s in subs:
                    if s["cell"] == "Unsafe":
                        by.setdefault(s["unit"], {})[s["sub_cell"]] = s
                for unit in units:
                    cells += 1
                    elig_prompts = {}
                    for a in unit.harm:
                        if a.label == "Unsafe":
                            elig_prompts.setdefault("Unsafe/yes" if a.harmbench == "yes" else "Unsafe/no",
                                                    set()).add(a.prompt_id)
                    for sub in ("Unsafe/yes", "Unsafe/no"):
                        e = len(elig_prompts.get(sub, ()))
                        d = by[unit.label][sub]["drawn"]
                        if e >= 2 and d < 2:
                            lost += 1
                            if by[unit.label][sub]["available_prompts"] < 2:
                                lost_cross += 1
                            else:                                    # not caused by earlier seeds: show why
                                y, m = by[unit.label]["Unsafe/yes"], by[unit.label]["Unsafe/no"]
                                c = next(r for r in cell_recs if r["unit"] == unit.label and r["cell"] == "Unsafe")
                                print(f"  other: U {u} q {q} {unit.label} {sub}: eligible prompts {e}, drawn {d}; "
                                      f"yes prompts {y['available_prompts']} target {y['target']}; no prompts "
                                      f"{m['available_prompts']} target {m['target']}; cell prompts "
                                      f"{c['available_prompts']} quota {c['quota']}")
            print(f"{u:<5} {q:<4} {cells:<6} {lost:<4} | {lost_cross}")


main()
