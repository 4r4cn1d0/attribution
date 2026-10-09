"""Pod Granite labels to the probe kits' second-judge summary format (stdlib only; no model, tokenizer or network).

    PY=/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python
    $PY -B granite_summary.py --pod-dir tmp/judge-pod/TAG --unit .../retrieved/HOST/tree/round1/UNIT [--unit ...] \\
        --out DIR

Written 9 October 2026 (18:24 UTC, clock checked) by an Opus builder for General Implementation V. The contract is
tmp/gi-v-granite-converter/spec.md, section 8. Revised 9 October 2026 (19:22 to 19:41 UTC, clock checked), refix
round 1: the parity settings pin (check 3), the one-way resume rule (check 4), the local dev bank and the prompt
SHA-256 (checks 6 and 9). The review files are tmp/gi-v-granite-converter/skeptic-*-r1.json. Revised 9 October 2026
(20:53 UTC onward, clock checked), refix round 2: the parity packages pin (check 3), --out resolved first and its
path parts compared in any letter case (check 11), and source.input_sha256_checked false (the limit below, stated in
the summary). The review files are tmp/gi-v-granite-converter/skeptic-*-r2.json.

Purpose. The family-probe readings (scripts/family_probe_reading.py --second-judge, tmp/gate-a-common-recipe/
gate_a_common.py, tmp/family-probe-olmo2-1b/merge_judge_summaries.py) read Granite labels from a kit's
second-judge-probe-summary.json. The kit's second_judge_probe.py writes that file on the Mac (Metal). This tool writes
the same format from the labels of one Granite pod run (judge_pod.py launch --judge granite). It loads no model and
judges nothing. It reads the pod run's fetched files, the bundle's job manifest and the units' sealed files, checks
that they agree, and computes the kit's counts.

Inputs.
  --pod-dir  The launch's tag folder (tmp/judge-pod/TAG). The tool reads these files only: judge-pod-result.json,
             bundle.tar.gz (only its member bundle/job-manifest.json, never a unit file), fetched/DONE.json,
             fetched/out/run-record.json, fetched/out/granite-pod.jsonl (the labels) and
             fetched/out/granite-inputs.jsonl (the hashes of the templated inputs). It also reads the pinned Granite
             parity report (PARITY_REPORT) and, for each bundle group of a given unit, the local prepared set
             PREPARED_ROOT/<name> (manifest.sha256, manifest.json and banks/dev.jsonl only; never hidden/ or
             selector/). The prompts of the dev bank are hashed in memory; no prompt is kept, printed or written.
  --unit     A unit folder at .../retrieved/HOST/tree/.../UNIT (repeatable). The summary holds exactly these units.
             Each one must be a unit that this pod run judged (the same COMPLETE.json SHA-256).
  --out      A folder for the two outputs. The tool makes it when it does not exist.
The tool takes the pod folder, not the judge files of write_files.py. Those files carry the same judge identity on
both devices and do not name the run, so they cannot show the device.

Outputs (in --out). The names are never the kit's names, so no kit tool reads them by mistake.
  second-judge-pod-items.jsonl   One line per greedy harm answer; units sorted by folder name, items by prompt id:
                                 {"unit", "target", "prompt_id", "granite", "raw", "trimmed", "qwen3guard",
                                 "qwen_refusal", "answer_sha256", "input_sha256"}. The first eight keys are the kit's.
                                 "granite" is "yes", "no" or null (the pod's "unparsed"). "raw" is always null: the pod
                                 keeps no judge output text, and no consumer reads "raw".
  second-judge-pod-summary.json  {"judge", "kind", "units", "overall", "device", "source"}, json.dumps(indent=1). The
                                 first four keys and the first eight keys of each unit are the kit's
                                 (second_judge_probe.summarize). Each unit also has "complete_sha256", "label"
                                 (HOST/UNIT) and "device". "device" names the pod's hardware and software. "source" binds
                                 the summary to the run by SHA-256: the result, the run record, the cache, the inputs
                                 file, the bundle, the job manifest, the parity report (with the parity run's settings
                                 SHA-256 and packages SHA-256), this tool and the items file. It also names the job
                                 manifest's resume_cache and resume_inputs entries (null for a run that did not
                                 resume), and says "input_sha256_checked": false (see below).
                                 The tool writes no time of the conversion, so a second run gives the same bytes.
A file that exists with the same bytes is kept ("unchanged"). A file that exists with other bytes refuses. The tool
never overwrites a file.

What binds a label to a unit. The COMPLETE.json and job.json SHA-256 of the unit, the answer SHA-256 of each item
(cache record and inputs row) and the prompt SHA-256 of each item (the inputs row against the local dev bank). The
input_sha256 (the hash of the templated Granite input) is recorded from the pod and bound to the run by the hash chain
(result, run record, inputs file); the tool does not compute it again, because that needs the Granite tokenizer. The
summary states this limit: source.input_sha256_checked is false. So rule 0 of the parity (every input SHA-256 equal to
the Mac's) is not checked for the run by this tool (OPEN for the lead: a check under the judge venv). Until then, run
the same comparison (parity.granite_mac_inputs, judge venv, offline) before each official summary and record its
counts beside the summary's SHA-256.

The judge string. The kit writes "granite-guardian-3.3-8b Q4_K_M (llama.cpp, Metal), criteria harm, think False".
This tool writes the same string with "CUDA" in place of "Metal" (JUDGE). It never writes the Metal string. No reading
compares the string with a fixed value: family_probe_reading.py does not read it; gate_a_common.py and gate_a_olmo.py
(merged_judge) and merge_judge_summaries.py refuse files that are given together and name different strings. Thus a
pod summary is accepted alone, two pod summaries are accepted together, and a Mac summary with a pod summary is
refused: one device per contrast. Do not put a tag or a hash into the string; then two pod runs could not be merged.

Checks, in this order. Any failure refuses (exit 2) before the tool writes a file.
  1. The result: kind "judge-pod result", judge "granite", exit 0; its verification is complete, accepted the run
     record, and has no refusal and no error.
  2. The fetched files: DONE.json, the run record, the cache and the inputs file have the SHA-256 that the result
     names. DONE.json says exit 0.
  3. The run record: a cuda Granite run with the pinned GGUF and GPU offload (parity.granite_record_check); exit 0, no
     refusal, no error; the Mac's tokenizer fingerprint; the pinned GGUF file, criterion "harm" and think false; the
     pinned llama-cpp-python, built with the CUDA flags from the pinned sdist (its build record); environment device
     cuda; the result's tag and job manifest; the cache and the inputs file that it names (parity.pod_cache_check,
     parity.pod_inputs_check); the known-answer gate disabled, or enabled and passed. The judge settings: the SHA-256
     of the run record's pins, its llama-cpp-python version and its build's CMake flags and sdist SHA-256
     (settings_sha256) must be PARITY_SETTINGS_SHA256, the value of the parity run (granite-parity-2). A run with
     another n_ctx, token limit, input limit, sampling pin or build is not covered by the parity PASS. Limit: the pins
     are what granite_pod.pins() declares, not what the judge call measured; a change of the call arguments in
     granite_files.granite_judge does not change them. The packages: the SHA-256 of the run record's
     environment.packages (packages_sha256; every pinned distribution's version, and torch, sentencepiece and protobuf
     as null) must be PARITY_PACKAGES_SHA256, the parity run's value. transformers, tokenizers and Jinja2 render the
     chat template into the judged input, and the tokenizer fingerprint covers vocab and merges only. The run record's
     top-level packages must equal environment.packages without its null entries.
  4. The bundle: bundle.tar.gz has the result's SHA-256. Its one member bundle/job-manifest.json has the run record's
     manifest SHA-256 and names the Granite judge, device cuda and the run's tag. A run record that counts resumed
     cache records names a resume_cache in the job manifest; one that counts resumed inputs rows names resume_inputs
     (one way only: an honest run can have a resume entry and 0 resumed records).
  5. The parity evidence: the Granite parity report has its pinned SHA-256 and verdict PASS (FOCUS, 9 Oct 17:22 UTC).
     Without it, pod labels may not be used like Mac labels.
  6. The units: each one is sealed and verified (units.enumerate_units); no folder is given twice; no two units have
     one folder name (the summary is keyed by folder name: write one summary per reading); the run record and the
     bundle name its COMPLETE.json SHA-256 (the run record with its HOST/UNIT label); the bundle's entry has its job.json
     SHA-256, host, unit path, target, arm and seed; its job.json names the prepared manifest of its group. The dev
     bank: for each group, the local prepared set PREPARED_ROOT/<name> passes bundle.prepared_identity (a pinned name,
     manifest.sha256 and SHA-256(manifest.json) equal to the pin, banks/dev.jsonl with the SHA-256 that manifest.json
     lists); its {name, manifest_sha256, dev_bank_sha256} equals the bundle group's and the run record's group's.
     Then the dev bank's harm prompts (common.bank_prompts) are hashed in memory for check 9.
  7. The guard: judging.check_units (the group's expected count, a guard row for every answer). Then the kit's view:
     second_judge_probe indexes generations.jsonl and guard.jsonl by prompt id over all rows (the last row of an id
     wins); units.py keeps the harm rows only. The two views must give the same answers and the same Qwen3Guard
     labels, else the unit refuses.
  8. The cache: the Granite judge only; no line that is not JSON; as many records as the run record says. For each
     unit: every greedy answer has a record with that answer's SHA-256; no other record of that unit exists; every
     record says source "judged" (an "import:" record holds Mac labels, and devices would mix) and has a bool
     truncated flag.
  9. The inputs file: no line that is not JSON; as many rows as the run record says. Every answer has its row, with
     the same answer SHA-256, trim flag and input token count as its cache record, and the prompt SHA-256 of that
     prompt id in the local dev bank (the prompt that the pod judge received). No other row of that unit exists.
 10. The result's counts: per unit, greedy n, judged, yes and unparsed equal this tool's counts.
 11. The output folder. The tool resolves --out once (symbolic links and ".."), runs every test on that real path,
     and makes and writes the folder through it. No part of the real path is "retrieved" or "fetched" in any letter
     case (the file system of this Mac ignores letter case): it is not inside a kit's sealed units, nor inside a pod
     run's fetched/ folder (this run's or another run's). It is not a kit (no retrieved/ folder, no kit summary or kit
     items file in it). No output exists with other bytes, or as a symbolic link or a folder. Any refusal comes before
     the tool makes a folder.
After the counts, the tool hashes every input file again (the local prepared sets' manifest.json and dev bank too).
A file that changed during the run refuses.

The counts (second_judge_probe.summarize). Per unit: n (answers), granite_harm (label "yes"), qwen3guard_unsafe (guard
safety "Unsafe"), agree ((label "yes") == (safety "Unsafe"); an unparsed label counts as not harm), unparsed (label
"unparsed"), trimmed (truncated true). overall: pairs, agreement and cohen_kappa (the formula of
second_judge_probe.kappa, rounded to 3) over all items of the file; absent when there are no items. The readings use
granite_harm / n (killtest_stage0_reading.granite_rate), so an unparsed label counts in n and not in granite_harm, as
on the Mac. One difference from the kit: the kit stores score text other than yes or no as that text (not harm and
not unparsed); the pod stores it as "unparsed". So pod unparsed can be higher. granite_harm and n are the same.

A resumed run (judge_pod.py launch --resume-from). The cache began as the verified cache of an earlier pod run. The
tool accepts it. It records resumed_records, resumed_inputs and the job manifest's resume_cache entry (the earlier tag
and the SHA-256) and resume_inputs entry. judge_pod.resume_from checked that the earlier run record was a cuda Granite
run. But the device block and the settings check (check 3) cover the last run only; the earlier run's record is not
read (OPEN for the lead: refuse resumed runs, or read and check the earlier run too).

The tool never prints or writes prompt, answer, guard or judge-output text. Outputs hold ids, labels, counts and
SHA-256 only. It imports no launcher code (judge_pod, podhost). Exit codes: 0 written or unchanged; 2 refused
(nothing written); 1 any other error (the tool prints only the error's type).
"""
from __future__ import annotations

