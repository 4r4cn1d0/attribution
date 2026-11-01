"""REQ-13: Self-Inf-N-style (LW-18: built before wave 1; if not committed at W1, post-Gate-B exploratory, ADD-6.6; it
counts toward the plant's "finds a known cause", ADD-8.2). Mac, $0 marginal; the lead runs it on the real unit.

    python scripts/stage1/score_selfinf_n.py --prepared P --unit DIR --out DIR

The wave-0b attributes unit (the one T1's A1 contract reads) is checked and read only through T1's
``write_score_edit.check_attributes_unit`` (its COMPLETE.json pinned in write_score_edit.json; its own files verify;
rows.jsonl is parsed from the same bytes it hashed). Per training row, at checkpoint q: the code refuses unless the row's
grad_norm is equal in both anchor sets' records (a row's gradient does not depend on the anchors); SI = grad_norm^2;
len = the row's response tokens without the end-of-turn token (P's target tokens - 1); score = ln(SI + 1) + ln(len + 1).
Written as T1's scorer output (scorer selfinf_n, high = remove): write_score_edit.py's scorer path makes the top 600
(scored only: the rank tables and the Jaccard matrix). Report only (``selfinf_n_sensitivities.json``): the same score at
e1, and with SI summed over q and e1, each with its top-600 Jaccard against the primary. Costs: the marginal cost is $0
(no new pass), and the full charge is the attributes unit's own recorded costs; both are reported.
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

from experiments.safety_selection.common import canonical_json  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "score_selfinf_n.json"
SETTINGS_SHA256 = "02a0bfee6d4478c548d5197875c1e2b980bccf36a1911207c48a70f08f6297ab"
SETTINGS_NAME = "score_selfinf_n"
OUTPUT, SENSITIVITIES = "selfinf_n_scores.json", "selfinf_n_sensitivities.json"


def grad_norms(rows_bytes: bytes, view: s1.PreparedView, checkpoints: list[str]) -> dict[str, dict[str, float]]:
    """Per row and checkpoint the grad_norm, refused unless equal in both anchor sets' records."""
    out = {}
    for number, row in enumerate(s1.iter_jsonl_bytes(rows_bytes, "rows.jsonl"), 1):
        rid = row.get("row_id")
        if not isinstance(rid, str) or rid not in view.tokens or rid in out:
            raise s1.Refusal(f"rows.jsonl line {number}: the row id is unknown or repeated")
        per = row.get("per_checkpoint") or {}
        norms = {}
        for c in checkpoints:
            sets = per.get(c) or {}
            values = [sets.get(name, {}).get("grad_norm") for name in ("harmful", "safe")]
            if any(isinstance(v, bool) or not isinstance(v, (int, float)) or not math.isfinite(v) or v < 0 for v in values):
                raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c} has no finite grad_norm in both sets")
            if values[0] != values[1]:
                raise s1.Refusal(f"rows.jsonl line {number}: checkpoint {c}: grad_norm differs between the anchor sets")
            norms[c] = float(values[0])
        out[rid] = norms
    if set(out) != set(view.tokens):
        raise s1.Refusal(f"rows.jsonl misses {len(set(view.tokens) - set(out))} training rows")
    return out


def score(si: float, response_tokens: int) -> float:
    return math.log(si + 1.0) + math.log(response_tokens + 1.0)


def jaccard(a: list[str], b: list[str]) -> float:
    sa, sb = set(a), set(b)
    return len(sa & sb) / len(sa | sb)


def build(*, prepared_root: Path, unit_dir: Path, settings: dict, settings_sha256: str,
          wse_settings: tuple[dict, str] | None = None) -> dict[str, bytes]:
    """``wse_settings`` = (write_score_edit's settings, SHA-256); None loads the committed file by its literal pin."""
    from scripts.stage1 import write_score_edit as wse

    s1.check_settings(settings, SETTINGS_NAME)
    wsettings, wdigest = wse_settings or s1.load_settings(wse.SETTINGS_PATH, wse.SETTINGS_SHA256, wse.SETTINGS_NAME)
    view = wse.view_of(prepared_root, wsettings)
    unit = wse.check_attributes_unit(unit_dir, wsettings["a1"]["attributes_unit"], view)
    norms = grad_norms(unit["bytes"]["rows.jsonl"], view, settings["checkpoints"])
    length = {r: view.tokens[r] - 1 for r in view.tokens}
    if any(v < 0 for v in length.values()):
        raise s1.Refusal("a row has no target tokens")
    primary = {r: score(norms[r][settings["primary"]] ** 2, length[r]) for r in view.tokens}
    sens = {"e1": {r: score(norms[r]["e1"] ** 2, length[r]) for r in view.tokens},
            "q_plus_e1": {r: score(norms[r]["q"] ** 2 + norms[r]["e1"] ** 2, length[r]) for r in view.tokens}}
    k = settings["k"]                             # write_score_edit.py selects the primary top k; nothing is drawn here
    inputs = {"attributes_complete": unit["complete_sha256"], "rows": unit["files"]["rows.jsonl"],
              "prepared_manifest": view.manifest_sha256, "write_score_edit_settings": wdigest}
    prov = s1.provenance(Path(__file__).resolve(), settings_sha256, inputs, settings["label_entries"])
    costs = {"marginal_usd": 0.0, "marginal_gpu_seconds": 0.0, "full_charge": unit["costs"],
             "rule": settings["costs_rule"]}
    doc = {"kind": settings["scorer_output"]["kind"], "version": settings["scorer_output"]["version"],
           "scorer": "selfinf_n", "manifest_sha256": view.manifest_sha256,
           "orientation": settings["scorer_output"]["orientation"], "scores": dict(sorted(primary.items())),
           "costs": costs, "provenance": {**prov, "checkpoint": settings["primary"], "rule": settings["rule"]}}

    def order(scores):                            # report only: an unsealed top-k by score, ties by row id
        return sorted(scores, key=lambda r: (-scores[r], r))[:k]
    base = order(primary)
    report = {"kind": "stage1 selfinf-n sensitivities", "version": 1, "report_only": True, "k": k,
              "variants": {name: {"rule": settings["sensitivities"][name], "scores": dict(sorted(values.items())),
                                  "top_k_jaccard_with_primary": jaccard(order(values), base)}
                           for name, values in sens.items()},
              "tie_note": "the top-k sets here are ordered by score, then row id (report only); the primary selection is write_score_edit.py's",
              "provenance": prov}
    return {OUTPUT: canonical_json(doc), SENSITIVITIES: canonical_json(report)}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    for flag in ("--prepared", "--unit", "--out"):
        parser.add_argument(flag, type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH)
    args = parser.parse_args(argv)
    try:
        settings, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        files = build(prepared_root=args.prepared, unit_dir=args.unit, settings=settings, settings_sha256=digest)
        written = s1.write_new_files(args.out.resolve(), files)
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} (nothing written)", file=sys.stderr)
        return 2
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
