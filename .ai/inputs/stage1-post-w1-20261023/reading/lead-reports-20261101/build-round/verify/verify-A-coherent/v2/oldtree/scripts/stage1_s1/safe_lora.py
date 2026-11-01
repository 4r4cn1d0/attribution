"""B11: the Safe LoRA transform (Hsu et al., arXiv 2405.16833v2) as a post-hoc CPU state transform.

Settings: ``settings/safe_lora.json`` (pinned below by SHA-256). REF = the reference-arm pre-registration draft,
revision 2, section R.1. Nothing here trains, downloads or evaluates; the evaluation is B10's.

1. Inputs, each checked before any arithmetic:
   - a0's e1 adapter at seed j: an engine ``adapter.safetensors`` file, or the state folder that holds it with its
     ``state.json``. It is accepted only if its engine fingerprint equals the Gate A unit's at that seed (REF R.0.7).
   - the aligned model (OLMo-2-0425-1B-Instruct, the untuned model of every arm) and the unaligned model (the
     OLMo-2-0425-1B base), each a local snapshot folder. The folder name must match the pinned commit and its
     safetensors files must match the pinned files. Nothing is downloaded.
2. For each adapted matrix i (7 modules x 16 blocks = 112), paired by exact module name and never by position:
   V_i = float32(W_i aligned) - float32(W_i unaligned); n_i = ||V_i||_F;
   B'_i = V_i (V_i^T B_i) / n_i, the fast form C = V V^T / ||V||_F applied to lora_B (C is never formed);
   cos_i and rho_i compare B'_i A_i with B_i A_i (A_i = lora_A) in float64 without rounding: cos_i is the Frobenius
   cosine and rho_i = ||B'_i A_i||_F / ||B_i A_i||_F. The LoRA scale alpha/r cancels in both.
3. All matrices are ranked together by (cos_i ascending, module name). A point maps exactly its first K matrices:
   lora_B <- float32(B'_i). lora_A and every unmapped lora_B stay byte for byte. K = 39 is the pre-registered point;
   K = 12 runs only if the user adds it (REF UQ9; PREREG FC-27). The third point, "certify", maps nothing (K = 0)
   and is never a reference point: it is REF R.1.4's certification of the B10 file path (LQ11; RS D2).
4. Outputs: the new adapter (still a rank-r PEFT adapter, never merged) with its engine fingerprint, and a record
   with module names, numbers and hashes only (per matrix: name, block, module, shape, ||V||_F, cos, rho, rank,
   mapped; the K-th cosine; how many matrices tau = 0.35 and tau = 0.5 would map; the module and block mix; flags).
   ``check`` is the $0 weight-only check of REF R.1.5: it writes the record for the two reference points (default
   and conditional) and no adapter. Both commands also write a timing file (REF section C.9: the transform's
   measured seconds), kept apart from the record so that the record stays byte-identical on a re-run.
5. ``vcheck`` is the V/V' diagnostic (addendum section 11 point 8; section 13 point 3: the Safe LoRA pod job runs it
   before the projection, with both snapshots at their pinned commits). V' = float32(W aligned) -
   float32(bfloat16(W unaligned)). Per matrix it gives ||V - V'||_F / ||V||_F; it also says whether the default
   point's mapped set (K = 39, the fast form, the same ranking rule) changes between V and V'. V stays the primary
   (REF R.1.3 row 5); the diagnostic changes no adapter and no K.

Outputs through B10's transform hook, in two forms:
- the file form (B10's "file" external transform; REF R.1.4 "B10's script evaluates a given adapter file"): the
  ``transform`` command writes ``adapter.safetensors`` and ``safe_lora_record.json`` to a new folder. The record holds
  the five fields B10 checks, at the dotted paths of ``B10_RECORD_KEYS`` (this module's SHA-256, the source and
  output adapter fingerprints, the output file's SHA-256 and the settings' SHA-256: B10's fifth key, addendum
  section 11 point 5); B10's settings allowlist this module and these settings by SHA-256 (``safe_lora``);
- the in-process form: ``SafeLoRA(settings, aligned_folder, base_folder, seed=..., point=...)`` is a callable
  ``hook(adapter) -> TransformResult``. ``adapter`` maps the engine's adapter names to tensors; the result holds the
  new tensors (``result.adapter``), their engine fingerprint, their safetensors bytes and the record. The caller loads
  ``result.adapter`` with the engine's ``load_lora_state`` and checks the fingerprint.

Command line (exit 0 on success, 2 on a refusal; nothing is written on a refusal):
  python -m scripts.stage1_s1.safe_lora check --adapter A --seed 1101 --aligned DIR --base DIR --out NEW_DIR
  python -m scripts.stage1_s1.safe_lora transform --point default|conditional|certify --adapter A --seed 1101
      --aligned DIR --base DIR --out NEW_DIR
  python -m scripts.stage1_s1.safe_lora vcheck --adapter A --seed 1101 --aligned DIR --base DIR --out NEW_DIR
``check`` writes safe_lora_check.json and safe_lora_timing.json; ``transform`` writes adapter.safetensors,
safe_lora_record.json and safe_lora_timing.json; ``vcheck`` writes safe_lora_vcheck.json and safe_lora_timing.json
(the names are the settings' outputs and v_diagnostic.output). The printed line holds the
command, the SHA-256 of each file written and the stage seconds.

Messages and records carry module names, counts, numbers and hashes only. This module reads no dataset file.
"""

from __future__ import annotations

import argparse
import contextlib
import json
import math
import re
import statistics
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

import numpy  # noqa: E402
import torch  # noqa: E402
from safetensors import safe_open  # noqa: E402
from safetensors.torch import load as safetensors_load  # noqa: E402
from safetensors.torch import save as safetensors_save  # noqa: E402

from experiments.safety_selection.common import canonical_json, sha256_bytes, sha256_file  # noqa: E402
from experiments.safety_selection.engine import lora_fingerprint  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

__all__ = ["Refusal", "NAME", "SETTINGS_PATH", "SETTINGS_SHA256", "B10_RECORD_KEYS", "Settings", "validate_settings",
           "load_pinned_settings", "pin_matches", "Snapshot", "open_snapshot", "SourceAdapter", "read_adapter",
           "check_adapter", "adapter_fingerprint", "alignment_matrix", "project_b", "similarity",
           "bf16_rounding_share", "ranking", "tau_counts", "MatrixResult", "Analysis", "analyse", "apply_point",
           "TransformResult", "SafeLoRA", "main", "download_pin", "stored_dtype_counts", "alignment_matrix_prime",
           "relative_difference", "compare_selection", "v_diagnostic"]

