"""Re-verifier's hand mutants on the fixed track-E code (fix round 3). A mutant root R holds symlinks to every entry of the
read-only worktree except scripts/, which is a real folder with real copies of scripts/stage1 and scripts/scale78b (so
s1.rel sees one root and no worktree file is ever touched). Each mutant is applied to a fresh copy of the worktree's
scripts/scale78b, the whole scorer suite runs, and a summary row is appended to mutants-rv-results.jsonl.
Usage: python -B mutants_rv.py NAME [NAME ...]  |  --list.  Standard library only; no study text is read."""
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

S = Path(__file__).resolve().parent
W = Path("/private/tmp/claude-501/-Users-spiderishi-Coding-attribution--claude-worktrees-pensive-stonebraker-bf6d79/b609d8b8-9fca-458c-826f-4c781de96013/scratchpad/b78/ws-e")
R = S / "mutroot"
TARGET = R / "scripts" / "scale78b"
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
LOG = S / "mutants-rv-results.jsonl"
SW, MK, PINS = "scorers_78b.py", "make_scorer_settings_78b.py", "settings/pins_78b.json"
ENV = {"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin", "HOME": "/Users/spiderishi"}


def build_root():
    if R.exists():
        shutil.rmtree(R)
    R.mkdir()
    for entry in W.iterdir():
        if entry.name != "scripts":
            (R / entry.name).symlink_to(entry)
    (R / "scripts").mkdir()
    for entry in (W / "scripts").iterdir():
        if entry.name not in ("scale78b", "stage1"):
            (R / "scripts" / entry.name).symlink_to(entry)
    shutil.copytree(W / "scripts" / "stage1", R / "scripts" / "stage1")


def fresh():
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(W / "scripts" / "scale78b", TARGET)


def replace(rel: str, old: str, new: str, count: int = 1):
    p = TARGET / rel
    text = p.read_text(encoding="utf-8")
    assert text.count(old) == count, (rel, old[:70], text.count(old))
    p.write_text(text.replace(old, new), encoding="utf-8")


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def maker_and_repin():
    """Run the (possibly mutated) maker in R, then set the wrapper's literal to the new index hash."""
    proc = subprocess.run([PY, "-I", "-B", str(TARGET / MK)], cwd=R, capture_output=True, text=True, env=ENV)
    assert proc.returncode == 0, proc.stderr[-500:]
    idx = sha(TARGET / "settings" / "PINS-78B.json")
    p = TARGET / SW
    p.write_text(re.sub(r'PINS_FILE_SHA256 = "[0-9a-f]{64}"', f'PINS_FILE_SHA256 = "{idx}"', p.read_text(encoding="utf-8")), encoding="utf-8")
    return idx


# ----- the mutants (one tuple: file, old, new; or a function) ---------------------------------------------------------
SIMPLE = {
    # D1 (PP2)
    "d1a_check_untuned_calls_never_refuses": (SW, '    if "s4" in lists and (len(lists) > 1 or losses):\n        raise',
                                              '    if False:\n        raise'),
    "d1b_doses_on_every_untuned_call": (SW, '            and "s4" in checked.get("lists", []):', '            and True:'),
    "d1c_named_values_keeps_whole_spec": (SW, '            names.append(argv[k + 1].partition("=")[0])', '            names.append(argv[k + 1])'),
    "d1d_check_after_recipe_checks": (SW,
        '    if kind == "untuned_answers":\n        checked.update(check_untuned_calls(argv))\n    if takes_prepared:',
        '    if takes_prepared:'),
    "d1e_lists_gt_2": (SW, '    if "s4" in lists and (len(lists) > 1 or losses):', '    if "s4" in lists and (len(lists) > 2 or losses):'),
    "d1f_loss_beside_s4_allowed": (SW, '    if "s4" in lists and (len(lists) > 1 or losses):', '    if "s4" in lists and (len(lists) > 1):'),
    "d1g_named_values_ignores_eq_form": (SW, '        elif item.startswith(flag + "="):\n            names.append(', '        elif False:\n            names.append('),
    # C4
    "c4a_main_no_doses_except": (SW,
        '    except DosesRefusal as exc:\n        print(f"REFUSED after the 1B pass: the 1B outputs are written in {exc.out}; the doses were not written ({exc})",\n              file=sys.stderr)\n        return 2\n',
        ''),
    "c4b_run_kind_no_wrap": (SW, '            raise DosesRefusal(str(exc), out) from None', '            raise'),
    "c4c_message_without_out": (SW, 'the 1B outputs are written in {exc.out}; the doses', 'the 1B outputs are written; the doses'),
    # C5
    "c5a_flag_value_first_not_last": (SW, "        if item == flag and k + 1 < len(argv):\n            value = argv[k + 1]",
                                      "        if item == flag and k + 1 < len(argv) and value is None:\n            value = argv[k + 1]"),
    "c5b_record_exit_code_always_0": (SW, '"command": checked["command"], "exit_code": code,', '"command": checked["command"], "exit_code": 0,'),
    # the doses step and the fallback exit codes
    "x1_doses_only_on_exit_0": (SW, '    if kind == "untuned_answers" and code in (0, 3) and "doses" in settings', '    if kind == "untuned_answers" and code == 0 and "doses" in settings'),
    "x2_few_kept_returns_0": (SW, '        return {"kept": len(kept_ids), "fallback_fired": True, "lists": {}}, mua.EXIT_FEW',
                              '        return {"kept": len(kept_ids), "fallback_fired": True, "lists": {}}, 0'),
    "x3_record_exists_check_dropped": (SW, '        if target.exists():\n            raise s1.Refusal(f"{WRAPPER_RECORD} exists in {out}")\n', ''),
    # D2 / D3 on the maker (regenerated, literal re-pinned, so only a test against sources or the frozen check can catch it)
}


