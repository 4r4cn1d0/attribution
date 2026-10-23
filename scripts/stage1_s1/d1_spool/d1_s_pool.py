"""REQ-6 under post-W1 deviation D-1 (addendum section 18): the S-pool and its lists, with the S3 subset size k.
Mac, CPU, $0, engine X; the lead runs it on the real files in place of scripts/stage1/build_s_pool.py, with the same
arguments. It prints counts and hashes only.

What it reuses. The W1 file scripts/stage1/build_s_pool.py is loaded by path, from the bytes that passed two checks:
their SHA-256 equals the W1 manifest's entry for that path and the pin in settings/d1_s_pool.json. Its own settings
(scripts/stage1/settings/build_s_pool.json) pass the same two checks and build_s_pool.py's literal pin. Its build()
then runs unchanged (the candidate rule, the seven filters in order, S1, the S4 candidates, every file writer, the
record, the text scan), with two of its module functions replaced for that call only, in the privately loaded module
(the module that ``import scripts.stage1.build_s_pool`` gives is never touched):

- lists_of: S1 and the S4 candidates come from build_s_pool's own lists_of; the S3 subset is the first k ids of
  sealed_order(S-pool ids, s3.subset), k the largest integer k <= 1,000 (and k <= N) for which at least decoy_rows (37)
  S-pool rows lie outside S1, the first k ids and the S4 candidates (section 18 point 2);
- check_sizes: the stop is N < 597 (48 + 512 + 37), or no k >= 48 meets the rule, or S1 or the S4 candidates cannot be
  filled (section 18 point 3); counts only, nothing written. k < 600 is section 18 point 7's fallback trigger: the
  wrapper then stops with counts only and exit code 3, since the fallback's S3 subset (all N rows) and its missing
  decoy are not this wrapper's outputs.

Outputs: the same files as build_s_pool.py (s_pool.json, s1.json, s3_subset.json, s4_candidates.json and
s3_safe.pool.json under --full-out, inside a folder named tmp; the text-free s_pool_record.json into --out). The record
is build_s_pool's record (kind "stage1 s-pool record") with its provenance block replaced by this wrapper's (script, its
settings' SHA-256, every input of the base record plus build_s_pool.py, its settings and the W1 manifest) and a "d1"
block: the planned size (1,000), N, k, the rows outside the lists at k (and at k + 1), the rule text, the stop text,
the reference to addendum section 18, the SHA-256s of the loaded build_s_pool.py, its settings and the W1 manifest, and
build_s_pool's own provenance block. The record's bytes are scanned for every S-pool text before they are returned.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from dataclasses import dataclass
from pathlib import Path
from types import ModuleType

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from experiments.safety_selection.common import canonical_json, sha256_bytes  # noqa: E402
from scripts.stage1 import s1common as s1  # noqa: E402

SETTINGS_PATH = HERE / "settings" / "d1_s_pool.json"
SETTINGS_SHA256 = "53acf788292c2bd3b430cb40000a8eb71af796d8d04b984272ae3129bccbe679"
SETTINGS_NAME = "d1_s_pool"
MANIFEST_KIND = "stage-1 W1 commitments"
S3_KEY = "s3.subset"
EXIT_FALLBACK = 3


class FallbackTrigger(s1.Refusal):
    """Addendum section 18 point 7: k < 600. Counts only, nothing written, exit code 3."""


@dataclass(frozen=True)
class Base:
    """build_s_pool.py loaded by path after its checks, with its checked settings."""

    module: ModuleType
    settings: dict
    settings_sha256: str
    script_sha256: str
    manifest_sha256: str


# ----- the W1 file, by path, after its SHA-256 checks ------------------------------------------------------------


def w1_root() -> Path:
    """The checkout that holds the W1 package scripts.stage1 (the workspace; under this package's mutation runner too,
    whose copy holds only scripts/stage1_s1/d1_spool)."""
    spec = importlib.util.find_spec("scripts.stage1")
    return Path(spec.origin).resolve().parents[2]


def manifest_entries(path: Path) -> tuple[dict[str, str], str]:
    """{path: SHA-256} of the W1 manifest's entries, and the manifest's own SHA-256."""
    try:
        data = Path(path).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"the W1 manifest cannot be read ({type(exc).__name__})") from None
    doc = s1.strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != MANIFEST_KIND or not isinstance(doc.get("entries"), list):
        raise s1.Refusal("not the stage-1 W1 commitments manifest")
    entries = {e["path"]: e.get("sha256") for e in doc["entries"] if isinstance(e, dict) and isinstance(e.get("path"), str)}
    return entries, sha256_bytes(data)


def pinned_bytes(root: Path, rel: str, pin: str, entries: dict[str, str], what: str) -> bytes:
    """The file's bytes, refused unless the manifest's entry and the D-1 pin agree and the bytes hash to them."""
    if entries.get(rel) != pin:
        raise s1.Refusal(f"{what}: the W1 manifest names {entries.get(rel)}, the D-1 settings pin {pin}")
    try:
        data = (Path(root) / rel).read_bytes()
    except OSError as exc:
        raise s1.Refusal(f"{what} cannot be read ({type(exc).__name__})") from None
    if sha256_bytes(data) != pin:
        raise s1.Refusal(f"{what} hashes to {sha256_bytes(data)}, the W1 manifest and the D-1 settings pin {pin}")
    return data


def load_base(d1: dict, root: Path | None = None) -> Base:
    """build_s_pool.py and its settings, each checked against the W1 manifest's entry and the D-1 pin; the module runs
    from the checked bytes (no second read of the file) and is not put in sys.modules."""
    root = Path(root) if root is not None else w1_root()
    base = d1["base"]
    entries, manifest_sha256 = manifest_entries(root / base["manifest"])
    code = pinned_bytes(root, base["script"], base["script_sha256"], entries, "build_s_pool.py")
    settings_bytes = pinned_bytes(root, base["settings"], base["settings_sha256"], entries, "build_s_pool.json")
    path = (Path(root) / base["script"]).resolve()
    spec = importlib.util.spec_from_file_location("stage1_d1_build_s_pool", path)
    module = importlib.util.module_from_spec(spec)
    exec(compile(code, str(path), "exec"), module.__dict__)
    if module.SETTINGS_SHA256 != base["settings_sha256"]:
        raise s1.Refusal("build_s_pool.py's own settings pin is not the D-1 settings' base.settings_sha256")
    settings = s1.check_settings(s1.strict_json(settings_bytes), module.SETTINGS_NAME)
    return Base(module, settings, sha256_bytes(settings_bytes), sha256_bytes(code), manifest_sha256)


# ----- the D-1 rule (section 18 points 2 and 3) ------------------------------------------------------------------


def check_consistency(settings: dict, d1: dict) -> None:
    """The D-1 numbers against REQ-6's settings: the planned size is REQ-6's S3 subset size, min_pool is S1 + S4 +
    decoy_rows, the S3 key is s3.subset, and k_min and the fallback threshold are integers in range."""
    sizes = settings["lists"]
    if sizes["s3_subset"]["key"] != S3_KEY:
        raise s1.Refusal(f"REQ-6's S3 subset key is {sizes['s3_subset']['key']!r}, D-1 reads {S3_KEY!r}")
    if d1["planned_s3_subset_size"] != sizes["s3_subset"]["size"]:
        raise s1.Refusal(f"D-1's planned S3 subset size {d1['planned_s3_subset_size']} is not REQ-6's "
                         f"{sizes['s3_subset']['size']}")
    need = sizes["s1"]["size"] + sizes["s4_candidates"]["size"] + settings["decoy_rows"]
    if d1["min_pool"] != need:
        raise s1.Refusal(f"D-1's min_pool {d1['min_pool']} is not S1 + S4 + decoy_rows = {need}")
    for name, value in (("k_min", d1["k_min"]), ("fallback.k_below", d1["fallback"]["k_below"])):
        if isinstance(value, bool) or not isinstance(value, int) or value < 1:
            raise s1.Refusal(f"D-1's {name} is not a positive integer")
    if d1["k_min"] > d1["planned_s3_subset_size"]:
        raise s1.Refusal("D-1's k_min exceeds the planned S3 subset size")


def choose_k(order: list[str], covered: set[str], n: int, planned: int, decoy_rows: int, k_min: int) -> dict:
    """outside(j) = n - |covered | order[:j]| (covered = S1 | S4, inside the n pool ids), which never grows with j.
    k = the largest j <= min(planned, n) with outside(j) >= decoy_rows, if that j is at least k_min; else k is None."""
    limit = min(planned, n, len(order))
    seen = set(covered)
    outside = n - len(seen)
    at = [outside]
    for row in order[:limit]:
        if row not in seen:
            seen.add(row)
            outside -= 1
        at.append(outside)
    best = max((j for j in range(limit + 1) if at[j] >= decoy_rows), default=None)
    k = best if best is not None and best >= k_min else None
    return {"k": k, "limit": limit, "largest_j_meeting_the_rule": best,
            "outside_at_k": at[k] if k is not None else None,
            "outside_at_k_plus_1": at[k + 1] if k is not None and k < limit else None,
            "outside_at_k_min": at[k_min] if k_min <= limit else None}


def d1_lists(pool_ids: list[str], settings: dict, d1: dict, base_lists_of) -> tuple[dict[str, list[str]], dict]:
    """S1 and the S4 candidates by build_s_pool's own lists_of; the S3 subset = the first k of s3.subset."""
    lists = base_lists_of(pool_ids, settings)
    order = s1.sealed_order(pool_ids, S3_KEY)
    covered = set(lists["s1"]) | set(lists["s4_candidates"])
    info = choose_k(order, covered, len(pool_ids), d1["planned_s3_subset_size"], settings["decoy_rows"], d1["k_min"])
    return {"s1": lists["s1"], "s3_subset": order[:info["k"] or 0], "s4_candidates": lists["s4_candidates"]}, info