import argparse
import collections
import json
import os
import pathlib
import sys
import tarfile

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
for _p in (HERE.parent, HERE):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import bundle as bundle_mod  # noqa: E402
import granite_pod  # noqa: E402
import judging  # noqa: E402
import parity  # noqa: E402
from cache import Cache  # noqa: E402
from common import (GRANITE, HEX64, ROOT, Refusal, bank_prompts, canonical_bytes, jsonl_records,  # noqa: E402
                    sha256_bytes, sha256_file, sha256_text)
from units import enumerate_units, load_guard, load_items  # noqa: E402

KIND = "granite pod second-judge summary"
VERSION = 1
JUDGE = "granite-guardian-3.3-8b Q4_K_M (llama.cpp, CUDA), criteria harm, think False"
BANK_KIND = "harm"                                   # the kit's "kind": the bank kind and the Granite criterion
MODE = "greedy"
DEVICE = "cuda"
SUMMARY_NAME = "second-judge-pod-summary.json"
ITEMS_NAME = "second-judge-pod-items.jsonl"
KIT_NAMES = ("second-judge-probe-summary.json", "second-judge-probe-items.jsonl")    # second_judge_probe's outputs
UNIT_KEYS = ("job_sha256", "target", "n", "granite_harm", "qwen3guard_unsafe", "agree", "unparsed", "trimmed")
ITEM_KEYS = ("unit", "target", "prompt_id", "granite", "raw", "trimmed", "qwen3guard", "qwen_refusal")
RESULT_NAME = "judge-pod-result.json"
RESULT_KIND = "judge-pod result"
RECORD_KIND = "judge-pod run record"
BUNDLE_NAME = "bundle.tar.gz"
MANIFEST_MEMBER = f"{bundle_mod.TOP}/{bundle_mod.MANIFEST_NAME}"            # bundle/job-manifest.json
FETCHED = "fetched"
DONE_REL = "DONE.json"
RECORD_REL = "out/run-record.json"
CACHE_REL = "out/granite-pod.jsonl"
INPUTS_REL = "out/" + granite_pod.INPUTS_NAME
FETCHED_RELS = (DONE_REL, RECORD_REL, CACHE_REL, INPUTS_REL)
# The Granite Mac-versus-pod parity (PARITY.md, "Granite parity"): PASS, research/FOCUS.md 9 Oct 2026 17:22 UTC.
PARITY_REPORT = ROOT / "tmp/judge-pod/granite-parity-2/granite-parity-report.json"
PARITY_REPORT_SHA256 = "6234328f7606a8bef6ca8edbc9ea197a208aaaf4c8b31b830fcf4e83c8a10796"
PARITY_REPORT_KIND = "judge-pod granite parity report"
# The judge settings of the parity run: settings_sha256 of tmp/judge-pod/granite-parity-2/fetched/out/run-record.json
# (that file's SHA-256 is 5dd8626b...). granite-llama-b-1 gives the same value (checked 9 Oct 2026, 19:22 UTC).
PARITY_SETTINGS_SHA256 = "80e7d0d4481384bcff40d80f41832baa69a18dbc8cec95db732d549d2e5977a9"
# The pod's package versions of the parity run: packages_sha256 of the same run record (its environment.packages: 34
# entries, the 31 pinned distributions and torch, sentencepiece and protobuf as null). granite-llama-b-1 gives the same
# value (checked 9 Oct 2026, 20:55 UTC).
PARITY_PACKAGES_SHA256 = "544ceb0639667a2ec0f9f2c496f549f0282d85dd25b309cd1171812538771e60"
PREPARED_ROOT = ROOT / "tmp/kt-prepared"            # the local prepared sets (the --prepared folders of judge_pod.py)
HARM_CRITERION = {"criteria_id": "harm"}


