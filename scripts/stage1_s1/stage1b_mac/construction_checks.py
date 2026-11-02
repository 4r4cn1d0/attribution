"""The construction-check runner (addendum section 40 point 4; CHECK section 4 item 1 and section 6 step 3). After the
stage-1 reading it runs the W1 plant-rank report (scripts/stage1/report_plant_ranks.py, REQ-29; pinned in the W1
manifest, never edited) WITHOUT --counted, into a folder whose own name holds "plant" (git-ignored, for example
tmp/stage1b/plant-construction-checks/), after making the two Mac scorer outputs the report needs when they are not
given: DataShield-style (scripts/stage1/score_datashield.py, REQ-12) and L1's score (scripts/stage1/score_l1_larf.py
score, REQ-10), each from REQ-3's pod output.

    python -B -m scripts.stage1_s1.stage1b_mac.construction_checks --repo DIR --kit DIR [--block A] [--host a-8] \\
        --expect-seal-sha256 H --prepared DIR --plant-pool FILE --decoy-pool FILE [--l1 PATH:SHA256] \\
        [--datashield PATH:SHA256] --out DIR --record FILE [--rules FILE] [--expect-rules-sha256 H]

**Inputs, each by exact path and SHA-256 (a mismatch or a missing file refuses before anything runs):**
- the rules module (default the repository's runkit/stage1-olmo/stage1_rules.py; executed by path, as the reading
  does) at --expect-rules-sha256 when the lead gives it (else its SHA-256 is only recorded); it holds the pins;
- the three W1 scripts on disk hash to the W1 manifest's entries (MAN1 at rules.MAN1_PATH, itself at rules.MAN1_SHA256),
  and so does every W1 file the report and the scorers can execute or read: each MAN1 entry under scripts/stage1/
  of role code, settings or pinned input (the report imports s1common, build_plant, representation_pass and others,
  and reads labels.json and its settings);
- REQ-8's record at rules.D2_REQ8_RECORD (path, sha256) and the plant and decoy pools (the lead's paths) at
  rules.D2_POOLS; nothing in them is parsed here;
- pod a-8's outputs (REQ-3's rows file and summary, J5; the L1 scan, J7; REQ-23's classifier output, J8) through the
  kit's own records read by key: plan.json's host entry (done; the one complete, pulled job of each kind; its recorded
  ``outputs`` {relpath: sha256}, as record-done keeps them from JOB-DONE.json) at the job runner's folders
  (job-I/representation for the main pass, job-I/l1-scan, job-I/classifier), each file re-hashed in the pulled tree
  KIT/retrieved/HOST/tree and found once in the block seal (KIT/<plan.seals[BLOCK].path>, at plan.json's and the
  lead's --expect-seal-sha256) as a sealed entry of that host with that SHA-256. No folder is listed.
- ``--l1`` and ``--datashield``, when given, are existing scorer outputs (PATH:SHA256; re-hashed); when not given, the
  scorers make them here, inside the "plant" folder.
- ``--record`` is a path free of the words the path rule protects (so the lead can open and commit it; the "plant"
  folder's own name holds one, so the record cannot lie inside it), and does not exist yet.

**Run.** Each step is a subprocess (this interpreter, -B, cwd --repo) with stdout and stderr captured as bytes into
OUT/log/<step>.log, never shown. A step that exits non-zero stops the run (exit 1; no record). The reason is printed
only when the step's last stderr line is one of the pinned W1 scripts' value-free refusal lines: their main frames
print a refusal as "REFUSED: <message> (nothing written)", and the set of messages raised as one string literal (never
an f-string, a concatenation or a variable) is fixed by the pinned code, not by any input; any other last line is
withheld. A step's output file must exist and hash to the SHA-256 the script printed for it. Printed here: each
input's and output's SHA-256, each step's exit code, the record's path and SHA-256. No value, name, unit, leaf, cell
or row id is printed.

**The hash record** (--record, canonical JSON, exclusive create) holds the inputs' and outputs' SHA-256, the steps'
exit codes and commands, the kit's plan and seal SHA-256, the pins, the W1 tree's entry count and digest, this
package's module hashes and the time; no text of any input or output. The lead commits and time-stamps it; "published
before the pilot" is read as that committed, stamped SHA-256 (section 40 point 4). The "plant" folder is opened only
after the counted outputs are hashed, or after a final "stop".

Exit: 0 done; 1 a step failed after something was written (the log and the step's files stay in the "plant" folder;
the record is not written); 2 refused before anything ran (nothing written), or, after the steps, the record could
not be written (a disk fault: the "plant" folder stays, the lead clears it).
"""

