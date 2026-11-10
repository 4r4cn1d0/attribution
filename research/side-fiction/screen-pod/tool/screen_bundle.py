"""The screen's bundle: planned and staged on the Mac, verified and read on the pod.

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Mac side (screen_pod.py bundle and
launch): every input is checked against its pin before anything is built:
  - the specification and the rules (SCREEN-SPEC.md 81dc487a..., rules-v2.json c23672cf...): a changed file refuses
    until this build is checked against it again;
  - round 1: dark.jsonl and light.jsonl (SHA-256 and 5,000 rows each, exactly the four fields, a book category of the
    file's arm) and the Dolly baseline, the prepared set's engine/train_rows.jsonl (manifest.sha256 = SHA-256 of
    manifest.json = 9ed61826...; the manifest lists the file at 1efa8571...; 4,800 rows); rounds 2 and 3: the refill
    file refill-rN.jsonl that sf_screen.py wrote, whose SHA-256 the lead gives on the command line (the four fields
    plus slot_arm, slot_line and rank), and the refill report sf_screen.py wrote beside it, which must name that file,
    its SHA-256 and its row count, and the pinned sf_screen.py (165f1a30..., SCREEN-SPEC section 7) as its writer;
  - the engine code: experiments/minimal_safety and experiments/safety_selection (.py, .json, .md, .lock; no
    __pycache__, no symlink), as the probe kits' pack_setup.py selects it, with its code identity
    (safety_selection.common.code_identity), which must be the pinned e49a978c..., the git commit, the SHA-256 of all
    shipped engine files and the engine files changed since commit 8801456; uncommitted engine files refuse, as in the
    kits; recipe B's config (a47138f2...) with the pinned guard block.

Revised 9 October 2026 (17:11 UTC, clock checked): ONE Granite-on-CUDA backend, the lead's. The bundle's gate_b/ folder
IS a bundle of the lead's Granite pod mode, staged by the lead's own bundle.stage_bundle (scripts/gate_b_mac_judges/pod/
bundle.py, 2694bd0) with no requested unit and the known-answer gate on (bundle.plan_known_answers: the lead's
reference granite-known-answers.json b5b2678e..., unit 1101-a0-e1-a1, COMPLETE.json 8f0fa83a..., its dev bank), so it
holds the lead's modules (tool/, tool/pod/: pod_run_granite.sh, granite_pod.py, granite-requirements.txt, ...), the
Mac's pinned Granite tokenizer folder (granite-tokenizer/) and the gate's files (known/), with the lead's own
job-manifest.json. The builder refuses unless that gate is the screen's expected unit, reference and rule, and every
lead file in it has its pinned SHA-256 (screen_pins.LAUNCHER_PINS). On the pod the lead's pod_run_granite.sh runs on it
unchanged (screen_run.sh links /workspace/judge/bundle to it), and the screen's granite step loads the same
tokenizer folder. The screen's own Granite prompt, parse, build and requirements files are gone; its own known-answer
files (ka/, the Mac labels, prepared/) are gone too (the gate is the lead's).

The bundle holds only: the screen's own files (tool/); the lead's Granite bundle (gate_b/); the engine code (engine/);
the input files (data/); optionally a resumed launch's two caches (resume/); and job-manifest.json (every other file's
SHA-256, the lead bundle's manifest SHA-256). No hidden or selector file. Every staged file passes the kits' secret
patterns (a hit refuses, naming the file and the pattern only). The tar is the lead's bundle.write_tar (deterministic).
Pod side: verify_bundle refuses unless the folder holds exactly the listed files with their SHA-256, the lead's own
verify_bundle accepts gate_b/ with its recorded manifest, and every pin agrees; pod_sources reads the rows.
"""
from __future__ import annotations

import json
import pathlib
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
import screen_pins as P  # noqa: E402
import screen_rows as R  # noqa: E402
import bundle as lead_bundle  # noqa: E402  (the lead's pod/bundle.py: stage_bundle, verify_bundle, write_tar)
import granite_pod  # noqa: E402  (the lead's Granite pins, the gate's reference and rule)
from common import GRANITE, Refusal, bank_prompts, canonical_bytes, sha256_bytes, sha256_file  # noqa: E402
from units import load_items  # noqa: E402

