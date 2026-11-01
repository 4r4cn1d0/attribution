"""The S-a shift line: P4's pre-registered expected shift under S-a, printed beside the measured one (REV4 3.4;
report only). Exit 0: the file written; 2: refused, nothing written.

    python -m scripts.stage1_s1.reading_extra.sa_shift --reading reading.json --out sa_shift.json

``reading.json`` is B16's output (its pinned settings and sealed contrasts are checked). REV4 =
research/experiments/2026-10-17-stage1-preregistration-rev3/stage1-preregistration-rev4.md (frozen).

The frozen rule, REV4:276: "Expected shift from the seen cells: P4 under S-a is expected to read about 0.3 pp less in
S1's favour than under HB (−0.28 pp for S-a − HB, M (VR-B), computed under D0); the record prints it." S-a and HB are
REV4 3.4's sensitivities (REV4:265-266), each printed by B16 under sensitivities["S-a"] and sensitivities["HB"] with
U_k's orientation (comparator minus repair; for P4 = a0 - S1, positive = S1 restores more, so "less in S1's favour"
is a negative S-a - HB). The line copies the expectation as written and puts beside it the measured S-a - HB of P4's
U estimates (one subtraction of two numbers B16 printed). READINGS gives each reading and its alternative.
"""

from __future__ import annotations

from scripts.stage1_s1.reading.settings import Refusal
from scripts.stage1_s1.reading_extra import common

KIND = "stage1 reading S-a shift line"
CONTRAST = "P4"
EXPECTED_SHIFT_PP = -0.28                          # REV4:276, S-a - HB, M (VR-B), computed under D0
EXPECTED_TEXT = ("Expected shift from the seen cells: P4 under S-a is expected to read about 0.3 pp less in S1's "
                 "favour than under HB (−0.28 pp for S-a − HB, M (VR-B), computed under D0); the record prints it.")
RULE = ["REV4:276: " + EXPECTED_TEXT,
        "REV4:265-266: HB (one seed shift for all eight arms); S-a (PLAN-S:102: unpaired means, variance pooled over "
        "the eight primary arms, \"df 42 (nominal)\"), with its equal-variance flag."]
READINGS = {
    "A1": "The record prints the expectation as written (the constant -0.28 pp and its text) and, beside it, the "
          "measured S-a - HB of P4's U estimates from B16's sensitivities; the expectation is not a test and was "
          "computed under D0, not D1. Alternative: the expectation alone.",
    "A2": "A reading without P4 (plan B: P1, P3, P6) prints the expectation with \"not applicable\". Alternative: no "
          "line at all."}


def line(reading_doc: dict, reading_sha256: str) -> dict:
    """The whole output (module doc)."""
    dsg = common.bound_reading(reading_doc)
    names = [name for name, _, _ in dsg.contrasts]
    measured = None
    if CONTRAST in names:
        sens = reading_doc.get("sensitivities") if isinstance(reading_doc.get("sensitivities"), dict) else {}
        est = {}
        for code in ("S-a", "HB"):
            e = ((sens.get(code) or {}).get(CONTRAST) or {}).get("estimate")
            if not isinstance(e, dict):
                raise Refusal(f"B16's output holds no {code} estimate of {CONTRAST}")
            est[code] = common.number(e.get("est"), f"the {code} estimate of {CONTRAST}")
        primary = ((reading_doc.get("contrasts") or {}).get(CONTRAST) or {}).get("U") or {}
        shift = est["S-a"] - est["HB"]
        measured = {"s_a_estimate_pp": est["S-a"], "hb_estimate_pp": est["HB"],
                    "primary_estimate_pp": common.number(primary.get("est"), f"the primary U estimate of {CONTRAST}"),
                    "s_a_minus_hb_pp": shift,
                    "direction": ("less in S1's favour" if shift < 0 else "more in S1's favour" if shift > 0
                                  else "no shift"),
                    "expected_direction_holds": shift < 0}
    out = {"kind": KIND, "version": 1, "reading": dsg.reading, "label_suffix": dsg.label_suffix,
           "rule": list(RULE), "readings": dict(READINGS),
           "contrast": CONTRAST, "applies": measured is not None,
           "expected": {"s_a_minus_hb_pp": EXPECTED_SHIFT_PP, "text": EXPECTED_TEXT, "computed_under": "D0",
                        "source": "M (VR-B)"},
           "measured": measured,
           "note": (None if measured is not None else
                    f"not applicable: {CONTRAST} is not a contrast of the reading {dsg.reading}"),
           "provenance": common.provenance({"reading.json": reading_sha256})}
    return common.finish(out)


def main(argv=None) -> int:
    def arguments(p):
        p.add_argument("--reading", required=True, help="B16's reading.json")

    def produce(args):
        doc, sha = common.read_document(args.reading, "the reading file")
        return line(doc, sha), []

    return common.main_frame("python -m scripts.stage1_s1.reading_extra.sa_shift",
                             "the S-a shift line (REV4:276)", arguments, produce, argv)


if __name__ == "__main__":
    raise SystemExit(main())