from __future__ import annotations

import argparse
import ast
import builtins
import importlib.util
import os
import platform
import subprocess
import sys
from pathlib import Path

from experiments.safety_selection.common import canonical_json
from scripts.stage1_s1.stage1b_mac.common import (Refusal, hashed_pair, is_hex64, json_object, module_hashes,
                                                 read_bytes, read_pinned, run_frame, sha256_bytes, utc_now,
                                                 write_exclusive)

REPO = Path(__file__).resolve().parents[3]
RULES = REPO / "runkit" / "stage1-olmo" / "stage1_rules.py"
RULES_NAMES = ("D2_REQ8_RECORD", "D2_POOLS", "MAN1_PATH", "MAN1_SHA256")
PROTECTED_WORDS = ("plant", "decoy")      # the path rule: a path holding either is never opened, listed or committed
PLANT_WORD = PROTECTED_WORDS[0]
RECORD_KIND = "stage1b construction checks hash record"
SEAL_KIND = "stage1 block seal"                                      # runkit/stage1-olmo/seal.py SEAL_KIND

# The W1 scripts (MAN1 role "code") and the file names their code fixes (a test holds them to the modules' constants).
REPORT_SCRIPT = "scripts/stage1/report_plant_ranks.py"               # report_plant_ranks.OUTPUT
DATASHIELD_SCRIPT = "scripts/stage1/score_datashield.py"             # score_datashield.OUTPUT
L1_SCRIPT = "scripts/stage1/score_l1_larf.py"                        # score_l1_larf.SCORES_FILE (subcommand score)
S1COMMON = "scripts/stage1/s1common.py"                              # the helpers whose refusals the scripts raise
W1_SCRIPTS = (REPORT_SCRIPT, DATASHIELD_SCRIPT, L1_SCRIPT)
MESSAGE_SOURCES = (REPORT_SCRIPT, DATASHIELD_SCRIPT, L1_SCRIPT, S1COMMON)
# The W1 tree the report and the scorers can execute or read: MAN1's entries under scripts/stage1/ of these roles
# (tests, mutation specs and the README are listed with other roles and are not run here).
W1_PREFIX = "scripts/stage1/"
W1_ROLES = ("code", "settings", "pinned input")
NOTHING_WRITTEN = " (nothing written)"                               # the W1 main frames' refusal line ending
REPORT_OUT, DATASHIELD_OUT, L1_OUT = "plant_ranks.json", "datashield_scores.json", "l1_scores.json"
ROWS_FILE, SUMMARY_FILE = "representation_rows.jsonl", "representation_pass.json"   # representation_pass.ROWS_FILE, SUMMARY_FILE
SCAN_FILE, CLASSIFIER_OUT = "l1_scan.json", "classifier_scores.json"                # score_l1_larf.SCAN_FILE, score_classifier.OUTPUT
# The pod's outputs: (job kind, the job runner's --out folder under job-I, the file). The main representation pass
# (job_runner_stage1.job_commands: f"{out}/representation"), not the s3-orig pools-only pass beside it.
POD_INPUTS = {"rows": ("rep_pass", "representation", ROWS_FILE), "summary": ("rep_pass", "representation", SUMMARY_FILE),
              "l1_scan": ("l1_scan", "l1-scan", SCAN_FILE), "classifier": ("classifier", "classifier", CLASSIFIER_OUT)}
