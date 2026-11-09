"""The 7-8B kit's state rule, Mac side (ruling 11 KD5; KCR §6; the user's 31 Oct rule on stopped pods; the PORT of the
OLMo 3 kit's runkit/family-probe-olmo3/states_tool.py, K2 of T4).

    python3.11 -B states_tool.py check HOST CHECKPOINT      unpack the newest states tar of HOST (host.py pull-states)
                                                            into retrieved/HOST/tree and verify every saved state of
                                                            CHECKPOINT against each unit's COMPLETE.json
    python3.11 -B states_tool.py rule                       print the rule
    python3.11 -B states_tool.py keep-list                  (R2 K2) every pod of this copy's block: stopped, e1 states
                                                            verified, and whether the a0 rule keeps it (no delete)
    python3.11 -B states_tool.py check-deletion-list FILE --sha256 H
                                                            (R2 K2) the lead's per-block deletion list, checked before
                                                            the user is asked for a yes by pod name

R2 K2 (Part 2 §2.6; DESO2 item 31; plan-ab item 11): the lead's per-block deletion list {kind "stage1-78b deletion list",
version 1, block, pods: [HOST, ...], backup: {tag, manifest: {path, sha256}}, utc, recorded_by} names EVERY stopped pod
of the block (a pod launched: hosts/HOST/pod.json), so one user yes by pod name covers them all; each pod's e1 states
verified by this tool's check (a states-e1-check record with at least one verified unit) when it ran a state-keeping
job; the verified backup's manifest.json at its SHA-256, of that release tag. A pod that holds an a0 e1 state at
1104-1107 (block A's a0-1104, block B's a0-1105 to -1107) is kept until the references at that seed have used it: every
reference job (ref_eval, safe_lora) of the family's block-B copy (tmp/<prefix><F>-B/plan.json) at that seed recorded
complete, and at least one there; a list that names such a pod refuses. The kit still has no delete command.

The rule (KD5: "50 GB volumes with a free-space check before each job; the state rule of the OLMo 3 kit: pull the e1
states, verified backup, then the user's yes by pod name before any delete; the kit has no delete command"; KCR §6:
states live only on the pod's volume, about $0.33 per stopped 50 GB pod per day):
  1. the finisher pulls the light tar (no model states), then, while the pod still has its SSH address, pulls every
     unit's states/e1/ (host.py pull-states HOST e1: the adapter, the optimizer moments and the RNG files) and runs
     this check; only then does it stop the pod. The result is finished.json's "states" entry; a pull or check that
     fails leaves the status review-needed-stopped and the states on the pod's volume;
  2. when that entry is not verified, the lead repeats the pull by hand: the user starts the stopped pod (the console,
     or a zero-GPU resume on the user's yes, as stage 1 did on 30 Oct), then host.py get HOST, host.py pull-states
     HOST e1, states_tool.py check HOST e1, host.py stop HOST. A failed check is a refusal, never a delete;
  3. the pulled states (the states-e1-*.tar, which the finisher never removes) go into the next verified backup
     (backup_records_stage1.py --states; download-back hashes checked);
  4. the stopped pod is deleted only after that backup is verified and the user says yes to that pod by name. This
     kit has no delete command and no start command; host.py stop is its only stop.
What the records leave open (reported, not decided here): whether the init and q states are pulled too (block A's
reference phase needs the a0 e1 adapters; nothing names init or q for N's R arms), and the backup's name and date.
host.py pull-states is the launch path's port (K3; the OLMo 3 kit's host.py:335-360): until it lands, the finisher's
pull records "unknown command" and the states stay on the volume (the safe failure of step 1).

The check: the newest retrieved/HOST/states-CHECKPOINT-*.tar is unpacked (members under round1/<unit>/states/
CHECKPOINT/ only; anything else refuses) into retrieved/HOST/tree, beside the light pull; then for every unit of the
tree that lists a states/CHECKPOINT/ file in its COMPLETE.json, every such file must be present with its SHA-256. A
unit that saved no CHECKPOINT state is recorded as "not saved" and skipped; the check refuses when no unit lists the
checkpoint, and when the tar holds a unit the tree does not verify. The result is one canonical JSON record,
retrieved/HOST/states-CHECKPOINT-check-<stamp>.json (written once; names, counts, hashes and byte sizes only: no
evaluation value is read, COMPLETE.json is read for its ``complete`` flag and its ``files`` hashes), and the line
"states verified: N units" or a refusal (exit 2).
"""
import datetime as dt, hashlib, json, pathlib, re, sys, tarfile

