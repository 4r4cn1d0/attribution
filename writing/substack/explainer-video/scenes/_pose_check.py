"""Check a scene's joins against the poses of world.py, and render the pose gallery.

    # after render.py S07 (draft) or render.py S07 -q review:
    tmp/explainer-venv/bin/python writing/substack/explainer-video/scenes/_pose_check.py S07
    tmp/explainer-venv/bin/python writing/substack/explainer-video/scenes/_pose_check.py S07 -q review

    # the targets: every pose as a still, its lint, a contact sheet, and the dark-run check of 3.6 on P09
    tmp/explainer-venv/bin/python writing/substack/explainer-video/scenes/_pose_check.py --poses
    tmp/explainer-venv/bin/python writing/substack/explainer-video/scenes/_pose_check.py --poses P06 P07 --size 854x480

"SNN" compares BUILD/frames/<quality>/SNN/first.png (written by render.py) with a still of pose P(N-1) and last.png
with a still of P(N). The stills are rendered here, in this process, with the scene class (Narrated, FxCamera, the
vignette) at the resolution of the PNG files, with idle motion at rest, as at the two ends of every scene. It prints
the pixel differences and writes BUILD/frames/<quality>/SNN/posecheck.png: for each end, the scene's frame, the
pose still, and the difference x8. Exit status 1 if any pixel differs by more than 3 levels.

"--poses" writes <out>/PNN.png (default out: BUILD/poses/<W>x<H>), prints the kit lint and the word count of
each pose, writes <out>/sheet.png, and for P09 renders a control still (heads, glows, trails and the condition line
hidden) and measures the longest run of track 1 between the head's centre and the line's centre that is within 3
grey levels of the control (3.6: at least 80 px at 1080p). Exit status 1 if a lint issue or a failed check is found.

It uses its own Manim media directory (BUILD/media/posecheck-<pid>), removed at the end.
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
from pathlib import Path

VID = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(VID))
os.environ["EXPLAINER_NO_AUDIO"] = "1"
for _v in ("EXPLAINER_QUALITY", "EXPLAINER_SNAP", "EXPLAINER_LINT", "EXPLAINER_TIMINGS_USED", "EXPLAINER_LINT_JSON"):
    os.environ.pop(_v, None)

import numpy as np  # noqa: E402
from manim import config, tempconfig  # noqa: E402
from PIL import Image, ImageDraw, ImageFont  # noqa: E402

from kit import *  # noqa: E402,F401,F403
from kit import fx  # noqa: E402
from kit.paths import BUILD  # noqa: E402
from kit.type import FONT_FILES  # noqa: E402

import world  # noqa: E402

MEDIA = BUILD / "media" / f"posecheck-{os.getpid()}"
config.media_dir = str(MEDIA)
config.verbosity = "ERROR"
config.progress_bar = "none"
FPS = {"draft": 15, "review": 30, "final": 30}


def _key_for(pose: str) -> tuple[str, bool]:
    """The scene whose first frame is this pose (its last frame for P11), and whether it is a last frame."""
    n = int(pose[1:])
    return f"S{min(n + 1, 11):02d}", n == 11


def render_pose(pose: str, width: int, height: int, fps: float = 30, hide=None) -> dict:
    """Render pose ``pose`` as one frame of its scene at rest. Returns img (H, W, 3), issues, words, ns."""
    key, last = _key_for(pose)
    out: dict = {}

    class Still(Narrated):
        def construct(self):
            self.key = key
            try:
                self._open()
                self._set_film((self.total_frames - 1) / self.fps if last else 0.0)
                ns = world.pose(pose, self)
                if hide is not None:
                    hide(ns)
                self.update_mobjects(0)
                self.renderer.update_frame(self, ignore_skipping=True)
                out["img"] = np.array(self.camera.pixel_array[:, :, :3])
                out["issues"] = check_layout(list(self.mobjects), frame=self.camera.frame)
                out["words"] = word_count(self.mobjects)
                out["ns"] = ns
            finally:
                fx.film.driven, fx.film.gain = False, 1.0

    with tempconfig(dict(pixel_width=width, pixel_height=height, frame_rate=fps, dry_run=True, disable_caching=True,
                         media_dir=str(MEDIA))):
        Still().render()
    return out


def _diff_stats(a: np.ndarray, b: np.ndarray) -> dict:
    d = np.abs(a.astype(int) - b.astype(int)).max(axis=2)
    n = d.size
    return dict(max=int(d.max()), mean=float(d.mean()), any=int((d > 0).sum()), over3=int((d > 3).sum()),
                over10=int((d > 10).sum()), share=float((d > 0).sum() / n), d=d)


def _font(px: int):
    try:
        return ImageFont.truetype(str(VID / "kit" / FONT_FILES["Inter"][1]), px)
    except Exception:  # noqa: BLE001
        return ImageFont.load_default()


def _thumb(img: np.ndarray, w: int) -> Image.Image:
    im = Image.fromarray(img)
    return im.resize((w, int(round(im.height * w / im.width))), Image.LANCZOS) if im.width != w else im


def check_scene(key: str, quality: str) -> int:
    n = int(key[1:])
    frames = BUILD / "frames" / quality / key
    pairs = [("first.png", f"P{n - 1:02d}"), ("last.png", f"P{n:02d}")]
    rows, status = [], 0
    for fname, pose in pairs:
        path = frames / fname
        if not path.exists():
            print(f"{key} {fname}: missing ({path}); run render.py {key}{'' if quality == 'draft' else ' -q ' + quality} first")
            status = 1
            continue
        frame = np.array(Image.open(path).convert("RGB"))
        h, w = frame.shape[:2]
        still = render_pose(pose, w, h, FPS[quality])["img"]
        s = _diff_stats(frame, still)
        verdict = "EXACT" if s["max"] == 0 else ("within 3 levels" if s["max"] <= 3 else "DIFFERS")
        print(f"{key} {fname:9s} vs {pose}: {verdict}. max {s['max']} levels, mean {s['mean']:.4f}; pixels that differ: "
              f"{s['any']} ({100 * s['share']:.3f}%), by more than 3: {s['over3']}, by more than 10: {s['over10']}")
        if s["max"] > 3:
            status = 1
            ys, xs = np.nonzero(s["d"] > 3)
            print(f"    the differences lie in x {xs.min()}..{xs.max()}, y {ys.min()}..{ys.max()} (pixels)")
        amp = np.clip(s["d"].astype(int) * 8, 0, 255).astype(np.uint8)
        rows.append((fname, pose, frame, still, np.dstack([amp, amp, amp])))
    if rows:
        tw = min(rows[0][2].shape[1], 960)
        font = _font(max(14, tw // 40))
        tiles = []
        for fname, pose, frame, still, amp in rows:
            ims = [_thumb(x, tw) for x in (frame, still, amp)]
            th = ims[0].height
            strip = Image.new("RGB", (3 * tw + 40, th + 34), (12, 14, 19))
            dr = ImageDraw.Draw(strip)
            for j, (im, cap) in enumerate(zip(ims, (f"{key} {fname}", f"pose {pose}", "difference x8"))):
                strip.paste(im, (10 + j * (tw + 10), 30))
                dr.text((10 + j * (tw + 10), 6), cap, fill=(200, 204, 214), font=font)
            tiles.append(strip)
        sheet = Image.new("RGB", (tiles[0].width, sum(t.height for t in tiles)), (12, 14, 19))
        y = 0
        for t in tiles:
            sheet.paste(t, (0, y))
            y += t.height
        out = frames / "posecheck.png"
        sheet.save(out)
        print(f"wrote {out}")
    return status


def dark_run(img: np.ndarray, ctrl: np.ndarray) -> tuple[int, int, int]:
    """3.6: the longest run of pixels on the row of track 1 (P-local y = -1.3, frame P), from the head's centre
    (x = 3.65) to the condition line's centre (x = 4.4), that differ from the control by at most 3 grey levels."""
    h, w = img.shape[:2]
    k = h / 8.0
    r = int(round(h / 2 + 1.3 * k - 0.5))
    x0, x1 = int(np.ceil(w / 2 + 3.65 * k - 0.5)), int(np.floor(w / 2 + 4.4 * k - 0.5))
    d = np.abs(img[r, x0:x1 + 1].astype(int) - ctrl[r, x0:x1 + 1].astype(int)).max(axis=1)
    best = cur = 0
    for ok in d <= 3:
        cur = cur + 1 if ok else 0
        best = max(best, cur)
    return best, x1 - x0 + 1, r


