"""Write one synthetic world under ROOT/world and its pins file ROOT/pins.json.

    python -B mkworld.py ROOT SEED [KIND]

KIND (optional) crafts adverse units with hlc_world.make(crafted=...), keeping every other unit's random stream:
  plain       hlc_world.make(seed) as is
  lowu        S3 at 1102-1104 and a0 at 1101-1103 with low Unsafe shares (0.01-0.04), many prompts holding a HarmBench
              "yes" and a "no" Unsafe answer, and theta0 at 0.03
  zerou       H1 1103 with no Unsafe answer; L1 1102 with exactly one; S1 1104 with no "Refusal: Yes" and one "No"
  bothlabels  every Unsafe answer of A1 1102-1104 sits on a prompt that holds a "yes" and a "no" Unsafe answer
"""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import v2lib  # noqa: E402
import hlc_world as hw  # noqa: E402

HARM, OVR = hw.HARM, hw.OVR


def spec(rng, unsafe, both=0.5, yes_hb=0.5, invalid=0.03, contro=0.05, yes=0.12, pair_prompts=None):
    """A unit whose Unsafe answers cluster: a prompt is 'hot' with probability ``unsafe``*1.5; on a hot prompt each
    sample is Unsafe w.p. 2/3; with ``both`` a hot prompt's Unsafe answers get one 'yes' and one 'no' HarmBench label."""
    harm, hb, benign = [], {}, {}
    for p in HARM:
        hot = (pair_prompts is not None and p in pair_prompts) or (pair_prompts is None and rng.random() < unsafe * 1.5)
        mixed = rng.random() < both
        n_unsafe = 0
        for k in range(3):
            tokens, stop = int(rng.integers(1, 400)), ("max_new_tokens" if rng.random() < 0.03 else "eos")
            r = rng.random()
            if r < invalid:
                reason = hw.OVER_LIMIT if rng.random() < 0.6 else (hw.CONTROL if rng.random() < 0.5 else hw.GUARD_CAP)
                harm.append((p, k, False, None, None, reason, tokens, stop))
                hb[(p, k)] = "no"
                continue
            if hot and (pair_prompts is not None and k < 2 or pair_prompts is None and rng.random() < 2 / 3):
                harm.append((p, k, True, "Unsafe", ["Violent"], None, tokens, stop))
                if mixed or pair_prompts is not None:
                    hb[(p, k)] = "yes" if n_unsafe % 2 == 0 else ("unparsed" if rng.random() < 0.2 else "no")
                else:
                    hb[(p, k)] = "yes" if rng.random() < yes_hb else "no"
                n_unsafe += 1
            elif rng.random() < contro:
                harm.append((p, k, True, "Controversial", ["Non-violent Illegal Acts"], None, tokens, stop))
                hb[(p, k)] = "yes" if rng.random() < 0.05 else "no"
            else:
                harm.append((p, k, True, "Safe", [], None, tokens, stop))
                hb[(p, k)] = "yes" if rng.random() < 0.02 else "no"
    for d in OVR:
        tokens, stop = int(rng.integers(1, 900)), ("max_new_tokens" if rng.random() < 0.03 else "eos")
        if rng.random() < 0.02:
            benign[d] = (False, None, None, None, hw.CONTROL, tokens, stop)
        else:
            benign[d] = (True, "Safe", "Yes" if rng.random() < yes else "No", [], None, tokens, stop)
    return hw.Spec(harm, hb, benign)


def crafted(kind: str, seed: int) -> dict:
    rng = np.random.default_rng(10_000 + seed)
    out = {}
    if kind == "lowu":
        for j in (1101, 1102, 1103):
            out[f"a0 {j}"] = spec(rng, 0.02 + 0.01 * (j - 1101), both=0.6)
        for j in (1102, 1103, 1104):
            out[f"S3 {j}"] = spec(rng, 0.01 + 0.01 * (j - 1102), both=0.7, yes_hb=0.3)
        out["theta0"] = spec(rng, 0.03, both=0.5, yes=0.17)
    elif kind == "zerou":
        out["H1 1103"] = spec(rng, 0.0)
        s = spec(rng, 0.0)
        s.harm[30] = (s.harm[30][0], s.harm[30][1], True, "Unsafe", ["Violent"], None, 5, "eos")
        out["L1 1102"] = s
        s = spec(rng, 0.2)
        first = True
        for d in list(s.benign):
            v = s.benign[d]
            s.benign[d] = (True, "Safe", "No" if first else "Yes", [], None, v[5], v[6]) if v[0] else v
            first = False
        out["S1 1104"] = s
        out["theta0"] = spec(rng, 0.005, yes=0.17)
    elif kind == "bothlabels":
        for j in (1102, 1103, 1104):
            pairs = set(HARM[5 * (j - 1100): 5 * (j - 1100) + 4 + (j - 1102)])
            out[f"A1 {j}"] = spec(rng, 0.0, pair_prompts=pairs)
    elif kind != "plain":
        raise SystemExit(f"unknown kind {kind}")
    return out


root = Path(sys.argv[1])
seed = int(sys.argv[2]) if len(sys.argv) > 2 else 0
kind = sys.argv[3] if len(sys.argv) > 3 else "plain"
w = hw.make(root / "world", seed=seed, crafted=crafted(kind, seed) or None)
(root / "pins.json").write_text(__import__("json").dumps(v2lib.world_pins(w)))
print("world", root / "world", "seed", seed, "kind", kind)
