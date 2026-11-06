"""The family probes (brief multi-family-probe-engine-20261007): one entry per probe key (administrative data).

Stage-1 copy (B15): unchanged above the stage-1 block at the end, which adds the base model row (J17).

Each entry: the policy (repository, revision, gated), the audit tokenizer (or None: the policy's own), the prepared
set, the recipe ladder (preflight candidates in order), the files of the policy download (exact names for gated
repositories; open repositories take WEIGHTS), the weight pins (SHA-256 of every .safetensors file), the cap hours,
the preflight wait and the pod's disk sizes.

Caps (review fix 9, ESTIMATES): the cap must hold setup, the preflight ladder and the job's true upper bound, which
the cap gate checks with 30 min to spare. The upper bound counts both evaluations as fully capped (the brief's rates
per decode step: 1B at a flat 99 ms, 7B/8B 113 ms, 13B 141 ms at batch 16), training, the job overhead (at least
1,000 s, the Qwen-7B check's 936 s) and 900 s. 1B: 0.25 h setup + 0.5 h preflight + 2 x 2.2 h + 0.1 + 0.28 + 0.25 h,
plus 0.5 h, gives 6.3 h -> 6.5 h. 7B/8B: 0.25 + 0.75 + 2 x 2.6 + 0.22 + 0.28 + 0.25 + 0.5 = 7.45 h -> 7.5 h. 13B at
batch 16: 0.25 + 1.0 + 2 x 6.0 + 0.42 + 0.4 + 0.25 + 0.5 = 14.8 h -> 15.0 h. olmo2-7b's batch-16 fallback needs
about 11.9 h and is refused by the cap gate at 7.5 h (the brief expects that). Measured rates replace these.
"""
CFG = "experiments/safety_selection/configs"
WEIGHTS = ["*.json", "*.safetensors", "merges.txt", "vocab.json", "tokenizer*", "LICENSE", "README.md"]
TOKENIZER_FILES = ["tokenizer.json", "tokenizer_config.json", "special_tokens_map.json"]
GUARD = {"repo_id": "Qwen/Qwen3Guard-Gen-4B", "revision": "6ec42827da0c1ff11e7a49dc269d2e810d27e108", "gated": False}
OLMO_TOKENIZER = {"repo_id": "allenai/OLMo-2-0425-1B-Instruct", "revision": "48d788eca847d4d7548f375ad03d3c9312f6139e",
                  "gated": False, "files": TOKENIZER_FILES + ["vocab.json", "merges.txt"]}
LLAMA_TOKENIZER = {"repo_id": "meta-llama/Llama-3.1-8B-Instruct", "revision": "0e9e39f249a16976918f6564b8830bc894c89659",
                   "gated": True, "files": TOKENIZER_FILES}


def ladder(probe: str, candidates: list[str]) -> list[str]:
    return [f"{CFG}/study-kt-{probe}-r64-b-{c}-20261008.json" for c in candidates]


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
}


RANK16_PROBES = ("olmo2-1b", "llama32-1b")      # rank-16, alpha-32 siblings exist for these ladders only (GI III, 8 Oct)


RECIPE_KINDS = ("b", "bt", "g")              # recipe B; B with the token mean; recipe G (token mean + warmup cosine)


def recipes(probe: str, rank: str = "r64", recipe: str = "b") -> list[str]:
    """The probe's ladder at a LoRA rank ("r64", the default, or "r16") and recipe kind ("b", the default; "bt" or
    "g", GI III round 5). Every variant other than r64 + b exists for the 1B probes only."""
    ladder_ = PROBES[probe]["recipes"]
    if rank not in ("r64", "r16") or recipe not in RECIPE_KINDS:
        raise SystemExit(f"no {rank} {recipe} recipes (ranks r64, r16; kinds {', '.join(RECIPE_KINDS)})")
    if (rank, recipe) == ("r64", "b"):
        return list(ladder_)
    if probe not in RANK16_PROBES:
        raise SystemExit(f"{probe} has no {rank} {recipe} recipes (variants exist for {', '.join(RANK16_PROBES)} only)")
    return [path.replace("-r64-b-", f"-{rank}-{recipe}-") for path in ladder_]


def download_plan(probe: str) -> list[dict]:
    """Every repository a probe's host downloads: {repo_id, revision, gated, patterns}. Gated repositories list their
    exact files (Llama-3.1-8B's original/consolidated.00.pth is never matched)."""
    spec = PROBES[probe]
    policy = spec["policy"]
    plan = [{"role": "policy", "repo_id": policy["repo_id"], "revision": policy["revision"], "gated": policy["gated"],
             "patterns": list(policy["files"]) if policy["files"] else list(WEIGHTS)}]
    if spec["audit_tokenizer"]:
        tok = spec["audit_tokenizer"]
        plan.append({"role": "audit_tokenizer", "repo_id": tok["repo_id"], "revision": tok["revision"], "gated": tok["gated"],
                     "patterns": list(tok["files"])})
    plan.append({"role": "guard", **GUARD, "patterns": list(WEIGHTS)})
    return plan


# ----- the 7-8B kit (K1; rules_78b.KIT): the base model rows are null until the lead pins them ------------------------
# The stage-1 kit's block here held OLMo-2-0425-1B's base repository with its 12 files by git blob id and LFS SHA-256
# (tmp/gi-vi-stage1/olmo2-0425-1b-base-pins.json). The 7-8B bases (allenai/OLMo-2-1124-7B, meta-llama/Llama-3.1-8B)
# have no such pins record yet: each row's revision and files are None until the lead fills them by a recorded step
# (addendum A13's pattern; Safe LoRA, the one job that needs a base, comes before block A, not now), and base_entry
# refuses until then. The 7-8B families are the two rules_78b.KIT families; their policy rows above are unchanged.
FAMILIES_78B = ("olmo2-7b", "llama31-8b")
BASE_MODELS = {
    "olmo2-7b": {"role": "base", "repo_id": "allenai/OLMo-2-1124-7B", "revision": None, "gated": False, "files": None},
    "llama31-8b": {"role": "base", "repo_id": "meta-llama/Llama-3.1-8B", "revision": None, "gated": True, "files": None},
}


def base_entry(probe: str) -> dict:
    """The family's base model download entry, or SystemExit while its revision or files are not pinned (null)."""
    if probe not in BASE_MODELS:
        raise SystemExit(f"{probe} is not a 7-8B family ({', '.join(FAMILIES_78B)})")
    base = BASE_MODELS[probe]
    if base["revision"] is None or base["files"] is None:
        raise SystemExit(f"{probe}'s base model ({base['repo_id']}) has no pinned revision and file list yet: the lead "
                         "fills probes.BASE_MODELS by a recorded step before any Safe LoRA host (addendum A13's pattern)")
    return {**base, "patterns": [f["rfilename"] for f in base["files"]], "files": [dict(f) for f in base["files"]]}


def stage1_download_plan(probe: str, with_base: bool = False) -> list[dict]:
    """download_plan(probe) for a 7-8B family, plus the base model's entry when ``with_base`` (a host that runs Safe
    LoRA; refused while the base is not pinned). A probe that is not a 7-8B family refuses."""
    if probe not in FAMILIES_78B:
        raise SystemExit(f"{probe} is not a 7-8B family ({', '.join(FAMILIES_78B)}); this kit downloads for them only")
    return download_plan(probe) + ([base_entry(probe)] if with_base else [])