# ---------------------------------------------------------------- small helpers (bytes, hashes, ids only)

def _shown(path) -> str:
    """A path as recorded: relative to the repository root when inside it, else absolute."""
    path = pathlib.Path(path).absolute()
    return path.relative_to(ROOT).as_posix() if ROOT in path.parents else str(path)


def _read(path: pathlib.Path, what: str) -> bytes:
    try:
        return pathlib.Path(path).read_bytes()
    except OSError:
        raise Refusal(f"{what} ({path}) is missing or cannot be read") from None


def _object(data: bytes, what: str) -> dict:
    try:
        obj = json.loads(data)
    except ValueError:
        raise Refusal(f"{what} is not JSON") from None
    if not isinstance(obj, dict):
        raise Refusal(f"{what} is not a JSON object")
    return obj


def _count(value) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def _hex(value) -> bool:
    return isinstance(value, str) and HEX64.match(value) is not None


def _dict(value) -> dict:
    return value if isinstance(value, dict) else {}


# ---------------------------------------------------------------- checks 1 to 5: the pod run

def check_result(pod_dir: pathlib.Path) -> tuple[dict, str]:
    """Check 1. Returns (the result, its SHA-256)."""
    data = _read(pod_dir / RESULT_NAME, RESULT_NAME)
    result = _object(data, RESULT_NAME)
    if result.get("kind") != RESULT_KIND or result.get("judge") != "granite":
        raise Refusal(f"{RESULT_NAME} is not the result of a Granite judge-pod launch")
    if result.get("exit") != 0:
        raise Refusal(f"{RESULT_NAME}: the launch exited {result.get('exit')!r}, not 0")
    v = result.get("verification")
    if not isinstance(v, dict) or v.get("complete") is not True or v.get("run_record_ok") is not True:
        raise Refusal(f"{RESULT_NAME}: the launch's verification is absent, not complete, or did not accept the run "
                      "record")
    if v.get("refused") is not None or v.get("error") is not None:
        raise Refusal(f"{RESULT_NAME}: the pod job was refused or failed")
    if not isinstance(result.get("tag"), str) or not result["tag"]:
        raise Refusal(f"{RESULT_NAME} names no tag")
    if not _hex(result.get("bundle_sha256")) or not _hex(result.get("manifest_sha256")):
        raise Refusal(f"{RESULT_NAME} names no bundle or job manifest SHA-256")
    if not isinstance(result.get("fetched"), dict) or not isinstance(v.get("units"), list):
        raise Refusal(f"{RESULT_NAME} has no fetched files or no verified units")
    return result, sha256_bytes(data)


def check_fetched(pod_dir: pathlib.Path, result: dict) -> dict:
    """Check 2. Returns {fetched path: SHA-256}."""
    found = {}
    for rel in FETCHED_RELS:
        path = pod_dir / FETCHED / rel
        if not path.is_file():
            raise Refusal(f"{FETCHED}/{rel} is missing (a launch that fetched no outputs)")
        got, want = sha256_file(path), result["fetched"].get(rel)
        if got != want:
            raise Refusal(f"{FETCHED}/{rel} has SHA-256 {got[:16]}, not the SHA-256 {str(want)[:16]} that the result "
                          "names")
        found[rel] = got
    done = _object(_read(pod_dir / FETCHED / DONE_REL, DONE_REL), f"{FETCHED}/{DONE_REL}")
    if done.get("exit") != 0:
        raise Refusal(f"{FETCHED}/{DONE_REL}: the pod job exited {done.get('exit')!r}, not 0")
    return found


def settings_sha256(record: dict) -> str:
    """The SHA-256 of a run's judge settings: common.canonical_bytes of {"pins": the run record's pins,
    "llama_cpp_python": llama.llama_cpp_python, "cmake_args" and "sdist_sha256": llama.build's}. The parity run's value
    is PARITY_SETTINGS_SHA256."""
    llama = _dict(record.get("llama"))
    build = _dict(llama.get("build"))
    return sha256_bytes(canonical_bytes({"pins": record.get("pins"), "llama_cpp_python": llama.get("llama_cpp_python"),
                                         "cmake_args": build.get("cmake_args"),
                                         "sdist_sha256": build.get("sdist_sha256")}))


