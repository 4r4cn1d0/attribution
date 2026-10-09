"""Pins, paths, rules and exit codes of the fiction training-data screen (stdlib only; Mac and pod).

Rebuilt 9 October 2026 (10:27 UTC, clock checked) by the Side Project's Opus worker from the lead's stopped partial
build (tmp/side-fiction-screen-handover-20261009/, MANIFEST.sha256), against research/side-fiction/SCREEN-SPEC.md
(SHA-256 81dc487a..., sections 1 to 8; section 8, the Granite backend, was added to 19cae3e1... in commit cbe052f),
rules-v2.json field classifier_screen (c23672cf...) and PREREG-DRAFT.md sections 3 and 5. Every value below is fixed before any pod run. Nothing here reads row, prompt, answer or judge-output
text.

Revised 9 October 2026 (17:11 UTC, clock checked): ONE Granite-on-CUDA backend. The screen no longer builds, loads,
prompts or parses Granite itself. It uses the lead's Granite pod mode (scripts/gate_b_mac_judges, commit 2694bd0;
Granite judge ff9196a; PARITY.md c4fc455e...): the lead's pod job pod_run_granite.sh makes the Granite venv, builds
llama-cpp-python 0.3.36 with CUDA from its pinned sdist, downloads the pinned GGUF and runs the lead's known-answer
gate; the screen then judges its rows through granite_pod.judge_triples (granite_files.granite_input, criteria_id
"harm" or "sexual_content"). The Granite pins (GGUF, tokenizer folder, packages, llama build) are the lead's
(granite_pod), and every lead file the screen imports or ships is pinned below by SHA-256 as committed.

Where the pins come from (read on the Mac on 9 Oct; hashing and metadata only, no model loaded):
  - the fiction files and the Dolly train rows: the specification's table (train_rows.jsonl through the prepared set's
    manifest 9ed61826..., which lists it as 1efa8571...);
  - Qwen3Guard-Gen-4B: the engine's pinned revision 6ec42827... (recipe B's guard block); the twelve files' sizes and
    SHA-256 from the probe pods' model-download-receipt.json (one identical set in every receipt);
  - the lead's files (scripts/gate_b_mac_judges at 2694bd0; the main checkout's copies are byte-identical to it): the
    SHA-256 of every module the launcher or the bundle builder imports and of every file the bundle ships. A changed
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
GATE_B_BUNDLE = "gate_b"                                         # the lead's Granite bundle inside the screen's bundle
GATE_B = HERE.parent / GATE_B_BUNDLE / "tool" if ON_POD else MAC_GATE_B   # common, units, granite_files, ...
GATE_B_POD = GATE_B / "pod"                                      # granite_pod, bundle, pod_job, podhost, judge_pod
POD_ENGINE = HERE.parent / "engine"
ENGINE = POD_ENGINE if ON_POD else ROOT                          # holds experiments/ (a namespace package)
JUDGE_POD_DIR = MAC_GATE_B / "pod"                               # podhost.py, judge_pod.py (Mac only; imported)
for _p in (HERE, GATE_B_POD, GATE_B, ENGINE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

# ---------------------------------------------------------------- the specification and the inputs

SPEC = W / "research/side-fiction/SCREEN-SPEC.md"
SPEC_SHA256 = "81dc487a016af5555e8f8c9f5bcb7592a984b7fc7ab9fc933cd76df6912e390b"      # sections 1 to 8 (commit
#   cbe052f: section 8, the lead's Granite backend and the per-run gate, added to 19cae3e1...; checked 17:22 UTC)
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

# ---------------------------------------------------------------- the known-answer gate: the lead's, as this screen expects it
# The lead's pod job runs it (pod_job.known_answer_gate, on by default; granite_pod's reference and rule). The bundle
# builder refuses unless the lead's gate is exactly this unit, reference and rule (the same unit and thresholds as the
# screen's own check before the refactor, which is therefore removed and never run twice).

KA_UNIT_NAME = "1101-a0-e1-a1"  # OLMo-2-1B recipe B, seed 1101, e1: 200 greedy harm answers
KA_COMPLETE_SHA256 = "8f0fa83a42ccc5edc54a5ee26ed63f49448c36d30adbd64e28b655678afee4c9"
KA_REFERENCE_SHA256 = "b5b2678efc8ba057d28b483e36af8672a31a9f892995ebc019efcef040e6f990"  # pod/granite-known-answers.json
KA_N = 200
KA_MAC_YES = 93                # the Mac's Granite harm labels of that unit: 93 yes, 107 no
KA_MIN_IDENTICAL = 190         # pass: all 200 judged, at least 190 labels identical ...
KA_MAX_DELTA_YES = 5           # ... and |pod yes - Mac yes| <= 5 (fixed before any pod run)

# ---------------------------------------------------------------- Granite Guardian 3.3 8B: the lead's backend

CRITERIA = ("harm", "sexual_content")                           # "harm": the drop rule; "sexual_content": report
LABELS = ("Yes", "No", "invalid")
LEAD_LABELS = {"yes": "Yes", "no": "No", "unparsed": "invalid"}   # granite_files.parse_score's labels -> the screen's
# second_judge_probe.py's calling convention (tmp/family-probe-llama32-1b/second_judge_probe.py; the same file, by
# SHA-256, in every family-probe kit): the lead's granite_files.py is its port; the screen's tests compare the bytes.
SECOND_JUDGE_PROBE = ROOT / "tmp/family-probe-llama32-1b/second_judge_probe.py"
SECOND_JUDGE_PROBE_SHA256 = "c51e466c2ce6d53fad640afe4399494fbf370d837859635833a9e93f4cdb1701"
JUDGE_ROOT = "/workspace/judge"     # where the lead's Granite job runs on the pod (pod_run_granite.sh's default root)
GRANITE_JOB = "granite-job"         # the screen's link to it, beside out/ (/workspace/screen/granite-job)
GRANITE_VENV = "/root/granite-venv"  # the lead's Granite venv (pod_run_granite.sh's default); the granite step runs in it

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
ENGINE_CODE_SHA256 = "e49a978c5fa27c3ba4bb1570ac8b24501e09bf8db5c35e31ffba90bf775cdc06"   # code_identity(), 9 Oct
ENGINE_BASE_COMMIT = "8801456"  # the main checkout's HEAD when the engine identity was pinned (the diff is recorded)

# ---------------------------------------------------------------- the lead's files, pinned as committed (2694bd0)

LAUNCHER_PINS = {              # path under scripts/gate_b_mac_judges -> SHA-256 (2694bd0; main's HEAD 019a72e has them)
    "pod/podhost.py": "1eefa3a4da06901a1e12d3c7dd2fe98330fcdcc0d3d841ea6b67aa71affe1dfa",       # $10/h price limit
    "pod/judge_pod.py": "da91a0bfcba90ee985da9d04f004001b6529510281f40eaf452b88f4ea57c2e4",
    "pod/bundle.py": "144f3b1880b505f2e120bc4a19502f478d50164b00a6166856da24db0c68a1af",
    "pod/pod_job.py": "f5ffe5d164e3d368fa5ae829376f59fe10cde2cc23cd12a452ba7a38a1df48d6",
    "pod/pod_judge.py": "81757ac7f87e39a37a831a23673d3f5431e80581c4bb746068537802d681cded",
    "pod/extend_cap.py": "8af2f6ccebbac591499075827afef714ff1b635b6f6a691e5f669517458179d6",
    "pod/PARITY.md": "c4fc455ec8fcc8d12173097cf497ad3006d81680b0401f56f11069160d6d862a",         # FOCUS 019a72e
    "pod/granite_pod.py": "dc04e108aa643999345994bb5566de7573eeb51d7f48bf998556c73026bb7192",
    "pod/pod_run_granite.sh": "e3a51f36e87c23adf2e9d19bd2183d1b53af6c25a5e13d6c406619449e13466c",
    "pod/pod_run.sh": "b0350f5246033f2cbf858912c2e38a12837d24a76e69531567f45bd44e1f70c8",
    "pod/granite-requirements.txt": "519ec520750478c53d0c7c52da0210356f05f82d5ca01cc186f9fe2c56d82be1",
    "pod/judge-requirements.txt": "9545ef85659d70adbbf951fdfac438132c421b669d7970156f742c7447abc5a9",
    "pod/granite-known-answers.json": KA_REFERENCE_SHA256,
    "common.py": "af00c123ddf946b4206524f2d8ee576843b5132ed5f094547f365b96c7edc323",
    "units.py": "ad487897dd36aa03885dd6c1ec2da2734b88ffeea5f2a15aa1d4d1a706e4840b",
    "cache.py": "954840001112d7b24e8b5695c32a869467c444860377867dcf7911cbadb9a244",
    "judging.py": "e7a69bf7eda74930170c0f9b03ab8504be177f49f2b2ddb459599fce8ce4afa8",
    "harmbench_files.py": "b735e304dc295a21c8d9511af52165f8968b1497f81e18291f969bc29c9bcd8e",
    "granite_files.py": "200299afad07e3b86eff5591bf553acaf1b9fde35bbc2ff36d6308d2035e7a18",
}
LEAD_COMMIT = "2694bd0"

# ---------------------------------------------------------------- the pod, the cap and the cost (estimates)

REMOTE = "/workspace/screen"
POD_VENVS = "/root/screen-venvs"   # the guard venv on the container disk (the 8 Oct judge pod's pip into /workspace
#                                    took 14 min for 19 wheels; the container disk took 14.5 GB of downloads in 37 s)
TAG_PREFIX = "sp-"             # the user's rule for side kits: "sp-" names; the pod is attribution-judge-<tag>
SETUP_UPPER_S = 3600           # cap planning: pod start, the lead's Granite job (venv, CUDA build, GGUF, gate setup),
#                                the guard venv, the 8.8 GB Qwen3Guard download, two model loads
GRANITE_S_PER_CALL = 0.4       # cap planning per Granite call (estimate 0.12 to 0.30 s; README "Time and cost")
QWEN_S_PER_ROW = 0.25          # cap planning per Qwen3Guard row (an A100 gave 0.165 s per item at batch 8, gate A)
EST_SETUP_S = (1200, 2700)
EST_GRANITE_S = (0.12, 0.30)
EST_QWEN_S = (0.08, 0.17)
MARGIN_S = 900
MAX_CAP_HOURS = 6.0

# ---------------------------------------------------------------- exit codes

POD_EXIT_OK, POD_EXIT_ERROR, POD_EXIT_REFUSED, POD_EXIT_KA_FAILED, POD_EXIT_STOPPED = 0, 1, 2, 4, 5
POD_EXIT_TOO_SLOW = 3          # known answers passed, but their s/answer x r (the round's tokens per Granite call over
#                                the known answers' tokens) is above GRANITE_S_PER_CALL: no row is screened
LEAD_EXIT_GATE_FAILED = 3      # the lead's pod_job.py run: the known-answer gate failed (pod_job.EXIT_KNOWN_ANSWER)
EXIT_KA_FAILED = 8             # the launcher's code for a failed known-answer gate (0 and 2 to 7: as judge_pod.py)
EXIT_TOO_SLOW = 9              # the launcher's code for POD_EXIT_TOO_SLOW: the round would not fit its planned cap