KIND, VERSION, MANIFEST_NAME = "fiction-screen job manifest", 3, P.MANIFEST_NAME
TOOL_FILES = ("screen_pins.py", "screen_rows.py", "screen_models.py", "granite_screen.py", "guard_screen.py",
              "screen_job.py", "screen_bundle.py", "screen_run.sh", "guard-requirements.txt")
GATE_B = P.GATE_B_BUNDLE                                          # the lead's Granite bundle, beside tool/
KA_REFERENCE = f"{GATE_B}/{lead_bundle.KNOWN_REFERENCE}"          # gate_b/known/granite-known-answers.json
DATA_NAME = {"dark": "data/dark.jsonl", "light": "data/light.jsonl", "dolly": "data/dolly-train_rows.jsonl",
             "refill": "data/refill.jsonl"}
RESUME = {"granite": "resume/granite.jsonl", "qwen": "resume/qwen.jsonl"}


def lead_pin_of(rel: str) -> str | None:
    """The LAUNCHER_PINS key of a file of the lead's staged bundle (its tool files and the gate's reference), or None
    for the files the lead's own verify_bundle pins (the tokenizer folder, the gate's unit and dev bank)."""
    if rel.startswith("tool/pod/"):
        return "pod/" + rel[len("tool/pod/"):]
    if rel.startswith("tool/"):
        return rel[len("tool/"):]
    if rel == lead_bundle.KNOWN_REFERENCE:
        return "pod/" + granite_pod.KNOWN_ANSWERS_NAME
    return None


# ---------------------------------------------------------------- Mac side: inputs

def check_documents(spec: pathlib.Path = None, rules: pathlib.Path = None) -> dict:
    """The specification and the rules this build implements, by SHA-256 (a changed document refuses)."""
    found = {}
    for name, path, pin in (("spec", spec or P.SPEC, P.SPEC_SHA256), ("rules", rules or P.RULES, P.RULES_SHA256)):
        found[name] = sha256_file(path)
        if found[name] != pin:
            raise Refusal(f"{pathlib.Path(path).name} has SHA-256 {found[name][:16]}, not {pin[:16]} that this build "
                          "implements; have the build checked against the changed document first")
    return {"spec_sha256": found["spec"], "rules_v2_sha256": found["rules"]}


def prepared_check(prepared: pathlib.Path) -> dict:
    """The prepared set's pins (hashes only): manifest.sha256 = SHA-256(manifest.json) = the pin; the files it lists
    for the Dolly train rows and the dev bank."""
    prepared = pathlib.Path(prepared)
    text = (prepared / "manifest.sha256").read_text(encoding="utf-8").strip()
    manifest_bytes = (prepared / "manifest.json").read_bytes()
    if text != P.PREPARED_MANIFEST or sha256_bytes(manifest_bytes) != P.PREPARED_MANIFEST:
        raise Refusal(f"{prepared.name}: manifest.sha256 or SHA-256(manifest.json) is not the pinned "
                      f"{P.PREPARED_MANIFEST[:16]}")
    try:
        listed = json.loads(manifest_bytes)["files"]
    except (ValueError, KeyError, TypeError):
        raise Refusal(f"{prepared.name}: manifest.json lists no files") from None
    if listed.get(P.DOLLY_REL) != P.DATA_PINS["dolly"][0]:
        raise Refusal(f"{prepared.name}: manifest.json does not list {P.DOLLY_REL} at the pinned SHA-256")
    dev = listed.get(P.DEV_BANK_REL)
    if not isinstance(dev, str) or sha256_file(prepared / P.DEV_BANK_REL) != dev:
        raise Refusal(f"{prepared.name}: {P.DEV_BANK_REL} does not have the SHA-256 its manifest.json lists")
    return {"name": prepared.name, "manifest_sha256": P.PREPARED_MANIFEST, "dev_bank_sha256": dev}


