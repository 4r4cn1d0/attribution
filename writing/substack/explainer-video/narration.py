"""Build the explainer's narration with Kokoro-82M, offline: one mastered WAV per scene, word times, subtitles.

Input: script.json and the reviewed script (script-and-storyboard.md).

    {"voice": "af_heart",
     "scenes": [{"key": "S01", "title": "The case", "tail": 0.6,
                 "lines": [{"text": "exact words", "pause_after": 0.5, "speed": 1.0,
                            "say": "exact words with [reviewed](+2) pronunciation markup", "pauses": {"word,": 0.2}}]}]}

"pause_after" is seconds, or short (0.30 s), normal (0.50 s) or long (0.90 s); it is the time from the end of the
line's last word to the start of the next line's first word.  "speed", "say", "pauses" and "tail" are optional.
"pauses" sets the length of a pause that Kokoro makes after a word inside the line.  Keys that start with "_" are
ignored.

The last line of a scene: its pause runs across the scene boundary (the scene's tail, then the 0.40 s before the
next scene's first word).  The tail is 0.6 s (1.5 s for the last scene), or longer if that pause asks for more;
"tail" on the scene sets it directly.

The safety rule: every spoken line must appear word for word, and in order, in the narration that the reviewed
script marks (a paragraph "- **Narration:** ...", or the cells of a table column named "Words to speak", "Words",
"Spoken words", "Narration" or "Voice-over"; --narration-column adds a name), and nothing of that narration may
stay unspoken.  Where the reviewed script has numbered scene headings ("### S03 Title", "### 3. Title"), the
lines of scene S03 must stand under a heading of scene 3: a line cannot move to another scene.  A reviewed script
that marks no narration stops the build; --whole-file looks each line up in the whole file instead, and then the
check cannot tell whether a reviewed sentence was left out.  A line's "text" holds only the letters a to z,
digits and the marks . , ; : ! ? ' " ( ) % - — … and curly quotes (a hidden or look-alike character would be
spelt out).  "say" may add markup from the reviewed table below but no words.  Kokoro's own text analysis must
give back exactly the words of the line (no skipped word, no dropped phoneme, no second call), and a word that
its dictionary does not hold stops the build unless its fallback reading is in FALLBACK_READINGS.  The build
report lists every override and every pronunciation risk for the ear.

Output in --out (default tmp/explainer-build-v2/audio): <SceneKey>.wav (48 kHz, mono, 16 bit; the whole programme
is mastered with one gain to -16 LUFS; the limiter's ceiling is -2.5 dBTP, so that the true peak stays under
-1.5 dBTP after the film's AAC encode too), timings.json, narration.srt, build_report.txt
and cache/ (a line is synthesised once; a pause change re-builds in seconds).

timings.json holds what INTERFACES.md names (wav, duration, starts, sentences with words, cues, _meta) and more.
Per scene: "frames" (the duration in frames at 15, 30 and 60 fps), "tail", "lufs", "title", and "built_from" (a
fingerprint of the scene's lines; narration_verify.py works out the same value from script.json by itself).  In
_meta: the mastering gain, "overrides", and "missing", "stale" and "partial_since_full" (scenes that builds with
--only left unbuilt, left out of date, or built alone).

Timing rules: the first word of a scene starts at 0.40 s; "duration" is the end of the last word plus the tail,
rounded up to a multiple of 1/15 s (a whole number of frames at 15, 30 and 60 fps), and the WAV has exactly that
length.  Word times are Kokoro's own inside running speech and the sound's own edges next to a silence (plan for
about +-30 ms; a short word that follows a silence keeps at least 40 ms).

Run from the project root (no network is used):

    tmp/explainer-venv/bin/python writing/substack/explainer-video/narration.py
        [--script script.json] [--reviewed script-and-storyboard.md] [--out DIR] [--voice af_heart]
        [--only S03 S04] [--check-only] [--allow-unspoken] [--narration-column NAME] [--whole-file]
        [--device cpu|mps] [--lufs -16] [--pitch-range 1.0]

--check-only runs the safety checks and prints the word count, the estimated length and every pronunciation risk,
without synthesis (it loads Kokoro's text analysis, which takes some seconds).  --only builds some scenes with the
gain of the last full build and names the scenes that it left as they were although the script changed them.  Then run narration_verify.py: it fails when a scene's audio
is older than the script, and without --only also when scenes were built with --only since the last full build.

For scene code: word_time(timings, "S03", 2, "gate") gives the scene time at which that word of line 2 starts.
"""

from __future__ import annotations

import argparse
import difflib
import functools
import hashlib
import io
import json
import os
import re
import sys
import time
import unicodedata
import warnings
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import soundfile as sf

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
os.environ.setdefault("HF_HOME", str(ROOT / "tmp" / "explainer-hf"))
os.environ["HF_HUB_OFFLINE"] = "1"                      # the builder never downloads
sys.path.insert(0, str(HERE))
import narration_audio as fx  # noqa: E402

BUILD = Path(os.environ.get("EXPLAINER_BUILD") or ROOT / "tmp" / "explainer-build-v2")
DEFAULT_SCRIPT, DEFAULT_REVIEWED, DEFAULT_OUT = HERE / "script.json", HERE / "script-and-storyboard.md", BUILD / "audio"

REPO, VOICE, SEED = "hexgrad/Kokoro-82M", "af_heart", 0
RATE, OUT_RATE, GRID_FPS = 24000, 48000, 15             # Kokoro's rate; the WAVs' rate; durations are multiples of 1/15 s
LEAD, TAIL, LAST_TAIL = 0.40, 0.60, 1.50                # before a scene's first word; after its last word
PAUSE_NAMES = {"short": 0.30, "normal": 0.50, "long": 0.90}
PAUSE_RANGE, INNER_RANGE, TAIL_RANGE, SPEED_RANGE = (0.15, 5.0), (0.05, 3.0), (0.30, 5.0), (0.80, 1.20)
TRIM_DB, PRE_ROLL, POST_ROLL = -50.0, 0.020, 0.060      # what is kept of a Kokoro call around its speech
FADE_IN, FADE_OUT, SPLICE_FADE = 0.005, 0.020, 0.004
EDGE_DB, PAUSE_MIN, GAP_MIN = -40.0, 0.120, 0.050       # silence: dB below the line's loudest 10 ms; a pause; a short gap
BLIP_DB, BLIP_MAX = -30.0, 0.150                        # a sound this weak and short inside a pause is a breath
MIN_KEEP = 0.030                                        # a pause is never cut shorter than this at its quietest part
MIN_WORD = 0.040                                        # a word that starts at the sound's edge is never shorter than this
TARGET_LUFS, PEAK_LIMIT_DBTP = -16.0, -1.5
CEILING_DBTP = -2.5                                     # the limiter's ceiling: the AAC encode of the film adds up to 0.2 dB (measured)
MAX_PHONEMES = 510                                      # Kokoro's context; a longer call is split or truncated
LINE_CHARS, CUE_MIN, CUE_GAP, CUE_HOLD = 42, 1.0, 0.08, 0.6
WORD_TARGET, WORD_MAX = (520, 600), 620                 # the design brief's length for the whole script

# The only phoneme overrides that "say" may use (word in lower case -> phonemes -> what a listener should hear).
# The script check cannot prove that phonemes say the written word, so a person reviews this table and listens.
PRONUNCIATIONS: dict[str, dict[str, str]] = {
    "1,440": {"fˌɔɹtˈin fˈɔɹTi": "fourteen forty (Kokoro's own reading: one thousand four hundred forty)"},
    "one-step": {"wˈʌnstˌɛp": "ONE-step, like Kokoro's TWO-step (its own reading: one-STEP)"},
    "retraining": {"ɹitɹˈAnɪŋ": "REE-training, like Kokoro's retrain (its own reading has a weak first vowel)"},
    "ai": {"ˌAˈI": "A-I with the stress on I (Kokoro's own reading stresses the A)"},
    "post-training": {"pˈOst tɹˈAnɪŋ": "POST TRAINing, two stresses (Kokoro's own reading: one word, stress on train)"},
}
# Words that Kokoro's dictionary does not hold, with the reading of its fallback that was accepted (word in lower
# case -> phonemes -> what a listener should hear).  A fallback reading that is not here stops the build.
FALLBACK_READINGS: dict[str, dict[str, str]] = {
    "underway": {"ˌʌndəɹwˈA": "under-WAY, as in version 1 (accepted from its phonemes; not yet heard by a person)"},
}
# Words that the TTS probe found risky; --check-only names them when the script uses them without an override.
KNOWN_RISKS = {
    "1,440": "read as 'one thousand four hundred forty' (about 1.6 s); 'fourteen forty' is in PRONUNCIATIONS",
    "1440": "read as a year, 'fourteen forty'; write 1,440 and choose the reading with 'say'",
    "ai": "stress on the A; an override with the stress on I is in PRONUNCIATIONS",
    "post-training": "one word with the stress on 'train'; a two-stress override is in PRONUNCIATIONS",
    "retraining": "weak first vowel, unlike 'retrain'; an override is in PRONUNCIATIONS",
    "one-step": "'one-STEP' beside 'TWO-step'; write 'one- or two-step' or use the override",
    "logits": "read as 'lodge-its'",
    "tracin": "read as 'track in'",
}
HETERONYMS = frozenset("""estimate estimates read lead live close use uses used record records present object content
refuse project projects separate minute wind tear coordinate duplicate alternate approximate associate contrast
produce increase decrease conduct subject permit contract perfect learned""".split())
PHONEMES_PER_SECOND = {"af_heart": 13.4, "am_michael": 12.2}   # measured while speaking; used only for estimates

MARKUP = re.compile(r"\[([^\]\[]+)\]\(([^)]*)\)")
STRESS_OK, FLAGS_OK = re.compile(r"[+-]?[012]|[+-]?0\.5"), re.compile(r"#[&an]*#")
NARRATION = re.compile(r"^(\s*)(?:[-+*]\s+)?(?:\*\*|__)?\s*(?:narration|voice-?over)(?:\s*\([^)]*\))?"
                       r"\s*(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(.*)$", re.I)
