"""Hand mutants on the track-E code and settings (verifier). Each mutant is applied to a fresh copy of the pristine
scripts/scale78b in the mutant root (symlinks to the read-only worktree for everything else), the scorer suite runs,
and the summary line is recorded. Usage: python mutants.py NAME [NAME ...]  |  python mutants.py --list"""
import hashlib
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

S = Path(__file__).resolve().parent
R = S / "mutroot"
PRISTINE = S / "pristine-scale78b"
TARGET = R / "scripts" / "scale78b"
PY = "/Users/spiderishi/Coding/attribution/tmp/minimal-experiment-20261002/venv/bin/python"
LOG = S / "mutants-results.jsonl"


def replace(path: Path, old: str, new: str, count: int = 1):
    text = path.read_text(encoding="utf-8")
    assert text.count(old) == count, (path.name, old[:60], text.count(old))
    path.write_text(text.replace(old, new), encoding="utf-8")


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def set_literal(index_sha: str):
    sw = TARGET / "scorers_78b.py"
    text = sw.read_text(encoding="utf-8")
    import re
    new = re.sub(r'PINS_FILE_SHA256 = "[0-9a-f]{64}"', f'PINS_FILE_SHA256 = "{index_sha}"', text)
    assert new != text or index_sha in text
    sw.write_text(new, encoding="utf-8")


def rebuild_index_by_hand():
    """Recompute the index entries from the (hand-edited) settings files, keep its other fields, then the literal."""
    idx_path = TARGET / "settings" / "PINS-78B.json"
    idx = json.loads(idx_path.read_bytes())
    for name in idx["files"]:
        idx["files"][name] = sha(TARGET / "settings" / name)
    idx_path.write_bytes((json.dumps(idx, indent=2, sort_keys=True, ensure_ascii=False) + "\n").encode())
    set_literal(sha(idx_path))


def run_maker_and_pin():
    sys.path.insert(0, str(R))
    for m in [k for k in sys.modules if k.startswith("scripts.")]:
        del sys.modules[m]
    from scripts.scale78b import make_scorer_settings_78b as mk
    assert mk.SETTINGS_DIR == TARGET / "settings", mk.SETTINGS_DIR
    code = mk.main([])
    assert code == 0, code
    set_literal(sha(TARGET / "settings" / "PINS-78B.json"))


SW = "scorers_78b.py"
MK = "make_scorer_settings_78b.py"
MUTANTS = {
    "m01_manifest_never_refuses": (SW, '    if digest != expected:\n        raise s1.Refusal(f"the prepared manifest is',
                                   '    if False:\n        raise s1.Refusal(f"the prepared manifest is'),
    "m02_doses_suffix_not_prefix": (SW, "lists = {names[str(n)]: list(kept_ids[:n]) for n in sizes if len(kept_ids) >= n}",
                                    "lists = {names[str(n)]: list(kept_ids[-n:]) for n in sizes if len(kept_ids) >= n}"),
    "m03_fallback_at_exactly_192": (SW, "    fallback = len(kept_ids) < sizes[-1]", "    fallback = len(kept_ids) <= sizes[-1]"),
    "m04_sizing_floor": (SW, "    return math.ceil(target * answered / kept)", "    return math.floor(target * answered / kept)"),
    "m05_null_pins_star_only": (SW, '        if ("*" in needed or command in needed) and get_path(settings, dotted) is None:',
                                '        if ("*" in needed) and get_path(settings, dotted) is None:'),
    "m06_patched_not_restored": (SW, "        for name, value in self.saved.items():\n            setattr(self.module, name, value)\n        return False",
                                 "        for name, value in self.saved.items():\n            pass\n        return False"),
    "m07_recipe_hash_unchecked": (SW, "        checked[flag] = check_recipe(Path(value), get_path(settings, dotted), flag)",
                                  "        checked[flag] = get_path(settings, dotted)"),
    "m08_no_subcommand_prepend": (SW, "    return [sub] + list(argv)", "    return list(argv)"),
    "m09_flag_value_first_not_last": (SW, "        if item == flag and k + 1 < len(argv):\n            value = argv[k + 1]",
                                      "        if item == flag and k + 1 < len(argv) and value is None:\n            value = argv[k + 1]"),
    "m10_record_exit_code_always_0": (SW, '"command": checked["command"], "exit_code": code,', '"command": checked["command"], "exit_code": 0,'),
    "m11_answers_hash_unchecked": (SW, '    if s4.get("answers_file_sha256") != sha256_bytes(answers_bytes):', "    if False:"),
    "m12_maker_keep_48": (MK, '    s4["keep"] = keep\n', '    s4["keep"] = 48\n'),
    "m15_stage1_code_unchecked": (SW, "        if digest != pin:\n            raise s1.Refusal(f\"{rel} hashes to {digest}, the wrapper pins {pin}",
                                  "        if False:\n            raise s1.Refusal(f\"{rel} hashes to {digest}, the wrapper pins {pin}"),
    "m16_pool_pins_flag_dropped": (SW, '                if module is rp:\n                    argv += ["--pool-pins", str(path)]',
                                   '                if False:\n                    argv += ["--pool-pins", str(path)]'),
    "m17_build_doses_skips_s4_list_check": (SW, "        if listed != kept_ids:\n            raise s1.Refusal(\"the record's kept ids and s4.json's ids differ\")",
                                            "        if False:\n            raise s1.Refusal(\"the record's kept ids and s4.json's ids differ\")"),
}
LLAMA_MANIFEST = "c52a50afddcfcfa818512ac7f1536c34c959774e815095bd30f69320b083d55a"
OLMO_MANIFEST = "9ed61826f1634dcab5a7385f18556b108b3ba8db95fc17215fa4cf4f6cb993b9"


