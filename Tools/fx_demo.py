"""Builds the throwaway level /Game/Maps/_FXDemo: jump pads, flames, a fire barrel and a fire pit side by side, to look at effects.

    powershell -File Tools\\run_ue.ps1 -Script Tools\\fx_demo.py
    powershell -File Tools\\shots_b.ps1 -Map _FXDemo -Prefix fx -Views "pad=-380,-250,150,-18,35"
Delete the level afterwards (Content\\Maps\\_FXDemo.umap). IA_FX_LOOK selects the light look (default dusk).
"""

import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
import mapkit  # noqa: E402
import props  # noqa: E402,F401
import mapkit_fx  # noqa: E402,F401
from matlib import surface  # noqa: E402

b = mapkit.MapBuilder("/Game/Maps/_FXDemo")
b.look(os.environ.get("IA_FX_LOOK", "dusk"))
b.box("Floor", 0, 0, -10, 6000, 6000, 20, mat=surface("ConcreteDirty"))
b.box("Wall", 1800, 0, 300, 40, 3000, 600, mat=surface("ConcreteDirty"))
b.starts([(-2500, -2500, 0, 45)])

# jump pads (launch along +x, -y, +y diagonal)
b.jump_pad("PadA", 0, 0, 0, (1500, 0, 200), color=(0.0, 0.8, 1.0))
b.jump_pad("PadB", 600, -700, 0, (600, -1900, 0), color=(1.0, 0.45, 0.1))
b.jump_pad("PadC", 600, 700, 0, (1700, 1700, 100), color=(1.0, 0.2, 0.6))

# flames
b.flame("FlameBig", -500, 500, 0, scale=1.0)
b.flame("FlameSmall", -500, 800, 0, scale=0.55, embers=False)
b.flame("FlameHuge", -500, 1200, 0, scale=1.6)
b.flame("FlameBlue", -500, 100, 0, scale=1.0, colour=(0.2, 0.45, 1.0))
b.prop("Barrel", "barrel_fire", -900, -400, 0)
b.prop("Pit", "fire_pit", -900, -900, 0)
b.prop("BarrelRed", "barrel_red", -900, -150, 0)
b.finish()
