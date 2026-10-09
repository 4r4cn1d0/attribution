"""The screen's bundle: planned and staged on the Mac, verified and read on the pod.

Rebuilt 9 October 2026 (10:27 UTC, clock checked) from the lead's partial build. Mac side (screen_pod.py bundle and
launch): every input is checked against its pin before anything is built:
  - the specification and the rules (SCREEN-SPEC.md 19cae3e1..., rules-v2.json c23672cf...): a changed file refuses
    until this build is checked against it again;
  - round 1: dark.jsonl and light.jsonl (SHA-256 and 5,000 rows each, exactly the four fields, a book category of the
    file's arm) and the Dolly baseline, the prepared set's engine/train_rows.jsonl (manifest.sha256 = SHA-256 of
    manifest.json = 9ed61826...; the manifest lists the file at 1efa8571...; 4,800 rows); rounds 2 and 3: the refill
    file refill-rN.jsonl that sf_screen.py wrote, whose SHA-256 the lead gives on the command line (the four fields
    plus slot_arm, slot_line and rank), and the refill report sf_screen.py wrote beside it, which must name that file,
    its SHA-256 and its row count, and the pinned sf_screen.py (165f1a30..., SCREEN-SPEC section 7) as its writer;
  - the known-answer unit 1101-a0-e1-a1 through units.py (COMPLETE.json 8f0fa83a..., job.json 3e60568a...; target e1,
    arm a0, seed 1101, the prepared manifest), its 200 greedy harm answers, their prompt ids in the dev bank
    (common.bank_prompts, manifest-checked), and the Mac's Granite labels of that unit (second-judge-probe-items.jsonl
    c2ef1130..., only its unit, prompt_id, target and granite fields are read: 93 yes, 107 no; the summary be2b4286...
    names the unit's job.json SHA-256);
  - the engine code: experiments/minimal_safety and experiments/safety_selection (.py, .json, .md, .lock; no
    __pycache__, no symlink), as the probe kits' pack_setup.py selects it, with its code identity
    (safety_selection.common.code_identity), which must be the pinned e49a978c..., the git commit, the SHA-256 of all
    shipped engine files and the engine files changed since commit 8801456; uncommitted engine files refuse, as in the
    kits; recipe B's config (a47138f2...) with the pinned guard block.
The bundle holds only: the screen's own files; gate_b_mac_judges' common.py and units.py; the engine code; the input
files; the known-answer unit's job.json, COMPLETE.json and eval/e1/generations.jsonl; the Mac labels as ids and labels
only (ka/mac-labels.json); the prepared set's manifest.sha256 and banks/dev.jsonl (the known answers' prompts, as the
HarmBench pod); optionally a resumed launch's two caches; and job-manifest.json (every other file's SHA-256). No
hidden or selector file, no other prepared file. Every staged file passes the kits' secret patterns (a hit refuses,
naming the file and the pattern only). The tar is gate_b_mac_judges/pod/bundle.write_tar's deterministic tar.gz.
Pod side: verify_bundle refuses unless the folder holds exactly the listed files with their SHA-256 and every pin
agrees; pod_sources and pod_ka read the rows and the known answers from it.
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
from common import Refusal, bank_prompts, canonical_bytes, jsonl_records, sha256_bytes, sha256_file  # noqa: E402
from units import Unit, load_items  # noqa: E402

KIND, VERSION, MANIFEST_NAME = "fiction-screen job manifest", 2, P.MANIFEST_NAME
TOOL_FILES = ("screen_pins.py", "screen_rows.py", "screen_models.py", "granite_screen.py", "guard_screen.py",
              "screen_job.py", "screen_bundle.py", "screen_run.sh", "granite-requirements.txt",
              "guard-requirements.txt", "llama-requirements.txt")
GATE_B_FILES = ("common.py", "units.py")
KA_FILES = ("job.json", "COMPLETE.json", "eval/e1/generations.jsonl")
DATA_NAME = {"dark": "data/dark.jsonl", "light": "data/light.jsonl", "dolly": "data/dolly-train_rows.jsonl",
             "refill": "data/refill.jsonl"}
KA_MAC_LABELS = "ka/mac-labels.json"
PREPARED_DIR = f"prepared/{P.PREPARED_NAME}"
RESUME = {"granite": "resume/granite.jsonl", "qwen": "resume/qwen.jsonl"}


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


def read_mac_labels(path: pathlib.Path, sha256: str, unit_name: str) -> dict:
    """{prompt id: Yes/No/invalid} of one unit in second_judge_probe's cache; only the unit, prompt_id, target and
    granite fields are read (the cache's `raw` field is never touched)."""
    data = pathlib.Path(path).read_bytes()
    if sha256_bytes(data) != sha256:
        raise Refusal("the Mac Granite labels file does not have its pinned SHA-256")
    labels = {}
    for lineno, entry in jsonl_records(data, "Mac Granite labels"):
        if not isinstance(entry, dict) or entry.get("unit") != unit_name:
            continue
        pid = entry.get("prompt_id")
        if not isinstance(pid, str) or pid in labels or entry.get("target") != "e1":
            raise Refusal(f"Mac Granite labels: line {lineno} has no new e1 prompt id")
        labels[pid] = R.mac_label(entry.get("granite"))
    return labels


def check_mac_summary(path: pathlib.Path, sha256: str, unit_name: str, job_sha256: str) -> None:
    data = pathlib.Path(path).read_bytes()
    if sha256_bytes(data) != sha256:
        raise Refusal("the Mac Granite summary does not have its pinned SHA-256")
    unit = (json.loads(data).get("units") or {}).get(unit_name) or {}
    if (unit.get("job_sha256") != job_sha256 or unit.get("n") != P.KA_N or unit.get("granite_harm") != P.KA_MAC_YES
            or unit.get("unparsed") != 0):
        raise Refusal("the Mac Granite summary does not name this unit's job.json with 200 labels and 93 yes")


def ka_plan(unit_dir: pathlib.Path = None, prepared: pathlib.Path = None) -> dict:
    """The known-answer unit and labels, checked (ids and hashes only)."""
    from units import enumerate_units
    unit_dir = pathlib.Path(P.KA_UNIT if unit_dir is None else unit_dir)
    prepared = pathlib.Path(P.PREPARED if prepared is None else prepared)
    (unit,), _ = enumerate_units((), [unit_dir], ("e1",))
    if (unit.complete_sha256, unit.job_sha256) != (P.KA_COMPLETE_SHA256, P.KA_JOB_SHA256):
        raise Refusal("the known-answer unit's COMPLETE.json or job.json is not the pinned one")
    if (unit.arm, unit.seed, unit.target, unit.manifest_sha256) != ("a0", 1101, "e1", P.PREPARED_MANIFEST):
        raise Refusal("the known-answer unit is not a0, seed 1101, e1, on the pinned prepared manifest")
    items = load_items(unit, "greedy")
    ids = [it.prompt_id for it in items]
    if len(ids) != P.KA_N or len(set(ids)) != P.KA_N:
        raise Refusal(f"the known-answer unit has {len(ids)} greedy harm answers, not {P.KA_N} distinct ones")
    missing = sorted(set(ids) - set(bank_prompts(prepared, P.PREPARED_MANIFEST)))
    if missing:
        raise Refusal(f"{len(missing)} known-answer prompt ids are not in the dev bank (first {missing[0]})")
    labels = read_mac_labels(P.KA_MAC_ITEMS, P.KA_MAC_ITEMS_SHA256, unit.name)
    if set(labels) != set(ids):
        raise Refusal("the Mac labels do not cover exactly the known-answer unit's 200 prompt ids")
    if sum(v == "Yes" for v in labels.values()) != P.KA_MAC_YES:
        raise Refusal(f"the Mac labels do not give {P.KA_MAC_YES} yes")
    check_mac_summary(P.KA_MAC_SUMMARY, P.KA_MAC_SUMMARY_SHA256, unit.name, unit.job_sha256)
    return {"unit": unit, "labels": dict(sorted(labels.items())),
            "answer_sha256": {it.prompt_id: it.answer_sha256 for it in items}}


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
    """The speed stop's ratio r, from the bundle's own inputs, with the Granite tokenizer and template (the Mac's pinned
    tokenizer folder; transformers renders and counts it as the Mac judge venv does, checked on 600 items):
      - fiction: the mean tokens one Granite call evaluates over this round's selected Granite rows, the `harm` call
        its whole template, the `sexual_content` call only the tokens after the prefix it shares with the `harm`
        call of the same row (the screen calls them in that order, so llama.cpp reuses that prefix);
      - known answers: the mean template tokens of the 200 known answers (each a new conversation);
      - r = fiction mean / known-answer mean.
    Counts only (no text kept or printed). Cached per input hashes in this process."""
    import granite_screen as G
    tok_dir = pathlib.Path(P.MAC_GRANITE_TOKENIZER if tok_dir is None else tok_dir)
    found = {f.name: (f.stat().st_size, sha256_file(f)) for f in tok_dir.iterdir() if f.is_file()}
    if found != P.GRANITE_TOK_FILES:
        raise Refusal(f"{tok_dir.name}: the Granite tokenizer folder is not the ten pinned files")
    sources = {name: s for name, s in planned["sources"].items() if name in P.GRANITE_SOURCES}
    key = (tuple(sorted((name, s["sha256"]) for name, s in sources.items())), limit,
           planned["ka"]["unit"].complete_sha256, str(tok_dir))
    if key in _TOKEN_CACHE:
        return dict(_TOKEN_CACHE[key])
    tok = G.load_tokenizer(tok_dir)

    def ids(rendered):
        return tok(rendered, add_special_tokens=False)["input_ids"]
    per_call = []
    for s in sources.values():
        for row in G.selected(s["rows"], limit):
            harm = ids(G.granite_prompt(tok, row.user_turn, row.assistant_turn, "harm")[0])
            sexual = ids(G.granite_prompt(tok, row.user_turn, row.assistant_turn, "sexual_content")[0])
            shared = 0
            for a, b in zip(harm, sexual):
                if a != b:
                    break
                shared += 1
            per_call += [len(harm), len(sexual) - shared]
    unit = planned["ka"]["unit"]
    prompts = bank_prompts(P.PREPARED, P.PREPARED_MANIFEST)
    ka = [G.granite_prompt(tok, prompts[it.prompt_id], it.text, "harm")[1]
          for it in load_items(unit, "greedy", with_text=True)]
    if not per_call or len(ka) != P.KA_N:
        raise Refusal("no Granite call to count, or not 200 known answers")
    from importlib import metadata
    fiction, known = sum(per_call) / len(per_call), sum(ka) / len(ka)
    out = {"fiction_calls": len(per_call), "fiction_mean_tokens_per_call": round(fiction, 3),
           "ka_items": len(ka), "ka_mean_tokens": round(known, 3), "ratio": round(fiction / known, 6),
           "definition": "fiction: harm call whole template, sexual_content call tokens after the prefix shared with "
                         "the row's harm call; known answers: whole harm template",
           "tokenizer": {"transformers": metadata.version("transformers"), "tokenizers": metadata.version("tokenizers"),
                         "folder_files": "the ten pinned files"}}
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
    return {"round": round_, "sources": sources, "prepared": prepared_check(P.PREPARED), "ka": ka_plan(),
            "documents": documents, "refill": refill_info}


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
    for name in GATE_B_FILES:
        _copy(P.MAC_GATE_B / name, stage, f"gate_b/{name}", files, P.LAUNCHER_PINS[name])
    for rel, src in engine["files"].items():
        _copy(src, stage, f"engine/{rel}", files)
    if files[f"engine/{P.RECIPE_REL}"] != P.RECIPE_SHA256:
        raise Refusal("the recipe config does not have its pinned SHA-256")
    sources = []
    for source, entry in planned["sources"].items():
        rel = _copy(entry["path"], stage, DATA_NAME[source], files, entry["sha256"])
        sources.append({"source": source, "path": rel, "sha256": entry["sha256"], "rows": len(entry["rows"])})
    ka, unit = planned["ka"], planned["ka"]["unit"]
    for rel in KA_FILES:
        _copy(unit.path / rel, stage, f"ka/unit/{rel}", files)
    if (files["ka/unit/COMPLETE.json"], files["ka/unit/job.json"]) != (P.KA_COMPLETE_SHA256, P.KA_JOB_SHA256):
        raise Refusal("the known-answer unit changed after it was checked")
    if files["ka/unit/eval/e1/generations.jsonl"] != unit.files["generations"]["sha256"]:
        raise Refusal("the known-answer answers changed after they were checked")
    (stage / KA_MAC_LABELS).parent.mkdir(parents=True, exist_ok=True)
    (stage / KA_MAC_LABELS).write_bytes(canonical_bytes({
        "unit": unit.name, "complete_sha256": unit.complete_sha256, "source_sha256": P.KA_MAC_ITEMS_SHA256,
        "labels": ka["labels"], "answer_sha256": ka["answer_sha256"]}))
    files[KA_MAC_LABELS] = sha256_file(stage / KA_MAC_LABELS)
    prep = planned["prepared"]
    _copy(P.PREPARED / "manifest.sha256", stage, f"{PREPARED_DIR}/manifest.sha256", files)
    _copy(P.PREPARED / P.DEV_BANK_REL, stage, f"{PREPARED_DIR}/{P.DEV_BANK_REL}", files, prep["dev_bank_sha256"])
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
                "ka": {"unit": {"host": unit.host, "unit": unit.unit, "dir": "ka/unit", "arm": unit.arm,
                                "seed": unit.seed, "target": unit.target, "complete_sha256": unit.complete_sha256,
                                "job_sha256": unit.job_sha256, "completed_utc": unit.completed_utc,
                                "manifest_sha256": unit.manifest_sha256,
                                "generations": "ka/unit/eval/e1/generations.jsonl"},
                       "mac_labels": KA_MAC_LABELS, "n": P.KA_N, "mac_yes": P.KA_MAC_YES,
                       "prepared": {**prep, "dir": PREPARED_DIR}},
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
    """The judges' pins, for the manifest, the bundle record and the summary."""
    return {"granite": {"gguf_repo": P.GRANITE_GGUF_REPO, "gguf_revision": P.GRANITE_GGUF_REVISION,
                        "gguf_file": P.GRANITE_GGUF_FILE, "gguf_sha256": P.GRANITE_GGUF_SHA256,
                        "tokenizer_repo": P.GRANITE_TOK_REPO, "tokenizer_revision": P.GRANITE_TOK_REVISION,
                        "tokenizer_files": {k: v[1] for k, v in sorted(P.GRANITE_TOK_FILES.items())},
                        "criteria": list(P.CRITERIA), "n_ctx": P.N_CTX, "new_tokens": P.NEW_TOKENS, "seed": P.SEED,
                        "convention_sha256": P.SECOND_JUDGE_PROBE_SHA256, "retry": "one, after llm.reset()"},
            "llama_cpp_python": {"version": P.LLAMA_VERSION, "sdist_sha256": P.LLAMA_SDIST_SHA256,
                                 "cmake_args": P.LLAMA_CMAKE_ARGS},
            "qwen3guard": {"repo": P.QWEN_REPO, "revision": P.QWEN_REVISION, "recipe": P.RECIPE_REL,
                           "recipe_sha256": P.RECIPE_SHA256, "guard_spec": dict(P.QWEN_GUARD_SPEC),
                           "files": {k: v[1] for k, v in sorted(P.QWEN_FILES.items())}},
            "known_answer": {"unit": P.KA_UNIT_NAME, "complete_sha256": P.KA_COMPLETE_SHA256, "n": P.KA_N,
                             "mac_yes": P.KA_MAC_YES, "rule": R.KA_RULE},
            "spec_sha256": P.SPEC_SHA256, "rules_v2_sha256": P.RULES_SHA256}


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


def verify_bundle(root: pathlib.Path) -> dict:
    """Refuses unless root holds exactly the manifest's files with their SHA-256 and every pin agrees. Returns the
    manifest with "manifest_sha256" added. Run from a bundle (the pod), the engine on sys.path must be the bundle's."""
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
    for name in GATE_B_FILES:
        if listed.get(f"gate_b/{name}") != P.LAUNCHER_PINS[name]:
            raise Refusal(f"gate_b/{name} is not the pinned one")
    unit = manifest["ka"]["unit"]
    if (listed.get("ka/unit/COMPLETE.json"), listed.get("ka/unit/job.json")) != (P.KA_COMPLETE_SHA256,
                                                                                  P.KA_JOB_SHA256):
        raise Refusal("the known-answer unit is not the pinned one")
    complete = json.loads((root / "ka/unit/COMPLETE.json").read_bytes())
    job = json.loads((root / "ka/unit/job.json").read_bytes())
    if (complete.get("complete") is not True or complete.get("job_sha256") != P.KA_JOB_SHA256
            or (complete.get("files") or {}).get("eval/e1/generations.jsonl") != listed.get(unit["generations"])
            or (job.get("arm"), job.get("seed"), job.get("target_checkpoint"), job.get("manifest_sha256"))
            != ("a0", 1101, "e1", P.PREPARED_MANIFEST) or unit["complete_sha256"] != P.KA_COMPLETE_SHA256):
        raise Refusal("the known-answer unit's COMPLETE.json and job.json do not agree with its record")
    prep = manifest["ka"]["prepared"]
    if ((root / PREPARED_DIR / "manifest.sha256").read_text(encoding="utf-8").strip() != P.PREPARED_MANIFEST
            or listed.get(f"{PREPARED_DIR}/{P.DEV_BANK_REL}") != prep["dev_bank_sha256"]):
        raise Refusal("the prepared set's manifest or dev bank is not the recorded one")
    labels = json.loads((root / KA_MAC_LABELS).read_bytes())
    values = list((labels.get("labels") or {}).values())
    if (len(values) != P.KA_N or sum(v == "Yes" for v in values) != P.KA_MAC_YES
            or labels.get("complete_sha256") != P.KA_COMPLETE_SHA256
            or set(labels.get("answer_sha256") or {}) != set(labels.get("labels") or {})):
        raise Refusal("the Mac labels are not the unit's 200 labels with 93 yes")
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
    for judge, entry in (manifest.get("resume") or {}).items():
        if judge != "from_tag" and listed.get(entry["path"]) != entry["sha256"]:
            raise Refusal(f"the resume cache of {judge} does not have its recorded SHA-256")
    return {**manifest, "manifest_sha256": msha}


def pod_sources(root: pathlib.Path, manifest: dict) -> dict:
    """{source: rows} read from the bundle (hash-checked again)."""
    return {s["source"]: R.read_rows(s["source"], pathlib.Path(root) / s["path"], s["sha256"], s["rows"],
                                     manifest["round"]) for s in manifest["sources"]}


def pod_ka(root: pathlib.Path, manifest: dict) -> tuple[list, dict]:
    """The known answers (prompt id, answer SHA-256, user turn, assistant turn), sorted by prompt id as
    second_judge_probe judged them, and the Mac labels; the answers load through units.load_items, the prompts
    through common.bank_prompts."""
    root = pathlib.Path(root).absolute()
    e = manifest["ka"]["unit"]
    listed = manifest["files"]
    unit = Unit(host=e["host"], unit=e["unit"], path=root / e["dir"], kind="run-one", arm=e["arm"], seed=e["seed"],
                target=e["target"], complete_sha256=e["complete_sha256"], job_sha256=e["job_sha256"],
                completed_utc=e["completed_utc"], manifest_sha256=e["manifest_sha256"],
                files={"generations": {"path": str(root / e["generations"]), "sha256": listed[e["generations"]]},
                       "samples": None, "guard": None, "guard_samples": None})
    items = load_items(unit, "greedy", with_text=True)
    prompts = bank_prompts(root / PREPARED_DIR, P.PREPARED_MANIFEST)
    mac = json.loads((root / KA_MAC_LABELS).read_bytes())
    if {it.prompt_id: it.answer_sha256 for it in items} != mac["answer_sha256"]:
        raise Refusal("the known answers' SHA-256 differ from the ones the Mac labels were recorded with")
    ka_items = sorted((it.prompt_id, it.answer_sha256, prompts[it.prompt_id], it.text) for it in items)
    return ka_items, dict(mac["labels"])