Refusal = s1.Refusal
NAME = "safe_lora"
OWNER = "scripts/stage1_s1/safe_lora.py"
SETTINGS_PATH = HERE / "settings" / "safe_lora.json"
SETTINGS_SHA256 = "c5610c3d4f0a0809e391055d84697fd62b9a15cf16e0b1f63aee02b03b6d14cf"
RECORD_KIND = "stage1 safe lora record"
TIMING_KIND = "stage1 safe lora timing"
VCHECK_KIND = "stage1 safe lora v diagnostic"
POINTS = ("default", "conditional", "certify")
CHECK_POINTS = ("default", "conditional")          # the two reference points; the $0 check reports these only
OUTPUT_KEYS = ("adapter", "record", "check_record", "timing")
ADAPTER_FILE = "adapter.safetensors"
STATE_FILE = "state.json"
MODULE_PART = {"q_proj": "self_attn", "k_proj": "self_attn", "v_proj": "self_attn", "o_proj": "self_attn",
               "gate_proj": "mlp", "up_proj": "mlp", "down_proj": "mlp"}
ADAPTER_KEY = re.compile(r"^base_model\.model\.(?P<module>model\.layers\.(?P<block>0|[1-9][0-9]*)\."
                         r"(?P<part>self_attn|mlp)\.(?P<proj>[a-z_]+))\.lora_(?P<factor>[AB])\.default\.weight$")
HEX = re.compile(r"^[0-9a-f]+$")
COMMIT = re.compile(r"^[0-9a-f]{40}$")
SEED = re.compile(r"^[0-9]{4}$")
DTYPES = {"bfloat16": torch.bfloat16, "float32": torch.float32}
STORED_DTYPE = {"bfloat16": "BF16", "float32": "F32"}  # the safetensors header name of each pinned dtype
HUB_FILE_KEYS = {"rfilename", "size", "git_blob_id", "lfs_sha256"}
GIT_BLOB = re.compile(r"^[0-9a-f]{40}$")
COMMIT_PIN = (8, 40)
FILE_PIN = (12, 64)
# Where B10's file-transform check finds its four fields in the record (dotted paths; B10's record_keys).
B10_RECORD_KEYS = {"transform_sha256": "provenance.script_sha256",
                   "source_adapter_fingerprint": "input_adapter.fingerprint",
                   "output_adapter_fingerprint": "output.fingerprint",
                   "output_file_sha256": "output.adapter_sha256",
                   "transform_settings_sha256": "provenance.settings_sha256"}   # B10's fifth key (addendum 11.5)


# ----- settings -------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class Settings:
    doc: dict
    sha256: str
    modules: tuple[str, ...]
    blocks: int
    rank: int
    matrices: int
    parameters: int
    accepted: dict[str, str]          # seed -> the accepted engine fingerprint
    state_checks: dict[str, str]
    aligned: dict
    unaligned: dict
    points: dict[str, int]
    point_status: dict[str, str]
    taus: tuple[float, ...]
    threads: int
    v_point: str                      # the point whose mapped set the V/V' diagnostic compares
    v_output: str                     # the V/V' diagnostic's file name


def _int(value: Any, what: str, low: int = 0) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < low:
        raise Refusal(f"settings {NAME}: {what} is not an integer of at least {low}")
    return value


def _hex_pin(value: Any, bounds: tuple[int, int], what: str) -> str:
    low, high = bounds
    if not isinstance(value, str) or not HEX.match(value) or not low <= len(value) <= high:
        raise Refusal(f"{what}: the pin is not {low}-{high} lowercase hex characters")
    return value


def _model_spec(spec: Any, role: str) -> dict:
    if not isinstance(spec, dict):
        raise Refusal(f"settings {NAME}: models.{role} is not an object")
    if not isinstance(spec.get("repo_id"), str) or "/" not in spec["repo_id"]:
        raise Refusal(f"settings {NAME}: models.{role}.repo_id is not a repository id")
    _hex_pin(spec.get("revision"), COMMIT_PIN, f"settings {NAME}: models.{role}.revision")
    if spec.get("dtype") not in DTYPES:
        raise Refusal(f"settings {NAME}: models.{role}.dtype is not one of {sorted(DTYPES)}")
    files = spec.get("files")
    if not isinstance(files, list) or not files:
        raise Refusal(f"settings {NAME}: models.{role}.files is not a non-empty list")
    for pin in files:
        if not isinstance(pin, dict) or not set(pin) <= {"file", "bytes", "sha256"}:
            raise Refusal(f"settings {NAME}: a models.{role} file pin has other keys than file, bytes, sha256")
        _hex_pin(pin.get("sha256"), FILE_PIN, f"settings {NAME}: a models.{role} file pin")
        if "file" in pin and (not isinstance(pin["file"], str) or not pin["file"].endswith(".safetensors")):
            raise Refusal(f"settings {NAME}: a models.{role} file pin names no safetensors file")
        if "bytes" in pin:
            _int(pin["bytes"], f"a models.{role} file pin's bytes", 1)
    if "total_bytes" in spec:
        _int(spec["total_bytes"], f"models.{role}.total_bytes", 1)
    if "stored_dtype" in spec:
        stored = spec["stored_dtype"]
        if (not isinstance(stored, dict) or set(stored) != {STORED_DTYPE[spec["dtype"]]}
                or not all(isinstance(v, int) and not isinstance(v, bool) and v >= 1 for v in stored.values())):
            raise Refusal(f"settings {NAME}: models.{role}.stored_dtype is not {{{STORED_DTYPE[spec['dtype']]}: a "
                          f"count}} (every stored tensor in the pinned dtype)")
    if "hub_files" in spec:
        _hub_files(spec, role)
    return spec


