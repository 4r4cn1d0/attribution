"""The family probes (brief multi-family-probe-engine-20261007): one entry per probe key (administrative data).

This is the OLMo 3 copy of runkit/family-probe/probes.py (the readiness scout's kit route, 1 Nov; O3A §16.8 "the kit
lives at a new path"). The original kit is unchanged. The five earlier entries are kept as they were; the OLMo 3 entry
``olmo3-7b`` is new (O3A §16.1, MC §1 and §6.3 item 5, CM §2.6):
  - an open repository (no token path), the three weight-shard pins and sizes of MC §1 (re-read from the Hub API by the
    lead's fetch of 1 Nov for the tokenizer files; the shard SHA-256 values are MC's, checked on the pod against the
    blob names by download_models_probe.py);
  - the download patterns are WEIGHTS plus ``chat_template.jinja`` (blocker B2: OLMo 3 keeps its template in that file);
  - ``audit_tokenizer`` None: the model's own tokenizer snapshot (the OLMo-2 pin does not apply, CM §6 alternative 2);
  - ``lock``: the OLMo 3-only lock, transformers 4.57.1, packed by hash in place of experiments/minimal_safety/
    requirements.lock (blocker B1); ``preflight_script``: scripts/cuda_preflight_olmo3.py (blocker B3; track A writes it);
  - ``rungs``: the per-family learning-rate ladder (FOCUS L163; O3A §16.2): rung 1 = 1e-4 ("b"), rung 2 = 5e-5
    ("b5e5"), rung 3 = 2e-5 ("b2e5"), each with the memory ladder mb2, mb1-gc, mb2-g16 (CM D-O5; mb4 is dropped, it ran
    out of memory on both 7-8B families, KCR §6). The recipe files carry the date suffix 20261104;
  - cap 7.0 h (O3A §1.2: the untuned evaluation at its all-capped bound plus the a0 arm), preflight wait 5,400 s and
    the 7B disk sizes.

Each entry: the policy (repository, revision, gated), the audit tokenizer (or None: the policy's own), the prepared
set, the recipe ladder (preflight candidates in order), the files of the policy download (exact names for gated
repositories; open repositories take WEIGHTS, or ``patterns`` when the entry lists them), the weight pins (SHA-256 of
every .safetensors file), the cap hours, the preflight wait and the pod's disk sizes.

Caps (review fix 9, ESTIMATES): the cap must hold setup, the preflight ladder and the job's true upper bound, which
the cap gate checks with 30 min to spare. The upper bound counts both evaluations as fully capped (the brief's rates
per decode step: 1B at a flat 99 ms, 7B/8B 113 ms, 13B 141 ms at batch 16), training, the job overhead (at least
1,000 s, the Qwen-7B check's 936 s) and 900 s. 1B: 0.25 h setup + 0.5 h preflight + 2 x 2.2 h + 0.1 + 0.28 + 0.25 h,
plus 0.5 h, gives 6.3 h -> 6.5 h. 7B/8B: 0.25 + 0.75 + 2 x 2.6 + 0.22 + 0.28 + 0.25 + 0.5 = 7.45 h -> 7.5 h. 13B at
batch 16: 0.25 + 1.0 + 2 x 6.0 + 0.42 + 0.4 + 0.25 + 0.5 = 14.8 h -> 15.0 h. olmo2-7b's batch-16 fallback needs
about 11.9 h and is refused by the cap gate at 7.5 h (the brief expects that). Measured rates replace these.
OLMo 3 (O3A §1.2, measured OLMo-2-7B times, KCR §4): 7.00 h for the probe pod; the same cap for a fine-tune-only pod
(KCR's 4.25 h would be the tight value; the lead may lower it per working copy).
"""
CFG = "experiments/safety_selection/configs"
WEIGHTS = ["*.json", "*.safetensors", "merges.txt", "vocab.json", "tokenizer*", "LICENSE", "README.md"]
TOKENIZER_FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]
GUARD = {"repo_id": "Qwen/Qwen3Guard-Gen-4B", "revision": "6ec42827da0c1ff11e7a49dc269d2e810d27e108", "gated": False}
OLMO_TOKENIZER = {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
                  "gated": False, "files": TOKENIZER_FILES + ["vocab.json", "merges.txt"]}