def lead_gate_plan(plan_known_answers=None) -> dict:
    """The lead's known-answer gate for this bundle (the lead's bundle.plan_known_answers: the reference by its pinned
    SHA-256 and counts, the unit found and verified as the Mac judges find it, its 200 answers equal to the reference's,
    its dev bank), refused unless it is the gate this screen expects: the same unit, reference and rule (so the
    screen's own check is not needed and is never run twice). Hashes, ids and counts only."""
    rule = (granite_pod.KNOWN_ANSWER_N, granite_pod.KNOWN_ANSWER_MAC_YES, granite_pod.KNOWN_ANSWER_MIN_IDENTICAL,
            granite_pod.KNOWN_ANSWER_MAX_DELTA_YES, granite_pod.KNOWN_ANSWERS_SHA256)
    want = (P.KA_N, P.KA_MAC_YES, P.KA_MIN_IDENTICAL, P.KA_MAX_DELTA_YES, P.KA_REFERENCE_SHA256)
    if rule != want:
        raise Refusal(f"the lead's known-answer rule {rule[:4]} or reference {rule[4][:16]} is not the screen's "
                      f"{want[:4]} / {want[4][:16]}; have this build checked against it first")
    plan = (plan_known_answers or lead_bundle.plan_known_answers)()
    unit = plan["unit"]
    if (plan["reference_sha256"], unit.complete_sha256, unit.name, plan["n"], plan["mac_yes"]) != (
            P.KA_REFERENCE_SHA256, P.KA_COMPLETE_SHA256, P.KA_UNIT_NAME, P.KA_N, P.KA_MAC_YES):
        raise Refusal("the lead's known-answer gate is not the screen's unit 1101-a0-e1-a1 with 200 answers and 93 yes")
    if plan["prepared"]["manifest_sha256"] != P.PREPARED_MANIFEST:
        raise Refusal("the lead's known-answer dev bank is not the pinned prepared set's")
    return plan


def ka_reference(path: pathlib.Path) -> dict:
    """{prompt id: Mac label (yes/no)} of the lead's known-answer reference (granite_pod.load_known_answers: its pinned
    SHA-256, 200 items, 93 yes)."""
    doc = granite_pod.load_known_answers(pathlib.Path(path), P.KA_REFERENCE_SHA256)
    return {r["prompt_id"]: r["label"] for r in doc["items"]}


def engine_files(root: pathlib.Path = None) -> dict:
    """{path under the engine root: file} of the shipped engine code (the kits' selection)."""
    root = pathlib.Path(P.ROOT if root is None else root)
    files = {}
    for component in P.ENGINE_COMPONENTS:
        for f in sorted((root / "experiments" / component).rglob("*")):
            if (f.is_file() and not f.is_symlink() and "__pycache__" not in f.parts
                    and f.suffix in P.ENGINE_SUFFIXES):
                files[f.relative_to(root).as_posix()] = f
    return files


def engine_provenance(runner=subprocess.run, root: pathlib.Path = None) -> dict:
    """The git commit, and a refusal when engine files are not committed (as pack_setup.py of the kits)."""
    root = pathlib.Path(P.ROOT if root is None else root)
    status = runner(["git", "-C", str(root), "status", "--porcelain", "--", "experiments/minimal_safety",
                     "experiments/safety_selection"], capture_output=True, text=True, check=True).stdout
    if status.strip():
        raise Refusal(f"{len(status.strip().splitlines())} engine file(s) are not committed; commit them first")
    commit = runner(["git", "-C", str(root), "rev-parse", "HEAD"], capture_output=True, text=True,
                    check=True).stdout.strip()
    return {"git_commit": commit}


def engine_identity(files: dict, runner=subprocess.run, root: pathlib.Path = None) -> dict:
    """The engine's code identity (safety_selection.common.code_identity), which must be the pinned one; the SHA-256
    of every shipped engine file (canonical JSON of {path: SHA-256}); and the engine files committed since the pin's
    base commit (git diff --name-only, recorded, not refused). Hashes and paths only."""
    from experiments.safety_selection.common import code_identity
    root = pathlib.Path(P.ROOT if root is None else root)
    code = code_identity()["sha256"]
    if code != P.ENGINE_CODE_SHA256:
        raise Refusal(f"the engine's code identity is {code[:16]}, not the pinned {P.ENGINE_CODE_SHA256[:16]}; have "
                      "this build checked against the changed engine first")
    try:
        changed = runner(["git", "-C", str(root), "diff", "--name-only", P.ENGINE_BASE_COMMIT, "HEAD", "--",
                          "experiments/"], capture_output=True, text=True, check=True).stdout.split()
    except (subprocess.CalledProcessError, OSError):
        raise Refusal(f"git diff {P.ENGINE_BASE_COMMIT} HEAD -- experiments/ failed in {root}") from None
    return {"code_sha256": code, "code_sha256_pinned": P.ENGINE_CODE_SHA256,
            "files_sha256": sha256_bytes(canonical_bytes({rel: sha256_file(f) for rel, f in sorted(files.items())})),
            "base_commit": P.ENGINE_BASE_COMMIT, "changed_since_base": changed}