def _hub_files(spec: Mapping[str, Any], role: str) -> None:
    """The full Hub pin of a snapshot (addendum section 11 point 6): every repository file with its size and git blob
    id, and the LFS SHA-256 of each LFS file. It needs the full 40-hex commit, and its safetensors files must be the
    file pins exactly (name, bytes and the full SHA-256), with total_bytes their sum."""
    what = f"settings {NAME}: models.{role}.hub_files"
    if not COMMIT.match(spec["revision"]):
        raise Refusal(f"{what} needs the full 40-hex commit as the revision")
    files = spec["hub_files"]
    if not isinstance(files, list) or not files:
        raise Refusal(f"{what} is not a non-empty list")
    names = []
    for entry in files:
        if not isinstance(entry, dict) or set(entry) != HUB_FILE_KEYS:
            raise Refusal(f"{what}: an entry is not {{{', '.join(sorted(HUB_FILE_KEYS))}}}")
        name = entry["rfilename"]
        if not isinstance(name, str) or not name or name.startswith("/") or ".." in name.split("/"):
            raise Refusal(f"{what}: an entry names no repository file")
        _int(entry["size"], f"the hub file {name}'s size", 1)
        if not isinstance(entry["git_blob_id"], str) or not GIT_BLOB.match(entry["git_blob_id"]):
            raise Refusal(f"{what}: {name} has no 40-hex git blob id")
        if entry["lfs_sha256"] is not None and (not isinstance(entry["lfs_sha256"], str)
                                                or not re.fullmatch(r"[0-9a-f]{64}", entry["lfs_sha256"])):
            raise Refusal(f"{what}: {name}'s LFS SHA-256 is not 64 hex characters or null")
        names.append(name)
    if len(set(names)) != len(names) or names != sorted(names):
        raise Refusal(f"{what} does not list distinct files in name order")
    weights = sorted(({"file": e["rfilename"], "bytes": e["size"], "sha256": e["lfs_sha256"]}
                      for e in files if e["rfilename"].endswith(".safetensors") and "/" not in e["rfilename"]),
                     key=lambda f: f["file"])
    if any(w["sha256"] is None for w in weights):
        raise Refusal(f"{what}: a safetensors file has no LFS SHA-256")
    if weights != sorted((dict(f) for f in spec["files"]), key=lambda f: f.get("file", "")):
        raise Refusal(f"{what}: the safetensors files are not the file pins (name, bytes, full SHA-256)")
    if spec.get("total_bytes") != sum(w["bytes"] for w in weights):
        raise Refusal(f"{what}: total_bytes is not the sum of the safetensors sizes")


def validate_settings(doc: Any, sha256: str) -> Settings:
    """A parsed safe_lora settings document, checked (s1common.check_settings, then this file's own rules)."""
    doc = s1.check_settings(doc, NAME)
    if doc.get("owner") != OWNER or doc.get("version") != 1:
        raise Refusal(f"settings {NAME}: not the version-1 settings owned by {OWNER}")
    if doc.get("label_entries") != {}:
        raise Refusal(f"settings {NAME}: Safe LoRA draws no random number, so it names no registry entry")
    adapter = doc.get("adapter")
    if not isinstance(adapter, dict):
        raise Refusal(f"settings {NAME}: no adapter section")
    modules = adapter.get("modules")
    if (not isinstance(modules, list) or not modules or len(set(modules)) != len(modules)
            or not all(m in MODULE_PART for m in modules)):
        raise Refusal(f"settings {NAME}: adapter.modules is not a list of distinct adapted module names")
    blocks = _int(adapter.get("blocks"), "adapter.blocks", 1)
    rank = _int(adapter.get("rank"), "adapter.rank", 1)
    matrices = _int(adapter.get("matrices"), "adapter.matrices", 1)
    if matrices != blocks * len(modules):
        raise Refusal(f"settings {NAME}: adapter.matrices is not blocks x modules")
    parameters = _int(adapter.get("parameters"), "adapter.parameters", 1)
    if adapter.get("dtype") != "float32":
        raise Refusal(f"settings {NAME}: the adapter dtype is not float32")
    accepted = adapter.get("accepted")
    if not isinstance(accepted, dict) or not accepted:
        raise Refusal(f"settings {NAME}: adapter.accepted is not a non-empty object")
    fingerprints = {}
    for seed, entry in accepted.items():
        if not SEED.match(seed) or not isinstance(entry, dict):
            raise Refusal(f"settings {NAME}: adapter.accepted has a malformed seed entry")
        fingerprints[seed] = _hex_pin(entry.get("fingerprint"), (64, 64), f"settings {NAME}: the fingerprint of {seed}")
    checks = adapter.get("state_checks")
    if not isinstance(checks, dict) or set(checks) != {"arm", "checkpoint"} or not all(
            isinstance(v, str) and v for v in checks.values()):
        raise Refusal(f"settings {NAME}: adapter.state_checks is not {{arm, checkpoint}}")
    models = doc.get("models")
    if not isinstance(models, dict) or set(models) != {"aligned", "unaligned"}:
        raise Refusal(f"settings {NAME}: models is not {{aligned, unaligned}}")
    aligned, unaligned = _model_spec(models["aligned"], "aligned"), _model_spec(models["unaligned"], "unaligned")
    transform = doc.get("transform")
    if not isinstance(transform, dict):
        raise Refusal(f"settings {NAME}: no transform section")
    if (transform.get("operator"), transform.get("factor"), transform.get("rule")) != ("fast_form_c", "lora_B", "top_k"):
        raise Refusal(f"settings {NAME}: the transform is not the fast form C on lora_B with a top-K rule")
    points = transform.get("points")
    if not isinstance(points, dict) or set(points) != set(POINTS):
        raise Refusal(f"settings {NAME}: transform.points is not {{{', '.join(POINTS)}}}")
    ks, status = {}, {}
    for point in POINTS:
        entry = points[point]
        if not isinstance(entry, dict) or not isinstance(entry.get("status"), str):
            raise Refusal(f"settings {NAME}: transform.points.{point} has no k and status")
        ks[point] = _int(entry.get("k"), f"transform.points.{point}.k")
        if ks[point] > matrices:
            raise Refusal(f"settings {NAME}: K = {ks[point]} of point {point} is outside 0..{matrices}")
        status[point] = entry["status"]
    if ks["certify"] != 0:
        raise Refusal(f"settings {NAME}: the certify point maps nothing (K = 0), not K = {ks['certify']}")
    threads = _int(transform.get("torch_threads"), "transform.torch_threads", 1)
    report = doc.get("report")
    taus = report.get("taus") if isinstance(report, dict) else None
    if not isinstance(taus, list) or not taus or not all(
            isinstance(t, float) and math.isfinite(t) and -1.0 < t <= 1.0 for t in taus):
        raise Refusal(f"settings {NAME}: report.taus is not a list of cosines")
    outputs = doc.get("outputs")
    names = [outputs.get(k) for k in OUTPUT_KEYS] if isinstance(outputs, dict) else []
    if (len(names) != len(OUTPUT_KEYS)
            or not all(isinstance(n, str) and re.fullmatch(r"[a-z0-9_]+\.(safetensors|json)", n) for n in names)
            or len(set(names)) != len(OUTPUT_KEYS)):
        raise Refusal(f"settings {NAME}: outputs does not name four distinct output files")
    diag = doc.get("v_diagnostic")
    if not isinstance(diag, dict) or not all(isinstance(diag.get(k), str) and diag[k]
                                             for k in ("point", "output", "v_prime", "measure", "rule", "when")):
        raise Refusal(f"settings {NAME}: no v_diagnostic section (point, output, v_prime, measure, rule, when)")
    if diag["point"] not in CHECK_POINTS:
        raise Refusal(f"settings {NAME}: the V/V' diagnostic compares a reference point, not {diag['point']!r}")
    if not re.fullmatch(r"[a-z0-9_]+\.json", diag["output"]) or diag["output"] in names:
        raise Refusal(f"settings {NAME}: the V/V' diagnostic's output is not a JSON file name apart from the outputs")
    outcomes = diag.get("outcomes")
    if not isinstance(outcomes, dict) or set(outcomes) != {"changes", "same"} or not all(
            isinstance(v, str) and v for v in outcomes.values()):
        raise Refusal(f"settings {NAME}: v_diagnostic.outcomes is not {{changes, same}}")
    return Settings(doc, sha256, tuple(modules), blocks, rank, matrices, parameters, fingerprints, dict(checks),
                    aligned, unaligned, ks, status, tuple(taus), threads, diag["point"], diag["output"])


