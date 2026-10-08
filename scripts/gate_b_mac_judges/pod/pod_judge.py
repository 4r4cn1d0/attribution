"""The HarmBench judge of harmbench_files.py, device-parametric: "mps" on the Mac, "cuda" on the pod.

Written 8 October 2026 (19:46 UTC, clock checked) for the lead; revised 8 October 2026 (20:51 UTC, clock checked):
the text path's packages and the tokenizer fingerprint. Nothing here changes harmbench_files.py: the Mac path
("mps") IS harmbench_files.harmbench_judge, called unchanged. The pod path ("cuda") imports every pinned piece from
harmbench_files and changes only the device:

  - the same objects: load_template (model card at the pinned revision, template SHA-256 c1c47e30...), load_tokenizer
    (the pinned tokenizer.model, SHA-256 dadfd56d..., through transformers' LlamaConverter, legacy=True,
    add_prefix_space=True, truncation_side "right"), clip_generation (HarmBench's 512-token truncation with BOS),
    label_from_token (the one decoded token, lower-cased; "unparsed" unless yes/no and finite logits), MAX_INPUT_TOKENS
    (2048, refused before the model loads), SNAPSHOT (Path.home()/.cache/huggingface/hub/... at revision 51182c7c...);
  - load_judge_on("cuda"): AutoModelForCausalLM.from_pretrained(SNAPSHOT, torch_dtype=float16, low_cpu_mem_usage=True,
    device_map="cuda"), the call of harmbench_files.load_judge with device_map "cuda" instead of "mps", and the same
    "entirely float16 on the one device" refusal;
  - the judge closure: the statements of harmbench_files.harmbench_judge's judge(), with ids.to(device) for
    ids.to("mps") and torch.cuda.empty_cache() for torch.mps.empty_cache() (every 25 items); batch size 1, one forward
    pass, use_cache=False, logits_to_keep=1, argmax of the last position (one greedy token).

tests/test_judge_pod.py compares these with harmbench_files by identity and syntax tree. The pod also pins the
snapshot's ten files by SHA-256 (SNAPSHOT_FILES, read on the Mac on 8 Oct from the Mac's snapshot; each blob name
equals its content hash, so they are the Hub's files at that revision) and the judge's packages (POD_PACKAGES, the
Mac venv's versions; torch 2.8.0 with any local label such as +cu128).

The text path: the Mac venv has neither sentencepiece nor protobuf, so harmbench_files.load_tokenizer builds the
tokenizer through its pure-Python SentencePiece reader. require_pod_packages refuses when either is installed (with
one of them, transformers could take another path), and the run record holds tokenizer_fingerprint(): the SHA-256 of
the built tokenizer's vocab and merges as canonical JSON. parity.py compares it with the Mac's. `python3 pod_judge.py
text-path` exits 0 when neither package is installed (pod_run.sh uses it to choose the venv). Never prints or stores
prompt or answer text.
"""
from __future__ import annotations