def refill_report(refill: pathlib.Path, round_: int, refill_sha256: str, rows: int) -> dict:
    """sf_screen.py's refill-rN-report.json beside refill-rN.jsonl must name this file, its SHA-256 and its rows, and
    the pinned sf_screen.py as its writer (script_sha256 = REFILL_TOOL_SHA256); anything else refuses."""
    refill = pathlib.Path(refill)
    if refill.name != f"refill-r{round_}.jsonl":
        raise Refusal(f"the round {round_} refill file must be sf_screen.py's refill-r{round_}.jsonl")
    path = refill.with_name(f"refill-r{round_}-report.json")
    try:
        data = path.read_bytes()
        report = json.loads(data)
        output = report["output"]
    except (OSError, ValueError, KeyError, TypeError):
        raise Refusal(f"no readable {path.name} beside the refill file (sf_screen.py writes both)") from None
    if (report.get("round") != round_ or output.get("file") != refill.name or output.get("sha256") != refill_sha256
            or output.get("rows") != rows):
        raise Refusal(f"{path.name} does not name this round, file, SHA-256 and row count")
    script = report.get("script_sha256")
    if script != P.REFILL_TOOL_SHA256:
        raise Refusal(f"{path.name} was written by sf_screen.py {str(script)[:16]}, not the pinned "
                      f"{P.REFILL_TOOL_SHA256[:16]} (SCREEN-SPEC section 7); have the build checked against it first")
    return {"report": path.name, "report_sha256": sha256_bytes(data), "script_sha256": script,
            "script_is_pinned_sf_screen": True}


_TOKEN_CACHE: dict = {}


def granite_token_means(planned: dict, limit: int | None, tok_dir: pathlib.Path = None) -> dict:
    """The speed stop's ratio r, from the bundle's own inputs, with the lead's prompt builder
    (granite_files.granite_input, the same function the pod's judge_triples calls) and the Mac's pinned Granite
    tokenizer folder (granite_pod.verify_tokenizer_dir; transformers renders and counts it as the Mac judge venv does,
    checked on 600 items):
      - fiction: the mean tokens one Granite call evaluates over this round's selected Granite rows, the `harm` call
        its whole template, the `sexual_content` call only the tokens after the prefix it shares with the `harm`
        call of the same row (the screen calls them in that order, so llama.cpp reuses that prefix);
      - known answers: the mean template tokens of the lead's gate's 200 answers (each a new conversation);
      - r = fiction mean / known-answer mean.
    Refuses a round whose longest input (after the trim) is above granite_files.INPUT_LIMIT (the pod's precheck would
    refuse it). Counts only (no text kept or printed). Cached per input hashes in this process."""
    import granite_files
    tok_dir = pathlib.Path(granite_pod.MAC_TOKENIZER if tok_dir is None else tok_dir)
    granite_pod.verify_tokenizer_dir(tok_dir)
    sources = {name: s for name, s in planned["sources"].items() if name in P.GRANITE_SOURCES}
    plan = planned["known_answers"]
    key = (tuple(sorted((name, s["sha256"]) for name, s in sources.items())), limit, plan["unit"].complete_sha256,
           str(tok_dir))
    if key in _TOKEN_CACHE:
        return dict(_TOKEN_CACHE[key])
    tok = granite_pod.load_tokenizer_at(tok_dir)

    def ids(templated):
        return tok(templated, add_special_tokens=False)["input_ids"]
    per_call, longest, trimmed = [], 0, 0
    for s in sources.values():
        for row in R.selected(s["rows"], limit):
            harm, n_harm, cut_harm = granite_files.granite_input(tok, row.user_turn, row.assistant_turn, "harm")
            sexual, n_sexual, cut_sexual = granite_files.granite_input(tok, row.user_turn, row.assistant_turn,
                                                                       "sexual_content")
            harm_ids, sexual_ids = ids(harm), ids(sexual)
            shared = 0
            for a, b in zip(harm_ids, sexual_ids):
                if a != b:
                    break
                shared += 1
            per_call += [len(harm_ids), len(sexual_ids) - shared]
            longest = max(longest, n_harm, n_sexual)
            trimmed += cut_harm + cut_sexual
    prompts = bank_prompts(plan["prepared"]["dir"], plan["prepared"]["manifest_sha256"])
    ka = [granite_files.granite_input(tok, prompts[it.prompt_id], it.text, "harm")[1]
          for it in load_items(plan["unit"], "greedy", with_text=True)]
    if not per_call or len(ka) != P.KA_N:
        raise Refusal("no Granite call to count, or not 200 known answers")
    if longest > granite_files.INPUT_LIMIT:
        raise Refusal(f"a Granite input of this round has {longest} tokens after the trim, above the pod's limit "
                      f"{granite_files.INPUT_LIMIT}")
    from importlib import metadata
    fiction, known = sum(per_call) / len(per_call), sum(ka) / len(ka)
    out = {"fiction_calls": len(per_call), "fiction_mean_tokens_per_call": round(fiction, 3),
           "ka_items": len(ka), "ka_mean_tokens": round(known, 3), "ratio": round(fiction / known, 6),
           "input_tokens_max": longest, "trimmed_inputs": trimmed,
           "definition": "fiction: harm call whole template, sexual_content call tokens after the prefix shared with "
                         "the row's harm call; known answers: whole harm template (granite_files.granite_input)",
           "tokenizer": {"transformers": metadata.version("transformers"), "tokenizers": metadata.version("tokenizers"),
                         "folder_files": "the ten pinned files (granite_pod.TOK_FILES)"}}
    _TOKEN_CACHE[key] = dict(out)
    return out


