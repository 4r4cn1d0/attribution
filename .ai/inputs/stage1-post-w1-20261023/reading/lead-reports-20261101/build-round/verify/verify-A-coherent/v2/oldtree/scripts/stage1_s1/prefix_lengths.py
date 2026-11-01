"""B10's safety-prefix prompt-length rule, counted on the Mac with no model (block-B pre-flight G5; settings
prefix.length_rule): for each prefixed bank, the number of prompts, the largest prefixed token count, its limit and the
number over it. It prints counts and hashes only: never a prompt's text or id.

    python -B scripts/stage1_s1/prefix_lengths.py --prepared DIR --prefix-file F
        [--oext-bank F --oext-record F [--w1-18-record F]]

It reads B10's pinned settings (settings/eval_adapter.json: the prefix pin, apply_to and the separator), B10's pinned
recipe file (the limits: model.max_prompt_tokens, model.max_train_tokens), the prefix file (its bytes must hash to the
pin), the pinned prepared set's dev bank and task rows, O-ext's PHTest prompts when its pinned bank, record and W1-18
record are given (they are prefixed when over-refusal is in apply_to), and the policy's cached tokenizer (the snapshot
of the recipe's tokenizer, read only and offline; no weights). The counts are B10's own (eval_adapter.
prepared_prefix_counts, the function the command line refuses on before any model loads), so a bank that fits here
fits on the pod.

Exit status: 0 every prefixed prompt fits its limit; 1 at least one is over (the counts say in which bank); 2 refused
(an input is not the pinned one, or the tokenizer is not cached).
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Sequence

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[1]
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))

from scripts.stage1_s1 import eval_adapter as ea  # noqa: E402
from scripts.stage1_s1 import oext_eval as oe  # noqa: E402

KIND = "stage1 B10 prefix length counts"
EXIT_OK, EXIT_OVER, EXIT_REFUSED = 0, 1, 2


def count(*, prepared: str | Path, prefix_file: str | Path, oext_bank: str | Path | None = None,
          oext_record: str | Path | None = None, w1_18_record: str | Path | None = None,
          settings: ea.Settings | None = None, recipe_path: str | Path | None = None, codec: Any = None,
          oext_settings: Any = None) -> dict:
    """The counts (text-free). ``settings``, ``recipe_path``, ``codec`` and ``oext_settings`` are for tests; by default
    B10's pinned settings, its pinned recipe file, the cached tokenizer and O-ext's pinned settings."""
    settings = settings if settings is not None else ea.load_pinned_settings()
    if settings.doc["prefix"]["text_sha256"] is None:
        raise ea.Refusal("the safety prefix text is not pinned in B10's settings")
    recipe = ea.load_pinned_recipe(recipe_path or ea.ENGINE_REPO / settings.doc["recipe"]["path"], settings)
    prefix = ea.load_prefix(prefix_file, settings)
    oext = None
    if any(p is not None for p in (oext_bank, oext_record, w1_18_record)):
        chosen = oext_settings if oext_settings is not None else oe.load_pinned_settings()
        oext = oe.prepare(chosen, bank_path=oext_bank, record_path=oext_record, w1_18_path=w1_18_record)
    codec = codec if codec is not None else ea.tokenizer_codec(recipe)
    counts = ea.prepared_prefix_counts(prepared, prefix, settings, recipe, codec, oext)
    phtest = oext is not None and oext.runs and "overrefusal" in settings.doc["prefix"]["apply_to"]
    return {"kind": KIND, "version": 1, "settings_sha256": settings.sha256,
            "recipe_file_sha256": settings.doc["recipe"]["file_sha256"], "phtest_counted": phtest,
            "rule": "settings prefix.length_rule", **counts}


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="prefix_lengths.py", description=__doc__.split("\n\n")[0])
    parser.add_argument("--prepared", required=True, help="the pinned prepared set (B10's prepared.manifest_sha256)")
    parser.add_argument("--prefix-file", required=True, help="the pinned prefix text file")
    parser.add_argument("--oext-bank", help="O-ext's bank file (oext_bank.json)")
    parser.add_argument("--oext-record", help="O-ext's pinned bank record (oext_record.json)")
    parser.add_argument("--w1-18-record", help="W1-18's pinned record (overrefusal_checks.json)")
    return parser


def main(argv: Sequence[str] | None = None, *, _settings: ea.Settings | None = None, _recipe: Any = None,
         _codec: Any = None, _oext_settings: Any = None) -> int:
    args = _parser().parse_args(argv)
    try:
        out = count(prepared=args.prepared, prefix_file=args.prefix_file, oext_bank=args.oext_bank,
                    oext_record=args.oext_record, w1_18_record=args.w1_18_record, settings=_settings,
                    recipe_path=_recipe, codec=_codec, oext_settings=_oext_settings)
    except (ea.Refusal, ValueError, OSError) as exc:          # DataError, TemplateError and FileNotFoundError included
        print(json.dumps({"ok": False, "refused": f"{type(exc).__name__}: {exc}"}), file=sys.stderr)
        return EXIT_REFUSED
    print(json.dumps(out, indent=2, sort_keys=True))
    return EXIT_OVER if out["over"] else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
