"""Join the rendered scenes into one video and write subtitles that follow the real scene lengths.

    python3 writing/substack/explainer-video/assemble.py MEDIA_SCENE_DIR AUDIO_DIR OUT_STEM
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ORDER = ["S01Title", "S02Decision", "S03Question", "S04SpecificNew", "S05SideEffects", "S06LookBackWhatIf",
         "S07Cost", "S08Status", "S09Pilot", "S10Coupling", "S11Gate", "S12Result", "S13NotShown",
         "S14Next", "S15Close"]


def duration(path: Path) -> float:
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=duration",
                          "-of", "csv=p=0", str(path)], capture_output=True, text=True, check=True).stdout
    return float(out.strip())


def srt_seconds(stamp: str) -> float:
    h, m, rest = stamp.split(":")
    s, ms = rest.split(",")
    return int(h) * 3600 + int(m) * 60 + int(s) + int(ms) / 1000


def srt_stamp(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    return f"{ms // 3600000:02d}:{ms // 60000 % 60:02d}:{ms // 1000 % 60:02d},{ms % 1000:03d}"


def main(scene_dir: str, audio_dir: str, out_stem: str) -> None:
    scenes = [Path(scene_dir) / f"{k}.mp4" for k in ORDER]
    missing = [str(p) for p in scenes if not p.exists()]
    if missing:
        raise SystemExit("missing scenes: " + ", ".join(missing))
    timings = json.loads((Path(audio_dir) / "timings.json").read_text())
    entries = re.findall(r"\d+\n([\d:,]+) --> ([\d:,]+)\n(.+?)\n", (Path(audio_dir) / "narration.srt").read_text() + "\n")
    lengths = [(srt_seconds(b) - srt_seconds(a), text) for a, b, text in entries]

    srt, offset, n = [], 0.0, 0
    for key, path in zip(ORDER, scenes):
        for start in timings[key]["starts"]:
            length, text = lengths[n]
            n += 1
            srt.append(f"{n}\n{srt_stamp(offset + start)} --> {srt_stamp(offset + start + length)}\n{text}\n")
        offset += duration(path)
    if n != len(lengths):
        raise SystemExit(f"subtitle count mismatch: {n} placed, {len(lengths)} narrated")

    out = Path(out_stem)
    with tempfile.NamedTemporaryFile("w", suffix=".txt", delete=False) as listing:
        listing.write("".join(f"file '{p.resolve()}'\n" for p in scenes))
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", listing.name,
                    "-c:v", "libx264", "-preset", "medium", "-crf", "18", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-movflags", "+faststart",
                    str(out.with_suffix(".mp4"))], check=True)
    out.with_suffix(".srt").write_text("\n".join(srt), encoding="utf-8")
    print(f"{out.with_suffix('.mp4')}: {duration(out.with_suffix('.mp4')):.1f} s, {n} subtitles")


if __name__ == "__main__":
    main(*sys.argv[1:4])
