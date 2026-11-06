"""The 7-8B kit's state rule, Mac side (ruling 11 KD5; KCR §6; the user's 31 Oct rule on stopped pods; the PORT of the
OLMo 3 kit's runkit/family-probe-olmo3/states_tool.py, K2 of T4).

    python3.11 -B states_tool.py check HOST CHECKPOINT      unpack the newest states tar of HOST (host.py pull-states)
                                                            into retrieved/HOST/tree and verify every saved state of
                                                            CHECKPOINT against each unit's COMPLETE.json
    python3.11 -B states_tool.py rule                       print the rule

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


def main(argv=None) -> int:
    args = argv if argv is not None else sys.argv[1:]
    if args[:1] == ["rule"]:
        print(__doc__)
        return 0
    if len(args) == 3 and args[0] == "check":
        return check(args[1], args[2])
    raise SystemExit("usage: states_tool.py check HOST CHECKPOINT | states_tool.py rule")


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(2)
        raise
