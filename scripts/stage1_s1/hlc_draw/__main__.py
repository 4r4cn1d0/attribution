"""Command line of the human-label-check draw (package doc). draw: exit 0 every file written, 2 refused (nothing
written); check: exit 0 every file matches, 1 a file differs, 2 refused.

    python -m scripts.stage1_s1.hlc_draw draw --kit DIR --oct9-key FILE --bank-manifest FILE --bank FILE
        --auditor FILE --sealed NEW_DIR --manifest FILE [--reduction 0|1|2|3] [--repo DIR] [--rules FILE]
    python -m scripts.stage1_s1.hlc_draw check --kit DIR --oct9-key FILE --bank-manifest FILE --bank FILE
        --auditor FILE --sealed DIR --manifest FILE [--reduction 0|1|2|3] [--repo DIR] [--rules FILE]

``--sealed`` is a new folder for the key and the weights file under the git-ignored tmp/ of the main checkout that
``--repo`` names (HLC 9: "a git-ignored folder of the main checkout ..., never only in a Claude worktree"; a worktree's
.git is a file, so it is refused); ``--manifest`` is the text-free manifest the lead commits (not inside the sealed
folder; its folder must exist). Every output is checked before any input is read, and a draw that fails while writing
removes what it wrote, so a refusal leaves nothing behind. ``--reduction`` is HLC 4.2's reduction step (0: nothing
cut). ``--repo`` is the folder that REJUDGED_PINS paths are relative to (default: this repository); ``--rules`` is the
kit's rules module (default: runkit/stage1-olmo/stage1_rules.py of this repository).
``check`` re-makes every document in a second process, with the same code and the same inputs, and compares bytes: a
reproducibility check. It is not HLC 4.3 item 4's "second, independent process", which needs separately written code
(an open point for the lead).
Printed: totals, SHA-256 values, paths and refusals; never an answer, a prompt, a label, or a count per arm, seed,
unit or cell. Any error other than a refusal prints its type only.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from scripts.stage1_s1.hlc_draw import draw as dr
from scripts.stage1_s1.reading.settings import Refusal
from scripts.stage1_s1.reading_input.sources import load_rules, sha256_bytes

REPO = Path(__file__).resolve().parents[3]
RULES = REPO / "runkit" / "stage1-olmo" / "stage1_rules.py"


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="python -m scripts.stage1_s1.hlc_draw",
                                description="the human-label-check draw (LN-31, LN-34; HLC 4.1-4.4, 8)")
    p.add_argument("command", choices=("draw", "check"))
    p.add_argument("--kit", required=True, type=Path)
    p.add_argument("--oct9-key", required=True, type=Path, help="the 9 Oct sheet's key.json (pinned)")
    p.add_argument("--bank-manifest", required=True, type=Path, help="the prepared-v3 manifest.json (pinned)")
    p.add_argument("--bank", required=True, type=Path, help="the dev bank, banks/dev.jsonl (pinned)")
    p.add_argument("--auditor", required=True, type=Path, help="the prepared-v3 auditor/construction.json")
    p.add_argument("--sealed", required=True, type=Path)
    p.add_argument("--manifest", required=True, type=Path)
    p.add_argument("--reduction", default="0", choices=dr.STEPS)
    p.add_argument("--repo", type=Path, default=REPO)
    p.add_argument("--rules", type=Path, default=RULES)
    return p


def _inside(path: Path, folder: Path) -> bool:
    return folder.resolve() in path.resolve().parents


IGNORE_TMP = {"tmp/", "/tmp/", "tmp", "/tmp"}


def _checkout_tmp(repo: Path) -> Path:
    """``repo``/tmp, refused unless ``repo`` is a main checkout (its .git is a folder; a worktree's is a file) whose
    .gitignore ignores tmp/ (HLC 9)."""
    if not (repo / ".git").is_dir():
        raise Refusal(f"{repo} is not a main checkout (its .git is not a folder): the sealed folder must sit under the "
                      "main checkout's git-ignored tmp/ (HLC 9)")
    ignore = repo / ".gitignore"
    lines = ignore.read_text().splitlines() if ignore.is_file() and not ignore.is_symlink() else []
    if not IGNORE_TMP & {x.strip() for x in lines}:
        raise Refusal(f"{repo}/.gitignore has no line that ignores tmp/ (HLC 9: the sealed folder is git-ignored)")
    return repo / "tmp"


def _paths(args) -> tuple[Path, Path, Path]:
    """The key, weights and manifest paths, after the checks of the command (before any input is read)."""
    cfg = dr.settings()
    key, weights = args.sealed / cfg["outputs"]["key"], args.sealed / cfg["outputs"]["weights"]
    if args.manifest.resolve() == args.sealed.resolve() or _inside(args.manifest, args.sealed):
        raise Refusal("--manifest must lie outside the sealed folder (the manifest is committed; the folder is not)")
    if args.command == "draw":
        for path, what in ((args.sealed, "the sealed folder"), (args.manifest, "the manifest")):
            if path.exists() or path.is_symlink():
                raise Refusal(f"{what} {path} exists; the draw never overwrites")
        if not args.manifest.parent.is_dir():
            raise Refusal(f"the manifest's folder {args.manifest.parent} does not exist (nothing is written)")
        if not _inside(args.sealed, _checkout_tmp(args.repo)):
            raise Refusal("the sealed folder must lie under the main checkout's git-ignored tmp/ (HLC 9; --repo)")
    else:
        for path in (key, weights, args.manifest):
            if path.is_symlink() or not path.is_file():
                raise Refusal(f"{path.name}: missing or not a regular file (check compares a finished draw)")
    return key, weights, args.manifest


def _write(sealed: Path, outputs: list) -> None:
    """The sealed folder, then every (path, bytes) by exclusive create; on any failure, everything this call created
    is removed again (nothing it did not create) and the error is raised."""
    made = []
    try:
        sealed.mkdir(parents=True)
        made.append(sealed)
        for path, data in outputs:
            with open(path, "xb") as handle:
                made.append(path)
                handle.write(data)
    except BaseException:
        for path in reversed(made):
            try:
                if path == sealed:
                    path.rmdir()
                else:
                    path.unlink()
            except OSError:
                pass
        raise


def _say(lines) -> None:
    for line in lines:
        print(line)


def _head(command: str, result: dr.Result, args, rules_sha: str) -> list[str]:
    k, i, t = result.kit, result.inputs, result.totals
    e = t["excluded"]
    return [f"hlc {command} (LN-31): plan {k['plan_code']}; plan.json {k['plan_sha256']}; "
            + "; ".join(f"seal {b} {h}" for b, h in sorted(k["seals"].items())) + " (block B complete)",
            f"settings {result.settings_sha256}; rules {args.rules} sha256 {rules_sha}; reduction step "
            f"{args.reduction}",
            f"pinned inputs: 9 Oct key {i['oct9_key'][:16]}; bank manifest {i['bank_manifest'][:16]}; dev bank "
            f"{i['dev_bank'][:16]}; auditor {i['auditor'][:16]}; HarmBench label cache {i['harmbench_cache'][:16]}",
            f"units read: {t['units']} (the population's cells and theta0)",
            f"excluded before the draw (totals): 9 Oct answers {e['oct9_answers']}; minors-rule prompts rule a "
            f"{e['minors_prompts']['rule_a']}, rule b {e['minors_prompts']['rule_b']} ({e['minors_answers']} answers); "
            f"unscored answers {e['unscored_answers']}; answers without a label {e['answers_without_a_label']}",
            f"drawn (totals): {t['items']['all']} items (harm {t['items']['harm']}, benign {t['items']['benign']}); "
            f"hidden repeats {t['repeats']}"]


def main(argv=None) -> int:
    args = parser().parse_args(argv)
    try:
        key, weights, manifest = _paths(args)
        rules, rules_sha = load_rules(args.rules)
        result = dr.run(args.kit, args.repo, rules, rules_sha, args.oct9_key, args.bank_manifest, args.bank,
                        args.auditor, args.reduction)
        if args.command == "draw":
            try:
                _write(args.sealed, [(key, result.key), (weights, result.weights), (manifest, result.manifest)])
            except FileExistsError:
                raise Refusal("an output exists; the draw never overwrites (what it wrote is removed)") from None
    except Refusal as exc:
        print(f"REFUSED: {exc}", file=sys.stderr)
        return 2
    except Exception as exc:  # noqa: BLE001 - any other error may carry a value in its text: print its type only
        print(f"REFUSED: an unexpected {type(exc).__name__} (its message is withheld: it may hold a value)",
              file=sys.stderr)
        return 2
    lines = _head(args.command, result, args, rules_sha)
    if args.command == "draw":
        _say(lines + [f"wrote {path} sha256 {sha256_bytes(data)}"
                      for path, data in ((key, result.key), (weights, result.weights), (manifest, result.manifest))])
        return 0
    same = {path: path.read_bytes() == data
            for path, data in ((key, result.key), (weights, result.weights), (manifest, result.manifest))}
    _say(lines[:1] + [f"{path}: {'match' if ok else 'mismatch'}" for path, ok in same.items()] + lines[-1:])
    return 0 if all(same.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
