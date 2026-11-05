"""Verifier's own recompute of the 7-8B constants from the 17 units' allow-listed timing files (no import of the
builder's code). Opens ONLY: hosts/<h>/{finished,create-result,verification}.json, retrieved/<h>/tree/{BOOTSTRAP-READY,
PREFLIGHT-DONE,JOB-DONE}.json, retrieved/<h>/tree/round1/<unit>/{ledger,progress}.jsonl. Prints numbers and short
host names only. Compares with the builder's FAMILIES constants (typed in here from rules_78b.py:132-152, R)."""
import json, pathlib, sys

ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution/tmp")
KITS = {
    "olmo2-7b": ["family-probe-sp-olmo2-7b-b-a0", "family-probe-sp-olmo2-7b-b-seed1102", "family-probe-sp-olmo2-7b-b-seed1103",
                 "family-probe-sp-olmo2-7b-b5e5-seed1101", "family-probe-sp-olmo2-7b-b5e5-seed1102", "family-probe-sp-olmo2-7b-b5e5-seed1103",
                 "family-probe-sp-olmo2-7b-g-seed1101", "family-probe-sp-olmo2-7b-g-seed1102", "family-probe-sp-olmo2-7b-g-seed1103"],
    "llama31-8b": ["family-probe-sp-llama31-8b-b-a0", "family-probe-sp-llama31-8b-b-seed1102", "family-probe-sp-llama31-8b-b-seed1103",
                   "family-probe-sp-llama31-8b-b5e5-1101", "family-probe-sp-llama31-8b-b5e5-seed1102",
                   "family-probe-sp-llama31-8b-g-seed1101", "family-probe-sp-llama31-8b-g-seed1102", "family-probe-sp-llama31-8b-g-seed1103"],
}
BUILDER = {  # R: rules_78b.py:132-152
    "olmo2-7b": dict(TRAIN_STEP_MAX_S=24.2545, FIRST_BATCH_MAX_S=314.049, BATCH_MAX_S=240.945, EARLY_MAX_S=19.877,
                     OUTSIDE_MAX_S=108.638, ARM_JOB_MAX_S=6450.0, PRE_TRAINING_S_MAX=1202.0527407700815,
                     PRE_MS_PER_STEP_MAX=269.0282543626381, A0_PADDED_TOKENS_PER_STEP=38342.79),
    "llama31-8b": dict(TRAIN_STEP_MAX_S=22.8848, FIRST_BATCH_MAX_S=246.86, BATCH_MAX_S=250.305, EARLY_MAX_S=19.703,
                       OUTSIDE_MAX_S=162.778, ARM_JOB_MAX_S=8466.0, PRE_TRAINING_S_MAX=1261.7852040079888,
                       PRE_MS_PER_STEP_MAX=104.31670475918509, A0_PADDED_TOKENS_PER_STEP=41311.74),
}
ALLOWED = {"finished.json", "create-result.json", "verification.json", "BOOTSTRAP-READY.json", "PREFLIGHT-DONE.json",
           "JOB-DONE.json", "ledger.jsonl", "progress.jsonl"}
EARLY = ("load_policy", "tokenize", "memory_preflight", "init_state")
OPENED = []


def rd(p: pathlib.Path):
    assert p.name in ALLOWED, p.name
    assert not any(part in ("eval", "generations", "samples", "prompts", "ssh", "hidden", "states") for part in p.parts), p
    OPENED.append(p.name)
    with open(p, "r", encoding="utf-8") as h:
        if p.suffix == ".jsonl":
            return [json.loads(l) for l in h if l.strip()]
        return json.load(h)