def load_pinned_settings(path: str | Path | None = None, expected_sha256: str | None = None) -> Settings:
    """The settings file, refused unless its bytes hash to the pin (SETTINGS_SHA256 by default)."""
    path = SETTINGS_PATH if path is None else Path(path)
    expected_sha256 = SETTINGS_SHA256 if expected_sha256 is None else expected_sha256
    doc, digest = s1.load_settings(path, expected_sha256, NAME)
    return validate_settings(doc, digest)


# ----- the two model snapshots --------------------------------------------------------------------------------


def pin_matches(observed: str, pin: str) -> bool:
    """The pin rule: an observed hex value matches a pin when it starts with it (a full-length pin: equality)."""
    return isinstance(observed, str) and observed.startswith(pin)


def download_pin(settings: Settings, role: str) -> dict:
    """What the stage-1 kit (B15) passes to the Hub download of one snapshot: the repository and the full pinned
    commit (``revision=<the commit>``, never ``main``; addendum section 11 point 6). A prefix pin refuses."""
    spec = {"aligned": settings.aligned, "unaligned": settings.unaligned}.get(role)
    if spec is None:
        raise Refusal(f"no model role {role!r}")
    if not COMMIT.match(spec["revision"]):
        raise Refusal(f"the {role} model is pinned by a commit prefix; a download needs the full commit")
    return {"repo_id": spec["repo_id"], "revision": spec["revision"]}


def stored_dtype_counts(paths: Sequence[Path], role: str) -> dict[str, int]:
    """The stored values per safetensors dtype over every tensor of these files (headers only; no tensor is read)."""
    counts: dict[str, int] = {}
    for path in paths:
        try:
            with safe_open(str(path), framework="pt", device="cpu") as handle:
                for key in handle.keys():
                    piece = handle.get_slice(key)
                    counts[piece.get_dtype()] = counts.get(piece.get_dtype(), 0) + math.prod(piece.get_shape())
        except Exception as exc:                               # safetensors' own error type, by name only
            raise Refusal(f"the {role} file {path.name} is not a safetensors file ({type(exc).__name__})") from None
    return dict(sorted(counts.items()))


@dataclass(frozen=True)
class Snapshot:
    role: str
    repo_id: str
    revision: str                     # the observed full commit (the snapshot folder's name)
    dtype: torch.dtype
    files: tuple[dict, ...]           # {file, bytes, sha256} of every safetensors file, by name
    key_file: dict[str, Path]
    stored_dtype: dict | None = None  # the observed stored values per dtype, when the settings pin them

    def weight(self, module: str) -> torch.Tensor:
        """The 2-D weight <module>.weight in the pinned dtype; a missing, misshaped or non-finite weight refuses."""
        key = f"{module}.weight"
        path = self.key_file.get(key)
        if path is None:
            raise Refusal(f"the {self.role} model has no weight {key}")
        with safe_open(str(path), framework="pt", device="cpu") as handle:
            tensor = handle.get_tensor(key)
        if tensor.dtype != self.dtype:
            raise Refusal(f"the {self.role} weight {key} is {tensor.dtype}, the settings pin {self.dtype}")
        if tensor.dim() != 2:
            raise Refusal(f"the {self.role} weight {key} is not a matrix")
        if not bool(torch.isfinite(tensor).all()):
            raise Refusal(f"the {self.role} weight {key} holds NaN or infinity")
        return tensor

    def identity(self) -> dict:
        out = {"repo_id": self.repo_id, "revision": self.revision, "dtype": str(self.dtype).replace("torch.", ""),
               "files": [dict(f) for f in self.files]}
        if self.stored_dtype is not None:
            out["stored_dtype"] = dict(self.stored_dtype)
        return out


def open_snapshot(folder: str | Path, spec: Mapping[str, Any], role: str) -> Snapshot:
    """One model snapshot checked against its pins (the pin rule of the settings), with a weight-name index."""
    folder = Path(folder)
    if not folder.is_dir():
        raise Refusal(f"the {role} snapshot folder does not exist")
    revision = folder.name
    if not COMMIT.match(revision):
        raise Refusal(f"the {role} snapshot folder is not named by a 40-hex commit")
    if not pin_matches(revision, spec["revision"]):
        raise Refusal(f"the {role} snapshot is commit {revision}, the settings pin {spec['revision']}")
    paths = sorted(p for p in folder.iterdir() if p.name.endswith(".safetensors"))
    if len(paths) != len(spec["files"]):
        raise Refusal(f"the {role} snapshot has {len(paths)} safetensors files, the settings pin {len(spec['files'])}")
    observed = [{"file": p.name, "bytes": p.stat().st_size, "sha256": sha256_file(p)} for p in paths]
    used: set[str] = set()
    for pin in spec["files"]:
        hits = [o for o in observed if pin_matches(o["sha256"], pin["sha256"])
                and pin.get("file", o["file"]) == o["file"] and pin.get("bytes", o["bytes"]) == o["bytes"]]
        if len(hits) != 1 or hits[0]["file"] in used:
            raise Refusal(f"the {role} snapshot's files do not match the file pin {pin['sha256']} one to one")
        used.add(hits[0]["file"])
    if "total_bytes" in spec and sum(o["bytes"] for o in observed) != spec["total_bytes"]:
        raise Refusal(f"the {role} snapshot's safetensors files do not sum to the pinned {spec['total_bytes']} bytes")
    key_file: dict[str, Path] = {}
    for path in paths:
        try:
            with safe_open(str(path), framework="pt", device="cpu") as handle:
                keys = list(handle.keys())
        except Exception as exc:                               # safetensors' own error type, by name only
            raise Refusal(f"the {role} file {path.name} is not a safetensors file ({type(exc).__name__})") from None
        for key in keys:
            if key in key_file:
                raise Refusal(f"the {role} weight {key} is in two files")
            key_file[key] = path
    stored = None
    if "stored_dtype" in spec:
        stored = stored_dtype_counts(paths, role)
        if stored != spec["stored_dtype"]:
            raise Refusal(f"the {role} snapshot stores {stored}, the settings pin {spec['stored_dtype']}")
    return Snapshot(role, spec["repo_id"], revision, DTYPES[spec["dtype"]], tuple(observed), key_file, stored)