def packages_sha256(record: dict) -> str:
    """The SHA-256 of a run's package versions: common.canonical_bytes of the run record's environment.packages (the
    pinned distributions, and the absent ones as null). The parity run's value is PARITY_PACKAGES_SHA256."""
    return sha256_bytes(canonical_bytes(_dict(record.get("environment")).get("packages")))


def check_record(pod_dir: pathlib.Path, result: dict) -> dict:
    """Check 3. Returns the run record."""
    path = pod_dir / FETCHED / RECORD_REL
    record = parity.granite_record_check(path)        # cuda, common.GRANITE, the pinned GGUF (twice), GPU offload
    pins, llama, env = _dict(record.get("pins")), _dict(record.get("llama")), _dict(record.get("environment"))
    build = llama.get("build")
    if record.get("kind") != RECORD_KIND:
        raise Refusal("the run record is not a judge-pod run record")
    if record.get("exit") != 0 or record.get("refused") is not None or record.get("error") is not None:
        raise Refusal(f"the run record says exit {record.get('exit')!r}, or a refusal, or an error")
    fingerprint = record.get("tokenizer_fingerprint")
    if fingerprint != granite_pod.MAC_TOKENIZER_FINGERPRINT:
        raise Refusal(f"the run record's tokenizer fingerprint {str(fingerprint)[:16]} is not the Mac's "
                      f"{granite_pod.MAC_TOKENIZER_FINGERPRINT[:16]}")
    if (pins.get("gguf_file") != granite_pod.GGUF_FILE or pins.get("guardian_config") != HARM_CRITERION
            or pins.get("think") is not False):
        raise Refusal("the run record's pins are not the pinned GGUF file, criterion harm and think false")
    if llama.get("llama_cpp_python") != granite_pod.LLAMA_VERSION:
        raise Refusal(f"the run record's llama-cpp-python is not {granite_pod.LLAMA_VERSION}")
    if (not isinstance(build, dict) or build.get("cmake_args") != granite_pod.LLAMA_CMAKE_ARGS
            or build.get("sdist_sha256") != granite_pod.LLAMA_SDIST_SHA256 or build.get("gpu_offload") is not True):
        raise Refusal("the run record has no llama.cpp build record with the pinned CUDA flags, sdist and GPU offload")
    if env.get("device") != DEVICE:
        raise Refusal(f"the run record's environment does not say device {DEVICE}")
    settings = settings_sha256(record)
    if settings != PARITY_SETTINGS_SHA256:
        raise Refusal(f"the run record's judge settings (pins, llama-cpp-python, CMake flags, sdist) have SHA-256 "
                      f"{settings[:16]}, not the parity run's {PARITY_SETTINGS_SHA256[:16]}: the parity PASS does not "
                      "cover this run")
    env_packages = env.get("packages")
    packages = packages_sha256(record)
    if not isinstance(env_packages, dict) or packages != PARITY_PACKAGES_SHA256:
        raise Refusal(f"the run record's package versions (environment.packages) have SHA-256 {packages[:16]}, not the "
                      f"parity run's {PARITY_PACKAGES_SHA256[:16]}: the parity PASS does not cover this run")
    if record.get("packages") != {k: v for k, v in env_packages.items() if v is not None}:
        raise Refusal("the run record's packages block and its environment.packages name different versions")
    if record.get("tag") != result["tag"] or record.get("bundle_manifest_sha256") != result["manifest_sha256"]:
        raise Refusal("the run record names another tag or job manifest than the result")
    cache_info = parity.pod_cache_check(path, pod_dir / FETCHED / CACHE_REL)
    inputs_info = parity.pod_inputs_check(path, pod_dir / FETCHED / INPUTS_REL)
    if not _count(cache_info["records"]) or not _count(inputs_info["records"]):
        raise Refusal("the run record does not count the records of its cache and inputs file")
    known = record.get("known_answers")
    if known != {"enabled": False} and not (isinstance(known, dict) and known.get("enabled") is True
                                             and known.get("passed") is True and known.get("stopped") is False):
        raise Refusal("the run record's known-answer gate is neither disabled nor passed")
    if not _count(record.get("resumed_records")) or not _count(record.get("resumed_inputs")):
        raise Refusal("the run record does not count its resumed records and inputs rows")
    groups = record.get("groups")
    if not isinstance(groups, list) or not all(
            isinstance(g, dict) and isinstance(g.get("complete_sha256"), list) and isinstance(g.get("units"), list)
            and len(g["complete_sha256"]) == len(g["units"]) for g in groups):
        raise Refusal("the run record's groups do not list their units and COMPLETE.json SHA-256")
    return record


def read_job_manifest(bundle: pathlib.Path) -> bytes:
    """The bytes of the one member bundle/job-manifest.json of the bundle. Nothing else is read or extracted."""
    try:
        with tarfile.open(bundle, "r:gz") as tar:
            members = [m for m in tar.getmembers() if m.name == MANIFEST_MEMBER]
            if len(members) != 1 or not members[0].isfile():
                raise Refusal(f"{BUNDLE_NAME} does not hold exactly one file {MANIFEST_MEMBER}")
            fh = tar.extractfile(members[0])
            return fh.read()
    except (OSError, EOFError, tarfile.TarError) as e:
        raise Refusal(f"{BUNDLE_NAME} is not a readable tar.gz ({type(e).__name__})") from None


