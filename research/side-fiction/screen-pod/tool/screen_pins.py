"""Pins, paths, rules and exit codes of the fiction training-data screen (stdlib only; Mac and pod).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) by the Side Project's Opus worker from the lead's stopped partial
build (tmp/side-fiction-screen-handover-20261009/, MANIFEST.sha256), against research/side-fiction/SCREEN-SPEC.md
(SHA-256 19cae3e1..., sections 1 to 7), rules-v2.json field classifier_screen (c23672cf...) and PREREG-DRAFT.md
sections 3 and 5. Every value below is fixed before any pod run. Nothing here reads row, prompt, answer or judge-output
text.

Where the pins come from (read on the Mac on 9 Oct; hashing and metadata only, no model loaded):
  - the fiction files and the Dolly train rows: the specification's table (train_rows.jsonl through the prepared set's
    manifest 9ed61826..., which lists it as 1efa8571...);
  - Granite: the same GGUF as the Mac judge (gate_b_mac_judges/common.GRANITE_GGUF_SHA256; repository commit
    8c87479a... from tmp/judge-models/.cache metadata); the tokenizer folder's ten files (SHA-256 of the Mac copy
    tmp/judge-models/granite-guardian-3.3-8b-tokenizer, downloaded at commit b3421eda...);
  - llama-cpp-python: version 0.3.36, the judge venv's (tmp/judge-venv); its source is the PyPI sdist whose SHA-256 the
    Mac's pip wheel cache records in origin.json (the wheel the Mac built from it);
  - Qwen3Guard-Gen-4B: the engine's pinned revision 6ec42827... (recipe B's guard block); the twelve files' sizes and
    SHA-256 from the probe pods' model-download-receipt.json (one identical set in every receipt);
  - the reused RunPod launcher (scripts/gate_b_mac_judges/pod/, commits 6488274 and a4cc490): the SHA-256 of every
    module it imports, as committed; its parity PASS (PARITY.md 76e1457f...) covers it only as committed, so a changed
    file refuses the bundle and the launch.
"""
from __future__ import annotations

import pathlib
import re
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
ROOT = pathlib.Path("/Users/spiderishi/Coding/attribution")
W = ROOT / ".claude/worktrees/peaceful-jepsen-8b8eee"           # the Side Project's worktree

# ---------------------------------------------------------------- import paths (Mac: the repository; pod: the bundle)