import hashlib
import json
import os
import pathlib
import sys
import time
from importlib import metadata

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
for _p in (HERE.parent, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import harmbench_files as hb  # noqa: E402
from common import Refusal  # noqa: E402
from harmbench_files import (MAX_INPUT_TOKENS, REPO, REVISION, SNAPSHOT, clip_generation,  # noqa: E402,F401
                             label_from_token, load_template, load_tokenizer)
from judging import log  # noqa: E402

DEVICES = ("mps", "cuda")
POD_DEVICE = "cuda"
POD_GPU = "NVIDIA A100-SXM4-80GB"
# The pinned snapshot (cais/HarmBench-Mistral-7b-val-cls at 51182c7c...): file -> (bytes, SHA-256). Read on 8 Oct from
# the Mac's snapshot; the LFS blobs' names are these SHA-256, the small files' blob names their git SHA-1, all matched.
SNAPSHOT_FILES = {
    "README.md": (6706, "fb438757655a2e8689dde1789eae65e4d3ca3115562c757f1219315796a41edd"),
    "config.json": (651, "80482d30e5899aa0b3389be28fc37d75917b36e4b2d00b958558ca0df68d02fb"),
    "generation_config.json": (111, "a30768e53dada01cf196b46f69aa4990f9f4285046793cb45b7c51e589778099"),
    "model-00001-of-00003.safetensors": (4943162336, "8254f960961cf37c2be61ce10445bfe048bbb00b9c261ce95c8a9cee07c4128c"),
    "model-00002-of-00003.safetensors": (4999819336, "d8291d04dc79742b8d5b2ffd7172a70372bf4aa411efecb1367a954b724a1e93"),
    "model-00003-of-00003.safetensors": (4540516344, "5f44a15c9223436dcb1119f79a285ddf389e3629b9c19e0f8f1f204bb0525ee3"),
    "model.safetensors.index.json": (23950, "a84fdfb94dda41f43767e02136d30bd102ef33c2d996218628cbd906b33e7dfb"),
    "special_tokens_map.json": (438, "719833ff26ac897a3ec8ed946028a135de2a351470af59b4008744ab1f0ee9b7"),
    "tokenizer.model": (493443, "dadfd56d766715c61d2ef780a525ab43b8e6da4de6865bda3d95fdef5e134055"),
    "tokenizer_config.json": (1470, "23d6cf3bb32e85c4e239599892e4b6ffbd0fd9c0afbbf062748f43364ad37ca4"),
}
# The judge's packages on the pod: the Mac minimal venv's versions (= the probe kits' requirements.lock). torch comes
# from the image and is checked on its public version (2.8.0; a local label such as +cu128 is recorded, not refused).
TORCH_PUBLIC = "2.8.0"
POD_PACKAGES = {"transformers": "4.56.2", "tokenizers": "0.22.2", "huggingface_hub": "0.36.2", "safetensors": "0.8.0",
                "accelerate": "1.15.0", "numpy": "2.2.6", "regex": "2026.9.29"}
TEXT_PATH_ABSENT = ("sentencepiece", "protobuf")   # not in the Mac venv: the tokenizer is built without them
LOADED: dict = {}                     # what load_judge_on recorded (device, dtypes, attention), for the run record


def sha256_path(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for block in iter(lambda: fh.read(1 << 24), b""):
            h.update(block)
    return h.hexdigest()


def verify_snapshot(snapshot: pathlib.Path = SNAPSHOT, pins: dict = SNAPSHOT_FILES) -> dict:
    """Refuses unless the snapshot folder holds exactly the pinned files with the pinned sizes and SHA-256 (symlinks to
    the hub cache's blobs are followed). Returns {file: sha256}. Reads bytes for hashing only."""
    snapshot = pathlib.Path(snapshot)
    if not snapshot.is_dir():
        raise Refusal(f"the snapshot folder {snapshot} is missing")
    names = sorted(p.name for p in snapshot.iterdir())
    if names != sorted(pins):
        raise Refusal(f"the snapshot holds {len(names)} files, not the {len(pins)} pinned ones; extra "
                      f"{sorted(set(names) - set(pins))}, missing {sorted(set(pins) - set(names))}")
    found = {}
    for name, (size, digest) in sorted(pins.items()):
        path = snapshot / name
        if not path.is_file() or path.stat().st_size != size:
            raise Refusal(f"snapshot file {name} is not a file of {size} bytes")
        found[name] = sha256_path(path)
        if found[name] != digest:
            raise Refusal(f"snapshot file {name} has SHA-256 {found[name][:16]}, not the pinned {digest[:16]}")
    return found


def public_version(version: str) -> str:
    return version.split("+", 1)[0]


def text_path_extras(version=metadata.version) -> list[str]:
    """The installed distributions of TEXT_PATH_ABSENT, as "name==version" (importlib.metadata only)."""
    extras = []
    for dist in TEXT_PATH_ABSENT:
        try:
            extras.append(f"{dist}=={version(dist)}")
        except metadata.PackageNotFoundError:
            pass
    return extras


def require_pod_packages(pins: dict = POD_PACKAGES, torch_public: str = TORCH_PUBLIC, version=metadata.version) -> dict:
    """Refuses unless every pinned distribution has its exact version, torch its public version, and neither
    sentencepiece nor protobuf is installed (the Mac's text path; importlib.metadata only, nothing is imported).
    Returns {distribution: version}."""
    extras = text_path_extras(version)
    if extras:
        raise Refusal(f"{extras} installed for {sys.executable}; the Mac venv has neither sentencepiece nor protobuf, "
                      "so the tokenizer would not be built as on the Mac")
    found = {}
    for dist, want in {**pins, "torch": None}.items():
        try:
            got = version(dist)
        except metadata.PackageNotFoundError:
            raise Refusal(f"package {dist} is not installed for {sys.executable}") from None
        ok = public_version(got) == torch_public if dist == "torch" else got == want
        if not ok:
            raise Refusal(f"package {dist} is {got} for {sys.executable}, not the pinned "
                          f"{torch_public if dist == 'torch' else want}")
        found[dist] = got
    return found


def tokenizer_fingerprint(tok=None) -> str:
    """SHA-256 of the built tokenizer's vocab and merges (its backend model's, as canonical JSON: sorted keys, no
    spaces, UTF-8). `tok` defaults to a fresh load_tokenizer(), built before any encode call."""
    tok = load_tokenizer() if tok is None else tok
    model = json.loads(tok.backend_tokenizer.to_str())["model"]
    data = json.dumps({"vocab": model["vocab"], "merges": model["merges"]}, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":"))
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------- the model on one device

def load_judge_on(device: str):
    """harmbench_files.load_judge on "mps" (unchanged, the Mac path); on "cuda" its from_pretrained call with
    device_map "cuda" and the same float16-on-one-device refusal."""
    if device not in DEVICES:
        raise Refusal(f"unknown device {device!r}; one of {list(DEVICES)}")
    if device == "mps":
        return hb.load_judge()
    import torch
    from transformers import AutoModelForCausalLM
    if not torch.cuda.is_available():
        raise SystemExit("CUDA is not available")
    t = time.time()
    model = AutoModelForCausalLM.from_pretrained(str(SNAPSHOT), torch_dtype=torch.float16, low_cpu_mem_usage=True,
                                                 device_map="cuda")
    model.eval()
    devs = sorted({str(p.device) for p in model.parameters()})
    dtypes = sorted({str(p.dtype) for p in model.parameters()})
    LOADED.update(device=device, devices=devs, dtypes=dtypes, attn=getattr(model.config, "_attn_implementation", None),
                  gpu=torch.cuda.get_device_name(0), seconds=round(time.time() - t, 1))
    log(event="judge_loaded", seconds=LOADED["seconds"], torch=torch.__version__, devices=devs, dtypes=dtypes,
        gpu=LOADED["gpu"], cuda_allocated_gib=round(torch.cuda.memory_allocated() / 1024 ** 3, 2),
        attn=LOADED["attn"])
    if devs != ["cuda:0"] or dtypes != ["torch.float16"]:
        raise SystemExit("judge is not entirely float16 on cuda")
    return torch, model


def make_factory(device: str):
    """The judge factory for judging.run on one device. "mps": harmbench_files.harmbench_judge itself. "cuda": the same
    steps (template and tokenizer first, every classifier input built and length-checked before the model loads, then
    one forward pass per answer); the tokenizer, template and model are loaded once per process and kept for later
    calls (one pod run judges each prepared set's units in its own judging.run call)."""
    if device not in DEVICES:
        raise Refusal(f"unknown device {device!r}; one of {list(DEVICES)}")
    if device == "mps":
        return hb.harmbench_judge
    kept: dict = {}

    def harmbench_judge_on_device(pairs):
        if "tok" not in kept:
            kept["template"] = load_template()
            kept["tok"] = load_tokenizer()
        template, tok = kept["template"], kept["tok"]
        for pair in pairs:                     # judging.Pair(where, prompt, answer); `where` holds ids only
            n = len(tok(template.format(behavior=pair.prompt, generation=clip_generation(tok, pair.answer)[0])).input_ids)
            if n > MAX_INPUT_TOKENS:
                raise Refusal(f"{pair.where}: the classifier input has {n} tokens, above the {MAX_INPUT_TOKENS} cap")
        if "model" not in kept:
            kept["torch"], kept["model"] = load_judge_on(device)
        torch, model = kept["torch"], kept["model"]
        state = {"n": 0}

        def judge(prompt: str, answer: str) -> dict:
            clipped, full_tokens, was_clipped = clip_generation(tok, answer)
            ids = tok(template.format(behavior=prompt, generation=clipped), return_tensors="pt").input_ids  # BOS added
            if ids.shape[1] > MAX_INPUT_TOKENS:
                raise Refusal(f"an input has {ids.shape[1]} tokens, above the {MAX_INPUT_TOKENS} cap")
            with torch.inference_mode():
                ids = ids.to(device)
                out = model(input_ids=ids, use_cache=False, logits_to_keep=1)
                last = out.logits[0, -1].float()
                finite = bool(torch.isfinite(last).all().item())
                tid = int(last.argmax().item())
            p = tok.decode([tid], skip_special_tokens=True)
            n_in = int(ids.shape[1])
            del out, last, ids
            state["n"] += 1
            if state["n"] % 25 == 0:
                torch.cuda.empty_cache()
            if state["n"] % 50 == 0:
                log(event="cuda", judged=state["n"], cuda_allocated_gib=round(torch.cuda.memory_allocated() / 1024 ** 3, 2),
                    cuda_reserved_gib=round(torch.cuda.memory_reserved() / 1024 ** 3, 2))
            return {"label": label_from_token(p, finite), "input_tokens": n_in, "answer_tokens": full_tokens - 1,
                    "truncated": was_clipped}

        return judge

    return harmbench_judge_on_device


def environment(device: str) -> dict:
    """The run record's environment block on the pod (imports torch and transformers; versions and flags only)."""
    import platform
    import subprocess

    import torch
    import transformers
    driver = None
    try:
        q = subprocess.run(["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader"], capture_output=True,
                           text=True, timeout=30)
        driver = q.stdout.strip().splitlines()[0] if q.returncode == 0 and q.stdout.strip() else None
    except (OSError, subprocess.SubprocessError):
        driver = None
    cuda = device == "cuda" and torch.cuda.is_available()
    cfg = pathlib.Path(sys.prefix) / "pyvenv.cfg"
    system_site = None
    if cfg.is_file():
        for line in cfg.read_text(encoding="utf-8", errors="replace").splitlines():
            if line.split("=", 1)[0].strip() == "include-system-site-packages":
                system_site = line.split("=", 1)[1].strip().lower() == "true"
    return {"device": device, "python": platform.python_version(), "torch": torch.__version__,
            "venv_system_site_packages": system_site, "text_path_extras": text_path_extras(),
            "torch_cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version() if cuda else None,
            "transformers": transformers.__version__,
            "packages": {d: metadata.version(d) for d in (*POD_PACKAGES, "torch")},
            "gpu": torch.cuda.get_device_name(0) if cuda else None,
            "gpu_count": torch.cuda.device_count() if cuda else 0, "driver": driver,
            "flags": {"matmul_allow_tf32": torch.backends.cuda.matmul.allow_tf32,
                      "matmul_allow_fp16_reduced_precision_reduction":
                          torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction,
                      "cudnn_allow_tf32": torch.backends.cudnn.allow_tf32,
                      "deterministic_algorithms": torch.are_deterministic_algorithms_enabled()},
            "env": {k: os.environ.get(k) for k in ("CUBLAS_WORKSPACE_CONFIG", "HF_HUB_OFFLINE", "TRANSFORMERS_OFFLINE",
                                                   "TOKENIZERS_PARALLELISM")},
            "loaded": dict(LOADED)}


def pins() -> dict:
    """The judge's pins, for the run record and the Mac log."""
    return {"repo": REPO, "revision": REVISION, "template_sha256": hb.TEMPLATE_SHA256,
            "tokenizer_model_sha256": hb.TOKENIZER_MODEL_SHA256, "num_tokens": hb.NUM_TOKENS,
            "max_input_tokens": MAX_INPUT_TOKENS, "dtype": "float16", "batch_size": 1, "new_tokens": 1,
            "snapshot_files": {k: v[1] for k, v in SNAPSHOT_FILES.items()}}


if __name__ == "__main__":
    if sys.argv[1:] == ["text-path"]:
        sys.exit(3 if text_path_extras() else 0)
    print(json.dumps(pins(), indent=1, sort_keys=True))