HEADING, SCENE_HEADING = re.compile(r"^#{1,6}\s+(.*)$"), re.compile(r"(?:scene\s*)?S?(\d{1,2})\b", re.I)
ITEM = re.compile(r"^\s*(?:[-+*]\s|\d+[.)]\s|#{1,6}\s|\|)")
LIST_PREFIX = re.compile(r"^\s*(?:>\s*)*(?:(?:[-+*]|\d+[.)])\s+)?")
TABLE_ROW, TABLE_RULE = re.compile(r"^\s*\|"), re.compile(r"^\s*\|?(?:\s*:?-+:?\s*\|)+\s*(?::?-+:?\s*)?$")
SPOKEN_COLUMN = re.compile(r"words(?: to speak)?|spoken(?: words| text)?|text to speak|narration|voice-?over", re.I)
PUNCT_PHONEMES = frozenset(';:,.!?—…"“”()')
TEXT_MARKS = frozenset(" .,;:!?'\"()%-—…’‘“”")           # what a line's text may hold besides a-z, A-Z and 0-9
SYMBOL_WORDS = frozenset("%&+@")                        # Kokoro speaks these when they stand alone


# ---------------------------------------------------------------- the script
@dataclass
class Line:
    text: str
    pause_after: float
    speed: float = 1.0
    say: str | None = None
    pauses: dict[str, float] = field(default_factory=dict)

    @property
    def spoken(self) -> str:
        return squash(self.say if self.say is not None else self.text)


@dataclass
class Scene:
    key: str
    title: str
    lines: list[Line]
    tail: float
    tail_from: str = "default"      # "script" (the scene's "tail"), "pause" (the last line's pause_after) or "default"
    last: bool = False              # the last scene of the script

    @property
    def fingerprint(self) -> str:
        """Changes when anything that the scene's audio is built from changes (the voice apart)."""
        said = [[ln.text, ln.pause_after, ln.speed, ln.say, sorted(ln.pauses.items())] for ln in self.lines]
        return hashlib.sha256(json.dumps([said, self.tail], ensure_ascii=False).encode()).hexdigest()[:16]


