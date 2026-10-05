"""kit: the shared style kit of the explainer film. One import surface for scene files:

    from kit import *        # Manim, the theme, type, fx, motion, shapes and the Narrated base class

The fonts are registered first, before anything can build a Text (a font that is registered later is listed by
Pango but not used). Two groups of Manim names are deliberately NOT what Manim exports:

    colour constants (BLUE, YELLOW, WHITE, ...)   removed: the film has one colour map, kit.theme, and a scene that
                                                   names another colour fails at once with a NameError
    Tex, MathTex, DecimalNumber, Integer, ...      replaced by stand-ins that say what to use: they need dvisvgm,
                                                   which is not installed (see NO_LATEX below)

How ``kit`` gets on sys.path (README.md, "Running a scene"):

    a scene file directly in explainer-video/     nothing to do: Manim puts the folder of the scene file on sys.path
    render.py                                     nothing to do: it sets PYTHONPATH
    a scene file in a sub-folder (scenes/), rendered on its own with the manim command:

        import sys; from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/
"""

import os as _os

from .type import register_fonts  # noqa: F401  (registers the fonts at import; must come before any Text)

import manim as _manim
from manim import *  # noqa: F401,F403,E402
import manim.utils.color.manim_colors as _mc  # noqa: E402

from . import fx, motion, paths, shapes, theme  # noqa: E402
from . import type as typekit  # noqa: E402
from .fx import *  # noqa: F401,F403,E402
from .motion import *  # noqa: F401,F403,E402
from .paths import BUILD, ROOT, VID  # noqa: E402
from .scene import *  # noqa: F401,F403,E402
from .shapes import *  # noqa: F401,F403,E402
from .theme import *  # noqa: F401,F403,E402
from .type import *  # noqa: F401,F403,E402
from . import scene as _scene  # noqa: E402

_MANIM_COLOURS = {n for n in vars(_mc) if n.isupper()} | {"AS2700", "BS381", "DVIPSNAMES", "SVGNAMES", "XKCD", "X11"}
for _name in _MANIM_COLOURS:
    globals().pop(_name, None)

# Manim classes that need dvisvgm (each one was tried on this machine: FileNotFoundError 'dvisvgm'), and the way out
NO_LATEX = {
    "Tex": "T() for words, tex() for a formula", "MathTex": "tex()", "SingleStringMathTex": "tex()",
    "DecimalNumber": "LiveNumber", "Integer": "LiveNumber", "Variable": "a T() label and a LiveNumber in a row()",
    "Title": "put(T(text, 'title'), -SAFE_X, TITLE_Y)", "BulletedList": "no lists on screen: one object, one label",
    "Matrix": "tex()", "DecimalMatrix": "tex()", "IntegerMatrix": "tex()", "MobjectMatrix": "tex()",
    "MathTable": "T() or tex() cells placed with row() and lines()", "DecimalTable": "T() cells placed with row() and lines()",
    "IntegerTable": "T() cells placed with row() and lines()", "BraceLabel": "Brace(...) and a T() label next to it",
}


class _NoLatex:
    """Stands in for a Manim class that cannot work here, so that a scene fails at the line that uses it."""

    def __init__(self, name: str, instead: str):
        self.name, self.instead = name, instead

    def __call__(self, *args, **kw):
        raise RuntimeError(f"kit: {self.name} needs dvisvgm, which is not installed on this machine. Use {self.instead}.")

    def __repr__(self) -> str:
        return f"<kit stand-in for manim.{self.name}: use {self.instead}>"


for _name, _instead in NO_LATEX.items():
    globals()[_name] = _NoLatex(_name, _instead)

__all__ = sorted(
    ({n for n in vars(_manim) if not n.startswith("_")} - _MANIM_COLOURS - {"type"})
    | set(theme.__all__) | set(typekit.__all__) | set(fx.__all__) | set(motion.__all__) | set(_scene.__all__) | set(shapes.__all__)
    | {"theme", "fx", "motion", "shapes", "typekit", "paths", "ROOT", "VID", "BUILD", "NO_LATEX"})

if _os.environ.get("EXPLAINER_CRF"):
    fx.set_encoder(int(_os.environ["EXPLAINER_CRF"]), _os.environ.get("EXPLAINER_PRESET", "veryfast"))