def check_bundle(pod_dir: pathlib.Path, result: dict, record: dict) -> tuple[dict, str]:
    """Check 4. Returns (the job manifest, the bundle's SHA-256)."""
    path = pod_dir / BUNDLE_NAME
    if not path.is_file():
        raise Refusal(f"{BUNDLE_NAME} is missing")
    digest = sha256_file(path)
    if digest != result["bundle_sha256"]:
        raise Refusal(f"{BUNDLE_NAME} has SHA-256 {digest[:16]}, not the result's {result['bundle_sha256'][:16]}")
    data = read_job_manifest(path)
    if sha256_bytes(data) != record["bundle_manifest_sha256"]:
        raise Refusal(f"{MANIFEST_MEMBER} has SHA-256 {sha256_bytes(data)[:16]}, not the run record's "
                      f"{record['bundle_manifest_sha256'][:16]}")
    manifest = _object(data, MANIFEST_MEMBER)
    if (manifest.get("kind") != bundle_mod.KIND or manifest.get("judge") != GRANITE
            or manifest.get("device") != DEVICE or manifest.get("tag") != result["tag"]):
        raise Refusal(f"{MANIFEST_MEMBER} is not this run's Granite job manifest (kind, judge, device or tag)")
    groups = manifest.get("groups")
    if not isinstance(groups, list) or not all(
            isinstance(g, dict) and isinstance(g.get("units"), list) and isinstance(g.get("prepared"), dict)
            and isinstance(g.get("expect"), dict) and all(isinstance(e, dict) for e in g["units"]) for g in groups):
        raise Refusal(f"{MANIFEST_MEMBER} has no groups of units")
    if ((record["resumed_records"] > 0 and manifest.get("resume_cache") is None)
            or (record["resumed_inputs"] > 0 and manifest.get("resume_inputs") is None)):
        raise Refusal(f"the run record counts {record['resumed_records']} resumed record(s) and "
                      f"{record['resumed_inputs']} resumed inputs row(s), but {MANIFEST_MEMBER} names no resume cache "
                      "or no resume inputs file for them")
    return manifest, digest


def check_parity() -> dict:
    """Check 5. Returns the summary's parity block."""
    data = _read(PARITY_REPORT, "the Granite parity report")
    digest = sha256_bytes(data)
    if digest != PARITY_REPORT_SHA256:
        raise Refusal(f"the Granite parity report has SHA-256 {digest[:16]}, not the pinned "
                      f"{PARITY_REPORT_SHA256[:16]}")
    report = _object(data, "the Granite parity report")
    if report.get("kind") != PARITY_REPORT_KIND or report.get("verdict") != "PASS":
        raise Refusal("the Granite parity report does not say PASS")
    return {"report": _shown(PARITY_REPORT), "sha256": digest, "verdict": "PASS",
            "settings_sha256": PARITY_SETTINGS_SHA256, "packages_sha256": PARITY_PACKAGES_SHA256}


# ---------------------------------------------------------------- checks 6 and 7: the units and their guard rows

def check_units(unit_dirs, record: dict, manifest: dict) -> list:
    """Check 6. Returns [(unit, its bundle group)] sorted by folder name."""
    if not unit_dirs:
        raise Refusal("give at least one --unit")
    resolved = [pathlib.Path(d).resolve() for d in unit_dirs]
    twice = sorted({str(p) for p in resolved if resolved.count(p) > 1})
    if twice:
        raise Refusal(f"the unit folder {twice[0]} is given twice")
    units, _ = enumerate_units((), unit_dirs)
    names = collections.Counter(u.name for u in units)
    same = sorted(n for n, c in names.items() if c > 1)
    if same:
        labels = sorted(u.label for u in units if u.name == same[0])
        raise Refusal(f"two units have the folder name {same[0]} ({', '.join(labels)}); a summary is keyed by folder "
                      "name: write one summary per reading")
    in_run = {}
    for g in record["groups"]:
        for complete, label in zip(g["complete_sha256"], g["units"]):
            in_run[complete] = (label, g)
    in_bundle = {}
    for g in manifest["groups"]:
        for e in g["units"]:
            in_bundle[e.get("complete_sha256")] = (e, g)
    pairs = []
    for u in sorted(units, key=lambda x: x.name):
        if u.complete_sha256 not in in_run or u.complete_sha256 not in in_bundle:
            raise Refusal(f"{u.label}: COMPLETE.json {u.complete_sha256[:16]} is not a unit of this pod run")
        label, run_group = in_run[u.complete_sha256]
        entry, group = in_bundle[u.complete_sha256]
        if label != u.label:
            raise Refusal(f"{u.label}: the run record names this attempt {label}")
        if ((entry.get("job_sha256"), entry.get("host"), entry.get("unit"), entry.get("target"), entry.get("arm"),
             entry.get("seed")) != (u.job_sha256, u.host, u.unit, u.target, u.arm, u.seed)):
            raise Refusal(f"{u.label}: the bundle's entry names another job.json SHA-256, host, unit, target, arm or "
                          "seed")
        prepared = group["prepared"].get("manifest_sha256")
        if u.manifest_sha256 != prepared or run_group.get("manifest_sha256") != prepared:
            raise Refusal(f"{u.label}: job.json, the bundle and the run record name different prepared manifests")
        pairs.append((u, group))
    return pairs


def local_prepared(name) -> dict:
    """bundle.prepared_identity of the local prepared set PREPARED_ROOT/name: {name, manifest_sha256,
    dev_bank_sha256}, after its pins are checked. It reads manifest.sha256, manifest.json and banks/dev.jsonl only."""
    if not isinstance(name, str) or name not in bundle_mod.KNOWN_PREPARED:
        raise Refusal(f"the bundle's prepared set {str(name)[:64]!r} is not one of the pinned sets "
                      f"{sorted(bundle_mod.KNOWN_PREPARED)}")
    folder = PREPARED_ROOT / name
    if not folder.is_dir():
        raise Refusal(f"the prepared set {name} is not on this machine ({folder})")
    try:
        return bundle_mod.prepared_identity(folder)
    except OSError:
        raise Refusal(f"the prepared set {name} ({folder}) cannot be read") from None


def check_prepared(pairs: list, record: dict) -> dict:
    """Check 6, the dev banks. For the bundle group of each unit: the local prepared set passes
    bundle.prepared_identity, and its {name, manifest_sha256, dev_bank_sha256} equals the bundle group's and the run
    record's group's (the group that names the unit's COMPLETE.json SHA-256). Then the harm prompts of its dev bank
    (common.bank_prompts) are hashed in memory. Returns {name: (identity, {prompt id: prompt SHA-256})}. No prompt is
    kept, printed or written."""
    run_group_of = {c: g for g in record["groups"] for c in g["complete_sha256"]}
    found = {}
    for u, group in pairs:
        p = group["prepared"]
        name = p.get("name")
        if not isinstance(name, str) or name not in found:
            ident = local_prepared(name)
            try:
                prompts = bank_prompts(PREPARED_ROOT / name, ident["manifest_sha256"])
            except (OSError, ValueError, KeyError):
                raise Refusal(f"the dev bank of the prepared set {name} cannot be read") from None
            found[name] = (ident, {pid: sha256_text(text) for pid, text in prompts.items()})
        run_group = run_group_of[u.complete_sha256]
        want = {"name": name, "manifest_sha256": p.get("manifest_sha256"), "dev_bank_sha256": p.get("dev_bank_sha256")}
        in_record = {"name": run_group.get("prepared"), "manifest_sha256": run_group.get("manifest_sha256"),
                     "dev_bank_sha256": run_group.get("dev_bank_sha256")}
        if found[name][0] != want or in_record != want:
            raise Refusal(f"{u.label}: the local prepared set {name}, the bundle and the run record name different "
                          "manifests or dev banks")
    return found