def check_granite_tokens(block) -> dict:
    """The manifest's token block: positive means, a ratio equal to their quotient, at least one fiction call."""
    ok = (isinstance(block, dict) and all(isinstance(block.get(k), (int, float)) and not isinstance(block.get(k), bool)
                                          and block[k] > 0 for k in ("fiction_mean_tokens_per_call", "ka_mean_tokens",
                                                                     "ratio", "fiction_calls", "ka_items"))
          and abs(block["ratio"] - block["fiction_mean_tokens_per_call"] / block["ka_mean_tokens"]) < 1e-3
          and block["ka_items"] == P.KA_N)
    if not ok:
        raise Refusal("the job manifest's Granite token block is missing or inconsistent")
    return block


def plan(round_: int, refill: pathlib.Path | None = None, refill_sha256: str | None = None) -> dict:
    """Every input read and checked; the rows (with their text, in memory only) by source."""
    if round_ not in P.ROUND_SOURCES:
        raise Refusal(f"--round must be 1, 2 or 3, not {round_}")
    documents = check_documents()
    sources, refill_info = {}, None
    if round_ == 1:
        if refill is not None or refill_sha256 is not None:
            raise Refusal("round 1 takes no refill file")
        for source in P.ROUND_SOURCES[1]:
            sha, rows = P.DATA_PINS[source]
            sources[source] = {"path": pathlib.Path(P.DATA_PATHS[source]), "sha256": sha,
                               "rows": R.read_rows(source, P.DATA_PATHS[source], sha, rows)}
    else:
        if refill is None or not isinstance(refill_sha256, str) or not R._hex64(refill_sha256):
            raise Refusal("rounds 2 and 3 need --refill and its 64-hex --refill-sha256")
        sources["refill"] = {"path": pathlib.Path(refill), "sha256": refill_sha256,
                             "rows": R.read_rows("refill", refill, refill_sha256, None, round_)}
        if not sources["refill"]["rows"]:
            raise Refusal("the refill file holds no row")
        refill_info = refill_report(refill, round_, refill_sha256, len(sources["refill"]["rows"]))
    return {"round": round_, "sources": sources, "prepared": prepared_check(P.PREPARED),
            "known_answers": lead_gate_plan(), "documents": documents, "refill": refill_info}


# ---------------------------------------------------------------- Mac side: the stage, the secret scan, the tar

def _copy(src: pathlib.Path, stage: pathlib.Path, rel: str, files: dict, expect: str | None = None) -> str:
    dst = stage / rel
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dst)
    files[rel] = sha256_file(dst)
    if expect is not None and files[rel] != expect:
        raise Refusal(f"{rel} changed after it was checked")
    return rel