def gallery(poses: list[str], width: int, height: int, out: Path) -> int:
    out.mkdir(parents=True, exist_ok=True)
    status, thumbs = 0, []
    for p in poses:
        res = render_pose(p, width, height)
        Image.fromarray(res["img"]).save(out / f"{p}.png")
        issues = res["issues"]
        ns = res["ns"]
        line = f"{p} ({ns.station}): {res['words']} words, tag {'on' if ns.tag is not None else 'off'}, lint {len(issues)} issue(s)"
        print(line)
        for it in issues:
            print(f"    {it['rule']}: {it['msg']}")
        status |= int(bool(issues))
        thumbs.append((p, res["img"], f"{p}  {ns.station}  {res['words']} words  lint {len(issues)}"))
        if p == "P09":
            def hide(ns_):
                ns_.ruler.shown[:] = 0.0
                ns_.ruler.cond_level = 0.0
                ns_.ruler.paint()
            ctrl = render_pose(p, width, height, hide=hide)["img"]
            Image.fromarray(ctrl).save(out / "P09-control.png")
            run, span, r = dark_run(res["img"], ctrl)
            need = int(round(80 * height / 1080))
            ok = run >= need
            print(f"    dark run (3.6): {run} px of {span} px between the head's centre and the line's centre on row {r} "
                  f"are within 3 levels of the control; need {need} -> {'PASS' if ok else 'FAIL'}")
            status |= int(not ok)
    cols, tw = 3, 640
    font = _font(20)
    th = int(round(tw * height / width))
    cell_h = th + 32
    rows = (len(thumbs) + cols - 1) // cols
    sheet = Image.new("RGB", (cols * (tw + 12) + 12, rows * (cell_h + 12) + 12), (12, 14, 19))
    dr = ImageDraw.Draw(sheet)
    for i, (p, img, cap) in enumerate(thumbs):
        x, y = 12 + (i % cols) * (tw + 12), 12 + (i // cols) * (cell_h + 12)
        sheet.paste(_thumb(img, tw), (x, y + 30))
        dr.text((x, y + 4), cap, fill=(200, 204, 214), font=font)
    sheet.save(out / "sheet.png")
    print(f"wrote {out / 'sheet.png'}")
    return status


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("key", nargs="*", help="a scene key (S01 to S11), or pose names with --poses")
    ap.add_argument("-q", "--quality", choices=("draft", "review", "final"), default="draft")
    ap.add_argument("--poses", action="store_true", help="render pose stills, lint them and write a contact sheet")
    ap.add_argument("--size", default="1920x1080", help="pose still size for --poses (default 1920x1080)")
    ap.add_argument("--out", default=None, help="output folder for --poses (default BUILD/poses/<W>x<H>)")
    a = ap.parse_args()
    try:
        if a.poses:
            w, h = (int(x) for x in a.size.lower().split("x"))
            poses = [p.upper() for p in a.key] or world.POSES
            return gallery(poses, w, h, Path(a.out) if a.out else BUILD / "poses" / f"{w}x{h}")
        if len(a.key) != 1 or not a.key[0].upper().startswith("S"):
            ap.error("give one scene key (S01 to S11), or --poses")
        key = a.key[0].upper()
        if not 1 <= int(key[1:]) <= 11:
            ap.error("scene keys run from S01 to S11")
        return check_scene(key, a.quality)
    finally:
        shutil.rmtree(MEDIA, ignore_errors=True)


if __name__ == "__main__":
    sys.exit(main())