# ----- the input adapter ----------------------------------------------------------------------------------------


@dataclass(frozen=True)
class SourceAdapter:
    tensors: dict[str, torch.Tensor]
    file_sha256: str
    file_bytes: bytes
    state_json_sha256: str | None
    state: dict | None


def adapter_fingerprint(tensors: Mapping[str, torch.Tensor]) -> str:
    """The engine's adapter fingerprint (lora_fingerprint over the sorted names), as state.json records it."""
    return lora_fingerprint(sorted(tensors.items()))


def read_adapter(path: str | Path) -> SourceAdapter:
    """An engine adapter file, or a state folder whose files hash to its state.json and whose adapter carries the
    recorded fingerprint."""
    path = Path(path)
    state, state_sha = None, None
    try:
        if path.is_dir():
            state_bytes = (path / STATE_FILE).read_bytes()
            state_sha, state = sha256_bytes(state_bytes), s1.strict_json(state_bytes)
            files = state.get("files") if isinstance(state, dict) else None
            if not isinstance(files, dict) or ADAPTER_FILE not in files:
                raise Refusal("the state folder's state.json lists no adapter file")
            for name, digest in sorted(files.items()):
                if sha256_file(path / name) != digest:
                    raise Refusal(f"the state folder's {name} differs from its state.json hash")
            path = path / ADAPTER_FILE
        data = path.read_bytes()
    except OSError as exc:
        raise Refusal(f"the input adapter cannot be read ({type(exc).__name__})") from None
    try:
        tensors = dict(safetensors_load(data))
    except Exception as exc:                                   # safetensors' own error type, by name only
        raise Refusal(f"the input adapter is not a safetensors file ({type(exc).__name__})") from None
    if state is not None and adapter_fingerprint(tensors) != state.get("adapter_fingerprint"):
        raise Refusal("the state folder's adapter differs from its recorded adapter_fingerprint")
    return SourceAdapter(tensors, sha256_bytes(data), data, state_sha, state)


def check_adapter(tensors: Mapping[str, torch.Tensor], settings: Settings) -> list[str]:
    """The adapter's module paths (sorted): exactly the settings' blocks x modules, each with one lora_A (r x in)
    and one lora_B (out x r), float32 and finite, with the settings' parameter count."""
    factors: dict[str, set[str]] = {}
    for key, tensor in tensors.items():
        match = ADAPTER_KEY.match(key) if isinstance(key, str) else None
        if match is None or match["proj"] not in settings.modules or MODULE_PART[match["proj"]] != match["part"] \
                or int(match["block"]) >= settings.blocks:
            raise Refusal(f"the adapter holds a tensor that is not one of the settings' LoRA matrices ({key!r})")
        if not isinstance(tensor, torch.Tensor) or tensor.dtype != torch.float32 or tensor.dim() != 2:
            raise Refusal(f"the adapter tensor {key} is not a float32 matrix")
        if not bool(torch.isfinite(tensor).all()):
            raise Refusal(f"the adapter tensor {key} holds NaN or infinity")
        factors.setdefault(match["module"], set()).add(match["factor"])
        shape, rank = tuple(tensor.shape), settings.rank
        if (match["factor"] == "A" and shape[0] != rank) or (match["factor"] == "B" and shape[1] != rank):
            raise Refusal(f"the adapter tensor {key} does not have rank {rank}")
    expected = {f"model.layers.{b}.{MODULE_PART[m]}.{m}" for b in range(settings.blocks) for m in settings.modules}
    if set(factors) != expected or any(f != {"A", "B"} for f in factors.values()):
        missing = len(expected - set(factors)) + sum(f != {"A", "B"} for f in factors.values())
        raise Refusal(f"the adapter's matrices are not the settings' {settings.matrices} ({missing} missing or "
                      f"incomplete, {len(set(factors) - expected)} extra)")
    count = sum(t.numel() for t in tensors.values())
    if count != settings.parameters:
        raise Refusal(f"the adapter has {count} values, the settings pin {settings.parameters}")
    return sorted(factors)


def _a(module: str) -> str:
    return f"base_model.model.{module}.lora_A.default.weight"


def _b(module: str) -> str:
    return f"base_model.model.{module}.lora_B.default.weight"


# ----- the arithmetic -------------------------------------------------------------------------------------------


def alignment_matrix(w_aligned: torch.Tensor, w_unaligned: torch.Tensor) -> torch.Tensor:
    """V = float32(W aligned) - float32(W unaligned): one elementwise subtraction in float32."""
    if tuple(w_aligned.shape) != tuple(w_unaligned.shape):
        raise Refusal(f"the aligned and unaligned weights differ in shape ({tuple(w_aligned.shape)} against "
                      f"{tuple(w_unaligned.shape)})")
    return w_aligned.to(torch.float32) - w_unaligned.to(torch.float32)


def alignment_matrix_prime(w_aligned: torch.Tensor, w_unaligned: torch.Tensor) -> torch.Tensor:
    """V' = float32(W aligned) - float32(bfloat16(W unaligned)): the unaligned weight rounded once to bfloat16 (the
    aligned model's storage dtype) before the same float32 subtraction (addendum section 11 point 8)."""
    return alignment_matrix(w_aligned, w_unaligned.to(torch.float32).to(torch.bfloat16))


def relative_difference(v: torch.Tensor, v_prime: torch.Tensor) -> float:
    """||V - V'||_F / ||V||_F in float64 from the two float32 matrices."""
    v64 = v.to(torch.float64)
    norm = float(torch.linalg.vector_norm(v64))
    if norm <= 0.0 or not math.isfinite(norm):
        raise Refusal("V is zero or not finite: the aligned and unaligned weights give no alignment matrix")
    return float(torch.linalg.vector_norm(v64 - v_prime.to(torch.float64))) / norm


def project_b(v: torch.Tensor, b: torch.Tensor) -> tuple[torch.Tensor, float]:
    """(B', ||V||_F): B' = V (V^T B) / ||V||_F in float64 from float32 V and B; C = V V^T / ||V||_F is never formed."""
    if v.dim() != 2 or b.dim() != 2 or v.shape[0] != b.shape[0]:
        raise Refusal(f"lora_B's output size does not match V ({tuple(b.shape)} against {tuple(v.shape)})")
    v64, b64 = v.to(torch.float64), b.to(torch.float64)
    norm = float(torch.linalg.vector_norm(v64))
    if not math.isfinite(norm) or norm <= 0.0:
        raise Refusal("V is zero or not finite: the aligned and unaligned weights give no alignment matrix")
    projected = (v64 @ (v64.T @ b64)) / norm
    if not bool(torch.isfinite(projected).all()):
        raise Refusal("the mapped lora_B is not finite")
    return projected, norm


