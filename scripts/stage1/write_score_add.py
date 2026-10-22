"""The score-to-add writer (REQ-11's selection; REQ-7's write_add_edit.py then makes the add edit). Mac, $0.

    python scripts/stage1/write_score_add.py --scorer s3 --scores PATH:SHA256 --candidates PATH:SHA256 --full-out DIR
        --out DIR

From an add scorer output (by SHA-256: kind "stage1 add scorer output", the scorer named in the settings, high = add)
and the candidate text file (by SHA-256: a stage-1 text pool or prompt list that holds every scored id with its prompt
and response; for S3, REQ-6's s3_safe pool, whose SHA-256 the scorer output must name), the writer selects the k ids
with the largest scores (S3: 48); ties go by the sealed rank of the scorer's registry key over the scored ids (S3:
s3.ties). It writes the selected rows, in selection order, as the stage-1 prompt list the settings name (S3: "s3"), the
input of REQ-7, under --full-out (which must lie in a folder named tmp), and the text-free ``<scorer>_add_selection.json``
into --out (the selected ids and scores, the boundary ties, the scorer output's reports, provenance).
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "write_score_add.json"
SETTINGS_SHA256 = "0c1679b47cdbdc340bfa7f959d94c818a84a144dff114991382349b621c5ba74"
SETTINGS_NAME = "write_score_add"
CANDIDATE_KINDS = ("stage1 text pool", "stage1 prompt list")


def read_pinned(pair: tuple[Path, str], what: str) -> bytes:
    path, digest = pair
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def build(*, scorer: str, scores: tuple[Path, str], candidates: tuple[Path, str], settings: dict,
          settings_sha256: str) -> tuple[dict[str, bytes], dict[str, bytes]]:
    s1.check_settings(settings, SETTINGS_NAME)
    spec = settings["scorers"].get(scorer)
    if spec is None:
        raise s1.Refusal(f"no scorer {scorer!r} in the settings")
    doc = s1.strict_json(read_pinned(scores, "the scorer output"))
    schema = settings["scorer_output"]
    if not isinstance(doc, dict) or (doc.get("kind"), doc.get("version"), doc.get("scorer")) != \
            (schema["kind"], schema["version"], scorer):
        raise s1.Refusal(f"not a version-{schema['version']} add scorer output of {scorer}")
    if doc.get("orientation") != spec["orientation"]:
        raise s1.Refusal("the scorer output states another orientation than the settings")
    if doc.get("candidate_pool_sha256") != candidates[1]:
        raise s1.Refusal("the candidate file is not the pool the scorer output names")
    cand = s1.strict_json(read_pinned(candidates, "the candidate file"))
    if not isinstance(cand, dict) or cand.get("kind") not in CANDIDATE_KINDS or not isinstance(cand.get("items"), list):
        raise s1.Refusal("the candidate file is not a stage-1 text pool or prompt list")
    by_id = {}
    for item in cand["items"]:
        if not isinstance(item, dict) or not isinstance(item.get("prompt"), str) or not isinstance(item.get("response"), str):
            raise s1.Refusal("candidate items need a text prompt and response")
        by_id[item["id"]] = item
    checked = s1.check_scores(doc["scores"])
    absent = [i for i in checked if i not in by_id]
    if absent:
        raise s1.Refusal(f"{len(absent)} scored ids are not in the candidate file")
    selected = s1.select_top(checked, spec["k"], spec["ties"])
    listing = {"kind": "stage1 prompt list", "version": 1, "name": spec["list_name"],
               "items": [{"id": i, "prompt": by_id[i]["prompt"], "response": by_id[i]["response"]} for i in selected]}
    list_bytes = canonical_json(listing)
    record = {"kind": "stage1 add selection", "version": 1, "scorer": scorer, "requirement": spec["requirement"],
              "rule": spec["rule"], "k": spec["k"], "selected": selected,
              "scores": {i: checked[i] for i in selected}, "ranked": len(checked),
              "boundary_ties": s1.boundary_ties(checked, selected),
              "list": {"file": f"{spec['list_name']}.json", "name": spec["list_name"], "sha256": sha256_bytes(list_bytes)},
              "reports": doc.get("reports"),
              "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                          {"scorer_output": scores[1], "candidates": candidates[1]},
                                          settings["label_entries"])}
    record_bytes = canonical_json(record)
    if s1._text_hits(record_bytes, [t for i in selected for t in (by_id[i]["prompt"], by_id[i]["response"])]):
        raise s1.Refusal("the record would hold text")
    return {f"{spec['list_name']}.json": list_bytes}, {f"{scorer}_add_selection.json": record_bytes}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--scorer", required=True)
    parser.add_argument("--scores", required=True, help="PATH:SHA256")
    parser.add_argument("--candidates", required=True, help="PATH:SHA256")
    parser.add_argument("--full-out", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)

        def pair(spec):
            path, _, sha = spec.rpartition(":")
            if not path or not s1.HEX64.match(sha):
                raise s1.Refusal("--scores and --candidates are PATH:SHA256")
            return Path(path), sha
        from scripts.stage1.build_s_pool import full_out_ok

        full_out = full_out_ok(args.full_out)
        full, record = build(scorer=args.scorer, scores=pair(args.scores), candidates=pair(args.candidates),
                             settings=settings, settings_sha256=digest)
        written = s1.write_new_files(full_out, full)
        written.update(s1.write_new_files(args.out.resolve(), record))
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
