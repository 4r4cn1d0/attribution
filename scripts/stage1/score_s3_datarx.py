"""REQ-11: S3, DataRx-style (RS B8; SPEC sections 3.4-3.6; lead decisions L10, L14 (1); Mac, $0; model-agnostic; it
reads REQ-3's pod output). The selection itself is write_score_add.py's; REQ-7 makes the add edit.

    python scripts/stage1/score_s3_datarx.py --rows PATH:SHA256 --summary PATH:SHA256 --s-pool-record PATH:SHA256
        --answers-record PATH:SHA256 --out DIR

Inputs, each by SHA-256: REQ-3's rows file and summary from the pass that scored the pools ``s3_safe`` (REQ-6's: the S3
subset and S1's rows outside it, with the PKU-safe response y^safe) and ``s3_orig`` (REQ-9's: the same prompts with the
untuned answer y^orig, ids ``<id>:orig``); REQ-6's ``s_pool_record.json`` (the S3 subset's and S1's ids, the s3_safe
pool's SHA-256); REQ-9's ``untuned_answers_record.json`` (per id: capped, lexicon class, encode_train; the s3_orig pool's
SHA-256). The summary must list both pools with exactly those SHA-256s.

For a candidate x and a response d, h^l = read (a) at hidden-state index l = 1..n (the embedding output excluded; index n
is the final-norm output, L4); C_r^l and C_c^l are REQ-3's safe and harmful anchor means; s^l(d) = cos(h^l, C_r^l) -
cos(h^l, C_c^l), that is cos_safe - cos_harmful; R(d) = the mean over l = 1..n; SAS(x) = R(x, y^safe) - R(x, y^orig). A
y^orig that encode_train refused (so absent from s3_orig) leaves the ranking and is counted (L14 (1)). Only the S3
subset is ranked; S1's rows (inside or outside the subset) get their SAS reported.

Writes ``s3_scores.json``: the add scorer output (scorer s3, high = add, scores over the ranked ids) with each scored id's
per-layer s^l for both responses (text-free floats) and the reports: S1's SAS, |S1 & S3 subset|, the share of the
subset's y^orig that the lexicon calls REFUSAL-OPENING, the capped count, the ids leaving the ranking.
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "score_s3_datarx.json"
SETTINGS_SHA256 = "6382dcc663e80ecab332ecf96b7cba621e3e535408481e6ab83ca614bc2b502f"
SETTINGS_NAME = "score_s3_datarx"
OUTPUT = "s3_scores.json"
ORIG_SUFFIX = ":orig"


def read_pinned(pair: tuple[Path, str], what: str) -> bytes:
    path, digest = pair
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != digest:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, expected {digest}")
    return data


def per_layer(line: dict, n: int, read: int) -> list[float]:
    """s^l = cos_safe - cos_harmful at read (a), l = 1..n."""
    return [float(line["cos_safe"][l][read]) - float(line["cos_harmful"][l][read]) for l in range(1, n + 1)]


def sas_of(safe: list[float], orig: list[float]) -> float:
    return math.fsum(safe) / len(safe) - math.fsum(orig) / len(orig)


def build(*, rows: tuple[Path, str], summary: tuple[Path, str], s_pool_record: tuple[Path, str],
          answers_record: tuple[Path, str], settings: dict, settings_sha256: str) -> dict[str, bytes]:
    from scripts.stage1 import representation_pass as rp

    s1.check_settings(settings, SETTINGS_NAME)
    summary_doc = s1.strict_json(read_pinned(summary, "REQ-3's summary"))
    rows_bytes = read_pinned(rows, "REQ-3's rows file")
    pool_rec = s1.strict_json(read_pinned(s_pool_record, "REQ-6's record"))
    ans_rec = s1.strict_json(read_pinned(answers_record, "REQ-9's record"))
    if summary_doc.get("kind") != "stage1 representation pass" or summary_doc["rows"]["sha256"] != rows[1]:
        raise s1.Refusal("the rows file is not the one REQ-3's summary names")
    if summary_doc["provenance"]["settings_sha256"] != settings["pins"]["representation_pass_settings_sha256"]:
        raise s1.Refusal("REQ-3's summary was not made with the pinned REQ-3 settings")
    if pool_rec.get("kind") != "stage1 s-pool record" or ans_rec.get("kind") != "stage1 untuned answers record":
        raise s1.Refusal("the S-pool record or the answers record is not of its kind")
    s3_entry = ans_rec.get("lists", {}).get("s3")
    if not isinstance(s3_entry, dict):
        raise s1.Refusal("REQ-9's record holds no s3 list")
    expected_pools = {"s3_safe": pool_rec["s3_pool"]["sha256"], "s3_orig": s3_entry["s3_orig_pool_sha256"]}
    listed = {p["name"]: p["sha256"] for p in summary_doc.get("pools", [])}
    for name, digest in expected_pools.items():
        if listed.get(name) != digest:
            raise s1.Refusal(f"REQ-3's summary does not list pool {name} with the SHA-256 its builder recorded")
    if s3_entry.get("list_sha256") != pool_rec["s3_pool"]["sha256"]:                    # RB-1: the chain REQ-6 -> REQ-9
        raise s1.Refusal("REQ-9's s3 list is not REQ-6's s3_safe pool (its list_sha256 differs from s3_pool.sha256)")
    n = summary_doc["layout"]["n_layers"]
    read = rp.READS.index(settings["read"])
    safe, orig = {}, {}
    for line in s1.iter_jsonl_bytes(rows_bytes, "REQ-3's rows file"):
        if line.get("source") == "s3_safe":
            safe[line["id"]] = per_layer(line, n, read)
        elif line.get("source") == "s3_orig":
            if not line["id"].endswith(ORIG_SUFFIX):
                raise s1.Refusal("an s3_orig row id does not end with ':orig'")
            orig[line["id"][:-len(ORIG_SUFFIX)]] = per_layer(line, n, read)
    subset = pool_rec["lists"]["s3_subset"]["ids"]
    s1_ids = pool_rec["lists"]["s1"]["ids"]
    missing_safe = [i for i in sorted(set(subset) | set(s1_ids)) if i not in safe]
    if missing_safe:
        raise s1.Refusal(f"{len(missing_safe)} rows of the S3 subset or S1 have no s3_safe features (REQ-3 refused them)")
    leaving = sorted(i for i in subset if i not in orig)
    scores = {i: sas_of(safe[i], orig[i]) for i in subset if i in orig}
    s1.check_scores(scores)
    rows_by_id = {r["id"]: r for r in s3_entry["rows"]}
    in_subset = [rows_by_id[i] for i in subset if i in rows_by_id]
    if len(in_subset) != len(subset):
        raise s1.Refusal("REQ-9's record does not hold every S3 subset id")
    reports = {"s1_sas": {i: (sas_of(safe[i], orig[i]) if i in orig else None) for i in s1_ids},
               "s1_and_s3_subset": len(set(s1_ids) & set(subset)),
               "y_orig_refusal_opening_share": sum(r["lex_class"] == "REFUSAL-OPENING" for r in in_subset) / len(subset),
               "y_orig_capped": sum(r["capped"] for r in in_subset),
               "leaving_the_ranking": {"count": len(leaving), "ids": leaving,
                                       "by_reason": {k: sum(1 for i in leaving if rows_by_id[i]["encode_train"] == k)
                                                     for k in sorted({rows_by_id[i]["encode_train"] for i in leaving}, key=str)}},
               "ranked": len(scores)}
    doc = {"kind": settings["scorer_output"]["kind"], "version": settings["scorer_output"]["version"], "scorer": "s3",
           "orientation": settings["scorer_output"]["orientation"], "candidate_pool_sha256": expected_pools["s3_safe"],
           "scores": dict(sorted(scores.items())),
           "per_layer": {i: {"safe": safe[i], "orig": orig[i]} for i in sorted(scores)},
           "reports": reports, "layers": {"from": 1, "to": n, "read": settings["read"]},
           "provenance": s1.provenance(Path(__file__).resolve(), settings_sha256,
                                       {"rows": rows[1], "summary": summary[1], "s_pool_record": s_pool_record[1],
                                        "answers_record": answers_record[1], **{f"pool_{k}": v for k, v in expected_pools.items()}},
                                       settings["label_entries"])}
    return {OUTPUT: canonical_json(doc)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for flag in ("--rows", "--summary", "--s-pool-record", "--answers-record"):
        parser.add_argument(flag, required=True, help="PATH:SHA256")
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)

        def pair(spec):
            path, _, sha = spec.rpartition(":")
            if not path or not s1.HEX64.match(sha):
                raise s1.Refusal("each input is PATH:SHA256")
            return Path(path), sha
        files = build(rows=pair(args.rows), summary=pair(args.summary), s_pool_record=pair(args.s_pool_record),
                      answers_record=pair(args.answers_record), settings=settings, settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