def similarity(b_new: torch.Tensor, b: torch.Tensor, a: torch.Tensor) -> tuple[float, float]:
    """(cos, rho) of B'A against BA in float64 through the r x r Gram form G = A A^T (the settings' formula)."""
    if a.dim() != 2 or a.shape[0] != b.shape[1] or b_new.shape != b.shape:
        raise Refusal("lora_A, lora_B and the mapped lora_B do not fit together")
    a64, b64, n64 = a.to(torch.float64), b.to(torch.float64), b_new.to(torch.float64)
    gram = a64 @ a64.T
    inner = float(((n64.T @ b64) * gram).sum())
    new = float(((n64.T @ n64) * gram).sum())
    old = float(((b64.T @ b64) * gram).sum())
    if not all(math.isfinite(x) for x in (inner, new, old)) or new <= 0.0 or old <= 0.0:
        raise Refusal("B A or B' A is zero or not finite: the cosine is undefined")
    return inner / math.sqrt(new * old), math.sqrt(new / old)


def bf16_rounding_share(w_unaligned: torch.Tensor, v_norm: float) -> float:
    """||W - float32(bfloat16(W))||_F / ||V||_F for the unaligned W (report only; a builder diagnostic)."""
    w = w_unaligned.to(torch.float32)
    rounded = w.to(torch.bfloat16).to(torch.float64)
    return float(torch.linalg.vector_norm(w.to(torch.float64) - rounded)) / v_norm


def ranking(cosines: Mapping[str, float]) -> list[str]:
    """Module names by (cosine ascending, name in Python string order)."""
    return sorted(cosines, key=lambda name: (cosines[name], name))


def tau_counts(cosines: Sequence[float], taus: Sequence[float]) -> dict:
    """How many matrices a threshold tau would map, by the paper's rule (cos < tau) and the official code's rule
    (numpy.round(cos, 5) <= tau)."""
    return {repr(float(tau)): {"paper_strict_below": sum(c < tau for c in cosines),
                               "official_code_rounded_at_or_below": sum(float(numpy.round(c, 5)) <= tau for c in cosines)}
            for tau in taus}


@contextlib.contextmanager
def _torch_threads(n: int) -> Iterator[None]:
    before = torch.get_num_threads()
    torch.set_num_threads(n)
    try:
        yield
    finally:
        torch.set_num_threads(before)


@dataclass(frozen=True)
class MatrixResult:
    module: str
    block: int
    proj: str
    shape: tuple[int, int]
    v_norm: float
    cosine: float
    rho: float
    base_bf16_rounding_share: float
    b_new: torch.Tensor               # float32(B'), the lora_B a point writes when it maps this matrix


@dataclass(frozen=True)
class Analysis:
    results: dict[str, MatrixResult]
    order: list[str]                  # the ranking

    def mapped(self, k: int) -> list[str]:
        if isinstance(k, bool) or not isinstance(k, int) or not 0 <= k <= len(self.order):
            raise Refusal(f"K = {k!r} is outside 0..{len(self.order)}")
        return self.order[:k]


def analyse(tensors: Mapping[str, torch.Tensor], settings: Settings, aligned: Snapshot, unaligned: Snapshot,
            threads: int | None = None, alignment: Any = alignment_matrix) -> Analysis:
    """Every matrix's V norm, B', cosine, rho and rounding share; refuses before any result on a bad input.
    ``alignment`` makes V from the two weights (alignment_matrix; the V/V' diagnostic also passes the V' form)."""
    modules = check_adapter(tensors, settings)
    results: dict[str, MatrixResult] = {}
    with _torch_threads(settings.threads if threads is None else threads):
        for module in modules:
            w_aligned, w_unaligned = aligned.weight(module), unaligned.weight(module)
            v = alignment(w_aligned, w_unaligned)
            a, b = tensors[_a(module)], tensors[_b(module)]
            if a.shape[1] != v.shape[1] or b.shape[0] != v.shape[0]:
                raise Refusal(f"the adapter's {module} does not fit its weight's shape {tuple(v.shape)}")
            b_new64, norm = project_b(v, b)
            cosine, rho = similarity(b_new64, b, a)
            b_new = b_new64.to(torch.float32).contiguous()
            if not bool(torch.isfinite(b_new).all()):
                raise Refusal(f"the mapped lora_B of {module} overflows float32")
            match = ADAPTER_KEY.match(_a(module))
            results[module] = MatrixResult(module, int(match["block"]), match["proj"], (int(v.shape[0]), int(v.shape[1])),
                                           norm, cosine, rho, bf16_rounding_share(w_unaligned, norm), b_new)
    return Analysis(results, ranking({m: r.cosine for m, r in results.items()}))


def apply_point(tensors: Mapping[str, torch.Tensor], analysis: Analysis, k: int) -> tuple[dict[str, torch.Tensor], list[str]]:
    """The adapter with the first K matrices' lora_B replaced by float32(B'); every other tensor is the input's."""
    mapped = analysis.mapped(k)
    out = {key: tensors[key] for key in sorted(tensors)}
    for module in mapped:
        out[_b(module)] = analysis.results[module].b_new
    return out, mapped


# ----- the record -----------------------------------------------------------------------------------------------


def _spread(values: Sequence[float]) -> dict | None:
    return {"min": min(values), "median": statistics.median(values), "max": max(values)} if values else None


def _point_record(analysis: Analysis, settings: Settings, point: str) -> dict:
    k = settings.points[point]
    mapped = analysis.mapped(k)
    res, order = analysis.results, analysis.order
    kth = res[order[k - 1]].cosine if k >= 1 else None
    next_cos = res[order[k]].cosine if k < len(order) else None
    ties = sum(res[m].cosine == kth for m in order[k:]) if kth is not None else 0
    module_mix = {m: sum(res[x].proj == m for x in mapped) for m in settings.modules}
    block_mix = {str(b): sum(res[x].block == b for x in mapped) for b in range(settings.blocks)}
    return {"k": k, "status": settings.point_status[point], "kth_cosine": kth, "next_cosine": next_cos,
            "boundary_ties": ties, "mapped": mapped, "module_mix": module_mix, "block_mix": block_mix,
            "mapped_rho_above_1": [m for m in mapped if res[m].rho > 1.0],
            "rho_of_mapped": _spread([res[m].rho for m in mapped])}