LLAMA_TOKENIZER = {"repo_id": "meta-llama/Llama-3.1-8B-Instruct", "revision": "0e9e39f249a16976918f6564b8830bc894c89659",
                   "gated": True, "files": TOKENIZER_FILES}

# OLMo 3 7B Instruct (O3A §16.1; MC §1): main at 6e5971d9 equals the weights commit d42dc9de in every weight, tokenizer
# and template file. Open repository, Apache-2.0. The lock is the engine lock with one line changed (transformers
# 4.56.2 -> 4.57.1), frozen 1 Nov 2026 (.ai/inputs/stage1-post-w1-20261023/olmo3/requirements-olmo3.lock).
OLMO3_REPO = "allenai/Olmo-3-7B-Instruct"
OLMO3_REVISION = "6e5971d9eba42665f5bd5a0fcf047f299ce1dccc"
OLMO3_CHAT_TEMPLATE = "chat_template.jinja"
OLMO3_SHARDS = {                     # MC §1: LFS SHA-256 -> bytes (identical in both tree reads of 17 Oct 2026)
    "e7bd4c8ba52177a815aee5929cb458a116a65799688d3e51402500a1cb77023c": 4_969_984_976,
    "ea92aa0499a2ca02400e5d87324009e172bdbfb9809f2ac501485d8224382328": 4_981_161_496,
    "d50f95e4f2ec5fc4fbce6217cbf54fd1d700928b05e5550c8ee08bf4ba948925": 4_644_917_240}
OLMO3_LOCK = {"path": "setup/requirements-olmo3.lock",                     # the kit's copy, relative to the kit folder
              "record": ".ai/inputs/stage1-post-w1-20261023/olmo3/requirements-olmo3.lock",   # the frozen record (ROOT-relative)
              "sha256": "e4aedff89a4bb0937f7e9f958beee8eb92f8e653a5b498d51e28da091c96ba66"}
OLMO3_PREFLIGHT = "cuda_preflight_olmo3.py"                                 # scripts/<name>; blocker B3 (track A)
OLMO3_DATE = "20261104"
RUNGS = {1: "b", 2: "b5e5", 3: "b2e5"}             # the recipe-name token of each learning-rate rung
LR_OF_RUNG = {1: 1e-4, 2: 5e-5, 3: 2e-5}           # the per-family LR rule's ladder (FOCUS L163)
OLMO3_MEMORY_LADDER = ["mb2", "mb1-gc", "mb2-g16"]  # CM D-O5


def ladder(probe: str, candidates: list[str]) -> list[str]:
    return [f"{CFG}/study-kt-{probe}-r64-b-{c}-20261008.json" for c in candidates]


def olmo3_ladder(rung: int) -> list[str]:
    """The OLMo 3 memory ladder at one learning-rate rung (the recipe files of this track, date 20261104)."""
    if rung not in RUNGS:
        raise SystemExit("rungs are 1 (1e-4), 2 (5e-5) and 3 (2e-5) (the per-family LR rule, FOCUS L163)")
    return [f"{CFG}/study-kt-olmo3-7b-r64-{RUNGS[rung]}-{c}-{OLMO3_DATE}.json" for c in OLMO3_MEMORY_LADDER]