sys.dont_write_bytecode = True
HERE = pathlib.Path(__file__).resolve().parent
CHECKPOINTS = ("init", "q", "e1")
MEMBER = re.compile(r"^round1/[A-Za-z0-9._-]+/states/(init|q|e1)(/[A-Za-z0-9._-]+)?$")
RECORD_KIND = "stage1-78b state rule (KD5): pulled states verified against each unit's COMPLETE.json"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def newest_tar(host: str, checkpoint: str) -> pathlib.Path:
    tars = sorted((HERE / "retrieved" / host).glob(f"states-{checkpoint}-*.tar"))
    if not tars:
        raise SystemExit(f"{host}: no states-{checkpoint}-*.tar under retrieved/{host}: run host.py pull-states first")
    return tars[-1]


def unpack(tar_path: pathlib.Path, tree: pathlib.Path, checkpoint: str) -> list[str]:
    """Extract the states members only; a member outside round1/<unit>/states/CHECKPOINT/ refuses."""
    names = []
    with tarfile.open(tar_path) as archive:
        for member in archive.getmembers():
            match = MEMBER.match(member.name)
            if not match or match.group(1) != checkpoint:
                raise SystemExit(f"{tar_path.name}: a member is outside round1/*/states/{checkpoint}/: refused")
            names.append(member.name)
        tree.mkdir(parents=True, exist_ok=True)
        archive.extractall(tree, filter="data")
    return names


NOT_SAVED = "not saved"


def verify(tree: pathlib.Path, checkpoint: str, tar_units: set[str] | None = None) -> dict:
    """Every file a unit's COMPLETE.json lists under states/CHECKPOINT/ is present with its hash. A unit that lists no
    such file saved no CHECKPOINT state and is recorded as NOT_SAVED; the check refuses when no unit lists the
    checkpoint, and when the tar holds a unit the tree does not verify."""
    results = {}
    for marker in sorted((tree / "round1").glob("*/COMPLETE.json")):
        unit = marker.parent
        record = json.loads(marker.read_text())
        if record.get("complete") is not True:
            raise SystemExit(f"{unit.name}: COMPLETE.json is not a complete seal")
        listed = {rel: digest for rel, digest in (record.get("files") or {}).items()
                  if rel.startswith(f"states/{checkpoint}/")}
        if not listed:
            results[unit.name] = NOT_SAVED
            continue
        bad = [rel for rel, digest in listed.items() if not (unit / rel).is_file() or sha256(unit / rel) != digest]
        if bad:
            raise SystemExit(f"{unit.name}: {len(bad)} state file(s) missing or changed under states/{checkpoint}/")
        results[unit.name] = {"files": len(listed), "bytes": sum((unit / rel).stat().st_size for rel in listed)}
    if not results:
        raise SystemExit("no sealed unit under round1/ in the tree: run the finisher's light pull first")
    verified = [name for name, result in results.items() if result != NOT_SAVED]
    if not verified:
        raise SystemExit(f"no unit of the tree lists a states/{checkpoint}/ file in its COMPLETE.json")
    extra = sorted(name for name in (tar_units or ()) if name not in verified)
    if extra:
        raise SystemExit(f"the tar holds states/{checkpoint}/ of {len(extra)} unit(s) the tree does not seal with that "
                         f"checkpoint: {', '.join(extra[:5])}")
    return results


def verified_count(results: dict) -> int:
    return sum(1 for result in results.values() if result != NOT_SAVED)