def secret_hits(stage: pathlib.Path, patterns: dict) -> list:
    """(file, pattern name) for every staged file holding a secret-like string (the kits' secret_scan patterns)."""
    hits = []
    for path in sorted(p for p in stage.rglob("*") if p.is_file()):
        content = path.read_bytes().decode("utf-8", "ignore")
        hits += [(path.relative_to(stage).as_posix(), name) for name, pat in patterns.items() if pat.search(content)]
    return hits


def secret_hits_bytes(data: bytes, patterns: dict) -> list:
    content = data.decode("utf-8", "ignore")
    return [name for name, pat in patterns.items() if pat.search(content)]


def stage_gate_b(stage: pathlib.Path, tag: str, plan: dict, files: dict) -> dict:
    """The lead's Granite bundle into stage/gate_b by the lead's own bundle.stage_bundle (no requested unit, the
    known-answer gate on, the Granite judge: its modules, the pinned tokenizer folder, the gate's files and its
    job-manifest.json). Every staged file goes into `files` (gate_b/...); every lead file in it must have its pinned
    SHA-256. Returns {the lead manifest's SHA-256 and the gate's entry} for the screen's manifest."""
    folder = pathlib.Path(stage) / GATE_B
    manifest = lead_bundle.stage_bundle([], folder, tag, P.MAC_GATE_B, judge="granite", known_answers=plan)
    for path in sorted(p for p in folder.rglob("*") if p.is_file()):
        rel = path.relative_to(folder).as_posix()
        files[f"{GATE_B}/{rel}"] = sha256_file(path)
        pin = lead_pin_of(rel)
        if pin is not None and files[f"{GATE_B}/{rel}"] != P.LAUNCHER_PINS.get(pin):
            raise Refusal(f"{GATE_B}/{rel} is not the lead's pinned {pin}")
    lead_sha = files[f"{GATE_B}/{lead_bundle.MANIFEST_NAME}"]
    ka = manifest["known_answers"]
    return {"dir": GATE_B, "manifest_sha256": lead_sha, "judge": dict(GRANITE), "lead_commit": P.LEAD_COMMIT,
            "tokenizer_dir": manifest["tokenizer_dir"], "groups": len(manifest["groups"]),
            "known_answers": {"reference": KA_REFERENCE, "reference_sha256": ka["reference_sha256"],
                              "unit": ka["unit"]["unit"], "complete_sha256": ka["unit"]["complete_sha256"],
                              "items": ka["items"], "mac_yes": ka["mac_yes"],
                              "rule": {"min_identical": granite_pod.KNOWN_ANSWER_MIN_IDENTICAL,
                                       "max_abs_delta_yes": granite_pod.KNOWN_ANSWER_MAX_DELTA_YES,
                                       "n": granite_pod.KNOWN_ANSWER_N, "mac_yes": granite_pod.KNOWN_ANSWER_MAC_YES}}}


def stage_bundle(planned: dict, stage: pathlib.Path, tag: str, limit: int | None, engine: dict, pins: dict,
                 resume: dict | None, patterns: dict) -> dict:
    """Writes the bundle's files into stage/ (which must not exist); returns the job manifest (also written)."""
    stage = pathlib.Path(stage)
    if stage.exists():
        raise Refusal(f"{stage.name} exists; the bundle is staged into a new folder")
    stage.mkdir(parents=True)
    files: dict = {}
    for name in TOOL_FILES:
        _copy(HERE / name, stage, f"tool/{name}", files)
    gate_b = stage_gate_b(stage, tag, planned["known_answers"], files)
    for rel, src in engine["files"].items():
        _copy(src, stage, f"engine/{rel}", files)
    if files[f"engine/{P.RECIPE_REL}"] != P.RECIPE_SHA256:
        raise Refusal("the recipe config does not have its pinned SHA-256")
    sources = []
    for source, entry in planned["sources"].items():
        rel = _copy(entry["path"], stage, DATA_NAME[source], files, entry["sha256"])
        sources.append({"source": source, "path": rel, "sha256": entry["sha256"], "rows": len(entry["rows"])})
    resume_entry = None
    if resume is not None:
        resume_entry = {"from_tag": resume["from_tag"]}
        for judge, rel in RESUME.items():
            if resume.get(judge) is not None:
                _copy(resume[judge]["path"], stage, rel, files, resume[judge]["sha256"])
                resume_entry[judge] = {"path": rel, "sha256": resume[judge]["sha256"],
                                       "records": resume[judge]["records"]}
    hits = secret_hits(stage, patterns)
    if hits:
        raise Refusal(f"a secret pattern is in a staged file: {hits[:10]}")
    manifest = {"kind": KIND, "version": VERSION, "tag": tag, "round": planned["round"], "limit": limit,
                "files": dict(sorted(files.items())), "sources": sources, "refill": planned.get("refill"),
                "gate_b": gate_b,
                "engine": {"root": "engine", "code_sha256": engine["code_sha256"], "git_commit": engine["git_commit"],
                           "recipe": f"engine/{P.RECIPE_REL}", "recipe_sha256": P.RECIPE_SHA256,
                           "files": len(engine["files"])},
                "pins": pins, "documents": planned.get("documents"), "resume": resume_entry,
                "granite_tokens": check_granite_tokens(planned.get("granite_tokens"))}
    if secret_hits_bytes(canonical_bytes(manifest), patterns):
        raise Refusal("a secret pattern is in the job manifest")
    (stage / MANIFEST_NAME).write_bytes(canonical_bytes(manifest))
    return manifest