def _sealed_rows(u, key: str):
    """(line number, row) of one sealed eval file of the unit, after its SHA-256 is checked again."""
    entry = u.files.get(key)
    if entry is None:
        raise Refusal(f"{u.label}: no sealed {key} file")
    data = pathlib.Path(entry["path"]).read_bytes()
    if sha256_bytes(data) != entry["sha256"]:
        raise Refusal(f"{u.label}: its {key} file changed after it was verified")
    for lineno, row in jsonl_records(data, f"{u.label}: {key} file"):
        if not isinstance(row, dict):
            raise Refusal(f"{u.label}: {key} file line {lineno} is not an object")
        yield lineno, row


def kit_view_check(u, items, guard: dict) -> None:
    """Check 7, second part: second_judge_probe.judge_units indexes generations.jsonl and guard.jsonl by prompt id over
    ALL rows (the last row of an id wins) and judges the ids whose row says kind "harm"; it copies safety and refusal
    from the guard row of that id. units.load_items and units.load_guard keep the harm rows only. The answers and the
    Qwen3Guard labels must be the same in both views, so that the summary is the one the kit would write. Reads the
    ids, kinds and labels only."""
    kind_of, last_guard = {}, {}
    for _, row in _sealed_rows(u, "generations"):
        kind_of[row.get("prompt_id")] = row.get("kind")
    for _, row in _sealed_rows(u, "guard"):
        last_guard[row.get("prompt_id")] = (row.get("safety"), row.get("refusal"))
    kit_ids = {pid for pid, kind in kind_of.items() if kind == BANK_KIND}
    ids = {it.prompt_id for it in items}
    if kit_ids != ids:
        raise Refusal(f"{u.label}: the kit's view of generations.jsonl gives {len(kit_ids)} harm answer ids, units.py "
                      f"gives {len(ids)} (an id shared by two kinds)")
    differ = sorted(pid for pid in ids if last_guard.get(pid) != (guard[(pid, None)]["safety"],
                                                                   guard[(pid, None)]["refusal"]))
    if differ:
        raise Refusal(f"{u.label}: the kit's view of guard.jsonl gives other Qwen3Guard labels for {len(differ)} "
                      f"id(s) (first: prompt {differ[0]})")


def check_guard(pairs: list) -> dict:
    """Check 7. Returns {COMPLETE.json SHA-256: (items sorted by prompt id, guard rows)}."""
    found = {}
    for u, group in pairs:
        judging.check_units([u], (MODE,), group["expect"], False, group["prepared"].get("manifest_sha256"))
        items = sorted(load_items(u, MODE), key=lambda it: it.prompt_id)
        guard = load_guard(u, MODE)
        kit_view_check(u, items, guard)
        found[u.complete_sha256] = (items, guard)
    return found


# ---------------------------------------------------------------- checks 8 to 10: the labels, the inputs, the counts

def check_cache(pod_dir: pathlib.Path, record: dict, pairs: list, answers: dict) -> dict:
    """Check 8. Returns {COMPLETE.json SHA-256: {prompt id: cache record}}."""
    cache = Cache(pod_dir / FETCHED / CACHE_REL, GRANITE)     # refuses another judge, malformed or conflicting records
    if cache.undecodable:
        raise Refusal(f"the cache has {cache.undecodable} line(s) that are not JSON")
    if len(cache) != record["cache"]["records"]:
        raise Refusal(f"the cache holds {len(cache)} records, the run record says {record['cache']['records']}")
    found = {}
    for u, _ in pairs:
        items, _ = answers[u.complete_sha256]
        wanted = {(u.complete_sha256, MODE, it.prompt_id, None) for it in items}
        extra = sorted(k for k in cache.entries if k[0] == u.complete_sha256 and k not in wanted)
        if extra:
            raise Refusal(f"{u.label}: the cache holds {len(extra)} record(s) that are not its greedy harm answers "
                          f"(first: {extra[0][1]} prompt {extra[0][2]} sample {extra[0][3]})")
        per = {}
        for it in items:
            entry = cache.get((u.complete_sha256, MODE, it.prompt_id, None))
            if entry is None:
                raise Refusal(f"{u.label}: the cache has no record of prompt {it.prompt_id}")
            if entry["answer_sha256"] != it.answer_sha256:
                raise Refusal(f"{u.label}: the cache record of prompt {it.prompt_id} names another answer SHA-256")
            if entry["source"] != "judged":
                raise Refusal(f"{u.label}: the cache record of prompt {it.prompt_id} has source {entry['source'][:14]}, "
                              "not judged on the pod (labels of two devices would mix)")
            if not isinstance(entry["truncated"], bool):
                raise Refusal(f"{u.label}: the cache record of prompt {it.prompt_id} has no bool truncated flag")
            per[it.prompt_id] = entry
        found[u.complete_sha256] = per
    return found


def check_inputs(pod_dir: pathlib.Path, record: dict, pairs: list, answers: dict, labels: dict, banks: dict) -> dict:
    """Check 9. Returns {COMPLETE.json SHA-256: {prompt id: inputs row}}."""
    rows, undecodable = granite_pod.read_inputs(pod_dir / FETCHED / INPUTS_REL)
    if undecodable:
        raise Refusal(f"the inputs file has {undecodable} line(s) that are not JSON")
    if len(rows) != record["inputs"]["records"]:
        raise Refusal(f"the inputs file holds {len(rows)} rows, the run record says {record['inputs']['records']}")
    found = {}
    for u, group in pairs:
        prompts = banks[group["prepared"]["name"]][1]
        items, _ = answers[u.complete_sha256]
        wanted = {(u.complete_sha256, it.prompt_id, None) for it in items}
        extra = sorted(k for k in rows if k[0] == u.complete_sha256 and k not in wanted)
        if extra:
            raise Refusal(f"{u.label}: the inputs file holds {len(extra)} row(s) that are not its greedy harm answers")
        per = {}
        for it in items:
            row = rows.get((u.complete_sha256, it.prompt_id, None))
            entry = labels[u.complete_sha256][it.prompt_id]
            if row is None:
                raise Refusal(f"{u.label}: the inputs file has no row of prompt {it.prompt_id}")
            if row["answer_sha256"] != it.answer_sha256:
                raise Refusal(f"{u.label}: the inputs row of prompt {it.prompt_id} names another answer SHA-256")
            if row["prompt_sha256"] != prompts.get(it.prompt_id):
                raise Refusal(f"{u.label}: the inputs row of prompt {it.prompt_id} names another prompt SHA-256 than "
                              f"the local dev bank of {group['prepared']['name']}")
            if row["trimmed"] != entry["truncated"] or row["input_tokens"] != entry["input_tokens"]:
                raise Refusal(f"{u.label}: the inputs row of prompt {it.prompt_id} has another trim flag or input "
                              "token count than its cache record")
            per[it.prompt_id] = row
        found[u.complete_sha256] = per
    return found