def check(host: str, checkpoint: str) -> int:
    if checkpoint not in CHECKPOINTS:
        raise SystemExit(f"checkpoint must be one of {', '.join(CHECKPOINTS)}")
    tar_path = newest_tar(host, checkpoint)
    tree = HERE / "retrieved" / host / "tree"
    if not (tree / "round1").is_dir():
        raise SystemExit(f"{host}: no retrieved/{host}/tree/round1: run the finisher's light pull first")
    members = unpack(tar_path, tree, checkpoint)
    results = verify(tree, checkpoint, {name.split("/")[1] for name in members})
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    record = {"kind": RECORD_KIND, "version": 2, "host": host, "checkpoint": checkpoint, "tar": tar_path.name,
              "tar_sha256": sha256(tar_path), "members": len(members), "units": results,
              "verified_units": verified_count(results), "utc": stamp}
    out = HERE / "retrieved" / host / f"states-{checkpoint}-check-{stamp}.json"
    with out.open("x") as handle:
        handle.write(json.dumps(record, indent=1, sort_keys=True) + "\n")
    print(f"states verified: {verified_count(results)} units ({out.name})")
    return 0


# ----- R2 K2: the per-block deletion list (Part 2 §2.6; DESO2 item 31) -----------------------------------------------
COPY_RE = re.compile(r"^family-probe-s78-(olmo2-7b|llama31-8b)-([0-9A-Za-z][0-9A-Za-z-]*)$")
LIST_KIND = "stage1-78b deletion list"
LIST_KEYS = ("kind", "version", "block", "pods", "backup", "utc", "recorded_by")
STATE_KINDS = frozenset({"arm", "a0_arm", "retrain", "a1_pass", "o_only_with_regenerate", "c0", "ref_train",
                         "ref_train_bqi"})        # the kinds that leave training states on the pod's volume
KEPT_A0_SEEDS = (1104, 1105, 1106, 1107)          # Part 2 §2.6: kept until the references at that seed used them
REF_KINDS = ("ref_eval", "safe_lora")             # the references that read a seed's a0 e1 adapter (Part 2 §3.2)


def copy_identity(here: pathlib.Path | None = None) -> tuple[str, str]:
    m = COPY_RE.match(pathlib.Path(here or HERE).name)
    if not m:
        raise SystemExit("this folder is not a 7-8B working copy tmp/family-probe-s78-<family>-<block>/ (KD7)")
    return m.group(1), m.group(2)


def load_plan(folder: pathlib.Path) -> dict:
    try:
        return json.loads((folder / "plan.json").read_text())
    except (OSError, ValueError):
        raise SystemExit(f"{folder.name}: no readable plan.json") from None


def verified_states(host: str) -> bool:
    """A states-e1-check record of this tool for HOST with at least one verified unit."""
    for path in sorted((HERE / "retrieved" / host).glob("states-e1-check-*.json")):
        try:
            doc = json.loads(path.read_text())
        except (OSError, ValueError):
            continue
        if doc.get("kind") == RECORD_KIND and doc.get("host") == host and doc.get("checkpoint") == "e1" and \
                isinstance(doc.get("verified_units"), int) and doc["verified_units"] >= 1:
            return True
    return False


def refs_done(family: str, seed: int) -> bool:
    """Every reference job (REF_KINDS) of the family's block-B copy at ``seed`` recorded complete, at least one."""
    folder = HERE.parent / f"family-probe-s78-{family}-B"
    if not (folder / "plan.json").is_file():
        return False
    plan = load_plan(folder)
    refs = [j for h in (plan.get("hosts") or {}).values() for j in h.get("jobs") or []
            if j.get("kind") in REF_KINDS and j.get("seed") == seed]
    return bool(refs) and all(j.get("status") == "complete" for j in refs)


def keep_list() -> dict:
    """Every pod of this copy's block: launched (stopped pods keep their volume), e1 states verified, and the a0 rule's
    hold (kept_until), names only."""
    family, block = copy_identity()
    plan = load_plan(HERE)
    out = {}
    for host, h in sorted((plan.get("hosts") or {}).items()):
        if h.get("block") != block:
            continue
        a0_seeds = sorted({j.get("seed") for j in h.get("jobs") or [] if j.get("arm") == "a0" and
                           j.get("kind") in ("a0_arm", "o_only_with_regenerate") and j.get("seed") in KEPT_A0_SEEDS})
        held = [s for s in a0_seeds if not refs_done(family, s)]
        out[host] = {"launched": (HERE / "hosts" / host / "pod.json").is_file(),
                     "keeps_states": any(j.get("kind") in STATE_KINDS for j in h.get("jobs") or []),
                     "states_verified": verified_states(host),
                     "kept_until": [f"the references at seed {s} have used its a0 e1 state" for s in held]}
    return {"family": family, "block": block, "pods": out}


