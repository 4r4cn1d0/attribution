import json, sys
p = "/Users/spiderishi/Coding/attribution/tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1/ledger.jsonl"
rows = [json.loads(l) for l in open(p) if l.strip()]
print("stage order and gaps (s) for unit 1103 (stage names and numbers only):")
prev_end = None
for r in rows:
    gap = (r["start_s"] - prev_end) if prev_end is not None else r["start_s"]
    print("  %-18s start %9.2f secs %8.2f gap_before %6.2f" % (r["stage"], r["start_s"], r["seconds"], gap))
    prev_end = r["end_s"]
