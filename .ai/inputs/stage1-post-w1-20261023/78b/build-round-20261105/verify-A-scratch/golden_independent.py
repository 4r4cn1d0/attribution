"""Verifier's independent golden numbers (no import of rules_78b): from KCR §4's printed constants (KCR:100) and from
the basis file's exact maxima; caps, guards, spend uppers, block-0 need. Compared with KCR §4/§7/§8/:177 values."""
import json, math, sys
from decimal import Decimal, ROUND_HALF_UP

BASIS = "/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-a/runkit/stage1-78b/measured-basis-78b.json"
KCR_C = {"olmo2-7b": (24.26, 314.0, 240.9, 20.0, 109.0, 6450.0), "llama31-8b": (22.89, 246.9, 250.3, 20.0, 163.0, 8466.0)}
KCR_EXPECT = {
    "olmo2-7b": dict(gen=8264, up38=10565, req38=12365, req33=12243, caps=[4.25, 6.5, 8.5, 10.5], guards=[13.86, 18.03, 21.73, 25.43],
                     spend=[5.12, None, None, 16.18], per_arm=[5.12, 4.40, 4.17, 4.05]),
    "llama31-8b": dict(gen=8510, up38=10813, req38=12613, req33=12499, caps=[4.5, 7.25, 9.75, 12.5], guards=[14.33, 19.41, 24.04, 29.13],
                       spend=[6.27, None, None, 20.80], per_arm=[6.27, 5.56, 5.32, 5.20]),
}
SCORE, START, OVERHEAD, STEP = 1250.0, 1800.0, 48 * 60, 900.0
RESERVE, PLAN, RATE, CONT = 6.0, 1.85, 1.79, 1.25


def cents(x):
    return float(Decimal(repr(x)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))


def up(x):  # round up to 0.25 h in seconds
    return math.ceil(round(x, 6) / STEP) * STEP


def table(c, label):
    tps, first, batch, early, outside, armmax = c
    gen = max(first, batch) + 33 * batch
    up38 = 38 * tps + gen + SCORE + early + outside
    up33 = 33 * tps + gen + SCORE + early + outside
    req38, req33 = up38 + START, up33 + START
    mu = 1.15 * armmax
    caps, guards, spends, per_arm = [], [], [], []
    for n in range(1, 5):
        reqs = [req33] * (n - 1) + [req38]
        worst = max(OVERHEAD + k * mu + reqs[k] for k in range(n))   # sum over j<k of the measured upper = k x mu
        cap_h = up(worst) / 3600
        caps.append(cap_h); guards.append(cents(RESERVE + cap_h * PLAN))
        spend = (OVERHEAD + n * mu) / 3600 * RATE
        spends.append(cents(spend)); per_arm.append(cents(spend / n))
    print(f"  [{label}] gen {gen:.3f} up38 {up38:.3f} up33 {up33:.3f} req38 {req38:.3f} req33 {req33:.3f} mu {mu:.2f}")
    print(f"           caps {caps} guards {guards} spends {spends} per_arm {per_arm}")
    return dict(gen=gen, up38=up38, req38=req38, req33=req33, caps=caps, guards=guards, spends=spends, per_arm=per_arm, mu=mu)


def main():
    basis = json.load(open(BASIS))
    ok = True
    live = {}
    for fam in ("olmo2-7b", "llama31-8b"):
        print("==", fam)
        k = table(KCR_C[fam], "KCR printed")
        f = basis["families"][fam]
        exact = (f["train_step_max_s"], f["first_batch_max_s"], f["batch_max_s"], f["early_max_s"], f["outside_max_s"], f["arm_job_max_s"])
        l = table(exact, "basis exact")
        live[fam] = l
        e = KCR_EXPECT[fam]
        checks = [
            ("KCR gen rounds to KCR", round(k["gen"]) == e["gen"]), ("KCR up38", round(k["up38"]) == e["up38"]),
            ("KCR req38", round(k["req38"]) == e["req38"]), ("KCR req33", round(k["req33"]) == e["req33"]),
            ("live req38 within 1.2 of KCR", abs(l["req38"] - e["req38"]) <= 1.2),
            ("live req33 within 1.2 of KCR", abs(l["req33"] - e["req33"]) <= 1.2),
            ("live caps == KCR §7", l["caps"] == e["caps"]), ("KCR-printed caps == KCR §7", k["caps"] == e["caps"]),
            ("live guards == KCR §7", l["guards"] == e["guards"]),
            ("live spend 1/4 == KCR §8", l["spends"][0] == e["spend"][0] and l["spends"][3] == e["spend"][3]),
            ("live per-arm == KCR §8 rule column", l["per_arm"] == e["per_arm"]),
        ]
        for name, c in checks:
            ok &= c
            print(f"   {'ok ' if c else 'BAD'} {name}")
        print(f"   live req38 - KCR = {l['req38'] - e['req38']:+.3f}; req33 diff {l['req33'] - e['req33']:+.3f}")
        # cap slack: seconds from the unrounded worst to the cap boundary, for 4 arms
        reqs = [l["req33"]] * 3 + [l["req38"]]
        worst4 = max(OVERHEAD + kk * l["mu"] + reqs[kk] for kk in range(4))
        print(f"   4-arm worst {worst4:.2f} s, cap {l['caps'][3]*3600:.0f} s, slack {l['caps'][3]*3600 - worst4:.2f} s")
    # block 0 (KCR:177): OLMo 3 x 33-step arms (cap 8.5 h); Llama 3 x 33 + a0 38 (cap 12.5 h)
    o, L = live["olmo2-7b"], live["llama31-8b"]
    cap_o = up(max(OVERHEAD + kk * o["mu"] + o["req33"] for kk in range(3))) / 3600
    cap_l = up(max(OVERHEAD + kk * L["mu"] + ([L["req33"]] * 3 + [L["req38"]])[kk] for kk in range(4))) / 3600
    guard = cents(RESERVE + PLAN * (cap_o + cap_l))
    spend_o = cents((OVERHEAD + 3 * o["mu"]) / 3600 * RATE); spend_l = cents((OVERHEAD + 4 * L["mu"]) / 3600 * RATE)
    need = cents(float(Decimal(repr(guard)) * Decimal(repr(CONT))))
    print(f"== block 0: caps {cap_o} / {cap_l}; guard {guard}; spend {spend_o} + {spend_l} = {cents(spend_o + spend_l)}; need {need}")
    b0 = cap_o == 8.5 and cap_l == 12.5 and guard == 44.85 and cents(spend_o + spend_l) == 33.30 and need == 56.06
    ok &= b0
    print("   ok block 0 == KCR:177" if b0 else "   BAD block 0")
    # two 33-step Llama arms: 7.0 h (KCR §7 note)
    two = up(max(OVERHEAD + L["req33"], OVERHEAD + L["mu"] + L["req33"])) / 3600
    print(f"== Llama two 33-step arms cap {two} (KCR: 7.0)"); ok &= two == 7.0
    print("ALL GOLDEN CHECKS PASS" if ok else "A GOLDEN CHECK FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