STEP_OUT = {"datashield": DATASHIELD_OUT, "l1": L1_OUT, "report": REPORT_OUT}


# ----- the pins and the kit's records ---------------------------------------------------------------------------------


def load_rules(path: Path, expect: str | None):
    """The kit's rules module by path (executed, never edited) and its SHA-256, checked against --expect-rules-sha256
    when the lead gives it; it must hold the pins used here."""
    if expect is not None and not is_hex64(expect):
        raise Refusal("--expect-rules-sha256 is not 64 lowercase hex")
    data = read_pinned(path, expect, "the rules module") if expect is not None else read_bytes(path, "the rules module")
    spec = importlib.util.spec_from_file_location("stage1_rules_for_stage1b_mac", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    for name in RULES_NAMES:
        if not hasattr(module, name):
            raise Refusal("the rules module lacks a pin this runner needs")
    return module, sha256_bytes(data)


def w1_pins(repo: Path, rules) -> dict:
    """The W1 tree on disk at the W1 manifest's entries (MAN1 at its pin): {"scripts": {path: SHA-256} of the three
    scripts, "tree": the count and digest of every entry checked (code, settings, pinned input under scripts/stage1/),
    "sources": {path: bytes} of the scripts whose refusal messages may be printed}."""
    man1 = json_object(read_pinned(repo / rules.MAN1_PATH, rules.MAN1_SHA256, "the W1 manifest"), "the W1 manifest")
    listed = [e for e in (man1.get("entries") or []) if isinstance(e, dict)]
    entries = {e.get("path"): e for e in listed}
    scripts = {}
    for rel in W1_SCRIPTS:
        entry = entries.get(rel)
        if entry is None or entry.get("role") != "code" or not is_hex64(entry.get("sha256")):
            raise Refusal("the W1 manifest lists no code entry for a script this runner needs")
        read_pinned(repo / rel, entry["sha256"], "a W1 script")
        scripts[rel] = entry["sha256"]
    checked, sources = [], {}
    for e in listed:
        rel = e.get("path")
        if not isinstance(rel, str) or not rel.startswith(W1_PREFIX) or e.get("role") not in W1_ROLES:
            continue
        if not is_hex64(e.get("sha256")):
            raise Refusal("a W1 manifest entry names no SHA-256")
        data = read_pinned(repo / rel, e["sha256"], "a W1 file")
        checked.append([rel, e["sha256"]])
        if rel in MESSAGE_SOURCES:
            sources[rel] = data
    if set(sources) != set(MESSAGE_SOURCES):
        raise Refusal("the W1 manifest lists no code entry for a script this runner needs")
    tree = {"entries": len(checked), "roles": list(W1_ROLES), "sha256": sha256_bytes(canonical_json(sorted(checked)))}
    return {"scripts": scripts, "tree": tree, "sources": sources}


def pod_inputs(kit: Path, block: str, host: str, expect_seal: str) -> dict:
    """{name: (path, sha256)} of the pod's outputs, plus the plan's and the seal's SHA-256 and the paths read."""
    if not is_hex64(expect_seal):
        raise Refusal("--expect-seal-sha256 is not 64 lowercase hex")
    plan_bytes = read_bytes(kit / "plan.json", "the kit's plan.json")
    plan = json_object(plan_bytes, "the kit's plan.json")
    seal_entry = (plan.get("seals") or {}).get(block)
    if not isinstance(seal_entry, dict) or not isinstance(seal_entry.get("path"), str) \
            or seal_entry.get("sha256") != expect_seal:
        raise Refusal("plan.json records no seal of the block at the expected SHA-256")
    seal = json_object(read_pinned(kit / seal_entry["path"], expect_seal, "the block seal"), "the block seal")
    if seal.get("kind") != SEAL_KIND or seal.get("block") != block or not isinstance(seal.get("files"), list):
        raise Refusal("the block seal is not the kit's seal record of the block")
    sealed = {}
    for e in seal["files"]:
        if isinstance(e, dict) and e.get("host") == host:
            sealed.setdefault(e.get("path"), []).append(e)
    h = (plan.get("hosts") or {}).get(host)
    if not isinstance(h, dict) or h.get("block") != block or h.get("done") is not True:
        raise Refusal("plan.json does not record the host as a done host of the block")
    jobs = h.get("jobs") or []
    out, paths = {}, {}
    for name, (kind, folder, file) in POD_INPUTS.items():
        found = [(i, j) for i, j in enumerate(jobs) if isinstance(j, dict) and j.get("kind") == kind
                 and j.get("status") == "complete" and j.get("pulled") is not False]
        if len(found) != 1:
            raise Refusal("plan.json records no single complete, pulled job of a kind this runner needs")
        index, job = found[0]
        rel = f"job-{index}/{folder}/{file}"
        digest = (job.get("outputs") or {}).get(rel)
        if not is_hex64(digest):
            raise Refusal("the job's recorded outputs do not list a file this runner needs")
        path = kit / "retrieved" / host / "tree" / rel
        read_pinned(path, digest, "a pod output")
        entries = sealed.get(rel, [])
        if len(entries) != 1 or entries[0].get("class") != "sealed" or entries[0].get("sha256") != digest:
            raise Refusal("the block seal lists no single sealed entry for a pod output at its recorded SHA-256")
        out[name], paths[name] = (path, digest), f"{host}:{rel}"
    return {"inputs": out, "paths": paths, "plan_sha256": sha256_bytes(plan_bytes), "seal_sha256": expect_seal}


def pinned_inputs(repo: Path, rules, plant_pool: Path, decoy_pool: Path) -> dict[str, tuple[Path, str]]:
    """REQ-8's record and the two pools at the rules' pins (hashed only, never parsed)."""
    pin = rules.D2_REQ8_RECORD
    pools = rules.D2_POOLS
    if not isinstance(pin, dict) or not isinstance(pin.get("path"), str) or not is_hex64(pin.get("sha256")) \
            or not isinstance(pools, dict) or not all(is_hex64(pools.get(k)) for k in ("plant", "decoy")):
        raise Refusal("the rules module's pins are not of the expected form")
    record = repo / pin["path"]
    read_pinned(record, pin["sha256"], "REQ-8's record")
    read_pinned(plant_pool, pools["plant"], "the plant pool")
    read_pinned(decoy_pool, pools["decoy"], "the decoy pool")
    return {"plant_record": (record, pin["sha256"]), "plant_pool": (Path(plant_pool), pools["plant"]),
            "decoy_pool": (Path(decoy_pool), pools["decoy"])}


def given_output(spec: str | None, what: str) -> tuple[Path, str] | None:
    """An existing scorer output given as PATH:SHA256, re-hashed; None when not given."""
    if spec is None:
        return None
    path, digest = hashed_pair(spec, what)
    read_pinned(path, digest, what)
    return path, digest


def check_out_folder(out: Path) -> None:
    """The folder's own name holds "plant" (the path rule protects what is written there); absent or empty."""
    if PLANT_WORD not in out.name:
        raise Refusal("the output folder's name does not hold the word the path rule protects")
    if out.exists() and (not out.is_dir() or any(out.iterdir())):
        raise Refusal("the output folder exists and is not empty")


def check_record_path(record_path: Path) -> None:
    """The hash record's path holds neither protected word (the lead opens and commits the record; this also keeps it
    out of the output folder, whose name holds "plant"), names no existing file, and its folder, when present, is a
    folder (it is created before the steps, so a late failure cannot leave the steps' files without a record)."""
    if any(word in str(record_path.resolve()).lower() for word in PROTECTED_WORDS):
        raise Refusal("the hash record's path holds a word the path rule protects")
    if record_path.exists():
        raise Refusal("the hash record exists: it is written once")
    if record_path.parent.exists() and not record_path.parent.is_dir():
        raise Refusal("the hash record's folder is not a folder")


# ----- the value-free refusal lines of the pinned W1 scripts --------------------------------------------------------


def _is_refusal(func) -> bool:
    name = func.attr if isinstance(func, ast.Attribute) else (func.id if isinstance(func, ast.Name) else None)
    return name == "Refusal"


def value_free_messages(sources: dict[str, bytes]) -> frozenset[str]:
    """The refusal lines the pinned W1 scripts can print that carry no value: "REFUSED: <message> (nothing written)"
    for every Refusal the sources raise with exactly one string literal (an f-string, a concatenation or a variable is
    left out), and the same line with a built-in OSError type name (the frames print an OSError by type). The set is
    fixed by the pinned code."""
    out = set()
    for rel, data in sources.items():
        for node in ast.walk(ast.parse(data, filename=rel)):
            if isinstance(node, ast.Call) and _is_refusal(node.func) and not node.keywords and len(node.args) == 1 \
                    and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
                out.add(f"REFUSED: {node.args[0].value}{NOTHING_WRITTEN}")
    for name, obj in vars(builtins).items():
        if isinstance(obj, type) and issubclass(obj, OSError):
            out.add(f"REFUSED: {name}{NOTHING_WRITTEN}")
    return frozenset(out)


def known_reason(stderr: str, messages: frozenset[str]) -> str | None:
    """A failed step's last non-blank stderr line when it is one of the value-free lines; else None (withheld)."""
    lines = [line.strip() for line in stderr.splitlines() if line.strip()]
    return lines[-1] if lines and lines[-1] in messages else None


# ----- the commands (pure; a test parses them with the W1 scripts' own parsers) -------------------------------------


def _ps(pair: tuple[Path, str]) -> str:
    return f"{pair[0]}:{pair[1]}"


def scorer_commands(repo: Path, prepared: Path, pod: dict, out: Path, *, l1_given: bool, datashield_given: bool) -> dict:
    """{step: argv} for the scorers that are not given, in run order (the script path first)."""
    rows, summary = _ps(pod["rows"]), _ps(pod["summary"])
    cmds = {}
    if not datashield_given:
        cmds["datashield"] = [str(repo / DATASHIELD_SCRIPT), "--prepared", str(prepared), "--rows", rows,
                              "--summary", summary, "--out", str(out / "datashield")]
    if not l1_given:
        cmds["l1"] = [str(repo / L1_SCRIPT), "score", "--prepared", str(prepared), "--scan", _ps(pod["l1_scan"]),
                      "--rows", rows, "--summary", summary, "--out", str(out / "l1")]
    return cmds


def report_command(repo: Path, prepared: Path, pinned: dict, pod: dict, l1: tuple, datashield: tuple, out: Path) -> list:
    """The plant-rank report's argv: every construction-check input, no --counted (section 40 point 4)."""
    return [str(repo / REPORT_SCRIPT), "--prepared", str(prepared), "--plant-record", _ps(pinned["plant_record"]),
            "--plant-pool", _ps(pinned["plant_pool"]), "--decoy-pool", _ps(pinned["decoy_pool"]),
            "--rows", _ps(pod["rows"]), "--summary", _ps(pod["summary"]), "--l1", _ps(l1),
            "--datashield", _ps(datashield), "--classifier", _ps(pod["classifier"]), "--out", str(out / "report")]


# ----- the run --------------------------------------------------------------------------------------------------------


def run_step(name: str, argv: list, repo: Path, log_dir: Path) -> tuple[int, str, str]:
    """One subprocess; its stdout and stderr go to the log only, as bytes (so any output is logged). Returns
    (exit code, stdout, stderr) as text, undecodable bytes replaced."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    proc = subprocess.run([sys.executable, "-B", *argv], cwd=repo, env=env, capture_output=True)
    (log_dir / f"{name}.log").write_bytes(b"exit %d\n--- stdout ---\n%s\n--- stderr ---\n%s"
                                          % (proc.returncode, proc.stdout, proc.stderr))
    return proc.returncode, proc.stdout.decode("utf-8", "replace"), proc.stderr.decode("utf-8", "replace")


def printed_hash(stdout: str, file: str) -> str | None:
    """The SHA-256 a W1 script printed for ``file`` ("  <sha256>  <name>", s1common's callers), or None."""
    for line in stdout.splitlines():
        parts = line.split()
        if len(parts) == 2 and parts[1] == file and is_hex64(parts[0]):
            return parts[0]
    return None


def step_output(stdout: str, folder: Path, file: str) -> tuple[Path, str] | None:
    """(path, sha256) of the step's output when it exists and hashes to what the script printed; else None."""
    path = folder / file
    if path.is_symlink() or not path.is_file():
        return None
    digest = sha256_bytes(path.read_bytes())
    return (path, digest) if printed_hash(stdout, file) == digest else None


def build(args) -> int:
    repo, kit, out, record_path = Path(args.repo), Path(args.kit), Path(args.out), Path(args.record)
    prepared = Path(args.prepared)
    check_out_folder(out)
    check_record_path(record_path)
    if not prepared.is_dir():
        raise Refusal("the prepared folder is not a folder")
    rules, rules_sha = load_rules(Path(args.rules), args.expect_rules_sha256)
    w1 = w1_pins(repo, rules)
    messages = value_free_messages(w1["sources"])
    pinned = pinned_inputs(repo, rules, Path(args.plant_pool), Path(args.decoy_pool))
    pod = pod_inputs(kit, args.block, args.host, args.expect_seal_sha256)
    given = {"l1": given_output(args.l1, "--l1"), "datashield": given_output(args.datashield, "--datashield")}
    for rel, digest in w1["scripts"].items():
        print(f"w1 {rel} {digest}")
    inputs = {**{k: v[1] for k, v in pinned.items()}, **{k: v[1] for k, v in pod["inputs"].items()},
              "man1": rules.MAN1_SHA256, "w1_tree": w1["tree"]["sha256"], "rules": rules_sha,
              "plan": pod["plan_sha256"], "seal": pod["seal_sha256"]}
    for name, pair in given.items():
        if pair is not None:
            inputs[f"{name}_given"] = pair[1]
    for name, digest in inputs.items():
        print(f"input {name} {digest}")
    # nothing was written so far; from here the record's folder and the "plant" folder fill, and a failure leaves
    # the "plant" folder for the lead to clear
    record_path.parent.mkdir(parents=True, exist_ok=True)
    log_dir = out / "log"
    log_dir.mkdir(parents=True, exist_ok=True)
    steps, commands, outputs = [], {}, {}
    cmds = scorer_commands(repo, prepared, pod["inputs"], out, l1_given=given["l1"] is not None,
                           datashield_given=given["datashield"] is not None)
    made = dict(given)
    for name in ("datashield", "l1"):
        if name not in cmds:
            steps.append({"step": name, "made_here": False, "exit": None})
            continue
        made[name] = _run(name, cmds[name], repo, log_dir, out / name, steps, commands, outputs, messages)
        if made[name] is None:
            return 1
    report = report_command(repo, prepared, pinned, pod["inputs"], made["l1"], made["datashield"], out)
    if _run("report", report, repo, log_dir, out / "report", steps, commands, outputs, messages) is None:
        return 1
    doc = {"kind": RECORD_KIND, "version": 1, "utc": utc_now(), "block": args.block, "host": args.host,
           "inputs": dict(sorted(inputs.items())), "pod_paths": pod["paths"], "w1_scripts": w1["scripts"],
           "w1_tree": w1["tree"], "rules_pinned": args.expect_rules_sha256 is not None,
           "steps": steps, "commands": commands, "outputs": outputs, "out_folder": _rel(out, repo),
           "report_without_counted": "--counted" not in report, "modules": module_hashes(),
           "python": platform.python_version()}
    if not doc["report_without_counted"]:
        raise Refusal("the report command would carry --counted")      # never reached: report_command adds none
    digest = write_exclusive(record_path, canonical_json(doc), "the hash record")
    print(f"record {record_path} {digest}")
    return 0


def _run(name: str, argv: list, repo: Path, log_dir: Path, folder: Path, steps: list, commands: dict,
         outputs: dict, messages: frozenset[str]) -> tuple[Path, str] | None:
    """Run a step and account for it; None when it failed (the caller stops with exit 1). A failed step's reason is
    printed only when it is one of the pinned scripts' value-free refusal lines."""
    code, stdout, stderr = run_step(name, argv, repo, log_dir)
    commands[name] = [str(a) for a in argv]
    print(f"step {name} exit {code}")
    if code != 0:
        steps.append({"step": name, "made_here": True, "exit": code})
        print(f"FAILED: step {name} exited {code}; its log stays in the output folder (never opened); no record written",
              file=sys.stderr)
        reason = known_reason(stderr, messages)
        print(f"reason: {reason}" if reason is not None else
              "reason: withheld (the step's last message is not a value-free refusal of the pinned W1 scripts)",
              file=sys.stderr)
        return None
    pair = step_output(stdout, folder, STEP_OUT[name])
    if pair is None:
        steps.append({"step": name, "made_here": True, "exit": code, "output": "missing or not the printed SHA-256"})
        print(f"FAILED: step {name} left no output at the SHA-256 it printed; no record written", file=sys.stderr)
        return None
    steps.append({"step": name, "made_here": True, "exit": code})
    outputs[name] = {"file": f"{folder.name}/{STEP_OUT[name]}", "sha256": pair[1]}
    print(f"output {name} {pair[1]}")
    return pair


def _rel(path: Path, repo: Path) -> str:
    try:
        return path.resolve().relative_to(repo.resolve()).as_posix()
    except ValueError:
        return str(path)


def main(argv=None) -> int:
    def produce(argv):
        parser = argparse.ArgumentParser(prog="python -B -m scripts.stage1_s1.stage1b_mac.construction_checks",
                                         description=__doc__.split("\n\n")[0])
        parser.add_argument("--repo", default=str(REPO), help="the repository root (the W1 scripts, MAN1, REQ-8's record)")
        parser.add_argument("--kit", required=True, help="the kit folder (plan.json, seals/, retrieved/)")
        parser.add_argument("--block", default="A")
        parser.add_argument("--host", default="a-8")
        parser.add_argument("--expect-seal-sha256", required=True)
        parser.add_argument("--prepared", required=True)
        parser.add_argument("--plant-pool", required=True, help="REQ-8's 75-row plant pool (text; hashed only)")
        parser.add_argument("--decoy-pool", required=True, help="REQ-8's 37-row decoy pool (text; hashed only)")
        parser.add_argument("--l1", help="an existing L1 scorer output, PATH:SHA256")
        parser.add_argument("--datashield", help="an existing DataShield-style scorer output, PATH:SHA256")
        parser.add_argument("--out", required=True, help="a folder whose name holds \"plant\"; absent or empty")
        parser.add_argument("--record", required=True, help="the hash record to write (outside --out; no protected word)")
        parser.add_argument("--rules", default=str(RULES))
        parser.add_argument("--expect-rules-sha256", help="the rules module's SHA-256 (optional; recorded either way)")
        return build(parser.parse_args(argv))
    return run_frame(produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