def pins_record() -> dict:
    """The judges' pins, for the manifest, the bundle record and the summary. Granite: the lead's backend's pins
    (granite_pod.pins(); its guardian_config names "harm", the lead's default, and the screen passes "sexual_content"
    too)."""
    return {"granite": {**granite_pod.pins(), "criteria": list(P.CRITERIA),
                        "backend": f"granite_pod.judge_triples (scripts/gate_b_mac_judges, {P.LEAD_COMMIT})",
                        "convention_sha256": P.SECOND_JUDGE_PROBE_SHA256,
                        "retry": "one, a second judge_triples call of an unparsed label (the lead's API has no reset)"},
            "qwen3guard": {"repo": P.QWEN_REPO, "revision": P.QWEN_REVISION, "recipe": P.RECIPE_REL,
                           "recipe_sha256": P.RECIPE_SHA256, "guard_spec": dict(P.QWEN_GUARD_SPEC),
                           "files": {k: v[1] for k, v in sorted(P.QWEN_FILES.items())}},
            "known_answer": {"gate": "the lead's (pod_job.known_answer_gate, run by pod_run_granite.sh)",
                             "unit": P.KA_UNIT_NAME, "complete_sha256": P.KA_COMPLETE_SHA256,
                             "reference_sha256": P.KA_REFERENCE_SHA256, "n": P.KA_N, "mac_yes": P.KA_MAC_YES,
                             "rule": R.KA_RULE},
            "lead_files": dict(P.LAUNCHER_PINS), "spec_sha256": P.SPEC_SHA256, "rules_v2_sha256": P.RULES_SHA256}


# ---------------------------------------------------------------- pod side

def load_manifest(root: pathlib.Path) -> tuple[dict, str]:
    data = (pathlib.Path(root) / MANIFEST_NAME).read_bytes()
    try:
        manifest = json.loads(data)
    except ValueError:
        raise Refusal(f"{MANIFEST_NAME} is not JSON") from None
    if not isinstance(manifest, dict) or manifest.get("kind") != KIND or manifest.get("version") != VERSION:
        raise Refusal(f"{MANIFEST_NAME} is not a {KIND} version {VERSION}")
    return manifest, sha256_bytes(data)