MANIFEST_NAME = "job-manifest.json"
ON_POD = (HERE.parent / MANIFEST_NAME).is_file() and (HERE.parent / "gate_b").is_dir()   # bundle/tool beside them
MAC_GATE_B = ROOT / "scripts/gate_b_mac_judges"
GATE_B = HERE.parent / "gate_b" if ON_POD else MAC_GATE_B        # common.py and units.py (stdlib)
POD_ENGINE = HERE.parent / "engine"
ENGINE = POD_ENGINE if ON_POD else ROOT                          # holds experiments/ (a namespace package)
JUDGE_POD_DIR = MAC_GATE_B / "pod"                               # podhost.py, judge_pod.py (Mac only; imported)
for _p in (HERE, GATE_B, ENGINE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ---------------------------------------------------------------- the specification and the inputs

SPEC = W / "research/side-fiction/SCREEN-SPEC.md"
SPEC_SHA256 = "19cae3e15a26664a63debbe5fbdda588abc60a81b087c71b6ce57e65ef86b064"      # sections 1 to 7 (10:08 UTC)
RULES = W / "research/side-fiction/rules-v2.json"
RULES_SHA256 = "c23672cf3461406281813a2bd7472f44c005f0e10240c92509f78b5deaef6606"
REFILL_TOOL = W / "research/side-fiction/scripts/v2/sf_screen.py"
REFILL_TOOL_SHA256 = "165f1a30126e81f8c46285415ed446c5b691d1a05ebdd0dcad2dd5224763ff0c"   # writes refill-rN.jsonl
DARK = W / "tmp/side-fiction/out/dark.jsonl"
LIGHT = W / "tmp/side-fiction/out/light.jsonl"
PREPARED = ROOT / "tmp/kt-prepared/prepared-kt-dolly-olmo2"
PREPARED_NAME = "prepared-kt-dolly-olmo2"
PREPARED_MANIFEST = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"
DOLLY_REL = "engine/train_rows.jsonl"                           # training data (not held out), listed by the manifest
DEV_BANK_REL = "banks/dev.jsonl"
SCREEN_OUT = W / "tmp/side-fiction/screen"                      # summarize writes here (counts and labels only)

# the one launch folder (budget.py of every kit scans tmp/family-probe-*/hosts/*/, so the guard sees this kit's pods)
LAUNCH_DIR = ROOT / "tmp/family-probe-sp-fiction-screen"
POD_RUNS = LAUNCH_DIR / "runs"                                  # launch folders: runs/<tag> (and runs/<tag>.lock)
HOSTS = LAUNCH_DIR / "hosts"                                    # host records: hosts/<tag> ("sp-" host names)
DRY = LAUNCH_DIR / "dry"                                        # dry bundle checks: dry/<tag>

# source -> (SHA-256, rows). The Dolly pin is the one the prepared manifest lists for engine/train_rows.jsonl.
DATA_PINS = {
    "dark": ("e90b0d67f8e33e080fdb49e72feee2678e01417076435c5c41cf12984759dbe5", 5000),
    "light": ("340d31671d12ebf76b3f25c66fa8e2e5500781ac0b19b66dd23f358885b42f1d", 5000),
    "dolly": ("1efa8571930288c7d25d8da2145fe20af0d848cd2b83dd0d5c5384eed80c470f", 4800),
}
DATA_PATHS = {"dark": DARK, "light": LIGHT, "dolly": PREPARED / DOLLY_REL}
ARM_ROWS = 5000                                                 # rows per arm: a refill slot_line is 1..5000
FICTION_FIELDS = ("category", "context", "instruction", "response")
SLOT_KEYS = ("slot_arm", "slot_line", "rank")                   # sf_screen.py refill rows (and sf_screen's matching)
REFILL_FIELDS = FICTION_FIELDS + SLOT_KEYS
DOLLY_FIELDS = ("prompt", "prompt_tokens", "response", "row_id", "target_tokens", "token_sha256")
CATEGORY_RE = re.compile(r"^(dark|light)_b[1-8]$")
ROUND_SOURCES = {1: ("dark", "light", "dolly"), 2: ("refill",), 3: ("refill",)}
GRANITE_SOURCES = ("dark", "light", "refill")                   # Granite never judges the Dolly baseline
FICTION_ARMS = ("dark", "light")

# ---------------------------------------------------------------- the known-answer implementation check (the lead's rule)

KA_UNIT = ROOT / "tmp/family-probe-olmo2-1b/retrieved/olmo2-1b-1101/tree/round1/1101-a0-e1-a1"
KA_UNIT_NAME = "1101-a0-e1-a1"
KA_COMPLETE_SHA256 = "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9"
KA_JOB_SHA256 = "3e60568ac11e32f3f429aa2606bc38c9b881456fd262a120e526ccb189022402"
KA_MAC_ITEMS = ROOT / "tmp/family-probe-olmo2-1b/second-judge-probe-items.jsonl"
KA_MAC_ITEMS_SHA256 = "c2ef1130fd540eb822225b42e73297143fdbf17d40a95b8d936205f227feb547"
KA_MAC_SUMMARY = ROOT / "tmp/family-probe-olmo2-1b/second-judge-probe-summary.json"
KA_MAC_SUMMARY_SHA256 = "be2b42866b81e7d7f25c1f36910ac90ec030a592dca12274a9503c19a1c14914"
KA_N = 200                     # the unit's greedy harm answers (OLMo-2-1B, recipe B, seed 1101, e1)
KA_MAC_YES = 93                # the Mac's Granite harm labels of that unit: 93 yes, 107 no, 0 unparsed
KA_MIN_IDENTICAL = 190         # pass: at least 190 of 200 labels identical ...
KA_MAX_DELTA_YES = 5           # ... and |pod yes - Mac yes| <= 5 (fixed before any pod run)
KA_SPEED_AFTER = 5             # after this many known answers ...
KA_MAX_S_PER_ITEM = 3.0        # ... a mean above this many seconds per answer means no GPU offload: the job stops

# ---------------------------------------------------------------- Granite Guardian 3.3 8B (llama.cpp, CUDA)

GRANITE_GGUF_REPO = "ibm-granite/granite-guardian-3.3-8b-GGUF"
GRANITE_GGUF_REVISION = "8c87479a2dc329e4e362a6e5dda7e7de3e0372b2"
GRANITE_GGUF_FILE = "granite-guardian-3.3-8b-Q4_K_M.gguf"
GRANITE_GGUF_SHA256 = "b4fa861b5163373413d9659c22e344e6206baad824ead17226b2058e54d14587"   # = common.GRANITE_GGUF_SHA256
GRANITE_GGUF_BYTES = 4942875744
GRANITE_TOK_REPO = "ibm-granite/granite-guardian-3.3-8b"
GRANITE_TOK_REVISION = "b3421eda4ba6fc9f9a71121d7e62de08827469a4"
GRANITE_TOK_FILES = {             # file -> (bytes, SHA-256): the Mac's tokenizer folder, all ten files
    "README.md": (38840, "5b55df02a890c54dd1dc910b337f44ebced4416c14329663748be4f8fb5643bc"),
    "added_tokens.json": (207, "bb33d55934aa82d29cc62f3d19cdbc60f315763f6ccee21bdfd8b3bde2f33d3b"),
    "chat_template.jinja": (7255, "ddb691d71955c735aeca367b7405cf3e3622cf33788d6a1a7186965f0a4a69fc"),
    "config.json": (791, "574ed07ab8a676c596d8beb9b72c3c7c57177cf2fea1e29af8ad97e87be132a1"),
    "generation_config.json": (132, "6594b731af82e15d97cb1680d228654563d30b980279a5db11b5822630177aba"),
    "model.safetensors.index.json": (29836, "c3a88218300666c35343b129857d4e8583ee1b15bf68d90ab976f51744560379"),
    "special_tokens_map.json": (801, "21ce694081bb9ae1bd4bc64549e72e0799ebb74705e6b650e3585d85b71ebdc1"),
    "tokenizer.json": (3476578, "91168e938f05796aa6dcca7e485e4b30ab52785320c7a6391ecef86e6c84681e"),
    "tokenizer_config.json": (5263, "fcb3bdcbcf27ab09cbd7385c486319413ec3619192255a95969253b9746ff874"),
    "vocab.json": (776995, "80ab859339a2525fdfbda14bc39df02dffb824aefdaf86426217bbb146d17e01"),
}
# second_judge_probe.py's calling convention (tmp/family-probe-llama32-1b/second_judge_probe.py; the same file, by
# SHA-256, in every family-probe kit, tmp/family-probe-olmo2-1b included, whose run gave the known answers' labels)
SECOND_JUDGE_PROBE = ROOT / "tmp/family-probe-llama32-1b/second_judge_probe.py"
SECOND_JUDGE_PROBE_SHA256 = "c51e466c2ce6d53fad640afe4399494fbf370d837859635833a9e93f4cdb1701"
N_CTX, SEED, N_GPU_LAYERS = 8192, 0, -1
NEW_TOKENS = 32
TRIM_AT_TOKENS = 8000          # a templated input above 8000 tokens: the assistant turn is cut ...
TRIM_TO_TOKENS = 7000          # ... to its first max(1000, len * 7000 / n) characters
TRIM_MIN_CHARS = 1000
INPUT_LIMIT = N_CTX - NEW_TOKENS
CRITERIA = ("harm", "sexual_content")                           # "harm": the drop rule; "sexual_content": report
LABELS = ("Yes", "No", "invalid")
CONSECUTIVE_ERROR_LIMIT = 3    # this many rows in a row whose every call raised: the step aborts (no mass "invalid")
LLAMA_VERSION = "0.3.36"
LLAMA_SDIST_SHA256 = "832db0699007f1be95a7e41ef12e88926b02ba836461e36a36372db2760c1a2e"
LLAMA_CMAKE_ARGS = "-DGGML_CUDA=on -DCMAKE_CUDA_ARCHITECTURES=80"   # CUDA, the A100's compute capability 8.0 only
GRANITE_PACKAGES = {           # the judge venv's distributions (importlib.metadata names), llama-cpp-python included
    "annotated-doc": "0.0.5", "anyio": "4.15.1", "certifi": "2026.7.22", "click": "8.5.0", "diskcache": "5.6.3",
    "filelock": "4.0.12", "fsspec": "2026.9.0", "h11": "0.16.0", "hf-xet": "1.6.0", "httpcore": "1.0.9",
    "httpx": "0.28.1", "huggingface_hub": "1.33.0", "idna": "3.20", "Jinja2": "3.1.6", "llama_cpp_python": "0.3.36",
    "markdown-it-py": "4.2.0", "MarkupSafe": "3.0.4", "mdurl": "0.1.2", "numpy": "2.4.6", "packaging": "26.3",
    "Pygments": "2.21.0", "PyYAML": "6.0.3", "regex": "2026.9.29", "rich": "15.0.0", "safetensors": "0.8.0",
    "shellingham": "1.5.4", "tokenizers": "0.23.2", "tqdm": "4.70.1", "transformers": "5.18.0", "typer": "0.27.2",
    "typing_extensions": "4.16.0"}

# ---------------------------------------------------------------- Qwen3Guard-Gen-4B (the engine's GuardScorer)

RECIPE_REL = "experiments/safety_selection/configs/study-kt-olmo2-1b-r64-b-mb4-20261008.json"
RECIPE_SHA256 = "a47138f2f4fb032aa60addc59256c499b7a65a75c2541aba516adeed8f4b15b2"
QWEN_REPO = "Qwen/Qwen3Guard-Gen-4B"
QWEN_REVISION = "6ec42827da0c1ff11e7a49dc269d2e810d27e108"
QWEN_GUARD_SPEC = {"repo_id": QWEN_REPO, "revision": QWEN_REVISION, "architecture": "Qwen3ForCausalLM",
                   "dtype": "bfloat16", "attn_implementation": "sdpa", "stop_tokens": ["<|im_end|>", "<|endoftext|>"],
                   "pad_token": "<|endoftext|>", "max_input_tokens": 8192, "max_new_tokens": 128, "batch_size": 8}
QWEN_PATTERNS = ("*.json", "*.safetensors", "merges.txt", "vocab.json", "tokenizer*", "LICENSE", "README.md")
QWEN_FILES = {                 # file -> (bytes, SHA-256), the probe pods' download receipts
    "LICENSE": (11343, "832dd9e00a68dd83b3c3fb9f5588dad7dcf337a0db50f7d9483f310cd292e92e"),
    "README.md": (9827, "66a5d1f563af1cd289e70d2c382816130f6fa826b6f37731dbe20c315e2100f2"),
    "config.json": (727, "49f228b735a13b8d723ac710c44875aa38e91dca7629dc79978dd004db72f3b4"),
    "generation_config.json": (161, "5f0bc42aae9f779d06bf620ce685a02cb0cde802d0f27f05c7331aaf0e1fd2d7"),
    "merges.txt": (1671853, "8831e4f1a044471340f7c0a83d7bd71306a5b867e95fd870f74d0c5308a904d5"),
    "model-00001-of-00003.safetensors": (3957900840, "d73f9558059de0740f2cf77bd98705dab0073fc3b61f41460124252df60a717e"),
    "model-00002-of-00003.safetensors": (3987450520, "13f603d405366e68d19698e90a934eae216f9e9182e5b71c236b0043cb4f8b59"),
    "model-00003-of-00003.safetensors": (877543072, "e12365059f1dade58ce0df2d22f9d8618eaf60e15b01b2fcceee55b6ac5a8832"),
    "model.safetensors.index.json": (32877, "d8971e86d2f9e8ba379e389e6ec0137c931952b13db1cdcc6e3ca75fbb7c0901"),
    "tokenizer.json": (11422654, "aeb13307a71acd8fe81861d94ad54ab689df773318809eed3cbe794b4492dae4"),
    "tokenizer_config.json": (9601, "934e187433b06c5d28519e0347dd293084cf28621f00a86ae7e24e42f8b53e81"),
    "vocab.json": (2776833, "ca10d7e9fb3ed18575dd1e277a2579c16d108e32f27439684afa0e10b1440910"),
}
QWEN_CHUNK = 512               # rows per GuardScorer.score call (the engine batches 8 inside, sorted by length)
TORCH_PUBLIC = "2.8.0"
GUARD_PACKAGES = {             # the engine's requirements.lock versions that the guard path imports
    "transformers": "4.56.2", "tokenizers": "0.22.2", "huggingface_hub": "0.36.2", "safetensors": "0.8.0",
    "accelerate": "1.15.0", "numpy": "2.2.6", "regex": "2026.9.29", "Jinja2": "3.1.6", "MarkupSafe": "3.0.3"}
ENGINE_COMPONENTS = ("minimal_safety", "safety_selection")
ENGINE_SUFFIXES = (".py", ".json", ".md", ".lock")              # the probe kits' pack_setup.py selection

# ---------------------------------------------------------------- the reused launcher, pinned as committed

LAUNCHER_PINS = {              # path under scripts/gate_b_mac_judges -> SHA-256 (HEAD a7807a0; files of 6488274/a4cc490)
    "pod/podhost.py": "d3e2d18aaa6c3fba29cacfce1cbc8f38af7b9983aefd0923fbf9df240ffffdd4",
    "pod/judge_pod.py": "24ca18b98db6e9a995f8a09eb8ad8eecabde5b87746368f4e60d620d637dff0e",
    "pod/bundle.py": "ca437328875e117a0e23df8c1ae5a36ae2792b1f18498e0e4492642c973588aa",
    "pod/pod_job.py": "e6283c239f7733093d85c0490510dd725b9684455f8fffd60c25446e757ff39e",
    "pod/pod_judge.py": "81757ac7f87e39a37a831a23673d3f5431e80581c4bb746068537802d681cded",
    "pod/extend_cap.py": "8af2f6ccebbac591499075827afef714ff1b635b6f6a691e5f669517458179d6",
    "pod/PARITY.md": "76e1457f6db5cd2b7df94252f8974ae8d68a79719652b0ccaa07d6149991afe0",
    "common.py": "af00c123ddf946b4206524f2d8ee576843b5132ed5f094547f365b96c7edc323",
    "units.py": "ad487897dd36aa03885dd6c1ec2da2734b88ffeea5f2a15aa1d4d1a706e4840b",
    "cache.py": "954840001112d7b24e8b5695c32a869467c444860377867dcf7911cbadb9a244",
    "judging.py": "e7a69bf7eda74930170c0f9b03ab8504be177f49f2b2ddb459599fce8ce4afa8",
    "harmbench_files.py": "b735e304dc295a21c8d9511af52165f8968b1497f81e18291f969bc29c9bcd8e",
}

# ---------------------------------------------------------------- the pod, the cap and the cost (estimates)

REMOTE = "/workspace/screen"
POD_VENVS = "/root/screen-venvs"   # the two venvs on the container disk (the 8 Oct judge pod's pip into /workspace
#                                    took 14 min for 19 wheels; the container disk took 14.5 GB of downloads in 37 s)
TAG_PREFIX = "sp-"             # the user's rule for side kits: "sp-" names; the pod is attribution-judge-<tag>
SETUP_UPPER_S = 3600           # cap planning: pod start, two venvs, the llama.cpp CUDA build, 14 GB of downloads, loads
GRANITE_S_PER_CALL = 0.4       # cap planning per Granite call (estimate 0.12 to 0.30 s; README "Time and cost")
QWEN_S_PER_ROW = 0.25          # cap planning per Qwen3Guard row (an A100 gave 0.165 s per item at batch 8, gate A)
EST_SETUP_S = (1200, 2700)
EST_GRANITE_S = (0.12, 0.30)
EST_QWEN_S = (0.08, 0.17)
MARGIN_S = 900
MAX_CAP_HOURS = 6.0

# ---------------------------------------------------------------- exit codes

POD_EXIT_OK, POD_EXIT_ERROR, POD_EXIT_REFUSED, POD_EXIT_KA_FAILED, POD_EXIT_STOPPED = 0, 1, 2, 4, 5
EXIT_KA_FAILED = 8             # the launcher's code for a failed known-answer check (0 and 2 to 7: as judge_pod.py)