def count_unit(u, items, guard: dict, labels: dict) -> dict:
    """The kit's eight unit keys (second_judge_probe.summarize), then this tool's three."""
    n = harm = unsafe = agree = unparsed = trimmed = 0
    for it in items:
        entry = labels[it.prompt_id]
        is_harm = entry["label"] == "yes"
        is_unsafe = guard[(it.prompt_id, None)]["safety"] == "Unsafe"
        n += 1
        harm += is_harm
        unsafe += is_unsafe
        agree += is_harm == is_unsafe
        unparsed += entry["label"] == "unparsed"
        trimmed += entry["truncated"] is True
    return {"job_sha256": u.job_sha256, "target": u.target, "n": n, "granite_harm": harm, "qwen3guard_unsafe": unsafe,
            "agree": agree, "unparsed": unparsed, "trimmed": trimmed, "complete_sha256": u.complete_sha256,
            "label": u.label, "device": DEVICE}


def check_result_counts(result: dict, pairs: list, counts: dict) -> None:
    """Check 10: the launch's own verification counted the same per unit."""
    verified = {}
    for row in result["verification"]["units"]:
        if isinstance(row, dict):
            verified[row.get("complete_sha256")] = row
    for u, _ in pairs:
        c = counts[u.name]
        row = verified.get(u.complete_sha256)
        want = {"n": c["n"], "judged": c["n"], "yes": c["granite_harm"], "unparsed": c["unparsed"]}
        if row is None or row.get("unit") != u.label or row.get(MODE) != want:
            raise Refusal(f"{u.label}: the result's verified greedy counts are not this tool's {want}")


def overall_of(counts: dict) -> dict | None:
    """second_judge_probe.summarize's "overall" over all pairs of the file (kappa's formula), or None without pairs."""
    n = sum(c["n"] for c in counts.values())
    if not n:
        return None
    a = sum(c["agree"] for c in counts.values()) / n
    p1 = sum(c["granite_harm"] for c in counts.values()) / n
    p2 = sum(c["qwen3guard_unsafe"] for c in counts.values()) / n
    pe = p1 * p2 + (1 - p1) * (1 - p2)
    return {"pairs": n, "agreement": round(a, 3), "cohen_kappa": round((a - pe) / (1 - pe) if pe < 1 else 1.0, 3)}


# ---------------------------------------------------------------- check 11 and the writes

def check_out(out_dir: pathlib.Path, files: list, pod_dir: pathlib.Path) -> tuple[pathlib.Path, dict]:
    """Check 11. Resolves --out once and tests that real path only. Returns (the real folder, {file name: "new" or
    "unchanged"}). Makes nothing: convert makes the real folder after this check. Besides the path parts, an existing
    ancestor of the real path (or the real path itself) that is the same folder as this run's fetched/ refuses
    (os.path.samefile): this also covers a fetched/ that is a symbolic link to a folder with another name."""
    real = out_dir.resolve()
    if real.exists() and not real.is_dir():
        raise Refusal(f"--out {out_dir} is not a folder")
    parts = {p.casefold() for p in real.parts}
    if "retrieved" in parts:
        raise Refusal(f"--out {out_dir} is inside a retrieved/ tree (a kit's sealed units); write outside the kits")
    fetched = pod_dir / FETCHED
    if FETCHED in parts or any(a.exists() and os.path.samefile(a, fetched) for a in (real, *real.parents)):
        raise Refusal(f"--out {out_dir} is inside a {FETCHED}/ folder (a pod run's fetched files); keep the fetched "
                      "files as fetched")
    if (real / "retrieved").exists():
        raise Refusal(f"--out {out_dir} holds a retrieved/ folder: it is a kit; write outside the kits")
    for name in KIT_NAMES:
        if (real / name).exists():
            raise Refusal(f"--out {out_dir} holds the kit file {name}: it is a kit; write outside the kits")
    state = {}
    for name, data in files:
        path = real / name
        if path.is_symlink() or (path.exists() and not path.is_file()):
            raise Refusal(f"{path} exists and is not a plain file")
        if path.exists():
            if path.read_bytes() != data:
                raise Refusal(f"{path} exists with other bytes; the tool never overwrites a file (choose a new --out)")
            state[name] = "unchanged"
        else:
            state[name] = "new"
    return real, state


def _write_new(path: pathlib.Path, data: bytes) -> None:
    """Writes a new file: a temporary file in the same folder, flushed and fsynced, then hard-linked to its name (the
    link fails when the name exists, so nothing is ever replaced), then the temporary file is removed."""
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    try:
        with open(tmp, "xb") as fh:
            fh.write(data)
            fh.flush()
            os.fsync(fh.fileno())
        try:
            os.link(tmp, path)
        except FileExistsError:
            raise Refusal(f"{path} appeared while the tool ran; nothing was replaced") from None
    finally:
        if tmp.exists():
            tmp.unlink()


# ---------------------------------------------------------------- the conversion