PROBES = {
    "olmo2-1b": {
        "policy": {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
                   "gated": False, "files": None},
        "audit_tokenizer": None, "prepared": "prepared-kt-dolly-olmo2",
        "recipes": ladder("olmo2-1b", ["mb4", "mb2", "mb2-eager"]),
        "weight_pins": ["36d044c73655bb904f822915e6294ba3dae8e6e1af5e703e9d452f2d6a3a294f"],
        "cap_hours": 6.5, "preflight_wait_s": 3600, "container_disk_gb": 60, "volume_gb": 20},
    "olmo2-7b": {
        "policy": {"repo_id": "allenai/OLMo-2-1124-7B-Instruct", "revision": "470b1fba1ae01581f270116362ee4aa1b97f4c84",
                   "gated": False, "files": None},
        "audit_tokenizer": OLMO_TOKENIZER, "prepared": "prepared-kt-dolly-olmo2",
        "recipes": ladder("olmo2-7b", ["mb4", "mb2", "mb1-gc", "mb1-gc-eager", "mb2-g16", "mb1-gc-g16"]),
        "weight_pins": ["05ae91e1171f1f1753b23df3a5a6740d89da377932b33a1661bb7485d6ec530e",
                        "0d41b81fe0d7e4c1d673a77beded5ee77080e39d6a6940b523e82f61eaa1dcbd",
                        "51d701cc400703094ae4b6434b067ee8810056170ce4703e93b2f5b2cb93a51d"],
        "cap_hours": 7.5, "preflight_wait_s": 5400, "container_disk_gb": 60, "volume_gb": 30},
    "olmo2-13b": {
        "policy": {"repo_id": "allenai/OLMo-2-1124-13B-Instruct", "revision": "3a5c85baefbb1896a54d56fe2e76c0395627ddf4",
                   "gated": False, "files": None},
        "audit_tokenizer": OLMO_TOKENIZER, "prepared": "prepared-kt-dolly-olmo2",
        "recipes": ladder("olmo2-13b", ["mb2-g16", "mb1-g16", "mb1-gc-g16", "mb1-gc-eager-g16"]),
        "weight_pins": ["884503480a474aaabf839123612eef8aa28f2d50d08a49bb7a62d0d756dd0377",
                        "23c10fee35770c0f44166e20991fa4a3da88044652ce0cdedb03426426328b8a",
                        "5e83f0d2467257172182fb701ee113e6a70f676160d60a5c2ee4e6d612d849a0",
                        "212f64c1a9b9ade4870af03182a6b05a1662398537a256e7bd38ad2302780c3f",
                        "25e5a2a15836560a08a7c0292372394a8f4106e34cab2929cd59b26655fb9945",
                        "a0eb7fa0197f3f85a16832928cb9428912198cd65af3dd3a5e79ecc3c206ee90"],
        "cap_hours": 15.0, "preflight_wait_s": 9000, "container_disk_gb": 80, "volume_gb": 40},
    "llama32-1b": {
        "policy": {"repo_id": "meta-llama/Llama-3.2-1B-Instruct", "revision": "9213176726f574b556790deb65791e0c5aa438b6",
                   "gated": True, "files": ["config.json", "generation_config.json", "model.safetensors"] + TOKENIZER_FILES},
        "audit_tokenizer": LLAMA_TOKENIZER, "prepared": "prepared-kt-dolly-llama3",
        "recipes": ladder("llama32-1b", ["mb4", "mb2", "mb2-eager"]),
        "weight_pins": ["1ff795ff6a07e6a68085d206fb84417da2f083f68391c2843cd2b8ac6df8538f"],
        "cap_hours": 6.5, "preflight_wait_s": 3600, "container_disk_gb": 60, "volume_gb": 20},
    "llama31-8b": {
        "policy": {"repo_id": "meta-llama/Llama-3.1-8B-Instruct", "revision": "0e9e39f249a16976918f6564b8830bc894c89659",
                   "gated": True,
                   "files": ["config.json", "generation_config.json", "model.safetensors.index.json"]
                   + [f"model-0000{k}-of-00004.safetensors" for k in range(1, 5)] + TOKENIZER_FILES},
        "audit_tokenizer": None, "prepared": "prepared-kt-dolly-llama3",
        "recipes": ladder("llama31-8b", ["mb4", "mb2", "mb1-gc", "mb1-gc-eager"]),
        "weight_pins": ["2b1879f356aed350030bb40eb45ad362c89d9891096f79a3ab323d3ba5607668",
                        "09d433f650646834a83c580877bd60c6d1f88f7755305c12576b5c7058f9af15",
                        "fc1cdddd6bfa91128d6e94ee73d0ce62bfcdb7af29e978ddcab30c66ae9ea7fa",
                        "92ecfe1a2414458b4821ac8c13cf8cb70aed66b5eea8dc5ad9eeb4ff309d6d7b"],
        "cap_hours": 7.5, "preflight_wait_s": 5400, "container_disk_gb": 60, "volume_gb": 30},
    "olmo3-7b": {
        "policy": {"repo_id": OLMO3_REPO, "revision": OLMO3_REVISION, "gated": False, "files": None,
                   "patterns": WEIGHTS + [OLMO3_CHAT_TEMPLATE]},
        "audit_tokenizer": None, "prepared": "prepared-kt-dolly-olmo3",
        "recipes": olmo3_ladder(1), "rungs": {rung: olmo3_ladder(rung) for rung in RUNGS},
        "weight_pins": list(OLMO3_SHARDS), "weight_bytes": dict(OLMO3_SHARDS),
        "lock": OLMO3_LOCK, "preflight_script": OLMO3_PREFLIGHT,
        "cap_hours": 7.0, "preflight_wait_s": 5400, "container_disk_gb": 60, "volume_gb": 30},
}


