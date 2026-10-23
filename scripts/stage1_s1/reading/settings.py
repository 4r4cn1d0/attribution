"""The pinned settings of the stage-1 reading and the sealed designs (REV3 sections 1.2-1.3, 3.5, 4.2, 6.4-6.7).

``settings/reading.json`` is loaded only if its bytes hash to SETTINGS_SHA256 (the same pin that scripts/stage1
uses for its settings). It holds the sealed designs (arms, clusters, seeds and contrasts of plan A, "block A only"
and plan B), the margin, tau_O, tau_L, the floors, the REML stop rule, the graph's weights and the texts. The
code holds no second copy of a number that the settings hold: the REML stop values and floor mode, Phi's alpha, the
interval level, the margin's tie tolerance and the reference bounds' one-sided level are all read from here.
"""

from __future__ import annotations

import hashlib
import json
import math
from dataclasses import dataclass
from fractions import Fraction
from pathlib import Path

HERE = Path(__file__).resolve().parent
SETTINGS_PATH = HERE / "settings" / "reading.json"
SETTINGS_SHA256 = "5d69af81de93bac9e36295016400e158f5ac6b3118fda8d773d3dfa63737924d"
SETTINGS_KIND = "stage1 reading settings"
SETTINGS_NAME = "reading"
READINGS = ("plan_a", "plan_a_block_a_only", "plan_b")
ENDPOINTS = ("U", "O", "L")


class Refusal(Exception):
    """A check failed; nothing is produced. The message holds names, counts and hashes only."""


def sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _no_duplicates(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refusal(f"a JSON object repeats the key {key!r}")
        out[key] = value
    return out


def _no_constant(name):
    raise Refusal(f"a JSON value is {name} (NaN and infinity are refused)")


def _finite_float(text):
    value = float(text)
    if not math.isfinite(value):
        raise Refusal("a JSON number overflows (refused)")
    return value


def strict_json(data: bytes | str):
    """JSON with no repeated key and no NaN or infinity."""
    try:
        return json.loads(data, object_pairs_hook=_no_duplicates, parse_constant=_no_constant,
                          parse_float=_finite_float)
    except ValueError:
        raise Refusal("the bytes are not valid JSON") from None


def canonical_json(doc) -> bytes:
    return (json.dumps(doc, indent=2, sort_keys=True, ensure_ascii=True) + "\n").encode()


def load_settings(path: str | Path = SETTINGS_PATH, expected_sha256: str = SETTINGS_SHA256) -> dict:
    """The settings, refused unless the file's bytes hash to the pin and the document names itself."""
    data = Path(path).read_bytes()
    digest = sha256_bytes(data)
    if digest != expected_sha256:
        raise Refusal(f"the reading settings hash to {digest}, expected {expected_sha256}")
    doc = strict_json(data)
    if not isinstance(doc, dict) or doc.get("kind") != SETTINGS_KIND or doc.get("name") != SETTINGS_NAME:
        raise Refusal("not the stage-1 reading settings")
    if doc.get("version") != 1 or set(doc["readings"]) != set(READINGS) or set(doc["endpoints"]) != set(ENDPOINTS):
        raise Refusal("the reading settings are not version 1 with the three readings and the three endpoints")
    if canonical_json(doc) != data:
        raise Refusal("the reading settings are not canonical JSON")
    return doc


_SETTINGS: dict | None = None


def settings() -> dict:
    global _SETTINGS
    if _SETTINGS is None:
        _SETTINGS = load_settings()
    return _SETTINGS


def fraction(text: str) -> Fraction:
    """An exact fraction from the settings' text form ("1/8", "1")."""
    return Fraction(text)


def alpha(doc: dict | None = None) -> Fraction:
    """Phi's familywise level as an exact fraction (settings phi.alpha, "1/20")."""
    return fraction((doc or settings())["phi"]["alpha"])


def level_per_comparison(doc: dict | None = None) -> float:
    """The per-comparison two-sided interval level (settings intervals.per_comparison, 0.90): grade 1, the
    feasibility states, the separation rule and the reference bounds' upper ends (REV3 3.2, 4.5, 4.9, 5.3, 6.4)."""
    return float((doc or settings())["intervals"]["per_comparison"])


@dataclass(frozen=True)
class Design:
    """One sealed reading: the arms with their clusters and seeds, the contrasts and the fit arms."""
    reading: str
    arms: tuple[str, ...]                 # every arm with cells (a0 included under plan B)
    fit_arms: tuple[str, ...]             # the arms of the HB-C fit (a0 is outside under plan B)
    cluster: dict                         # arm -> "full" | "removal"
    kind: dict                            # arm -> "comparator" | "removal" | "add"
    seeds: dict                           # arm -> tuple of seeds
    contrasts: tuple                      # ((name, comparator, repair), ...)
    familywise_sides: int                 # the Bonferroni count behind the familywise interval
    label_suffix: str | None

    def common_seeds(self, a: str, b: str) -> tuple[int, ...]:
        return tuple(sorted(set(self.seeds[a]) & set(self.seeds[b])))

    def cluster_arms(self, cluster: str) -> tuple[str, ...]:
        return tuple(arm for arm in self.fit_arms if self.cluster[arm] == cluster)

    def same_cluster(self, a: str, b: str) -> bool:
        return self.cluster[a] == self.cluster[b]

    def in_fit(self, arm: str) -> bool:
        return arm in self.fit_arms

    @property
    def removal_arms(self) -> tuple[str, ...]:
        return tuple(arm for arm in self.arms if self.kind[arm] == "removal")

    @property
    def repair_arms(self) -> tuple[str, ...]:
        return tuple(arm for arm in self.arms if self.kind[arm] != "comparator")


def design(reading: str, doc: dict | None = None) -> Design:
    doc = doc or settings()
    if reading not in doc["readings"]:
        raise Refusal(f"unknown reading {reading!r}; the sealed readings are {READINGS}")
    spec = doc["readings"][reading]
    arms = tuple(spec["seeds"])
    return Design(reading=reading, arms=arms, fit_arms=tuple(spec["fit_arms"]),
                  cluster={arm: doc["arms"][arm]["cluster"] for arm in arms},
                  kind={arm: doc["arms"][arm]["kind"] for arm in arms},
                  seeds={arm: tuple(int(s) for s in spec["seeds"][arm]) for arm in arms},
                  contrasts=tuple((name, doc["contrasts"][name]["comparator"], doc["contrasts"][name]["repair"])
                                  for name in spec["contrasts"]),
                  familywise_sides=int(spec["familywise_sides"]), label_suffix=spec["label_suffix"])


def module_hashes() -> dict:
    """SHA-256 of every Python file of the package and of the settings (for the output's provenance)."""
    out = {}
    for path in sorted(HERE.glob("*.py")):
        out[path.name] = sha256_bytes(path.read_bytes())
    out["settings/reading.json"] = sha256_bytes(SETTINGS_PATH.read_bytes())
    return out