def _record(*, mode: str, settings: Settings, analysis: Analysis, points: Sequence[str], seed: str, source: dict,
            aligned: Snapshot, unaligned: Snapshot, output: dict | None) -> dict:
    res, order = analysis.results, analysis.order
    rank = {m: i + 1 for i, m in enumerate(order)}
    mapped_at = {p: set(analysis.mapped(settings.points[p])) for p in points}
    matrices = [{"name": m, "block": r.block, "module": r.proj, "shape": list(r.shape), "v_norm": r.v_norm,
                 "cosine": r.cosine, "rho": r.rho, "rank": rank[m], "base_bf16_rounding_share": r.base_bf16_rounding_share,
                 "mapped": {p: m in mapped_at[p] for p in points}}
                for m, r in sorted(res.items())]
    inputs = {"adapter": source["digest"]}
    if source.get("state_json_sha256"):
        inputs["adapter_state_json"] = source["state_json_sha256"]
    for snap in (aligned, unaligned):
        for f in snap.files:
            inputs[f"{snap.role}/{f['file']}"] = f["sha256"]
    return {
        "kind": RECORD_KIND, "version": 1, "mode": mode, "points": {p: _point_record(analysis, settings, p) for p in points},
        "seed": seed,
        "input_adapter": {"fingerprint": source["fingerprint"], "accepted_fingerprint": settings.accepted[seed],
                          "file_sha256": source.get("file_sha256"), "state_json_sha256": source.get("state_json_sha256")},
        "models": {"aligned": aligned.identity(), "unaligned": unaligned.identity()},
        "matrices": matrices, "ranking": order,
        "tau_counts": tau_counts([res[m].cosine for m in order], settings.taus),
        "summary": {"n_matrices": len(order), "cosine": _spread([r.cosine for r in res.values()]),
                    "rho": _spread([r.rho for r in res.values()]),
                    "base_bf16_rounding_share": _spread([r.base_bf16_rounding_share for r in res.values()])},
        "output": output,
        "rules": {"no_stop_rule": "every number here is report only; the rule and K were fixed before this record "
                                  "(REF R.1.5, LQ13)", "torch_threads": settings.threads},
        "provenance": s1.provenance(Path(__file__).resolve(), settings.sha256, inputs, {}),
    }


# ----- the V/V' diagnostic (addendum section 11 point 8; section 13 point 3) ----------------------------------------


def compare_selection(analysis_v: Analysis, analysis_v_prime: Analysis, k: int) -> dict:
    """The mapped sets of K under V and under V' (each by the transform's own ranking rule) and their difference."""
    selected, selected_prime = analysis_v.mapped(k), analysis_v_prime.mapped(k)
    only_v = sorted(set(selected) - set(selected_prime))
    only_v_prime = sorted(set(selected_prime) - set(selected))
    return {"k": k, "mapped_v": sorted(selected), "mapped_v_prime": sorted(selected_prime), "only_v": only_v,
            "only_v_prime": only_v_prime, "set_changes": bool(only_v or only_v_prime),
            "same_order": analysis_v.order[:k] == analysis_v_prime.order[:k]}


def v_diagnostic(tensors: Mapping[str, torch.Tensor], settings: Settings, aligned: Snapshot, unaligned: Snapshot,
                 threads: int | None = None) -> dict:
    """Per matrix ||V - V'||_F / ||V||_F (V' = float32(W aligned) - float32(bfloat16(W unaligned))), each matrix's
    cosine and rank under V and V', and whether the settings' diagnostic point (K = 39) maps another set under V'.
    Report only: it writes no adapter and changes no rule (REF R.1.3 row 5 stays primary)."""
    analysis_v = analyse(tensors, settings, aligned, unaligned, threads)
    analysis_vp = analyse(tensors, settings, aligned, unaligned, threads, alignment=alignment_matrix_prime)
    rank_v = {m: i + 1 for i, m in enumerate(analysis_v.order)}
    rank_vp = {m: i + 1 for i, m in enumerate(analysis_vp.order)}
    rows = []
    with _torch_threads(settings.threads if threads is None else threads):
        for module in sorted(analysis_v.results):
            aligned_w, unaligned_w = aligned.weight(module), unaligned.weight(module)
            v = alignment_matrix(aligned_w, unaligned_w)
            rows.append({"name": module, "v_norm": analysis_v.results[module].v_norm,
                         "v_prime_norm": analysis_vp.results[module].v_norm,
                         "relative_difference": relative_difference(v, alignment_matrix_prime(aligned_w, unaligned_w)),
                         "cosine_v": analysis_v.results[module].cosine,
                         "cosine_v_prime": analysis_vp.results[module].cosine,
                         "rank_v": rank_v[module], "rank_v_prime": rank_vp[module]})
    selection = compare_selection(analysis_v, analysis_vp, settings.points[settings.v_point])
    outcomes = settings.doc["v_diagnostic"]["outcomes"]
    return {"point": settings.v_point, "matrices": rows, "selection": selection,
            "summary": {"n_matrices": len(rows), "relative_difference": _spread([r["relative_difference"] for r in rows])},
            "outcome": outcomes["changes"] if selection["set_changes"] else outcomes["same"]}


# ----- the hook ------------------------------------------------------------------------------------------------


@dataclass(frozen=True)
class TransformResult:
    adapter: dict[str, torch.Tensor]  # every adapter tensor by engine name (float32, CPU)
    fingerprint: str                  # the engine fingerprint of adapter
    adapter_bytes: bytes              # safetensors bytes of adapter (no metadata, as the engine saves a state)
    mapped: list[str]
    record: dict