def convert(pod_dir, unit_dirs, out_dir) -> dict:
    """Checks 1 to 11, then the two files. Returns {"units": [per-unit lines], "files": the final line}."""
    pod_dir, out_dir = pathlib.Path(pod_dir).absolute(), pathlib.Path(out_dir).absolute()
    result, result_sha = check_result(pod_dir)                                        # 1
    fetched = check_fetched(pod_dir, result)                                          # 2
    record = check_record(pod_dir, result)                                            # 3
    manifest, bundle_sha = check_bundle(pod_dir, result, record)                      # 4
    parity_block = check_parity()                                                     # 5
    pairs = check_units(unit_dirs, record, manifest)                                  # 6
    banks = check_prepared(pairs, record)                                             # 6, the dev banks
    answers = check_guard(pairs)                                                      # 7
    labels = check_cache(pod_dir, record, pairs, answers)                             # 8
    rows = check_inputs(pod_dir, record, pairs, answers, labels, banks)               # 9
    counts = {}
    item_lines = []
    for u, _ in pairs:
        items, guard = answers[u.complete_sha256]
        counts[u.name] = count_unit(u, items, guard, labels[u.complete_sha256])
        for it in items:
            entry, g = labels[u.complete_sha256][it.prompt_id], guard[(it.prompt_id, None)]
            item_record = {"unit": u.name, "target": u.target, "prompt_id": it.prompt_id,
                           "granite": entry["label"] if entry["label"] in ("yes", "no") else None}
            item_record["raw"] = None                 # the pod keeps no judge output text
            item_record.update(trimmed=entry["truncated"], qwen3guard=g["safety"], qwen_refusal=g["refusal"],
                               answer_sha256=it.answer_sha256,
                               input_sha256=rows[u.complete_sha256][it.prompt_id]["input_sha256"])
            item_lines.append(json.dumps(item_record) + "\n")
    check_result_counts(result, pairs, counts)                                        # 10
    items_bytes = "".join(item_lines).encode("ascii")

    # every input file again: nothing changed while the tool read it
    again = {rel: sha256_file(pod_dir / FETCHED / rel) for rel in FETCHED_RELS}
    if (again != fetched or sha256_file(pod_dir / RESULT_NAME) != result_sha
            or sha256_file(pod_dir / BUNDLE_NAME) != bundle_sha or sha256_file(PARITY_REPORT) != parity_block["sha256"]):
        raise Refusal("an input file of the pod run changed while the tool read it")
    for u, _ in pairs:
        sealed = [(u.path / "COMPLETE.json", u.complete_sha256), (u.path / "job.json", u.job_sha256)]
        sealed += [(pathlib.Path(f["path"]), f["sha256"]) for f in u.files.values() if f is not None]
        if any(sha256_file(p) != digest for p, digest in sealed):
            raise Refusal(f"{u.label}: a sealed file changed while the tool read it")
    for name, (ident, _) in sorted(banks.items()):
        folder = PREPARED_ROOT / name
        if (sha256_file(folder / "manifest.json") != ident["manifest_sha256"]
                or sha256_file(folder / bundle_mod.DEV_BANK) != ident["dev_bank_sha256"]):
            raise Refusal(f"the local prepared set {name} changed while the tool read it")

    env, llama = record["environment"], record["llama"]
    build = llama["build"]
    packages = _dict(env.get("packages")) or _dict(record.get("packages"))
    this_file = pathlib.Path(__file__).resolve()
    summary = {"judge": JUDGE, "kind": BANK_KIND, "units": {name: counts[name] for name in sorted(counts)}}
    overall = overall_of(counts)
    if overall is not None:
        summary["overall"] = overall
    summary["device"] = {
        "device": DEVICE, "gpu": env.get("gpu"), "driver": env.get("driver"), "python": env.get("python"),
        "llama_cpp_python": llama.get("llama_cpp_python"), "gpu_offload": llama.get("gpu_offload"),
        "cuda": build.get("cuda"), "cmake_args": build.get("cmake_args"), "sdist_sha256": build.get("sdist_sha256"),
        "gguf_sha256": record["files"]["gguf_sha256"], "tokenizer_fingerprint": record["tokenizer_fingerprint"],
        "transformers": packages.get("transformers") or env.get("transformers"), "pins": record.get("pins")}
    summary["source"] = {
        "kind": KIND, "version": VERSION, "tag": result["tag"], "pod_id": result.get("pod_id"),
        "result_sha256": result_sha, "run_record_sha256": fetched[RECORD_REL],
        "cache_sha256": fetched[CACHE_REL], "cache_records": record["cache"]["records"],
        "inputs_sha256": fetched[INPUTS_REL], "inputs_records": record["inputs"]["records"],
        "input_sha256_checked": False,              # recorded from the pod, not computed again (module text)
        "bundle_sha256": bundle_sha, "bundle_manifest_sha256": record["bundle_manifest_sha256"],
        "started_utc": record.get("started_utc"), "ended_utc": record.get("ended_utc"),
        "known_answers": record["known_answers"], "resumed_records": record["resumed_records"],
        "resumed_inputs": record["resumed_inputs"], "resume_cache": manifest.get("resume_cache"),
        "resume_inputs": manifest.get("resume_inputs"), "parity": parity_block,
        "converter": {"path": _shown(this_file), "sha256": sha256_file(this_file)},
        "items_file": {"name": ITEMS_NAME, "sha256": sha256_bytes(items_bytes)}}
    summary_bytes = (json.dumps(summary, indent=1) + "\n").encode("ascii")

    files = [(ITEMS_NAME, items_bytes), (SUMMARY_NAME, summary_bytes)]               # the items file first
    real, state = check_out(out_dir, files, pod_dir)                                  # 11
    real.mkdir(parents=True, exist_ok=True)                    # the checked real path, not the path as given
    for name, data in files:
        if state[name] == "new":
            _write_new(real / name, data)
    kinds = set(state.values())
    status = "unchanged" if kinds == {"unchanged"} else "written" if kinds == {"new"} else "completed"
    unit_lines = [{"unit": counts[u.name]["label"], "name": u.name, "complete_sha256": u.complete_sha256[:16],
                   "job_sha256": u.job_sha256[:16], **{k: counts[u.name][k] for k in UNIT_KEYS[1:]}}
                  for u, _ in pairs]
    final = {"status": status, "judge": JUDGE, "device": DEVICE, "tag": result["tag"],
             "summary": {"path": str(real / SUMMARY_NAME), "sha256": sha256_bytes(summary_bytes)},
             "items": {"path": str(real / ITEMS_NAME), "sha256": sha256_bytes(items_bytes)}}
    return {"units": unit_lines, "files": final}


def parser() -> argparse.ArgumentParser:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--pod-dir", required=True, type=pathlib.Path,
                    help="the launch's tag folder, tmp/judge-pod/TAG (judge-pod-result.json, bundle.tar.gz, fetched/)")
    ap.add_argument("--unit", action="append", required=True, type=pathlib.Path,
                    help="a unit folder at .../retrieved/HOST/tree/.../UNIT that this run judged (repeatable)")
    ap.add_argument("--out", dest="out_dir", required=True, type=pathlib.Path,
                    help=f"the folder for {ITEMS_NAME} and {SUMMARY_NAME} (never a kit folder)")
    return ap


def main(argv=None) -> int:
    a = parser().parse_args(argv)
    try:
        done = convert(a.pod_dir, a.unit, a.out_dir)
    except Refusal as e:
        print(f"refused: {e}", file=sys.stderr)
        return 2
    except Exception as e:  # noqa: BLE001 - only the type: a message could quote bytes of an input file
        print(f"error: {type(e).__name__}", file=sys.stderr)
        return 1
    for line in done["units"]:
        print(json.dumps(line))
    print(json.dumps(done["files"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
