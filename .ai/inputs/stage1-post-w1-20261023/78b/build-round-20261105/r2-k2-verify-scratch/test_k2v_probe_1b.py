"""K2V probe: the other 1B block-A record commands in a 7-8B block-A copy."""
import json
import pytest
import test_planning_ab_78b as T
from test_planning_ab_78b import wa  # noqa: F401


@pytest.mark.parametrize("cmd", ["record-block-a-plan", "record-block-a-replan", "record-block-a-not-run"])
def test_p7b(wa, capsys, cmd):
    w = wa
    hosts = T.released_a(w)
    rec = w.record({"kind": "stage1 block-a not-run decision", "jobs": ["arm A1 1102"], "reason": "r",
                    "utc": "2026-11-20T12:00:00+00:00", "recorded_by": "t"}, f"{cmd}.json")
    try:
        w.tool.main([cmd, str(rec), "--sha256", T.sha(rec)])
        result = "ran: " + capsys.readouterr().out[:200]
    except SystemExit as exc:
        result = "refused: " + str(exc)[:200]
    except Exception as exc:
        result = f"crashed: {type(exc).__name__}: {str(exc)[:150]}"
    print("P7b", cmd, "->", result)