def d2a_maker_drops_engine_rule():
    replace(MK, '            "engine_rule": self.shared["engine_rule_78b"],\n', '')
    # no regeneration: the committed files still carry engine_rule; the derivation test must notice


def d2b_rule_text_says_engine_y():
    replace(PINS, "every wrapper kind runs on engine X (engine_x above)", "every wrapper kind runs on engine Y (any identity)")
    maker_and_repin()


def d2c_derived_files_pin_another_engine():
    replace(MK, '        doc["labels_sha256"] = s1.labels_sha256()\n', '        doc["labels_sha256"] = s1.labels_sha256()\n        doc["engine_x"] = "0" * 64\n')
    maker_and_repin()


def d3a_pins_drop_classifier_rule():
    p = TARGET / PINS
    doc = json.loads(p.read_bytes())
    del doc["shared"]["classifier_recipe_78b"]
    del doc["shared"]["kind_names_78b"]
    p.write_bytes((json.dumps(doc, indent=2, ensure_ascii=False) + "\n").encode())
    maker_and_repin()


def d3b_classifier_pins_main_recipe():
    replace(MK, '    d.pin_or_null("pins.recipe_sha256", fam["recipe_s78"]["config_sha256"], fam["recipe_s78"]["waits"], ["*"])\n    doc["pools_rule"]',
            '    doc["pins"]["recipe_sha256"] = fam["main_recipe"]["config_sha256"]\n    doc["pools_rule"]')
    maker_and_repin()


SPECIAL = {"d2a_maker_drops_engine_rule": d2a_maker_drops_engine_rule, "d2b_rule_text_says_engine_y": d2b_rule_text_says_engine_y,
           "d2c_derived_files_pin_another_engine": d2c_derived_files_pin_another_engine,
           "d3a_pins_drop_classifier_rule": d3a_pins_drop_classifier_rule, "d3b_classifier_pins_main_recipe": d3b_classifier_pins_main_recipe}


def run_suite():
    started = time.monotonic()
    proc = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "-rf", "scripts/scale78b/tests/scorers"],
                          cwd=R, capture_output=True, text=True, env=ENV)
    lines = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    failed = [l.split(" - ")[0].replace("FAILED scripts/scale78b/tests/scorers/", "") for l in lines if l.startswith("FAILED ")]
    return lines[-1] if lines else "(no output)", failed, proc.returncode, round(time.monotonic() - started, 1)


def main(names):
    if names == ["--list"]:
        print("\n".join(sorted(list(SIMPLE) + list(SPECIAL) + ["baseline"])))
        return
    build_root()
    for name in names:
        fresh()
        if name == "baseline":
            pass
        elif name in SIMPLE:
            replace(*SIMPLE[name])
        elif name in SPECIAL:
            SPECIAL[name]()
        else:
            raise SystemExit(f"unknown mutant {name}")
        summary, failed, code, seconds = run_suite()
        verdict = "baseline" if name == "baseline" else ("KILLED" if code != 0 else "SURVIVED")
        row = {"mutant": name, "verdict": verdict, "pytest_exit": code, "summary": summary, "failed": failed[:8], "seconds": seconds}
        print(json.dumps(row))
        with LOG.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    fresh()


if __name__ == "__main__":
    main(sys.argv[1:])
