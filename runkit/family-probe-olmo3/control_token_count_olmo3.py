"""The ids-only control-token count for OLMo 3 units (O3A §16.1 "Control tokens (reported, F L351)"; stdlib; python3.11).

    python3.11 -B control_token_count_olmo3.py --unit UNIT [--unit UNIT ...] --out FILE

scripts/family_probe_reading.py knows the families olmo2 and llama3 only; for OLMo 3 it runs with family None and
prints no control-token report (FPR:86, :432). That report gates nothing. This script fills the gap without touching
FPR: for every sealed unit given (a round1/<name> folder with COMPLETE.json), and every evaluation it holds (eval/init,
eval/e1), it counts the answers whose ``output_ids`` hold any of OLMo 3's control ids (O3A §16.1):
<|im_start|> 100264, the FIM ids 100258-100260, <|endofprompt|> 100276 and the four function tags 100266-100269
(<|im_end|> 100265 and <|endoftext|> 100257 are stops, so they end an answer and are absent from its ids). Greedy
answers are the harm-kind rows of generations.jsonl, sampled answers the rows of samples.jsonl, as FPR counts them.

It reads ``output_ids`` and ``kind`` only; it never reads, prints or copies an answer's text. Each file it reads must
be listed in the unit's COMPLETE.json with the SHA-256 it has now (a changed or unlisted file refuses). The output is
one canonical JSON record (sorted keys), written once (exclusive create) and printed: counts per unit, evaluation,
kind and id. Exit 2 on a refusal.
"""
import argparse, hashlib, json, pathlib, sys

sys.dont_write_bytecode = True
CONTROL_IDS = {"<|fim_prefix|>": 100258, "<|fim_middle|>": 100259, "<|fim_suffix|>": 100260, "<|im_start|>": 100264,
               "<functions>": 100266, "</functions>": 100267, "<function_calls>": 100268, "</function_calls>": 100269,
               "<|endofprompt|>": 100276}
EVALUATIONS = ("init", "e1")
FILES = {"greedy": "generations.jsonl", "sampled": "samples.jsonl"}
HARM_KIND = "harm"


def sha256(path: pathlib.Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sealed_files(unit: pathlib.Path) -> dict:
    """The unit's COMPLETE.json file table (relative path -> SHA-256); a missing or malformed marker refuses."""
    marker = unit / "COMPLETE.json"
    if not marker.is_file():
        raise SystemExit(f"{unit.name}: no COMPLETE.json: not a sealed unit")
    record = json.loads(marker.read_text())
    files = record.get("files")
    if record.get("complete") is not True or not isinstance(files, dict):
        raise SystemExit(f"{unit.name}: COMPLETE.json is malformed")
    return files


def ids_of_rows(path: pathlib.Path, greedy: bool) -> list[list[int]]:
    """The output ids of every counted row of one answer file (the harm kind only for the greedy file); nothing else
    of a row is kept."""
    rows = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        row = json.loads(line)
        if greedy and row.get("kind") != HARM_KIND:
            continue
        ids = row.get("output_ids")
        if not isinstance(ids, list) or not all(isinstance(i, int) for i in ids):
            raise SystemExit(f"{path.parent.parent.parent.name}/{path.parent.name}/{path.name}: a row has no integer output_ids")
        rows.append(ids)
    return rows


def count_answers(rows: list[list[int]]) -> dict:
    wanted = set(CONTROL_IDS.values())
    return {"answers": len(rows),
            "answers_with_control_ids": sum(bool(wanted.intersection(ids)) for ids in rows),
            "answers_per_control_id": {name: sum(i in ids for ids in rows) for name, i in sorted(CONTROL_IDS.items())}}


def count_unit(unit: pathlib.Path) -> dict:
    files = sealed_files(unit)
    out = {}
    for evaluation in EVALUATIONS:
        folder = unit / "eval" / evaluation
        if not folder.is_dir():
            continue
        counts = {}
        for kind, name in FILES.items():
            rel = f"eval/{evaluation}/{name}"
            path = folder / name
            if rel not in files:
                raise SystemExit(f"{unit.name}: {rel} is not listed in COMPLETE.json")
            if not path.is_file() or sha256(path) != files[rel]:
                raise SystemExit(f"{unit.name}: {rel} is missing or differs from its sealed hash")
            counts[kind] = count_answers(ids_of_rows(path, kind == "greedy"))
        out[evaluation] = counts
    if not out:
        raise SystemExit(f"{unit.name}: no eval/init or eval/e1 folder")
    return out


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--unit", action="append", required=True, help="a sealed unit folder (round1/<name>)")
    ap.add_argument("--out", required=True, help="the record to write (refuses to overwrite)")
    a = ap.parse_args(argv)
    units = [pathlib.Path(u).resolve() for u in a.unit]
    record = {"kind": "OLMo 3 ids-only control-token count (reported, not gating; O3A §16.1; FPR runs with family None)",
              "version": 1, "control_ids": dict(sorted(CONTROL_IDS.items())), "reads": "output_ids and kind only",
              "units": {u.name: count_unit(u) for u in units},
              "script_sha256": sha256(pathlib.Path(__file__).resolve())}
    text = json.dumps(record, indent=1, sort_keys=True) + "\n"
    out = pathlib.Path(a.out)
    try:
        with out.open("x") as handle:
            handle.write(text)
    except FileExistsError:
        raise SystemExit(f"{out} exists: the count is written once") from None
    print(text, end="")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except SystemExit as exc:
        if isinstance(exc.code, str):
            print(exc.code, file=sys.stderr)
            sys.exit(2)
        raise