def d1_stop(n: int, lists: dict[str, list[str]], settings: dict, d1: dict, info: dict, counts: str) -> dict:
    """Section 18 point 3's stop (counts only), then point 7's fallback trigger; else build_s_pool's room block."""
    sizes, need = settings["lists"], settings["decoy_rows"]
    short = {name: len(lists[name]) for name in ("s1", "s4_candidates") if len(lists[name]) < sizes[name]["size"]}
    if n < d1["min_pool"] or short or info["k"] is None:
        raise s1.Refusal(f"D-1: the S-pool cannot fill its lists: N = {n} (D-1 min_pool {d1['min_pool']}), short lists "
                         f"{short}, k = {info['k']} (the largest k <= {info['limit']} with at least {need} rows outside "
                         f"S1, the first k of {S3_KEY} and S4 is {info['largest_j_meeting_the_rule']}; k_min "
                         f"{d1['k_min']}; {info['outside_at_k_min']} rows outside at k = {d1['k_min']}); {counts} "
                         f"(counts only; nothing written)")
    outside = n - len(set().union(*map(set, lists.values())))
    if outside != info["outside_at_k"] or outside < need or len(lists["s3_subset"]) != info["k"]:
        raise s1.Refusal("D-1: the lists disagree with the k computation")
    if info["k"] < d1["fallback"]["k_below"]:
        raise FallbackTrigger(f"D-1: k = {info['k']} < {d1['fallback']['k_below']}, addendum section 18 point 7's "
                              f"fallback applies (the S3 subset is all N rows and the decoy is not built): N = {n}, "
                              f"{outside} rows outside the lists at k; {counts} (counts only; nothing written)")
    return {"rows_outside_the_lists": outside, "decoy_rows_needed": need}


