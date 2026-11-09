"""K2V probe: every file record-done of block A creates or changes (outside the planted pulled trees) is scanned."""
import hashlib
import json
from pathlib import Path
import test_planning_ab_78b as T
from test_planning_ab_78b import wa  # noqa: F401


def snap(root: Path) -> dict:
    return {p: hashlib.sha256(p.read_bytes()).hexdigest() for p in root.rglob("*") if p.is_file()}


def test_p10_every_new_or_changed_file_is_free_of_planted_values(wa, capsys):
    w = wa
    hosts = T.released_a(w)
    for host in hosts:
        T.pull_planted(w, host)
    capsys.readouterr()
    before = snap(w.repo)
    for host in hosts:
        assert w.tool.main(["record-done", host]) == 0
    out = capsys.readouterr()
    after = snap(w.repo)
    changed = sorted(p for p, d in after.items() if before.get(p) != d)
    print("P10 changed files:", [p.relative_to(w.repo).as_posix() for p in changed])
    hits = [(p.name, s) for p in changed for s in T.SENTINELS if s in p.read_text(errors="replace")]
    assert hits == [] and not any(s in out.out + out.err for s in T.SENTINELS)