def check_deletion_list(path: str, sha256: str) -> dict:
    """The lead's deletion list (module doc, "R2 K2"), refused unless every rule holds; names and counts only."""
    p = pathlib.Path(path)
    if not p.is_file() or sha256 != hashlib.sha256(p.read_bytes()).hexdigest():
        raise SystemExit("the deletion list is missing or its SHA-256 differs from the one given")
    try:
        doc = json.loads(p.read_text())
    except ValueError:
        raise SystemExit("the deletion list is not JSON") from None
    family, block = copy_identity()
    if not isinstance(doc, dict) or set(doc) != set(LIST_KEYS) or doc.get("kind") != LIST_KIND or \
            doc.get("version") != 1 or type(doc.get("version")) is not int:
        raise SystemExit(f"not a {LIST_KIND!r} version 1 (exactly {list(LIST_KEYS)})")
    if doc["block"] != block:
        raise SystemExit(f"the list is block {doc['block']!r}'s; this copy is {family}'s block {block} (one list per "
                         "block, in its own copy)")
    if not all(isinstance(doc[k], str) and doc[k].strip() for k in ("utc", "recorded_by")):
        raise SystemExit("the list needs utc and recorded_by")
    pods = doc["pods"]
    if not isinstance(pods, list) or len(set(map(str, pods))) != len(pods):
        raise SystemExit("pods is a list of distinct host names")
    info = keep_list()["pods"]
    stopped = sorted(h for h, x in info.items() if x["launched"])
    if sorted(pods) != stopped:
        missing, extra = sorted(set(stopped) - set(pods)), sorted(set(pods) - set(stopped))
        raise SystemExit(f"the list must name every stopped pod of block {block} and no other (DESO2 item 31): "
                         f"missing {missing}, not a stopped pod of this block {extra}")
    bad = sorted(h for h in pods if info[h]["keeps_states"] and not info[h]["states_verified"])
    if bad:
        raise SystemExit(f"{len(bad)} pod(s) whose e1 states are not verified (states_tool.py check HOST e1): {bad}")
    kept = sorted(h for h in pods if info[h]["kept_until"])
    if kept:
        raise SystemExit(f"{len(kept)} pod(s) hold an a0 e1 state at 1104-1107 that a reference has not used yet "
                         f"(Part 2 §2.6): {kept}")
    backup = doc["backup"]
    manifest = backup.get("manifest") if isinstance(backup, dict) else None
    if not (isinstance(backup, dict) and set(backup) == {"tag", "manifest"} and isinstance(backup["tag"], str)
            and isinstance(manifest, dict) and set(manifest) == {"path", "sha256"}):
        raise SystemExit("backup is {tag, manifest: {path, sha256}} (the verified backup's manifest.json)")
    m = pathlib.Path(str(manifest["path"]))
    if not m.is_file() or hashlib.sha256(m.read_bytes()).hexdigest() != manifest["sha256"]:
        raise SystemExit("the backup's manifest.json is missing or differs from its SHA-256")
    try:
        release = json.loads(m.read_text()).get("release")
    except (ValueError, AttributeError):
        release = None
    if release != backup["tag"]:
        raise SystemExit("the backup's manifest.json is not the named release tag's")
    return {"ok": True, "family": family, "block": block, "pods": len(pods),
            "note": "the user's yes by pod name, for these pods, before any delete (KD5); the kit deletes nothing"}


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args[:1] == ["rule"]:
        print(__doc__)
        return 0
    if len(args) == 3 and args[0] == "check":
        return check(args[1], args[2])
    if args == ["keep-list"]:
        print(json.dumps(keep_list(), indent=1, sort_keys=True))
        return 0
    if len(args) == 4 and args[0] == "check-deletion-list" and args[2] == "--sha256":
        print(json.dumps(check_deletion_list(args[1], args[3]), sort_keys=True))
        return 0
    raise SystemExit("usage: states_tool.py check HOST CHECKPOINT | rule | keep-list | "
                     "check-deletion-list FILE --sha256 H")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(2)
        raise
