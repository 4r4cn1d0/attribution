"""OLMo 3 7B Instruct memory estimate on an A100-SXM4-80GB from OLMo-2-7B's measured peaks (stdlib only; numbers only).
Measured inputs (M): tmp/family-probe-sp-olmo2-7b-b-seed1103/retrieved/sp-olmo2-7b-1103/tree/round1/1103-a0-e1-a1/ledger.jsonl
and tmp/family-probe-sp-olmo2-7b-b-seed1103/hosts/sp-olmo2-7b-1103/verification.json (main checkout)."""
CARD = 85_093_777_408                      # environment.cuda.total_memory_bytes (M)
PRE_BASE, PRE_PEAK = 15_303_975_424, 59_231_364_608      # memory_preflight: allocated before / peak, 2 rows x 2,114 tokens (M)
TRAIN_PEAK, TRAIN_RES = 61_109_104_128, 63_854_084_096   # train stage peak allocated / reserved (M)
GEN_PEAK, GEN_RES = 61_216_966_144, 84_487_962_624       # generate stage peak allocated / reserved (M)
CHECK_PEAK, CHECK_RES, RETRIES = 66_630_790_656, 84_490_059_776, 204   # full-length check (M)
LONGEST_O2, DELTA = 2_114, 24              # longest prepared row (M, manifest token_audit); OLMo 3 wrapper +23/+24 tokens (calc/limit_margin)
KV = 2 * 32 * 32 * 128 * 2                 # bytes per token: K and V, 32 layers, 32 KV heads, head dim 128, bf16 (R: config.json)
per_token = (PRE_PEAK - PRE_BASE) / (2 * LONGEST_O2)
frag = TRAIN_RES - TRAIN_PEAK
base = TRAIN_PEAK - 2 * LONGEST_O2 * per_token
emb = (100_278 - 100_352) * 4096 * 2 * 2   # untied input + output rows, bf16
def gb(x): return round(x / 1e9, 2)
def pct(x): return round(100 * x / CARD, 1)
rows = {
    "per_token_activation_MB": round(per_token / 1e6, 3), "per_token_per_layer_KB": round(per_token / 32 / 1e3, 1),
    "weights_delta_MB": round(emb / 1e6, 2),
    "o3_preflight_peak_GB": gb(PRE_PEAK + emb + 2 * DELTA * per_token),
    "o3_train_peak_GB": gb(TRAIN_PEAK + emb + 2 * DELTA * per_token),
    "o3_train_reserved_GB_pct": (gb(TRAIN_RES + 2 * DELTA * per_token), pct(TRAIN_RES + 2 * DELTA * per_token)),
    "mb2_at_3072_alloc_GB_pct": (gb(base + 2 * 3072 * per_token), pct(base + 2 * 3072 * per_token)),
    "mb2_at_3072_reserved_GB_pct": (gb(base + 2 * 3072 * per_token + frag), pct(base + 2 * 3072 * per_token + frag)),
    "mb1_at_3072_alloc_GB_pct": (gb(base + 3072 * per_token), pct(base + 3072 * per_token)),
    "mb4_at_2138_alloc_GB_pct": (gb(base + 4 * 2138 * per_token), pct(base + 4 * 2138 * per_token)),
    "mb2_longest_row_at_90pct_reserved": int((0.9 * CARD - frag - base) / per_token / 2),
    "kv_bytes_per_token": KV, "o3_extra_kv_per_batch_GB": gb(32 * DELTA * KV),
    "o3_gen_peak_GB_pct": (gb(GEN_PEAK + 32 * DELTA * KV), pct(GEN_PEAK + 32 * DELTA * KV)),
    "o3_check_peak_GB_pct": (gb(CHECK_PEAK + 32 * DELTA * KV), pct(CHECK_PEAK + 32 * DELTA * KV)),
    "o2_measured_gen_reserved_pct": pct(GEN_RES), "o2_measured_check_reserved_pct": pct(CHECK_RES), "o2_check_retries": RETRIES,
    "params_recomputed": 32 * (4 * 4096 * 4096 + 2 * 4096 + 3 * 4096 * 11008 + 2 * 4096) + 4096 + 2 * 100_278 * 4096,
    "lora_r64_recomputed": 32 * 64 * (4 * (4096 + 4096) + 2 * (4096 + 11008) + (11008 + 4096)),
}
for k, v in rows.items():
    print(k, v)
