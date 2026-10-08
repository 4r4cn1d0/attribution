"""The scenes of the explainer film: one module per scene, ``sNN.py`` defining the Narrated class ``SNN``.

A scene module starts like this (the two path lines let ``manim`` render it on its own; render.py and
explainer.py do not need them):

    import sys; from pathlib import Path
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))     # the folder that holds kit/ and world.py
    from kit import *
    import world

    class S07(Narrated):
        def build(self):
            w = world.pose("P06", self)     # the closing pose of S06 is the first frame of S07
            ...                             # end in exactly world.pose("P07", ...)

``explainer.py`` imports every module of this package that exists; ``_pose_check.py SNN`` compares a rendered
scene's first and last frames with the stills of its two poses.
"""

KEYS = [f"S{i:02d}" for i in range(1, 12)]