def bundle_code_identity(root: pathlib.Path) -> str:
    """The engine's own code_identity(), computed over the bundle's copy (its common.py loaded from the bundle)."""
    import importlib.util
    path = pathlib.Path(root) / "engine/experiments/safety_selection/common.py"
    spec = importlib.util.spec_from_file_location("_screen_bundle_engine_common", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.code_identity()["sha256"]


def verify_gate_b(root: pathlib.Path, manifest: dict) -> dict:
    """The lead's Granite bundle in root/gate_b: the lead's own bundle.verify_bundle (every file of its manifest by
    SHA-256, the pinned tokenizer folder, the gate's reference, unit and dev bank), its manifest the one this bundle
    recorded, no requested unit, the gate on with the pinned reference and unit, and every lead file pinned. Returns
    the lead's manifest (with "manifest_sha256")."""
    entry = manifest.get("gate_b") or {}
    lead = lead_bundle.verify_bundle(pathlib.Path(root) / GATE_B)
    ka = lead.get("known_answers") or {}
    if (entry.get("dir") != GATE_B or lead["manifest_sha256"] != entry.get("manifest_sha256")
            or lead.get("judge") != GRANITE or lead.get("groups") != [] or lead.get("limit") is not None):
        raise Refusal("gate_b is not the lead's Granite bundle this bundle recorded (manifest, judge, no units)")
    if (ka.get("reference_sha256"), (ka.get("unit") or {}).get("complete_sha256")) != (P.KA_REFERENCE_SHA256,
                                                                                       P.KA_COMPLETE_SHA256):
        raise Refusal("gate_b's known-answer gate is off, or not the pinned reference and unit")
    for rel, digest in lead["files"].items():
        pin = lead_pin_of(rel)
        if pin is not None and digest != P.LAUNCHER_PINS.get(pin):
            raise Refusal(f"{GATE_B}/{rel} is not the lead's pinned {pin}")
    return lead


def verify_bundle(root: pathlib.Path) -> dict:
    """Refuses unless root holds exactly the manifest's files with their SHA-256 and every pin agrees (the lead's
    bundle in gate_b/ included). Returns the manifest with "manifest_sha256" added. Run from a bundle (the pod), the
    engine on sys.path must be the bundle's."""
    root = pathlib.Path(root)
    manifest, msha = load_manifest(root)
    listed = manifest.get("files")
    if not isinstance(listed, dict) or not listed:
        raise Refusal(f"{MANIFEST_NAME} lists no files")
    on_disk = {p.relative_to(root).as_posix() for p in root.rglob("*") if p.is_file()} - {MANIFEST_NAME}
    if on_disk != set(listed):
        raise Refusal(f"the bundle holds {len(on_disk)} files, its manifest lists {len(listed)}; unlisted "
                      f"{sorted(on_disk - set(listed))[:5]}, absent {sorted(set(listed) - on_disk)[:5]}")
    for rel, digest in sorted(listed.items()):
        if sha256_file(root / rel) != digest:
            raise Refusal(f"bundle file {rel} does not match its SHA-256")
    round_ = manifest.get("round")
    if round_ not in P.ROUND_SOURCES or [s["source"] for s in manifest["sources"]] != list(P.ROUND_SOURCES[round_]):
        raise Refusal("the manifest's round and sources do not match")
    for s in manifest["sources"]:
        if listed.get(s["path"]) != s["sha256"] or s["path"] != DATA_NAME[s["source"]]:
            raise Refusal(f"{s['source']}: the data file is not the one the manifest names")
        if s["source"] in P.DATA_PINS and (s["sha256"], s["rows"]) != P.DATA_PINS[s["source"]]:
            raise Refusal(f"{s['source']}: the data file is not the pinned one")
    verify_gate_b(root, manifest)
    check_granite_tokens(manifest.get("granite_tokens"))
    engine = manifest["engine"]
    if listed.get(engine["recipe"]) != P.RECIPE_SHA256:
        raise Refusal("the recipe config is not the pinned one")
    if bundle_code_identity(root) != engine["code_sha256"]:
        raise Refusal("the bundle's engine code identity differs from the packed one")
    if P.ON_POD:                                       # running from a bundle: the code imported is the code verified
        from experiments.safety_selection import prepare_task
        if not pathlib.Path(prepare_task.__file__).resolve().is_relative_to((root / "engine").resolve()):
            raise Refusal("the engine on sys.path is not the bundle's")
        if not pathlib.Path(granite_pod.__file__).resolve().is_relative_to((root / GATE_B).resolve()):
            raise Refusal("the lead's modules on sys.path are not the bundle's")
    for judge, entry in (manifest.get("resume") or {}).items():
        if judge != "from_tag" and listed.get(entry["path"]) != entry["sha256"]:
            raise Refusal(f"the resume cache of {judge} does not have its recorded SHA-256")
    return {**manifest, "manifest_sha256": msha}


def pod_sources(root: pathlib.Path, manifest: dict) -> dict:
    """{source: rows} read from the bundle (hash-checked again)."""
    return {s["source"]: R.read_rows(s["source"], pathlib.Path(root) / s["path"], s["sha256"], s["rows"],
                                     manifest["round"]) for s in manifest["sources"]}