def squash(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def fold(text: str) -> str:
    """The form in which the script and the reviewed text are compared: one space, straight quotes."""
    return squash(text.replace("’", "'").replace("‘", "'").replace("“", '"').replace("”", '"'))


def strip_markup(text: str) -> str:
    return MARKUP.sub(lambda m: m.group(1), text)


def split_words(text: str) -> list[str]:
    """The written words of a text (split at spaces); a mark that stands alone, such as a spaced dash, joins the
    word before it.  written_words() groups Kokoro's tokens in the same way."""
    out: list[str] = []
    pending = ""
    for item in text.split():
        if any(c.isalnum() for c in item) or item in SYMBOL_WORDS:
            out.append(pending + item)
            pending = ""
        elif out:
            out[-1] += " " + item
        else:
            pending += item + " "
    return out


def marked_words(say: str) -> dict[int, tuple[str, str]]:
    """{index of the written word: (word, markup)} for every [word](markup) of a 'say' text."""
    return {len(split_words(strip_markup(say[:m.start()]) + "x")) - 1: (m.group(1), m.group(2)) for m in MARKUP.finditer(say)}


def bare(word: str) -> str:
    """A written word without the punctuation around it, in lower case: 'gate:' -> 'gate', '18.5%.' -> '18.5'."""
    return re.sub(r"^\W+|\W+$", "", word).lower()


def _seconds(value, where: str, limits: tuple[float, float], problems: list[str]) -> float:
    if isinstance(value, str) and value.strip() in PAUSE_NAMES:
        return PAUSE_NAMES[value.strip()]
    if isinstance(value, str) and re.fullmatch(r"\s*\d+(?:\.\d+)?\s*s?\s*", value):     # "1.6 s" as in the script tables
        value = float(value.strip().rstrip("s"))
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        problems.append(f"{where}: {value!r} is not a number of seconds or one of {', '.join(PAUSE_NAMES)}")
        return limits[0]
    if not limits[0] <= value <= limits[1]:
        problems.append(f"{where}: {value} s is outside {limits[0]} to {limits[1]} s")
    return float(value)


def _extra_keys(obj: dict, known: tuple[str, ...], where: str, problems: list[str], unused: dict[str, list[str]]) -> None:
    """A key that looks like a misspelt known key is a problem; any other unknown key is only counted."""
    for k in obj:
        if k in known or k.startswith("_"):
            continue
        near = difflib.get_close_matches(k, known, n=1, cutoff=0.6)
        if near:
            problems.append(f"{where}: unknown key {k!r} (did you mean {near[0]!r}?)")
        else:
            unused.setdefault(k, []).append(where)


def _odd_characters(text: str) -> list[str]:
    """Characters that a line's text may not hold: a hidden or look-alike character passes a comparison with the
    reviewed text when both files have it, and Kokoro then spells the word out or reads it wrongly."""
    odd = {c: next((w for w in text.split() if c in w), text) for c in text if not (c.isascii() and c.isalnum()) and c not in TEXT_MARKS}
    return [f"the character {c!r} (U+{ord(c):04X}, {unicodedata.name(c, 'no name').lower()}) in {word!r} is not allowed in 'text': "
            "only the letters a to z, digits and . , ; : ! ? ' \" ( ) % - — … and curly quotes" for c, word in odd.items()]


def load_script(path: Path) -> tuple[str, list[Scene], list[str]]:
    """(voice, scenes, notes) from script.json; stops with every format problem at once."""
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        raise SystemExit(f"cannot read {path}: {e}")
    problems, unused, scenes = [], {}, []
    if not isinstance(data, dict) or not isinstance(data.get("scenes"), list) or not data["scenes"]:
        raise SystemExit(f"{path}: expected an object with a non-empty list 'scenes'")
    _extra_keys(data, ("voice", "scenes"), "script", problems, unused)
    voice = data.get("voice", VOICE)
    if not isinstance(voice, str) or not re.fullmatch(r"[a-z]{2}_[a-z0-9]+", voice):
        problems.append(f"script: voice {voice!r} is not a Kokoro voice name such as af_heart")
    for si, sc in enumerate(data["scenes"]):
        key = sc.get("key") if isinstance(sc, dict) else None
        if not isinstance(key, str) or not re.fullmatch(r"S\d{2}", key):
            problems.append(f"scene {si}: key {key!r} is not S01, S02, ...")
            continue
        if key in [s.key for s in scenes]:
            problems.append(f"{key}: the key is used twice")
        _extra_keys(sc, ("key", "title", "lines", "tail"), key, problems, unused)
        last = si == len(data["scenes"]) - 1
        lines = []
        if not isinstance(sc.get("lines"), list) or not sc["lines"]:
            problems.append(f"{key}: 'lines' must be a non-empty list")
        for li, ln in enumerate(sc.get("lines") or []):
            where = f"{key} line {li}"
            if not isinstance(ln, dict) or not isinstance(ln.get("text"), str) or not ln["text"].strip():
                problems.append(f"{where}: needs a non-empty 'text'")
                continue
            if MARKUP.search(ln["text"]) or "](" in ln["text"]:
                problems.append(f"{where}: markup belongs in 'say', not in 'text': {squash(ln['text'])}")
            else:
                problems += [f"{where}: {p}" for p in _odd_characters(squash(ln["text"]))]
            _extra_keys(ln, ("text", "pause_after", "speed", "say", "pauses"), where, problems, unused)
            if "pause_after" not in ln:
                problems.append(f"{where}: needs 'pause_after' (seconds, or short / normal / long)")
            speed = ln.get("speed", 1.0)
            if isinstance(speed, bool) or not isinstance(speed, (int, float)) or not SPEED_RANGE[0] <= speed <= SPEED_RANGE[1]:
                problems.append(f"{where}: speed {speed!r} is outside {SPEED_RANGE[0]} to {SPEED_RANGE[1]}")
                speed = 1.0
            say, pauses = ln.get("say"), ln.get("pauses", {})
            if say is not None and not isinstance(say, str):
                problems.append(f"{where}: 'say' must be text")
                say = None
            if not isinstance(pauses, dict):
                problems.append(f"{where}: 'pauses' must be an object such as {{\"gate:\": 0.5}}")
                pauses = {}
            pause = _seconds(ln.get("pause_after", "normal"), f"{where} pause_after", PAUSE_RANGE, problems)
            inner = {str(a): _seconds(v, f"{where} pause after {a!r}", INNER_RANGE, problems) for a, v in pauses.items()}
            lines.append(Line(text=squash(ln["text"]), pause_after=pause, speed=float(speed), say=say, pauses=inner))
        # The last line's pause runs across the scene boundary: the tail, then the lead of the next scene.
        tail, tail_from = (LAST_TAIL if last else TAIL), "default"
        asked = lines[-1].pause_after - (0.0 if last else LEAD) if lines else 0.0
        if "tail" in sc:
            tail, tail_from = _seconds(sc["tail"], f"{key} tail", TAIL_RANGE, problems), "script"
        elif asked > tail + 1e-9:
            tail, tail_from = round(asked, 3), "pause"
        scenes.append(Scene(key=key, title=str(sc.get("title", "")), lines=lines, tail=tail, tail_from=tail_from, last=last))
    if problems:
        raise SystemExit(f"{path.name} is not in the script.json format:\n  " + "\n  ".join(problems))
    notes = [f"key {k!r} is not used by the narration builder ({where[0] if len(where) == 1 else f'{len(where)} places, first in {where[0]}'})"
             for k, where in unused.items()]
    return voice, scenes, notes


# ---------------------------------------------------------------- the safety rule (no model needed)
def _cells(row: str) -> list[str]:
    """The cells of one row of a Markdown table."""
    cells = [c.replace("\\|", "|").strip() for c in re.split(r"(?<!\\)\|", row.strip())]
    return cells[1:-1] if row.strip().endswith("|") and len(cells) > 2 else cells[1:]


def narration_blocks(markdown: str, columns: tuple[str, ...] = ()) -> tuple[list[tuple[int | None, str]], list[str], str]:
    """What the reviewed script marks as narration, in order: paragraphs ('- **Narration:** ...') and the cells of
    a table column named 'Words to speak', 'Words', 'Spoken words', 'Narration' or 'Voice-over', or named in
    ``columns`` (cells without a letter are not narration).  Where the script has numbered scene headings
    ('### 3. Title', '## Scene 3', '### S03 ...'), only what stands under them counts, and each piece keeps the
    number of its heading; the rest is returned apart, so that a build can name it.
    Returns (narration as (scene number or None, text), marked text left out, where the narration was found)."""
    lines, found, scene, any_scene, i = markdown.splitlines(), [], None, False, 0
    named = {c.strip().lower() for c in columns}
    while i < len(lines):
        heading, m = HEADING.match(lines[i]), NARRATION.match(lines[i])
        i += 1
        if heading:
            number = SCENE_HEADING.match(heading.group(1))
            scene = int(number.group(1)) if number else None
            any_scene |= scene is not None
        if TABLE_ROW.match(lines[i - 1]) and i < len(lines) and TABLE_RULE.match(lines[i]):
            head = [c.replace("*", "").replace("`", "").strip() for c in _cells(lines[i - 1])]
            col = next((k for k, c in enumerate(head) if SPOKEN_COLUMN.fullmatch(c) or c.lower() in named), None)
            i += 1
            rows = []
            while i < len(lines) and TABLE_ROW.match(lines[i]):
                rows.append(_cells(lines[i]))
                i += 1
            cells = [r[col] for r in rows if col is not None and col < len(r) and any(c.isalpha() for c in r[col])]
            if cells:
                found.append((scene, " ".join(cells), "table"))
            continue
        if not m:
            continue
        indent, parts = len(m.group(1)), [m.group(2)]
        while i < len(lines):
            raw = lines[i]
            if not raw.strip():
                following = next((x for x in lines[i + 1:] if x.strip()), "")
                if len(following) - len(following.lstrip()) <= indent:
                    break
            elif len(raw) - len(raw.lstrip()) <= indent and (ITEM.match(raw) or NARRATION.match(raw)):
                break
            else:
                parts.append(LIST_PREFIX.sub("", raw))
            i += 1
        found.append((scene, " ".join(parts), "paragraph"))
    used = [(n, t, kind) for n, t, kind in found if n is not None or not any_scene]
    count = {kind: sum(k == kind for *_, k in used) for kind in ("table", "paragraph")}
    source = " and ".join(f"{n} {'narration column' if kind == 'table' else 'Narration: paragraph'}{'s' if n > 1 else ''}"
                          for kind, n in count.items() if n)
    return [(n, t) for n, t, _ in used], [t for n, t, _ in found if any_scene and n is None], source


def reviewed_text(markdown: str, columns: tuple[str, ...] = ()) -> tuple[str, str, list[str]]:
    """(the reviewed narration in the form in which lines are compared with it, or the whole file if the reviewed
    script marks none; where the marked narration was found, or ''; marked narration that was left out)."""
    blocks, ignored, source = narration_blocks(markdown, columns)
    text = " ".join(t for _, t in blocks) if blocks else "\n".join(LIST_PREFIX.sub("", x) for x in markdown.splitlines())
    return fold(text.replace("*", "")), source, [fold(t.replace("*", "")) for t in ignored]


def _find_words(hay: str, needle: str, start: int) -> int:
    """Index of needle in hay at or after start, where it does not begin or end inside a word; -1 if none."""
    k = hay.find(needle, start)
    while k >= 0:
        end = k + len(needle)
        if (k == 0 or not hay[k - 1].isalnum()) and (end == len(hay) or not hay[end].isalnum()):
            return k
        k = hay.find(needle, k + 1)
    return -1


def _closest(hay: str, needle: str) -> str:
    """The passage of the reviewed text that is most like the line (to show what differs)."""
    words, target = hay.split(), needle.split()
    n = len(target)
    if len(words) <= n:
        return hay
    hits = {w.lower() for w in target}
    starts = [i for i in range(len(words) - n + 1) if sum(w.lower() in hits for w in words[i:i + n]) >= n / 3] or [0]
    best = max(starts, key=lambda i: difflib.SequenceMatcher(None, target, words[i:i + n], autojunk=False).ratio())
    return " ".join(words[best:best + n])


def check_script(scenes: list[Scene], markdown: str, allow_unspoken: bool = False, whole_file: bool = False,
                 columns: tuple[str, ...] = ()) -> tuple[list[str], list[str]]:
    """The safety rule.  Returns (problems, notes); a build stops on any problem.  notes[0] states what was checked."""
    blocks, ignored, marked = narration_blocks(markdown, columns)
    by_scene = bool(blocks) and blocks[0][0] is not None        # numbered scene headings: every piece has its scene's number
    hays: dict[int | None, str] = {}                            # the reviewed narration of each scene (None: of the whole film)
    for number, text in blocks:
        hays[number] = (hays[number] + " " if number in hays else "") + fold(text.replace("*", ""))
    if not blocks:
        hays[None] = reviewed_text(markdown)[0]
    whole, where_from = " ".join(hays.values()), "narration" if marked else "script"
    problems, notes, pos, gaps, broken = [], [], dict.fromkeys(hays, 0), {}, set()
    for scene in scenes:
        n = int(scene.key[1:]) if by_scene else None
        hay = hays.get(n)
        if hay is None:
            problems.append(f"{scene.key}: the reviewed script has no narration under a heading of scene {n} "
                            f"(it has narration under headings of scene {', '.join(map(str, sorted(hays)))})")
        for li, line in enumerate(scene.lines):
            where = f"{scene.key} line {li}"
            needle = fold(line.text)
            if MARKUP.search(line.text) or "](" in line.text:
                problems.append(f"{where}: markup belongs in 'say', not in 'text': {line.text}")
            k = -1 if hay is None else _find_words(hay, needle, pos[n])
            if k >= 0:
                gaps.setdefault(n, []).append(hay[pos[n]:k].strip())
                pos[n] = k + len(needle)
            elif hay is not None and _find_words(hay, needle, 0) >= 0:
                broken.add(n)
                problems.append(f"{where}: out of order: the reviewed {where_from} has this line before the line "
                                f"that is spoken just before it: {line.text}")
            elif hay is not None:
                broken.add(n)
                home = next((m for m, other in hays.items() if m != n and _find_words(other, needle, 0) >= 0), None)
                if home is not None:
                    problems.append(f"{where}: in the wrong scene: the reviewed narration has this line under the heading of "
                                    f"scene {home}, not of scene {n}: {line.text}")
                else:
                    problems.append(f"{where}: not in the reviewed {where_from}, word for word: {line.text}\n"
                                    f"      the closest reviewed text is: {_closest(whole, needle)}")
            problems += [f"{where}: {p}" for p in _say_problems(line)]
            for anchor in line.pauses:
                hits = _anchor_hits(split_words(line.text), anchor)
                if len(hits) != 1:
                    problems.append(f"{where}: pause anchor {anchor!r} is {'not a word' if not hits else 'more than one word'} "
                                    f"(with its punctuation) of: {line.text}")
                elif hits[0] == len(split_words(line.text)) - 1:
                    problems.append(f"{where}: pause anchor {anchor!r} is the last word of the line; use pause_after")
    # What the reviewed narration holds between and after the spoken lines (not looked for where a line was not found).
    unspoken = [(n, u) for n, hay in hays.items() if marked and n not in broken for u in gaps.get(n, []) + [hay[pos[n]:].strip()] if u]
    of = lambda n: "" if n is None else f" of scene {n}"                               # noqa: E731
    if unspoken and not allow_unspoken:
        problems += [f"in the reviewed narration{of(n)} but not spoken: {u}" for n, u in unspoken]
        problems.append("(if the script is meant to leave reviewed narration out, pass --allow-unspoken)")
    elif unspoken:
        notes += [f"in the reviewed narration{of(n)} but not spoken (--allow-unspoken): {u}" for n, u in unspoken]
    if not marked and whole_file:
        notes.append("--whole-file: the reviewed script marks no narration, so each line was looked up in the whole file and the check "
                     "cannot tell whether a reviewed sentence was left out")
    elif not marked:
        problems.append("the reviewed script marks no narration (no 'Narration:' paragraph, and no table column named 'Words to speak', "
                        "'Words', 'Spoken words', 'Narration' or 'Voice-over'), so the check cannot tell whether a reviewed sentence was "
                        "left out; name the column with --narration-column NAME, or pass --whole-file to look each line up in the whole file")
    notes += [f"marked narration outside the numbered scene sections of the reviewed script was not taken as narration: {t}" for t in ignored]
    done = (f"{sum(len(s.lines) for s in scenes)} lines in {len(scenes)} scenes appear word for word and in order in the reviewed {where_from}"
            + (f" ({marked}{'; each scene under its own heading' if by_scene else ''})" if marked else ""))
    notes.insert(0, done + ("; nothing of the reviewed narration is left unspoken" if marked and not unspoken else ""))
    return problems, notes


def _say_problems(line: Line) -> list[str]:
    if line.say is None:
        return []
    out = []
    if squash(strip_markup(line.say)) != line.text:
        out.append(f"'say' changes the text (only markup may be added): {line.say}")
    if "[" in strip_markup(line.say) or "](" in strip_markup(line.say):
        out.append(f"'say' has markup that is not of the form [word](...): {line.say}")
    for m in MARKUP.finditer(line.say):
        word, spec = m.group(1), m.group(2)
        if " " in word.strip() or word != word.strip():
            out.append(f"markup must mark one written word: {m.group(0)}")
        elif spec.startswith("/") and spec.endswith("/") and len(spec) > 2:
            if spec[1:-1] not in PRONUNCIATIONS.get(word.lower(), {}):
                out.append(f"phonemes for {word!r} are not in the reviewed PRONUNCIATIONS table: {m.group(0)}")
        elif FLAGS_OK.fullmatch(spec):
            if not any(c.isdigit() for c in word):
                out.append(f"a number flag needs a numeral: {m.group(0)}")
        elif not STRESS_OK.fullmatch(spec):
            out.append(f"markup not allowed (use reviewed /phonemes/, a stress from -2 to +2, or #&#): {m.group(0)}")
    return out


def _anchor_hits(words: list[str], anchor: str) -> list[int]:
    """Indexes of the written words that the pause anchor names: exact ('gate:') first, else without punctuation."""
    if not bare(anchor):
        return []
    return [i for i, w in enumerate(words) if w == anchor] or [i for i, w in enumerate(words) if bare(w) == bare(anchor)]


# ---------------------------------------------------------------- Kokoro: text analysis, synthesis, cache
_PIPES: dict[str, object] = {}


def pipeline(device: str | None = None):
    """Kokoro's pipeline; device=None gives the text analysis only (no model is loaded)."""
    name = device or "quiet"
    if name not in _PIPES:
        warnings.filterwarnings("ignore")
        if device == "mps":
            os.environ.setdefault("PYTORCH_ENABLE_MPS_FALLBACK", "1")
        from kokoro import KPipeline
        loud = next((p for d, p in _PIPES.items() if d != "quiet"), None)
        if device is None and loud is not None:
            _PIPES[name] = loud
        else:
            _PIPES[name] = KPipeline(lang_code="a", repo_id=REPO, model=device is not None, device=device)
    return _PIPES[name]


def _hub_file(name: str) -> Path | None:
    """A file of the Kokoro model in the local Hugging Face cache (nothing is fetched)."""
    hub = Path(os.environ.get("HF_HUB_CACHE") or Path(os.environ["HF_HOME"]) / "hub")
    return next(iter(sorted(hub.glob(f"models--{REPO.replace('/', '--')}/snapshots/*/{name}"))), None)


def check_voice(voice: str) -> None:
    if _hub_file(f"voices/{voice}.pt") is None:
        config = _hub_file("config.json")
        have = sorted(p.stem for p in (config.parent / "voices").glob("*.pt")) if config else []
        raise SystemExit(f"voice {voice!r} is not in the local model cache ({os.environ['HF_HOME']}); cached voices: {', '.join(have) or 'none'}. "
                         "The builder works offline and does not download.")


def model_vocab() -> set[str]:
    config = _hub_file("config.json")
    if config is None:
        raise SystemExit(f"Kokoro's config.json is not in the local model cache ({os.environ['HF_HOME']})")
    return set(json.loads(config.read_text(encoding="utf-8"))["vocab"])


def is_spoken(tok: dict) -> bool:
    return any(c.isalpha() for c in tok["ps"])


def written_words(tokens: list[dict]) -> list[dict]:
    """Kokoro's tokens grouped into the words as they are written (split at spaces): [{w, toks, ps}].
    A mark that stands alone, such as a spaced dash, joins the word before it."""
    out, cur, pending = [], [], ""
    for i, t in enumerate(tokens):
        cur.append(t)
        if t["ws"] or i == len(tokens) - 1:
            text = "".join(x["w"] for x in cur)
            if any(is_spoken(x) for x in cur):
                ps = "".join((" " if is_spoken(x) and k and is_spoken(cur[k - 1]) else "") + x["ps"] for k, x in enumerate(cur))
                out.append({"w": pending + text, "toks": [x for x in cur if is_spoken(x)], "ps": ps})
                pending = ""
            elif out:
                out[-1]["w"] += " " + text
            else:
                pending += text + " "
            cur = []
    return out


def _core(ps: str) -> str:
    """A word's phonemes without the punctuation around them."""
    return "".join(c for c in ps if c not in PUNCT_PHONEMES).strip()


def fallback_words(words: list[dict]) -> list[tuple[dict, str | None]]:
    """The written words that Kokoro's dictionary does not hold, so that its fallback guessed their reading (rating
    2 or less): [(word, what a listener should hear if FALLBACK_READINGS accepts this reading, else None)].
    A word with reviewed phonemes in 'say' has the rating 5 and is not among them."""
    return [(w, FALLBACK_READINGS.get(bare(w["w"]), {}).get(_core(w["ps"]))) for w in words
            if any((t.get("rating") or 9) <= 2 for t in w["toks"])]


def fallback_problems(words: list[dict]) -> list[str]:
    return [f"{w['w']!r} is not in Kokoro's dictionary and its fallback reads /{w['ps']}/ (a guess; an unknown or damaged word is spelt "
            "out). Write the word another way, give reviewed phonemes in 'say', or listen and add this reading to FALLBACK_READINGS"
            for w, accepted in fallback_words(words) if accepted is None]


def read_line(pipe, text: str) -> tuple[list[dict], list[str]]:
    """Kokoro's text analysis of a line: (tokens [{w, ws, ps, tag, rating}], the phoneme string of each chunk)."""
    _, mtokens = pipe.g2p(text)
    chunks = list(pipe.en_tokenize(mtokens))
    toks = [{"w": t.text, "ws": t.whitespace, "ps": t.phonemes or "", "tag": t.tag,
             "rating": t.__dict__.get("rating") or (t._.rating if t._ else None)} for _, _, tks in chunks for t in tks]
    return toks, [ps for _, ps, _ in chunks]


def reading_problems(line: Line, toks: list[dict], chunks: list[str], default: list[dict] | None, vocab: set[str]) -> list[str]:
    """What must hold after Kokoro's text analysis: every word is spoken, nothing is dropped, split or re-worded,
    and no word is a guess of the fallback."""
    out = []
    rebuilt = "".join(t["w"] + t["ws"] for t in toks).strip()
    if squash(rebuilt) != line.text:
        out.append(f"Kokoro's tokens do not rebuild the line: {rebuilt!r}")
    if len(chunks) != 1 or len(chunks[0]) > MAX_PHONEMES:
        out.append(f"the line is {sum(map(len, chunks))} phoneme characters long (limit {MAX_PHONEMES}); make it two lines")
    silent = [t["w"] for t in toks if any(c.isalnum() for c in t["w"]) and not is_spoken(t)]
    if silent:
        out.append(f"Kokoro has no phonemes for {silent} (the word would be skipped)")
    missing = sorted({c for ps in chunks for c in ps if c not in vocab})
    if missing:
        out.append(f"phoneme characters {missing} are not in the model's vocabulary (they would be dropped)")
    if line.say is not None and default is not None and not out:
        specs = marked_words(line.say)
        core = _core
        plain = lambda ps: core(ps).replace("ˈ", "").replace("ˌ", "")                 # noqa: E731
        for i, (new, old) in enumerate(zip(written_words(toks), written_words(default))):
            spec = specs.get(i, ("", None))[1]
            if spec is None and new["ps"] != old["ps"]:
                out.append(f"the markup changes the reading of the unmarked word {new['w']!r}: /{old['ps']}/ -> /{new['ps']}/")
            elif spec and spec.startswith("/") and core(new["ps"]) != spec.strip("/"):
                out.append(f"{new['w']!r} is read /{new['ps']}/, not the reviewed /{spec.strip('/')}/")
            elif spec and STRESS_OK.fullmatch(spec) and plain(new["ps"]) != plain(old["ps"]):
                out.append(f"stress markup changes more than the stress of {new['w']!r}: /{old['ps']}/ -> /{new['ps']}/")
    return out + fallback_problems(written_words(toks))


def _infer_wide(pipe, text: str, voice: str, speed: float, pitch_range: float):
    """EXPERIMENTAL (--pitch-range): Kokoro's own inference steps (KModel.forward_with_tokens, kokoro 0.9.4) with
    one change: the predicted pitch is widened around its median in the log domain.  Durations are not touched."""
    import torch
    from types import SimpleNamespace
    from kokoro import KPipeline
    model = pipe.model
    _, mtokens = pipe.g2p(text)
    chunks = list(pipe.en_tokenize(mtokens))
    if len(chunks) != 1:
        return []
    _, ps, tks = chunks[0]
    ids = [model.vocab[c] for c in ps if c in model.vocab]
    ref = pipe.load_voice(voice)[len(ps) - 1].to(model.device)
    input_ids = torch.LongTensor([[0, *ids, 0]]).to(model.device)
    with torch.no_grad():
        lengths = torch.full((1,), input_ids.shape[-1], device=model.device, dtype=torch.long)
        mask = torch.gt(torch.arange(int(lengths.max()), device=model.device).unsqueeze(0) + 1, lengths.unsqueeze(1))
        d_en = model.bert_encoder(model.bert(input_ids, attention_mask=(~mask).int())).transpose(-1, -2)
        style = ref[:, 128:]
        d = model.predictor.text_encoder(d_en, style, lengths, mask)
        x, _ = model.predictor.lstm(d)
        pred_dur = torch.round(torch.sigmoid(model.predictor.duration_proj(x)).sum(axis=-1) / speed).clamp(min=1).long().squeeze()
        idx = torch.repeat_interleave(torch.arange(input_ids.shape[1], device=model.device), pred_dur)
        aln = torch.zeros((input_ids.shape[1], idx.shape[0]), device=model.device)
        aln[idx, torch.arange(idx.shape[0])] = 1
        aln = aln.unsqueeze(0)
        f0, noise = model.predictor.F0Ntrain(d.transpose(-1, -2) @ aln, style)
        voiced = f0 > 50
        median = torch.median(f0[voiced])
        f0 = torch.where(voiced, median * (f0 / median) ** pitch_range, f0)
        audio = model.decoder(model.text_encoder(input_ids, lengths, mask) @ aln, f0, noise, ref[:, :128]).squeeze().cpu()
    KPipeline.join_timestamps(tks, pred_dur.cpu())
    return [SimpleNamespace(audio=audio, phonemes=ps, tokens=tks)]


@functools.lru_cache(maxsize=None)
def kokoro_version() -> str:
    import importlib.metadata as md
    return md.version("kokoro")


def cache_path(line: Line, voice: str, cache: Path, device: str, pitch_range: float) -> Path:
    """One cache file per (what is spoken, voice, speed, seed, Kokoro version, device, pitch range)."""
    key = [line.spoken, voice, line.speed, SEED, kokoro_version(), device] + ([pitch_range] if pitch_range != 1.0 else [])
    return cache / (hashlib.sha256(json.dumps(key, ensure_ascii=False).encode()).hexdigest()[:24] + ".npz")


def load_cached(path: Path) -> tuple[np.ndarray, list[dict], dict] | None:
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        meta = json.loads(str(z["meta"]))
        return z["audio"], meta["tokens"], meta


def cached_reading(path: Path) -> tuple[list[dict], list[str]] | None:
    """Kokoro's reading of a line as the cache holds it (tokens with tag and rating, the phoneme string), without
    its audio; None if the line is not in the cache or an older builder made the entry without the ratings."""
    if not path.exists():
        return None
    with np.load(path, allow_pickle=False) as z:
        meta = json.loads(str(z["meta"]))
    return (meta["tokens"], [meta["phonemes"]]) if all("rating" in t for t in meta["tokens"]) else None


def _save_cache(path: Path, audio: np.ndarray, meta: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.stem + f".{os.getpid()}.tmp.npz")
    np.savez_compressed(tmp, audio=audio, meta=json.dumps(meta, ensure_ascii=False))
    os.replace(tmp, path)


def add_ratings(path: Path, toks: list[dict]) -> bool:
    """Give a cache entry that an older builder made the tags and ratings of Kokoro's reading (its audio stays).
    If Kokoro now reads the line in another way, the entry is removed, the line is synthesised again, and the
    result is False."""
    audio, tokens, meta = load_cached(path)
    if [(t["w"], t["ps"]) for t in tokens] != [(t["w"], t["ps"]) for t in toks]:
        path.unlink()
        return False
    meta["tokens"] = [dict(t, tag=a["tag"], rating=a["rating"]) for t, a in zip(tokens, toks)]
    _save_cache(path, audio, meta)
    return True


def synthesise(line: Line, voice: str, cache: Path, device: str, pitch_range: float = 1.0) -> tuple[np.ndarray, list[dict], dict, bool]:
    """Kokoro's audio (24 kHz) and tokens [{w, ws, ps, s, e, tag, rating}] for one line: (audio, tokens, meta, came from the cache).
    Stops if Kokoro would not speak exactly the words of the line."""
    path = cache_path(line, voice, cache, device, pitch_range)
    hit = load_cached(path)
    if hit is not None:
        return *hit, True
    import torch
    pipe = pipeline(device)                 # load first: building the model draws random numbers
    toks, chunks = read_line(pipe, line.spoken)
    default = read_line(pipe, line.text)[0] if line.say is not None else None
    problems = reading_problems(line, toks, chunks, default, set(pipe.model.vocab))
    if problems:
        raise SystemExit(f"Kokoro cannot speak this line as written: {line.text}\n  " + "\n  ".join(problems))
    torch.manual_seed(SEED)                 # the vocoder's noise is random; the seed makes a re-run identical
    if pitch_range == 1.0:
        results = list(pipe(line.spoken, voice=voice, speed=line.speed))
    else:
        results = _infer_wide(pipe, line.spoken, voice, line.speed, pitch_range)
    if len(results) != 1:
        raise SystemExit(f"Kokoro split this line into {len(results)} calls; make it two lines: {line.text}")
    r = results[0]
    tokens = [{"w": t.text, "ws": t.whitespace, "ps": t.phonemes or "", "s": t.start_ts, "e": t.end_ts} for t in r.tokens]
    if [(t["w"], t["ps"]) for t in tokens] != [(t["w"], t["ps"]) for t in toks]:
        raise SystemExit(f"Kokoro's synthesis did not use the reading that was checked: {line.text}")
    tokens = [dict(t, tag=a["tag"], rating=a["rating"]) for t, a in zip(tokens, toks)]
    if any(is_spoken(t) and (t["s"] is None or t["e"] is None) for t in tokens):
        raise SystemExit(f"Kokoro gave no timestamp for a word of: {line.text}")
    audio = np.asarray(r.audio, dtype=np.float32)
    meta = {"tokens": tokens, "phonemes": r.phonemes, "text": line.text, "spoken": line.spoken, "voice": voice, "speed": line.speed,
            "default_words": [w["ps"] for w in written_words(default)] if default else None}
    _save_cache(path, audio, meta)
    return audio, tokens, meta, False


# ---------------------------------------------------------------- one line: trim, word edges, inner pauses, fades
def shape(line: Line, audio: np.ndarray, tokens: list[dict]) -> tuple[np.ndarray, list[dict], dict]:
    """Cut a Kokoro call to its speech, put the word edges on the audio at pauses, and set the requested inner
    pauses.  Returns (audio, words [{w, s, e}], info); info['head'] and info['tail'] are the seconds before the
    first word and after the last word."""
    on, off = fx.speech_bounds(audio, RATE, TRIM_DB)
    a0, a1 = max(0.0, on - PRE_ROLL), min(len(audio) / RATE, off + POST_ROLL)
    cut = audio[int(round(a0 * RATE)):int(round(a1 * RATE))].copy()
    dur = len(cut) / RATE
    toks = [dict(t, s=min(max((t["s"] or 0.0) - a0, 0.0), dur), e=min(max((t["e"] or 0.0) - a0, 0.0), dur)) for t in tokens]
    words = written_words(toks)
    sp = [t for w in words for t in w["toks"]]              # the spoken tokens, in order
    kokoro_start, kokoro_end = [t["s"] for t in sp], [t["e"] for t in sp]
    if squash(" ".join(w["w"] for w in words)) != line.text:
        raise SystemExit(f"the words of the audio do not rebuild the line: {line.text}")

    # Inside running speech Kokoro's start_ts is on the word start within about 30 ms: it stays.  At the line's
    # edges and at every pause the times come from the audio: after a silence the sound starts 35-80 ms after
    # start_ts, and end_ts before a silence is about 0.2 s late (the last phoneme takes the decay).
    e_on, e_off = fx.speech_bounds(cut, RATE, EDGE_DB)
    sp[0]["s"], sp[-1]["e"] = e_on, e_off
    tt, db = fx.frame_db(cut, RATE)
    rel = db - db.max()
    gaps = [(a, b) for a, b in fx.silences(cut, RATE, EDGE_DB, GAP_MIN) if a > e_on and b < e_off]
    quiet = [(a, b) for a, b in gaps if b - a >= PAUSE_MIN]
    pauses = []
    for i in range(len(sp) - 1):
        # A pause: the silences that start after word i starts and end where word i+1 starts.  A silence that
        # ends earlier is a stop consonant inside word i.  Silences with only a weak, short sound between them
        # (a breath) are one pause.
        cand = [(a, b) for a, b in quiet if a > kokoro_start[i] - 0.02 and b <= kokoro_start[i + 1] + 0.12]
        if not cand or cand[-1][1] < kokoro_start[i + 1] - 0.10:
            # No pause, but a short silence that holds Kokoro's own word boundary: the sound of word i ends and
            # the sound of word i+1 starts at its edges (Kokoro's time lies up to 80 ms before the sound).
            hit = [(a, b) for a, b in gaps if kokoro_end[i] - 0.005 <= b <= kokoro_start[i + 1] + 0.12
                   and sp[i]["s"] + 0.02 < a <= kokoro_start[i + 1] + 0.005]
            if hit:
                sp[i]["e"], sp[i + 1]["s"] = hit[-1]
                if hit[-1][1] - hit[-1][0] >= PAUSE_MIN:
                    pauses.append({"after": i, "start": hit[-1][0], "end": hit[-1][1], "main": hit[-1]})
            continue
        chain = [cand[-1]]
        for a, b in reversed(cand[:-1]):
            between = rel[(tt > b) & (tt < chain[0][0])]
            if chain[0][0] - b > BLIP_MAX or (len(between) and between.max() >= BLIP_DB):
                break
            chain.insert(0, (a, b))
        sp[i]["e"], sp[i + 1]["s"] = chain[0][0], chain[-1][1]
        pauses.append({"after": i, "start": chain[0][0], "end": chain[-1][1], "main": max(chain, key=lambda ab: ab[1] - ab[0])})
    for i, (a, b) in enumerate(zip(sp, sp[1:])):
        if b["s"] < a["e"]:
            a["e"] = b["s"] = (a["e"] + b["s"]) / 2
        a["e"] = max(a["e"], a["s"])
        # A short word after a silence ('We', 'The', 'it'): its start moved to the sound, its end is still Kokoro's
        # early time, and 20 ms can be all that is left.  It gets MIN_WORD, taken from the word that follows it.
        short = a["s"] + MIN_WORD - a["e"]
        if short > 0 and a["s"] > kokoro_start[i] + 1e-6 and b["s"] - a["e"] < 1e-6 and b["e"] - b["s"] - short >= MIN_WORD:
            a["e"] = b["s"] = a["s"] + MIN_WORD

    word_of = {id(w["toks"][-1]): w["w"] for w in words}
    said = lambda p: word_of.get(id(sp[p["after"]]), sp[p["after"]]["w"])    # noqa: E731
    info = {"trim_lead": a0, "trim_tail": len(audio) / RATE - a1, "set": [],
            "natural": [(said(p), p["end"] - p["start"]) for p in pauses]}
    for anchor, target in line.pauses.items():
        k = _anchor_hits([w["w"] for w in words], anchor)
        hit = [p for p in pauses if k and sp[p["after"]] is words[k[0]]["toks"][-1]]
        if not hit:
            found = ", ".join(f"{w!r} {s:.2f} s" for w, s in info["natural"]) or "nowhere"
            raise SystemExit(f"no silence after {anchor!r} to adjust: Kokoro did not pause there (it paused after: {found}). "
                             f"Change the punctuation or drop this pause: {line.text}")
        p = hit[0]
        natural, (ma, mb) = p["end"] - p["start"], p["main"]
        mid, delta = (ma + mb) / 2, target - (p["end"] - p["start"])
        m = int(round(mid * RATE))
        if delta >= 0:
            cut = np.concatenate([cut[:m], np.zeros(int(round(delta * RATE)), dtype=np.float32), cut[m:]])
        else:
            if -delta > (mb - ma) - MIN_KEEP:
                raise SystemExit(f"the pause after {anchor!r} is {natural:.2f} s and its silent part is {mb - ma:.2f} s; it cannot "
                                 f"become {target:.2f} s. Ask for at least {natural - (mb - ma) + MIN_KEEP:.2f} s: {line.text}")
            n_cut = int(round(-delta * RATE))
            lo = m - n_cut // 2
            cut = np.concatenate([fx.fade(cut[:lo], RATE, 0, SPLICE_FADE), fx.fade(cut[lo + n_cut:], RATE, SPLICE_FADE, 0)])
            delta = -n_cut / RATE
        for t in sp:
            t["s"] += delta if t["s"] >= mid - 1e-9 else 0.0
            t["e"] += delta if t["e"] > mid + 1e-9 else 0.0
        for q in pauses:
            q["start"], q["end"] = q["start"] + (delta if q["start"] >= mid else 0.0), q["end"] + (delta if q["end"] > mid else 0.0)
            q["main"] = (q["main"][0] + (delta if q["main"][0] >= mid else 0.0), q["main"][1] + (delta if q["main"][1] > mid else 0.0))
        info["set"].append((anchor, natural, target))
    dur = len(cut) / RATE
    info["head"], info["tail"] = sp[0]["s"], dur - sp[-1]["e"]
    return fx.fade(cut, RATE, FADE_IN, FADE_OUT), [{"w": w["w"], "s": w["toks"][0]["s"], "e": w["toks"][-1]["e"]} for w in words], info


# ---------------------------------------------------------------- subtitles
def wrap(text: str) -> str | None:
    """The text on one line, or on two balanced lines of at most LINE_CHARS; None if it does not fit."""
    if len(text) <= LINE_CHARS:
        return text
    fits = [(abs(2 * i - len(text)) - (8 if text[i - 1] in ".?!" else 5 if text[i - 1] in ",;:—" else 0), i)
            for i, c in enumerate(text) if c == " " and i <= LINE_CHARS and len(text) - i - 1 <= LINE_CHARS]
    return None if not fits else text[:min(fits)[1]] + "\n" + text[min(fits)[1] + 1:]


def split_cues(words: list[dict]) -> list[list[dict]]:
    """A line's words as subtitle cues of at most two lines each, split at the punctuation nearest the middle."""
    text = " ".join(w["w"] for w in words)
    if wrap(text) is not None or len(words) == 1:
        return [words]
    best, run = None, 0
    for i, w in enumerate(words[:-1]):
        run += len(w["w"]) + 1
        last = w["w"].rstrip("\"”’')")[-1:]
        score = abs(run - len(text) / 2) - (len(text) / 2 if last in ".?!" else len(text) / 4 if last in ",;:—" else 0)
        if best is None or score < best[0]:
            best = (score, i + 1)
    return split_cues(words[:best[1]]) + split_cues(words[best[1]:])


def srt_time(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


# ---------------------------------------------------------------- one scene
def assemble(scene: Scene, shaped: list[tuple[np.ndarray, list[dict], dict]]) -> tuple[np.ndarray, dict, list[str]]:
    """Join a scene's shaped lines with exact pauses.  Returns (audio at 24 kHz, the scene's timings entry, notes)."""
    notes, pieces = [], []
    pos = int(round((LEAD - shaped[0][2]["head"]) * RATE))
    pieces.append(np.zeros(pos, dtype=np.float32))
    sentences, cues = [], []
    for li, (line, (audio, words, info)) in enumerate(zip(scene.lines, shaped)):
        t0 = pos / RATE
        entry = {"text": line.text, "start": round(t0 + words[0]["s"], 3), "end": round(t0 + words[-1]["e"], 3), "speed": line.speed,
                 "pause_after": None, "words": [{"w": w["w"], "s": round(t0 + w["s"], 3), "e": round(t0 + w["e"], 3)} for w in words]}
        for cue in split_cues(entry["words"]):
            cues.append({"start": cue[0]["s"], "end": cue[-1]["e"], "text": wrap(" ".join(w["w"] for w in cue)) or " ".join(w["w"] for w in cue)})
        if li + 1 < len(shaped):
            gap = int(round((line.pause_after - info["tail"] - shaped[li + 1][2]["head"]) * RATE))
            if gap < 0:                     # the sound around the words is longer than the pause: shorten this line's quiet tail
                keep = int(round(info["tail"] * RATE)) + gap
                if keep < int(0.02 * RATE):
                    raise SystemExit(f"{scene.key} line {li}: pause_after {line.pause_after:.2f} s is shorter than the sound around the words allows")
                audio, gap = fx.fade(audio[:len(audio) + gap], RATE, 0, FADE_OUT), 0
                notes.append(f"{scene.key} line {li}: the quiet tail was shortened to keep pause_after at {line.pause_after:.2f} s")
            pieces += [audio, np.zeros(gap, dtype=np.float32)]
            pos += len(audio) + gap
            entry["pause_after"] = round(line.pause_after, 3)
        else:
            pieces.append(audio)
            pos += len(audio)
            end = t0 + words[-1]["e"]
            grid = RATE // GRID_FPS
            total = -(-max(pos, int(np.ceil((end + scene.tail) * RATE - 1e-3))) // grid) * grid
            pieces.append(np.zeros(total - pos, dtype=np.float32))
            entry["pause_after"] = round(total / RATE - end, 3)
        sentences.append(entry)
    raw = np.concatenate(pieces)
    duration = len(raw) / RATE
    for a, b in zip(cues, cues[1:] + [{"start": duration + CUE_GAP}]):   # hold a cue to a readable length, never into the next
        latest = b["start"] - CUE_GAP
        a["end"] = round(max(a["end"], min(latest, max(a["start"] + CUE_MIN, a["end"] + CUE_HOLD))), 3)
    ticks = len(raw) // (RATE // GRID_FPS)
    return raw, {"title": scene.title, "wav": "", "duration": duration, "frames": {str(f): ticks * f // GRID_FPS for f in (15, 30, 60)},
                 "tail": round(duration - sentences[-1]["end"], 3), "starts": [s["start"] for s in sentences],
                 "sentences": sentences, "cues": cues}, notes


def word_time(timings: dict, key: str, line: int, word: str, nth: int = 1, edge: str = "s") -> float:
    """Scene time at which the nth occurrence (from 1) of ``word`` starts (edge='s') or ends (edge='e') in a line.
    Punctuation and case do not count ('gate' finds 'gate:', '18.5' finds '18.5%'); 'step' also finds 'two-step'."""
    words = timings[key]["sentences"][line]["words"]
    want = bare(word)
    hits = [w for w in words if bare(w["w"]) == want] or [w for w in words if want in bare(w["w"]).split("-")]
    if not 1 <= nth <= len(hits):
        raise KeyError(f"{word!r} (occurrence {nth}) is not in line {line} of {key}: {' '.join(w['w'] for w in words)}")
    return hits[nth - 1][edge]


# ---------------------------------------------------------------- --check-only: counts, length, pronunciation risks
def check_report(scenes: list[Scene], voice: str, cache: Path, device: str, pitch_range: float) -> list[str]:
    """Word count, estimated length and every pronunciation risk, from Kokoro's text analysis (no synthesis)."""
    pipe, vocab = pipeline(None), model_vocab()
    table, overrides, reads, problems = ["scene  lines  words  est. length    tail"], [], {}, []
    rate = PHONEMES_PER_SECOND.get(voice, 13.0)
    total_words, total_seconds, n_cached = 0, 0.0, 0
    for scene in scenes:
        seconds, n_words = LEAD, 0
        for li, line in enumerate(scene.lines):
            where = f"{scene.key} line {li}"
            toks, chunks = read_line(pipe, line.spoken)
            default = read_line(pipe, line.text)[0] if line.say is not None else None
            found = reading_problems(line, toks, chunks, default, vocab)
            problems += [f"{where}: {p}" for p in found]
            if found:
                continue
            words = written_words(toks)
            n_words += len(words)
            hit = load_cached(cache_path(line, voice, cache, device, pitch_range))
            if hit is not None:
                cut, _, info = shape(line, hit[0], hit[1])
                speech, n_cached = len(cut) / RATE - info["head"] - info["tail"], n_cached + 1
            else:
                asked = {_anchor_hits([w["w"] for w in words], a)[0]: v for a, v in line.pauses.items()}
                inner = sum(asked.get(i, 0.3) for i, w in enumerate(words[:-1]) if w["w"].rstrip("\"”’')")[-1:] in ",;:—.?!…")
                speech = sum(c.isalpha() and c not in "ˈˌ" for c in chunks[0]) / rate * (1 + 0.6 * (1 / line.speed - 1)) + inner
            seconds += speech + (0.0 if li + 1 == len(scene.lines) else line.pause_after)
            reads[scene.key, li] = toks, chunks
            marks = marked_words(line.say) if line.say is not None else {}
            for i, (new, old) in enumerate(zip(words, written_words(default or []))):
                if i in marks:
                    hear = PRONUNCIATIONS.get(marks[i][0].lower(), {}).get(marks[i][1].strip("/"), "stress or number markup")
                    overrides.append(f"{where}: [{marks[i][0]}]({marks[i][1]})  now /{new['ps']}/, Kokoro's own /{old['ps']}/  -> {hear}")
        seconds = float(np.ceil((seconds + scene.tail) * GRID_FPS - 1e-6)) / GRID_FPS
        table.append(f"{scene.key}    {len(scene.lines):5d}  {n_words:5d}  {seconds:8.1f} s  {scene.tail:4.2f} s  {scene.title}")
        total_words, total_seconds = total_words + n_words, total_seconds + seconds
    if problems:
        raise SystemExit("Kokoro cannot speak the script as written:\n  " + "\n  ".join(problems))
    risks = risk_list(scenes, reads)
    n_lines = sum(len(s.lines) for s in scenes)
    out = table + [f"words: {total_words} in {n_lines} lines (the brief asks for {WORD_TARGET[0]} to {WORD_TARGET[1]}, at most {WORD_MAX})"
                   + ("  WARNING: over the maximum" if total_words > WORD_MAX else "")]
    out.append(f"estimated length: {int(total_seconds // 60)}:{total_seconds % 60:04.1f} with leads, pauses and tails ({n_cached} of {n_lines} lines "
               f"are in the cache and exact; the others are estimated at {rate} phonemes per second for {voice})")
    if n_cached < n_lines and any(ln.pauses for s in scenes for ln in s.lines):
        out.append("note: a pause inside a line needs a silence that Kokoro made there; only a build (or the cache) can check that")
    out.append(f"overrides in 'say' ({len(overrides)}; listen to each one):")
    out += ["  " + o for o in overrides] or ["  none"]
    out.append(f"pronunciation and delivery risks ({len(risks)}):")
    out += ["  " + r for r in risks] or ["  none found"]
    return out


def risk_list(scenes: list[Scene], reads: dict[tuple[str, int], tuple[list[dict], list[str]]]) -> list[str]:
    """Every pronunciation and delivery risk for the ear: of each line that ``reads`` holds ((scene key, line) ->
    Kokoro's tokens and phoneme string), of each scene's pauses, and a word that is read in more than one way."""
    out, readings = [], {}
    plain = lambda ps: "".join(c for c in ps if c not in PUNCT_PHONEMES and c not in "ˈˌ").strip()   # noqa: E731
    for scene in scenes:
        for li, line in enumerate(scene.lines):
            if (scene.key, li) not in reads:
                continue
            where, (toks, chunks) = f"{scene.key} line {li}", reads[scene.key, li]
            words = written_words(toks)
            out += [f"{where}: {r}" for r in _line_risks(line, toks, words, chunks, li + 1 == len(scene.lines))]
            for w in words:
                if len(bare(w["w"])) >= 5:
                    readings.setdefault(bare(w["w"]), {}).setdefault(plain(w["ps"]), (where, w["ps"]))
        gaps = [ln.pause_after for ln in scene.lines[:-1]]
        if len(gaps) >= 4 and len(set(gaps)) == 1:
            out.append(f"{scene.key}: the {len(gaps)} pauses between its lines are all {gaps[0]:.2f} s; equal gaps sound like a metronome")
    for word, ways in readings.items():
        if len(ways) > 1:
            out.append(f"{word!r} is read in {len(ways)} ways: " + "; ".join(f"/{ps}/ ({where})" for where, ps in ways.values()))
    return out


def _line_risks(line: Line, toks: list[dict], words: list[dict], chunks: list[str], last: bool) -> list[str]:
    """What a listener should check in one line, from Kokoro's reading of it."""
    out = []
    marked = set(marked_words(line.say)) if line.say is not None else set()
    for i, w in enumerate(words):
        b = bare(w["w"])
        if i in marked:
            continue
        if b in KNOWN_RISKS:
            out.append(f"{w['w']!r} /{w['ps']}/: {KNOWN_RISKS[b]}")
        elif any(c.isdigit() for c in b):
            out.append(f"numeral {w['w']!r} is read /{w['ps']}/")
        elif any((t.get("rating") or 9) <= 2 for t in w["toks"]):
            out.append(f"{w['w']!r} is not in Kokoro's dictionary; its fallback reads /{w['ps']}/")
        elif b in HETERONYMS:
            out.append(f"{w['w']!r} has two readings; Kokoro chose /{w['ps']}/ (tagged {w['toks'][0].get('tag')})")
    for mark in ".?!,;:":
        n_text = len(re.findall(re.escape(mark) + r"+(?=[\"”’')\]]*(?:\s|$))", line.text))
        n_read = len(re.findall(re.escape(mark) + "+", chunks[0]))
        if n_read < n_text:
            out.append(f"{n_text - n_read} of the {n_text} {mark!r} in the text make no pause in Kokoro's reading "
                       f"(it happens after a single letter or an abbreviation): /{chunks[0]}/")
    if re.search(r"\s[-–]\s", line.text):
        out.append("a spaced hyphen or en dash is read without a reliable pause; use an em dash (—) or a comma")
    dropped = sorted({t["w"] for t in toks if not t["ps"] and t["w"] not in "-–'’‘"})
    if dropped:
        out.append(f"{dropped} is not spoken and makes no pause")
    if len(chunks[0]) > 0.8 * MAX_PHONEMES:
        out.append(f"{len(chunks[0])} phoneme characters, near Kokoro's limit of {MAX_PHONEMES}; consider two lines")
    if not last and line.text.rstrip("\"”’')").endswith("?") and line.pause_after < 0.7:
        out.append("a question: Kokoro's pitch does not rise, so let the pause carry it "
                   f"(pause_after is {line.pause_after:.2f} s; 0.7 s or more helps)")
    return out


# ---------------------------------------------------------------- build
def _wav_bytes(x: np.ndarray) -> bytes:
    buf = io.BytesIO()
    sf.write(buf, x, OUT_RATE, subtype="PCM_16", format="WAV")
    return buf.getvalue()


def _write_if_changed(path: Path, data: bytes) -> bool:
    """Write the file in one step (a scene that renders at the same time never reads half a file)."""
    if path.exists() and path.read_bytes() == data:
        return False
    tmp = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    tmp.write_bytes(data)
    os.replace(tmp, path)
    return True


def build(script: Path = DEFAULT_SCRIPT, reviewed: Path = DEFAULT_REVIEWED, out_dir: Path = DEFAULT_OUT, voice: str | None = None,
          only: list[str] | None = None, check_only: bool = False, allow_unspoken: bool = False, device: str = "cpu",
          target_lufs: float = TARGET_LUFS, pitch_range: float = 1.0, whole_file: bool = False, columns: tuple[str, ...] = ()) -> dict:
    """Check the script, then build the audio, timings.json, narration.srt and build_report.txt.  Returns the timings."""
    t_start = time.time()
    script_voice, scenes, notes = load_script(script)
    voice = voice or script_voice
    try:
        markdown = reviewed.read_text(encoding="utf-8")
    except OSError as e:
        raise SystemExit(f"cannot read the reviewed script {reviewed}: {e}")
    problems, check_notes = check_script(scenes, markdown, allow_unspoken, whole_file, columns)
    if problems:
        raise SystemExit(f"script check failed ({script.name} against {reviewed.name}); nothing was built:\n  " + "\n  ".join(problems)
                         + "".join(f"\n  note: {n}" for n in check_notes[1:]))
    notes = check_notes + notes
    keys = [s.key for s in scenes]
    if only and set(only) - set(keys):
        raise SystemExit(f"--only names scenes that are not in {script.name}: {sorted(set(only) - set(keys))}")
    check_voice(voice)
    cache = out_dir / "cache"
    head = [f"script   {script}", f"reviewed {reviewed}", "safety:  " + notes[0]] + ["note:    " + n for n in notes[1:]]
    if check_only:
        print("\n".join(head) + "\nloading Kokoro's text analysis (no synthesis; about 5 to 25 s) ...", flush=True)
        print("\n".join(check_report(scenes, voice, cache, device, pitch_range)))
        return {}

    chosen = [s for s in scenes if not only or s.key in only]
    old = json.loads((out_dir / "timings.json").read_text(encoding="utf-8")) if (out_dir / "timings.json").exists() else {}
    old_meta = old.get("_meta", {})
    settings = {"voice": voice, "device": device, "pitch_range": pitch_range, "target_lufs": target_lufs}
    if only and old_meta and any(old_meta.get(k) != v for k, v in settings.items()):
        raise SystemExit(f"--only would mix settings: the audio in {out_dir} was built with "
                         f"{ {k: old_meta.get(k) for k in settings} }, this build asks for {settings}. Run a full build.")

    # Kokoro's reading of every line, before any audio is made: from the cache, or from Kokoro's text analysis for a
    # line that is not in the cache (or whose entry an older builder made without the ratings).  A word that the
    # fallback guessed stops the build either way, so a reading that FALLBACK_READINGS no longer holds cannot come
    # back from the cache.
    reads, todo, problems = {}, [], []
    for sc in chosen:
        for li, ln in enumerate(sc.lines):
            path = cache_path(ln, voice, cache, device, pitch_range)
            got = cached_reading(path)
            if got is None:
                todo.append((sc.key, li, ln, path))
            else:
                reads[sc.key, li] = got
                problems += [f"{sc.key} line {li}: {p}" for p in fallback_problems(written_words(got[0]))]
    if todo:
        new = sum(not p.exists() for *_, p in todo)
        print(f"loading Kokoro to read {len(todo)} line(s) ({new} to synthesise) ...", flush=True)
        pipe, vocab = pipeline(device if new else None), model_vocab()
        for key, li, ln, path in todo:
            toks, chunks = read_line(pipe, ln.spoken)
            default = read_line(pipe, ln.text)[0] if ln.say is not None else None
            problems += [f"{key} line {li}: {p}" for p in reading_problems(ln, toks, chunks, default, vocab)]
            if path.exists():
                add_ratings(path, toks)
            reads[key, li] = toks, chunks
    if problems:
        raise SystemExit("Kokoro cannot speak the script as written; nothing was built:\n  " + "\n  ".join(problems))
    out_dir.mkdir(parents=True, exist_ok=True)

    raw, entries, line_report, overrides, late, longer, n_new = {}, {}, [], [], [], [], 0
    for scene in chosen:
        shaped = []
        for li, line in enumerate(scene.lines):
            audio, tokens, meta, cached = synthesise(line, voice, cache, device, pitch_range)
            n_new += not cached
            cut, words, info = shape(line, audio, tokens)
            shaped.append((cut, words, info))
            line_report.append(f"{scene.key} line {li}: speech {len(cut) / RATE:.2f} s (Kokoro {len(audio) / RATE:.2f} s; "
                               f"cut {info['trim_lead']:.2f} s before, {info['trim_tail']:.2f} s after), "
                               f"speed {line.speed}, {len(meta['phonemes'])} phoneme characters"
                               + "".join(f"; pause after {a!r} set {n:.2f} -> {t:.2f} s" for a, n, t in info["set"])
                               + ("; Kokoro paused after " + ", ".join(f"{w!r} {s:.2f} s" for w, s in info["natural"]) if info["natural"] else ""))
            now, was = written_words(tokens), meta.get("default_words") or []
            for k, (word, spec) in (marked_words(line.say) if line.say is not None else {}).items():
                overrides.append({"scene": scene.key, "line": li, "markup": f"[{word}]({spec})", "read_as": now[k]["ps"], "default": was[k],
                                  "hear": PRONUNCIATIONS.get(word.lower(), {}).get(spec.strip("/"), "stress or number markup")})
        raw[scene.key], entries[scene.key], scene_notes = assemble(scene, shaped)
        entries[scene.key]["built_from"] = scene.fingerprint
        late += scene_notes
        asked, edge = scene.lines[-1].pause_after, scene.tail + LEAD
        if scene.tail_from == "script" and not scene.last and abs(asked - edge) > 1 / GRID_FPS:
            late.append(f"{scene.key}: \"tail\" {scene.tail:.2f} s sets the end of the scene ({edge:.2f} s to the next scene's first word); "
                        f"the last line's pause_after ({asked:.2f} s) is not used")
        elif scene.tail_from == "default" and not scene.last and asked < edge - 1e-9:
            longer.append(scene.key)
    if longer:
        late.append(f"{' '.join(longer)}: the pause after the last line is {TAIL + LEAD:.1f} s or a little more (the tail of {TAIL} s, then "
                    f"{LEAD} s before the next scene's first word); that is longer than the line asks, and \"tail\" on the scene changes it")

    # One gain for the whole programme, so that scenes do not differ in level.  A full build measures it over all
    # scenes; a partial build re-uses the gain of the last full build, so the scenes it leaves alone still match.
    order = [k for k in keys if k in raw]
    joined = fx.to_48k(np.concatenate([raw[k] for k in order]), RATE)
    old_master = old_meta.get("mastering", {})
    stored = old_master.get("gain_db") if only else None
    mastered, m_info = fx.master(joined, OUT_RATE, target_lufs, CEILING_DBTP, gain_db=stored, parts=[2 * len(raw[k]) for k in order])
    scene_lufs = dict(zip(order, m_info.pop("parts_lufs")))
    m_info["gain_from"] = ("this full build" if not only else "this partial build" if stored is None
                           else {"this full build": "the last full build"}.get(old_master.get("gain_from"),
                                                                               "the first --only build; there is no full build yet"))
    pcm = np.round(np.clip(mastered, -1.0, 1.0) * 32767.0).astype(np.int16)
    m_info["true_peak_dbtp"] = round(fx.true_peak_db(pcm.astype(np.float32) / 32768.0), 2)
    if m_info["true_peak_dbtp"] > PEAK_LIMIT_DBTP or (stored is None and abs(m_info["lufs_after"] - target_lufs) > 0.3):
        raise SystemExit(f"mastering missed its targets ({m_info}); this is a fault in narration_audio.py, nothing was written")
    pos, written = 0, []
    for k in order:
        n = 2 * len(raw[k])
        wav = (out_dir / f"{k}.wav").resolve()
        if _write_if_changed(wav, _wav_bytes(pcm[pos:pos + n])):
            written.append(k)
        entries[k].update(wav=str(wav), lufs=scene_lufs[k])
        pos += n

    timings = {k: (entries.get(k) or old.get(k)) for k in keys if k in entries or k in old}
    missing = [k for k in keys if k not in timings]
    stale = [s.key for s in scenes if s.key in timings and s.key not in entries and timings[s.key].get("built_from") != s.fingerprint]
    since = [] if not only else sorted(set(old_meta.get("partial_since_full", [])) | set(order))
    timings["_meta"] = {**settings, "lufs": m_info["lufs_after"] if not only else old_meta.get("lufs", m_info["lufs_after"]),
                        "sample_rate": OUT_RATE, "seed": SEED, "kokoro": kokoro_version(), "lead": LEAD, "grid_fps": GRID_FPS,
                        "mastering": m_info if not only else old_meta.get("mastering", m_info), "scenes": [k for k in keys if k in timings],
                        "missing": missing, "stale": stale, "partial_since_full": since,
                        "overrides": overrides if not only else [o for o in old_meta.get("overrides", []) if o["scene"] not in order] + overrides,
                        "script": str(script.resolve()), "reviewed": str(reviewed.resolve()),
                        "note": "times are seconds from the start of the scene's WAV; line numbers count from 0; duration = frames['15'] / 15"}
    _write_if_changed(out_dir / "timings.json", (json.dumps(timings, indent=1, ensure_ascii=False) + "\n").encode("utf-8"))

    srt, offset, index = [], 0.0, 1
    for k in timings["_meta"]["scenes"]:
        for c in timings[k]["cues"]:
            srt.append(f"{index}\n{srt_time(offset + c['start'])} --> {srt_time(offset + c['end'])}\n{c['text']}\n")
            index += 1
        offset += timings[k]["duration"]
    _write_if_changed(out_dir / "narration.srt", "\n".join(srt).encode("utf-8"))

    report = [f"narration build, {time.strftime('%Y-%m-%d %H:%M:%S')}: " + ("all scenes" if not only else "only " + " ".join(order))] + head
    report.append(f"voice {voice}, seed {SEED}, device {device}, kokoro {kokoro_version()}"
                  + (f", pitch range x{pitch_range} (experimental)" if pitch_range != 1.0 else ""))
    report.append(f"mastering: gain {m_info['gain_db']:+.2f} dB (from {m_info['gain_from']}), {m_info['lufs_before']} -> "
                  f"{m_info['lufs_after']} LUFS over {'these scenes' if only else 'the programme'}, true peak "
                  f"{m_info['true_peak_dbtp']} dBTP; limiter at most {m_info['max_gain_reduction_db']} dB, "
                  f"over 1 dB for {100 * m_info['share_limited_over_1db']:.1f}% of the time")
    report.append(f"overrides ({len(overrides)}; listen to each one):")
    report += [f"  {o['scene']} line {o['line']}: {o['markup']}  now /{o['read_as']}/, Kokoro's own /{o['default']}/  -> {o['hear']}"
               for o in overrides] or ["  none"]
    risks = risk_list(chosen, reads)
    report.append(f"pronunciation and delivery risks ({len(risks)}; listen to each one):")
    report += ["  " + r for r in risks] or ["  none found"]
    report.append("scenes (line numbers count from 0):")
    tail_from = {s.key: {"script": " (set in the script)", "pause": " (from the last line's pause)"}.get(s.tail_from, "") for s in scenes}
    for k in order:
        t = timings[k]
        n_words = sum(len(s["words"]) for s in t["sentences"])
        speech = sum(s["end"] - s["start"] for s in t["sentences"])
        report.append(f"  {k}: {t['duration']:.3f} s = {t['frames']['15']} frames at 15 fps, {len(t['sentences'])} lines, "
                      f"{n_words} words, {60 * n_words / t['duration']:.0f} wpm over the scene, "
                      f"{60 * n_words / speech:.0f} wpm while speaking, tail {t['tail']:.2f} s{tail_from[k]}, {t['lufs']} LUFS, pauses "
                      + " ".join(f"{s['pause_after']:.2f}" for s in t["sentences"][:-1]))
    report += ["  " + x for x in line_report]
    report += ["note: " + n for n in late]
    if stale:
        report.append(f"note: NOT UP TO DATE: {' '.join(stale)}: the script changed these scenes after their audio was built; build them too")
    if missing:
        report.append(f"note: not built yet: {' '.join(missing)}; narration.srt holds only the built scenes")
    orphans = sorted(p.name for p in out_dir.glob("S[0-9][0-9].wav") if p.stem not in keys)
    if orphans:
        report.append(f"note: {' '.join(orphans)} in {out_dir} belong to no scene of the script; they were left as they are")
    if since:
        report.append(f"note: built with --only since the last full build: {' '.join(since)}; run a full build before the final video")
    total = sum(timings[k]["duration"] for k in timings["_meta"]["scenes"])
    report.append(f"programme: {len(timings['_meta']['scenes'])} scenes, {int(total // 60)}:{total % 60:06.3f}; wrote {len(written)} WAV file(s) "
                  f"({' '.join(written) or 'none changed'}); {n_new} line(s) synthesised, the rest from the cache; {time.time() - t_start:.1f} s")
    (out_dir / "build_report.txt").write_text("\n".join(report) + "\n", encoding="utf-8")
    print("\n".join(report))
    return timings


def main(argv: list[str] | None = None) -> None:
    ap = argparse.ArgumentParser(description="Build the explainer's narration (Kokoro-82M, offline).")
    ap.add_argument("--script", type=Path, default=DEFAULT_SCRIPT, help="script.json (default: next to this file)")
    ap.add_argument("--reviewed", type=Path, default=DEFAULT_REVIEWED, help="the reviewed script (default: script-and-storyboard.md)")
    ap.add_argument("--out", type=Path, default=DEFAULT_OUT, help=f"output directory (default: {DEFAULT_OUT})")
    ap.add_argument("--voice", help="a cached Kokoro voice; overrides the voice in script.json")
    ap.add_argument("--only", nargs="+", metavar="KEY", help="build only these scenes, with the gain of the last full build")
    ap.add_argument("--check-only", action="store_true", help="safety checks, word count, estimated length, pronunciation risks; no synthesis")
    ap.add_argument("--allow-unspoken", action="store_true", help="do not stop when reviewed narration is left unspoken")
    ap.add_argument("--narration-column", action="append", default=[], metavar="NAME",
                    help="one more name of the table column that holds the narration in the reviewed script (may be repeated)")
    ap.add_argument("--whole-file", action="store_true",
                    help="when the reviewed script marks no narration, look each line up in the whole file (cannot find a left-out sentence)")
    ap.add_argument("--device", choices=("cpu", "mps"), default=os.environ.get("KOKORO_DEVICE") or "cpu", help="one device for a whole build")
    ap.add_argument("--lufs", type=float, default=TARGET_LUFS, help="integrated loudness of the programme (default -16)")
    ap.add_argument("--pitch-range", type=float, default=1.0, help="EXPERIMENTAL: widen the pitch movement (1.0 = Kokoro as it is); listen first")
    a = ap.parse_args(argv)
    if not 0.7 <= a.pitch_range <= 1.6 or not -24.0 <= a.lufs <= -14.0:
        raise SystemExit("--pitch-range must be 0.7 to 1.6 and --lufs -24 to -14")
    build(a.script, a.reviewed, a.out, voice=a.voice, only=a.only, check_only=a.check_only, allow_unspoken=a.allow_unspoken,
          device=a.device, target_lufs=a.lufs, pitch_range=a.pitch_range, whole_file=a.whole_file, columns=tuple(a.narration_column))


if __name__ == "__main__":
    main()