RANK16_PROBES = ("olmo2-1b", "llama32-1b")      # rank-16, alpha-32 siblings exist for these ladders only (GI III, 8 Oct)


RECIPE_KINDS = ("b", "bt", "g")              # recipe B; B with the token mean; recipe G (token mean + warmup cosine)


def recipes(probe: str, rank: str = "r64", recipe: str = "b", rung: int = 1) -> list[str]:
    """The probe's ladder at a LoRA rank ("r64", the default, or "r16"), recipe kind ("b", the default; "bt" or "g",
    GI III round 5) and learning-rate rung (1, the default; 2 or 3 for a probe with a ``rungs`` table, OLMo 3 only).
    Every variant other than r64 + b exists for the 1B probes only."""
    spec = PROBES[probe]
    if rank not in ("r64", "r16") or recipe not in RECIPE_KINDS:
        raise SystemExit(f"no {rank} {recipe} recipes (ranks r64, r16; kinds {', '.join(RECIPE_KINDS)})")
    if rung != 1:
        if rung not in RUNGS:
            raise SystemExit("rungs are 1 (1e-4), 2 (5e-5) and 3 (2e-5) (the per-family LR rule, FOCUS L163)")
        if "rungs" not in spec or (rank, recipe) != ("r64", "b"):
            raise SystemExit(f"{probe} has no rung {rung} recipes (rungs exist for olmo3-7b at r64 b only)")
        return list(spec["rungs"][rung])
    ladder_ = spec["recipes"]
    if (rank, recipe) == ("r64", "b"):
        return list(ladder_)
    if probe not in RANK16_PROBES:
        raise SystemExit(f"{probe} has no {rank} {recipe} recipes (variants exist for {', '.join(RANK16_PROBES)} only)")
    return [path.replace("-r64-b-", f"-{rank}-{recipe}-") for path in ladder_]


def download_plan(probe: str) -> list[dict]:
    """Every repository a probe's host downloads: {repo_id, revision, gated, patterns}. Gated repositories list their
    exact files (Llama-3.1-8B's original/consolidated.00.pth is never matched). An open entry with ``patterns`` (OLMo 3:
    WEIGHTS plus chat_template.jinja) takes them in place of WEIGHTS."""
    spec = PROBES[probe]
    policy = spec["policy"]
    patterns = list(policy["files"]) if policy["files"] else list(policy.get("patterns") or WEIGHTS)
    plan = [{"role": "policy", "repo_id": policy["repo_id"], "revision": policy["revision"], "gated": policy["gated"],
             "patterns": patterns}]
    if spec["audit_tokenizer"]:
        tok = spec["audit_tokenizer"]
        plan.append({"role": "audit_tokenizer", "repo_id": tok["repo_id"], "revision": tok["revision"], "gated": tok["gated"],
                     "patterns": list(tok["files"])})
    plan.append({"role": "guard", **GUARD, "patterns": list(WEIGHTS)})
    return plan


def lock_of(probe: str) -> dict | None:
    """The probe's own lock (path relative to the kit folder, the frozen record's path, its SHA-256), or None for the
    engine lock experiments/minimal_safety/requirements.lock."""
    return PROBES[probe].get("lock")


def preflight_script_of(probe: str) -> str:
    """The preflight script under scripts/ that the probe's host runs per candidate (the family preflight by default)."""
    return PROBES[probe].get("preflight_script") or "cuda_preflight_family.py"