def one(family, kit_name):
    kit = ROOT / kit_name
    hosts = [h for h in (kit / "hosts").iterdir() if h.is_dir() and (h / "finished.json").is_file()]
    assert len(hosts) == 1, (kit_name, len(hosts))
    h = hosts[0]
    tree = kit / "retrieved" / h.name / "tree"
    fin = rd(h / "finished.json"); cr = rd(h / "create-result.json"); ver = rd(h / "verification.json")
    ready = rd(tree / "BOOTSTRAP-READY.json"); pre = rd(tree / "PREFLIGHT-DONE.json"); done = rd(tree / "JOB-DONE.json")
    assert fin["status"] == "verified-and-stopped" and fin["outer_exit"] == 0 and done["ok"]
    outer = float(fin["outer_elapsed_min"]) * 60
    units = sorted(p for p in (tree / "round1").iterdir() if p.is_dir())
    e1 = [p for p in units if "-e1-" in p.name]
    assert len(e1) == 1
    led = rd(e1[0] / "ledger.jsonl"); prog = rd(e1[0] / "progress.jsonl")
    other = sum(float(r["seconds"]) for p in units if p is not e1[0] for r in rd(p / "ledger.jsonl"))
    assert all(r["status"] == "ok" for r in led)
    # stage seconds: the builder rounds each stage to 3 dp before summing; I sum raw and also the 3-dp way.
    stage_raw = {}
    for r in led:
        stage_raw[r["stage"]] = stage_raw.get(r["stage"], 0.0) + float(r["seconds"])
    sum_raw = sum(stage_raw.values())
    sum_3dp = sum(round(v, 3) for v in stage_raw.values())
    train = [r for r in led if r["stage"] == "train"]
    steps = sum(int(r["steps"]) for r in train); train_s = sum(float(r["seconds"]) for r in train)
    padded = sum(int(r["padded_tokens"]) for r in train)
    early = sum(stage_raw.get(s, 0.0) for s in EARLY)
    gen = next(r for r in led if r["stage"] == "generate"); smp = next(r for r in led if r["stage"] == "sample")
    # batches: generate rows inside each stage window, differences of elapsed_s (very first from generate start_s)
    rows = sorted((r for r in prog if r.get("kind") == "generate"), key=lambda r: r["elapsed_s"])
    greedy = [r for r in rows if gen["start_s"] < r["elapsed_s"] <= gen["end_s"]]
    sampled = [r for r in rows if smp["start_s"] < r["elapsed_s"] <= smp["end_s"]]
    assert len(greedy) == 15 and len(sampled) == 19, (len(greedy), len(sampled))
    assert [int(r["batch"]) for r in greedy] == list(range(15)) and [int(r["batch"]) for r in sampled] == list(range(19))
    seq = greedy + sampled
    prev = float(gen["start_s"])
    secs = []
    for r in seq:
        secs.append(float(r["elapsed_s"]) - prev); prev = float(r["elapsed_s"])
    first = secs[0]
    cap32 = [s for s, r in zip(secs[1:], seq[1:]) if int(r["capped"]) > 0 and int(r["rows"]) == 32]
    # also: the slowest capped batch of ANY row count after the first (a stricter alternative)
    cap_any = [s for s, r in zip(secs[1:], seq[1:]) if int(r["capped"]) > 0]
    cp, fl = ver["cap_projection"], ver["full_length"]
    return dict(unit=h.name, n_units=len(units), outer=outer, train_s=train_s, steps=steps, tps=train_s / steps,
                padded_per_step=padded / steps, early=early, outside_raw=outer - sum_raw - other,
                outside_3dp=outer - sum_3dp - other, first=first, cap32max=max(cap32) if cap32 else None,
                cap_any_max=max(cap_any) if cap_any else None, n_cap32=len(cap32),
                pre_train=float(cp["training_s"]), pre_ms=float(fl["ms_per_step_full"]),
                pre_done_train=pre.get("training_s"), pre_done_ms=pre.get("ms_per_step_full"),
                pre_done_has_untuned=("untuned_projected_s" in pre), untuned=float(cp["untuned_projected_s"]),
                engine=ready["engine_sha256"][:8], gpu=ver["environment"]["cuda"]["name"], price=cr["pod"]["costPerHr"],
                scoring=sum(stage_raw.get(s, 0.0) for s in ("load_guard", "query_loss", "arc_utility", "guard", "guard_samples", "harm_scores", "verify_trajectory")),
                gen_last_batch_rows=int(greedy[-1]["rows"]), smp_last_batch_rows=int(sampled[-1]["rows"]))


def main():
    ok = True
    for fam, kits in KITS.items():
        us = [one(fam, k) for k in kits]
        ft = [u for u in us if u["n_units"] == 1]
        got = dict(
            TRAIN_STEP_MAX_S=round(max(u["tps"] for u in us), 4),
            FIRST_BATCH_MAX_S=round(max(u["first"] for u in us), 3),
            BATCH_MAX_S=round(max(u["cap32max"] for u in us), 3),
            EARLY_MAX_S=round(max(u["early"] for u in us), 3),
            OUTSIDE_MAX_S=round(max(u["outside_3dp"] for u in us), 3),
            ARM_JOB_MAX_S=max(u["outer"] for u in ft),
            PRE_TRAINING_S_MAX=max(u["pre_train"] for u in us),
            PRE_MS_PER_STEP_MAX=max(u["pre_ms"] for u in us),
            A0_PADDED_TOKENS_PER_STEP=round(min(u["padded_per_step"] for u in us), 2),
        )
        print(f"== {fam}: {len(us)} units, {len(ft)} fine-tune-only; engines {sorted({u['engine'] for u in us})}; "
              f"gpu {sorted({u['gpu'] for u in us})}; price {sorted({u['price'] for u in us})}")
        for k, v in got.items():
            b = BUILDER[fam][k]
            same = abs(v - b) < 1e-9
            ok &= same
            print(f"  {k:28s} mine {v!r:>22} builder {b!r:>22} {'EQUAL' if same else 'DIFF'}")
        print(f"  outside raw-sum max {max(u['outside_raw'] for u in us):.3f}; cap-any-rows max {max(u['cap_any_max'] for u in us):.3f}; "
              f"scoring max {max(u['scoring'] for u in us):.3f}; untuned_projected max {max(u['untuned'] for u in us):.3f}")
        print(f"  PREFLIGHT-DONE has untuned_projected_s: {sorted({u['pre_done_has_untuned'] for u in us})}; "
              f"PREFLIGHT-DONE training_s == verification cap_projection training_s on all: "
              f"{all(abs(float(u['pre_done_train']) - u['pre_train']) < 1e-9 for u in us)}; ms equal: "
              f"{all(abs(float(u['pre_done_ms']) - u['pre_ms']) < 1e-9 for u in us)}")
        print(f"  last greedy batch rows {sorted({u['gen_last_batch_rows'] for u in us})}, last sampled rows {sorted({u['smp_last_batch_rows'] for u in us})}")
        for u in us:
            print(f"    {u['unit']:24s} outer {u['outer']:8.1f} n_units {u['n_units']} tps {u['tps']:.4f} first {u['first']:.3f} "
                  f"cap32 {u['cap32max']:.3f} (n {u['n_cap32']:2d}) capany {u['cap_any_max']:.3f} early {u['early']:.3f} "
                  f"outside {u['outside_3dp']:.3f} pre {u['pre_train']:.2f}/{u['pre_ms']:.2f}")
    print("opened basenames:", sorted(set(OPENED)), "count", len(OPENED))
    print("ALL CONSTANTS EQUAL" if ok else "SOME CONSTANT DIFFERS")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