# ----- the build ---------------------------------------------------------------------------------------------------


def build(*, config_path: Path, sources_root: Path, prepared_root: Path, anchors_path: Path, rec_path: Path,
          codec, base: Base, d1: dict, d1_sha256: str) -> tuple[dict[str, bytes], dict[str, bytes]]:
    """(full files with text, record files without text); nothing is written here."""
    s1.check_settings(d1, SETTINGS_NAME)
    bsp, settings = base.module, base.settings
    check_consistency(settings, d1)
    state: dict = {}
    base_lists_of, base_check_sizes = bsp.lists_of, bsp.check_sizes

    def lists_of(pool_ids, s):
        lists, state["info"] = d1_lists(pool_ids, s, d1, base_lists_of)
        state["n"] = len(pool_ids)
        return lists

    def check_sizes(n, lists, s, result=None):
        return d1_stop(n, lists, s, d1, state["info"], bsp.filter_counts(result))

    bsp.lists_of, bsp.check_sizes = lists_of, check_sizes
    try:
        full, records = bsp.build(config_path=config_path, sources_root=sources_root, prepared_root=prepared_root,
                                  anchors_path=anchors_path, rec_path=rec_path, codec=codec, settings=settings,
                                  settings_sha256=base.settings_sha256)
    finally:
        bsp.lists_of, bsp.check_sizes = base_lists_of, base_check_sizes

    info, n = state["info"], state["n"]
    record = s1.strict_json(records[bsp.RECORD])
    base_prov = record["provenance"]
    record["provenance"] = s1.provenance(
        Path(__file__).resolve(), d1_sha256,
        {**base_prov["inputs"], "build_s_pool": base.script_sha256, "build_s_pool_settings": base.settings_sha256,
         "w1_manifest": base.manifest_sha256},
        {**settings["label_entries"], **d1["label_entries"]})
    record["d1"] = {
        "deviation": "D-1", "reference": d1["reference"], "decision": d1["decision"], "rule": d1["rule"],
        "stop": d1["stop"], "planned_s3_subset_size": d1["planned_s3_subset_size"], "N": n, "k": info["k"],
        "k_limit": info["limit"], "rows_outside_the_lists_at_k": info["outside_at_k"],
        "rows_outside_the_lists_at_k_plus_1": info["outside_at_k_plus_1"], "decoy_rows": settings["decoy_rows"],
        "k_min": d1["k_min"], "min_pool": d1["min_pool"],
        "fallback": {"k_below": d1["fallback"]["k_below"], "triggered": False},
        "list_sizes": {name: len(v["ids"]) for name, v in record["lists"].items()},
        "build_s_pool_sha256": base.script_sha256, "build_s_pool_settings_sha256": base.settings_sha256,
        "w1_manifest_sha256": base.manifest_sha256, "settings_sha256": d1_sha256, "base_provenance": base_prov}
    record_bytes = canonical_json(record)
    texts = [t for i in s1.strict_json(full[bsp.POOL_FILE])["items"] for t in (i["prompt"], i["response"])]
    if s1._text_hits(record_bytes, texts):
        raise s1.Refusal("the record would hold text")
    return full, {bsp.RECORD: record_bytes}