class SafeLoRA:
    """B10's transform hook: ``hook(adapter) -> TransformResult`` at one point; ``hook.check(adapter)`` gives the
    $0 weight-only record of the two reference points. The two snapshots are checked against their pins once, here."""

    name = NAME

    def __init__(self, settings: Settings, aligned_folder: str | Path, unaligned_folder: str | Path, *,
                 seed: int | str, point: str | None = "default"):
        seed = str(seed)
        if seed not in settings.accepted:
            raise Refusal(f"seed {seed} has no accepted a0 fingerprint in the settings")
        if point is not None and point not in POINTS:
            raise Refusal(f"the point {point!r} is not one of {list(POINTS)}")
        self.settings, self.seed, self.point = settings, seed, point
        self.aligned = open_snapshot(aligned_folder, settings.aligned, "aligned")
        self.unaligned = open_snapshot(unaligned_folder, settings.unaligned, "unaligned")

    def _accepted(self, tensors: Mapping[str, torch.Tensor], source: SourceAdapter | None) -> dict:
        check_adapter(tensors, self.settings)
        fingerprint = adapter_fingerprint(tensors)
        if fingerprint != self.settings.accepted[self.seed]:
            raise Refusal(f"the input adapter's fingerprint {fingerprint} is not the accepted a0 e1 fingerprint "
                          f"of seed {self.seed}")
        info = {"fingerprint": fingerprint, "digest": fingerprint, "file_sha256": None, "state_json_sha256": None}
        if source is not None:
            if adapter_fingerprint(source.tensors) != fingerprint:
                raise Refusal("the tensors given are not the source adapter's")
            if source.state is not None:
                checks = self.settings.state_checks
                if (source.state.get("checkpoint"), source.state.get("arm"), str(source.state.get("seed"))) != (
                        checks["checkpoint"], checks["arm"], self.seed):
                    raise Refusal(f"the state folder is not the {checks['arm']} {checks['checkpoint']} state of seed {self.seed}")
            info.update(digest=source.file_sha256, file_sha256=source.file_sha256,
                        state_json_sha256=source.state_json_sha256)
        return info

    def check(self, adapter: Mapping[str, torch.Tensor], *, source: SourceAdapter | None = None) -> dict:
        """The $0 weight-only check (REF R.1.5): the record of the two reference points; no adapter is made."""
        info = self._accepted(adapter, source)
        analysis = analyse(adapter, self.settings, self.aligned, self.unaligned)
        return _record(mode="check", settings=self.settings, analysis=analysis, points=CHECK_POINTS, seed=self.seed,
                       source=info, aligned=self.aligned, unaligned=self.unaligned, output=None)

    def vcheck(self, adapter: Mapping[str, torch.Tensor], *, source: SourceAdapter | None = None) -> dict:
        """The V/V' diagnostic record (addendum section 11 point 8): the pod job runs it before the projection."""
        info = self._accepted(adapter, source)
        diag = v_diagnostic(adapter, self.settings, self.aligned, self.unaligned)
        inputs = {"adapter": info["digest"]}
        if info.get("state_json_sha256"):
            inputs["adapter_state_json"] = info["state_json_sha256"]
        for snap in (self.aligned, self.unaligned):
            for f in snap.files:
                inputs[f"{snap.role}/{f['file']}"] = f["sha256"]
        rule = self.settings.doc["v_diagnostic"]
        return {"kind": VCHECK_KIND, "version": 1, "mode": "vcheck", "seed": self.seed, **diag,
                "rule": {"v": "V = float32(W aligned) - float32(W unaligned) (REF R.1.3 row 5; the primary)",
                         "v_prime": rule["v_prime"], "measure": rule["measure"], "torch_threads": self.settings.threads},
                "input_adapter": {"fingerprint": info["fingerprint"], "accepted_fingerprint": self.settings.accepted[self.seed],
                                  "file_sha256": info.get("file_sha256"), "state_json_sha256": info.get("state_json_sha256")},
                "models": {"aligned": self.aligned.identity(), "unaligned": self.unaligned.identity()},
                "provenance": s1.provenance(Path(__file__).resolve(), self.settings.sha256, inputs, {})}

    def __call__(self, adapter: Mapping[str, torch.Tensor], *, source: SourceAdapter | None = None) -> TransformResult:
        if self.point is None:
            raise Refusal("this hook was made for the check only (no point)")
        info = self._accepted(adapter, source)
        analysis = analyse(adapter, self.settings, self.aligned, self.unaligned)
        out, mapped = apply_point(adapter, analysis, self.settings.points[self.point])
        data = safetensors_save(out)
        fingerprint = adapter_fingerprint(out)
        output = {"point": self.point, "k": self.settings.points[self.point],
                  "adapter_file": self.settings.doc["outputs"]["adapter"], "adapter_sha256": sha256_bytes(data),
                  "fingerprint": fingerprint, "replaced_lora_b": mapped,
                  "identical_to_source_bytes": None if source is None else data == source.file_bytes}
        record = _record(mode="transform", settings=self.settings, analysis=analysis, points=(self.point,),
                         seed=self.seed, source=info, aligned=self.aligned, unaligned=self.unaligned, output=output)
        return TransformResult(out, fingerprint, data, mapped, record)


# ----- the command line -----------------------------------------------------------------------------------------


_clock = time.monotonic                               # wall-clock seconds for the timing file (a module name, so a
                                                      # test can drive it); never a random number


def _stage_seconds(start: float, read_done: float, hashed: float, done: float) -> dict:
    """The timing file's stages (REF section C.9): reading the settings and the input adapter, hashing both
    snapshots against their pins, the arithmetic with the record and the output bytes, and their total."""
    return {"read_adapter": round(read_done - start, 3), "hash_snapshots": round(hashed - read_done, 3),
            "transform": round(done - hashed, 3), "total": round(done - start, 3)}


def _timing_document(command: str, point: str | None, seed: str, settings: Settings, seconds: dict,
                     files: Mapping[str, bytes]) -> dict:
    return {"kind": TIMING_KIND, "version": 1, "command": command, "point": point, "seed": seed,
            "torch_threads": settings.threads, "seconds": seconds,
            "clock": "time.monotonic wall-clock seconds; writing the output files is not included",
            "outputs": {name: sha256_bytes(data) for name, data in sorted(files.items())},
            "settings_sha256": settings.sha256}


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="python -m scripts.stage1_s1.safe_lora",
                                     description="B11: the Safe LoRA transform, its $0 weight-only check and the "
                                                 "V/V' diagnostic")
    commands = parser.add_subparsers(dest="command", required=True)
    for command in ("check", "transform", "vcheck"):
        sub = commands.add_parser(command)
        sub.add_argument("--adapter", type=Path, required=True, help="an adapter.safetensors or its state folder")
        sub.add_argument("--seed", required=True, help="the a0 seed whose accepted fingerprint the adapter must have")
        sub.add_argument("--aligned", type=Path, required=True, help="the aligned model's snapshot folder")
        sub.add_argument("--base", type=Path, required=True, help="the unaligned (base) model's snapshot folder")
        sub.add_argument("--out", type=Path, required=True, help="a new (absent or empty) output folder")
        if command == "transform":
            sub.add_argument("--point", choices=POINTS, required=True)
    args = parser.parse_args(argv)
    point = args.point if args.command == "transform" else None
    try:
        start = _clock()
        settings = load_pinned_settings()
        source = read_adapter(args.adapter)
        read_done = _clock()
        hook = SafeLoRA(settings, args.aligned, args.base, seed=args.seed, point=point)
        hashed = _clock()
        outputs = settings.doc["outputs"]
        if args.command == "check":
            files = {outputs["check_record"]: canonical_json(hook.check(source.tensors, source=source))}
        elif args.command == "vcheck":
            files = {settings.v_output: canonical_json(hook.vcheck(source.tensors, source=source))}
        else:
            result = hook(source.tensors, source=source)
            files = {outputs["adapter"]: result.adapter_bytes, outputs["record"]: canonical_json(result.record)}
        seconds = _stage_seconds(start, read_done, hashed, _clock())
        timing = _timing_document(args.command, point, hook.seed, settings, seconds, files)
        files[outputs["timing"]] = canonical_json(timing)
        digests = s1.write_new_files(args.out, files)
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    print(json.dumps({"command": args.command, "written": digests, "seconds": seconds}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