def m13_hand_edited_settings_file():
    """A hand edit of one committed settings file (the OLMo rep_pass file pins Llama's manifest), with the index and the
    wrapper's literal re-pinned by hand so the index/literal consistency holds; only the derivation test can catch it."""
    p = TARGET / "settings" / "representation_pass__olmo2-7b.json"
    replace(p, f'"prepared_manifest_sha256": "{OLMO_MANIFEST}"', f'"prepared_manifest_sha256": "{LLAMA_MANIFEST}"')
    rebuild_index_by_hand()


def m14_pins_swapped_manifests():
    """The two families' manifest pins swapped in pins_78b.json, every settings file regenerated by the maker and the
    literal re-pinned: every internal consistency test passes; only the tests against the real sources can catch it."""
    p = TARGET / "settings" / "pins_78b.json"
    text = p.read_text(encoding="utf-8")
    assert text.count(OLMO_MANIFEST) >= 1 and text.count(LLAMA_MANIFEST) >= 1
    text = text.replace(OLMO_MANIFEST, "@@O@@").replace(LLAMA_MANIFEST, OLMO_MANIFEST).replace("@@O@@", LLAMA_MANIFEST)
    p.write_text(text, encoding="utf-8")
    run_maker_and_pin()


SPECIAL = {"m13_hand_edited_settings_file": m13_hand_edited_settings_file, "m14_pins_swapped_manifests": m14_pins_swapped_manifests}


def reset():
    if TARGET.exists():
        shutil.rmtree(TARGET)
    shutil.copytree(PRISTINE, TARGET)


def run_suite() -> tuple[str, int, float]:
    started = time.monotonic()
    proc = subprocess.run([PY, "-B", "-m", "pytest", "-q", "-p", "no:cacheprovider", "scripts/scale78b/tests/scorers"],
                          cwd=R, capture_output=True, text=True, env={"PYTHONDONTWRITEBYTECODE": "1", "PATH": "/usr/bin:/bin",
                                                                      "HOME": "/Users/spiderishi"})
    lines = [l for l in (proc.stdout + proc.stderr).splitlines() if l.strip()]
    summary = lines[-1] if lines else "(no output)"
    failed = [l for l in lines if l.startswith("FAILED ")]
    return summary + (" | " + "; ".join(f.split(" - ")[0][7:] for f in failed[:6]) if failed else ""), proc.returncode, time.monotonic() - started


def main(names):
    if names == ["--list"]:
        print("\n".join(sorted(list(MUTANTS) + list(SPECIAL) + ["baseline"])))
        return
    for name in names:
        reset()
        if name == "baseline":
            pass
        elif name in MUTANTS:
            fname, old, new = MUTANTS[name]
            replace(TARGET / fname, old, new)
        elif name in SPECIAL:
            SPECIAL[name]()
        else:
            raise SystemExit(f"unknown mutant {name}")
        summary, code, seconds = run_suite()
        verdict = "baseline" if name == "baseline" else ("KILLED" if code != 0 else "SURVIVED")
        row = {"mutant": name, "verdict": verdict, "pytest_exit": code, "summary": summary, "seconds": round(seconds, 1)}
        print(json.dumps(row))
        with LOG.open("a") as fh:
            fh.write(json.dumps(row) + "\n")
    reset()


if __name__ == "__main__":
    main(sys.argv[1:])