def refusal_state(folders) -> str:
    """build_s_pool.refusal_state's rule (usable before build_s_pool.py is loaded)."""
    left = sum(1 for d in folders if Path(d).exists() for p in Path(d).rglob("*") if p.is_file())
    return "nothing written" if left == 0 else f"{left} files left under the output folders"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--sources", type=Path, required=True, help="the folder the config's local paths start from")
    parser.add_argument("--prepared", type=Path, required=True)
    parser.add_argument("--anchors", type=Path, required=True, help="the full anchor prompt list (with text)")
    parser.add_argument("--rec", type=Path, required=True, help="REC, the recipe")
    parser.add_argument("--full-out", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--settings", type=Path, default=SETTINGS_PATH, help="D-1's settings (pinned by SHA-256)")
    args = parser.parse_args(argv)
    folders = []
    try:
        d1, digest = s1.load_settings(args.settings, SETTINGS_SHA256, SETTINGS_NAME)
        base = load_base(d1)
        bsp = base.module
        folders = bsp.check_output_folders(bsp.full_out_ok(args.full_out), args.out)
        full_out, out_dir = folders
        codec = bsp.real_codec(args.prepared, base.settings)
        full, record = build(config_path=args.config, sources_root=args.sources, prepared_root=args.prepared,
                             anchors_path=args.anchors, rec_path=args.rec, codec=codec, base=base, d1=d1,
                             d1_sha256=digest)
        written = s1.write_new_files(full_out, full)
        written.update(s1.write_new_files(out_dir, record))
    except FallbackTrigger as exc:
        print(f"FALLBACK: {exc} ({refusal_state(folders)})", file=sys.stderr)
        return EXIT_FALLBACK
    except (s1.Refusal, OSError) as exc:
        print(f"REFUSED: {exc if isinstance(exc, s1.Refusal) else type(exc).__name__} ({refusal_state(folders)})",
              file=sys.stderr)
        return 2
    doc = s1.strict_json(record[bsp.RECORD])
    d = doc["d1"]
    print(f"candidates {doc['candidates']}; N after each filter {doc['n_after_each_filter']}")
    print(f"D-1: N = {d['N']}; k = {d['k']} (planned {d['planned_s3_subset_size']}); rows outside the lists at k "
          f"{d['rows_outside_the_lists_at_k']}, at k + 1 {d['rows_outside_the_lists_at_k_plus_1']}; build_s_pool.py "
          f"{d['build_s_pool_sha256']}")
    for name, sha in sorted(written.items()):
        print(f"  {sha}  {name}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
