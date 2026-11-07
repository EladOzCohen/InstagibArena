"""DM-Skyline: five rooftops at sunset joined by bridges. Fall off and you die.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_skyline.py" -unattended -nullrhi -nosplash
"""

import math
import os
import random
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Skyline")

concrete = m.material("MI_Concrete", (0.46, 0.46, 0.48))
concrete2 = m.material("MI_ConcreteWarm", (0.52, 0.45, 0.40))
concrete3 = m.material("MI_ConcreteCool", (0.38, 0.42, 0.50))
asphalt = m.material("MI_RoofDark", (0.18, 0.18, 0.20))
steel = m.material("MI_Steel", (0.55, 0.58, 0.62), 0.4)
accent = m.material("MI_NeonPink", (1.0, 0.1, 0.55), 0.3)
city = m.material("MI_CityDark", (0.12, 0.13, 0.18))

# (name, cx, cy, size_x, size_y, top_z, material)
roofs = [
    ("Center", 0, 0, 1500, 1500, 600, concrete),
    ("North", 0, 2100, 1700, 1400, 450, concrete2),
    ("South", 0, -2100, 1700, 1400, 450, concrete3),
    ("East", 2300, 0, 1300, 1500, 800, concrete3),
    ("West", -2300, 0, 1300, 1500, 300, concrete2),
]
DEPTH = 1500.0
for name, cx, cy, sx, sy, top, mat in roofs:
    m.box("Building_" + name, cx, cy, top - DEPTH / 2, sx, sy, DEPTH, mat=mat)
    # Dark roof surface and a thin glowing edge line.
    m.box("RoofSurface_" + name, cx, cy, top - 10, sx - 80, sy - 80, 20, mat=asphalt, solid=False)
    for ex, ey, ssx, ssy in [(0, sy / 2 - 20, sx, 40), (0, -sy / 2 + 20, sx, 40), (sx / 2 - 20, 0, 40, sy), (-sx / 2 + 20, 0, 40, sy)]:
        m.box("Edge_" + name, cx + ex, cy + ey, top + 5, ssx, ssy, 10, mat=accent, solid=False)

# ---------------------------------------------------------------- bridges
W = 420.0
for x in (-450, 450):
    m.slope("Bridge_CN", (x, 750, 600), (x, 1400, 450), W, mat=steel)
    m.slope("Bridge_CS", (x, -750, 600), (x, -1400, 450), W, mat=steel)
m.slope("Bridge_CE", (750, 0, 600), (1650, 0, 800), W, mat=steel)
m.slope("Bridge_CW", (-750, 0, 600), (-1650, 0, 300), W, mat=steel)
m.slope("Bridge_NE", (800, 1700, 450), (1900, 700, 800), 380, mat=steel)
m.slope("Bridge_SE", (800, -1700, 450), (1900, -700, 800), 380, mat=steel)
m.slope("Bridge_NW", (-800, 1700, 450), (-1900, 700, 300), 380, mat=steel)
m.slope("Bridge_SW", (-800, -1700, 450), (-1900, -700, 300), 380, mat=steel)

# ---------------------------------------------------------------- roof props (cover)
def roof_props(cx, cy, top, seed):
    rng = random.Random(seed)
    for i in range(3):
        x = cx + rng.uniform(-450, 450)
        y = cy + rng.uniform(-450, 450)
        m.box("AirCon", x, y, top + 90, 260, 200, 180, yaw=rng.uniform(0, 90), mat=steel)
    m.column("WaterTank", cx + rng.uniform(-350, 350), cy + rng.uniform(-350, 350), top, top + 420, 300, mat=concrete2)

for i, (name, cx, cy, sx, sy, top, mat) in enumerate(roofs):
    roof_props(cx, cy, top, 100 + i)
# A tall billboard frame on the center roof for line-of-sight breaking.
m.box("BillboardPost", 0, 0, 600 + 200, 80, 80, 400, mat=steel)
m.box("Billboard", 0, 0, 600 + 460, 700, 40, 220, mat=accent, solid=False)

# ---------------------------------------------------------------- city backdrop (no collision)
rng = random.Random(7)
for i in range(26):
    ang = i / 26.0 * 2 * math.pi + rng.uniform(-0.1, 0.1)
    dist = rng.uniform(5200, 7800)
    height = rng.uniform(1500, 4200)
    m.box("Backdrop_%d" % i, math.cos(ang) * dist, math.sin(ang) * dist, height / 2 - 1000,
          rng.uniform(600, 1300), rng.uniform(600, 1300), height + 2000, yaw=rng.uniform(0, 90), mat=city, solid=False)

# ---------------------------------------------------------------- spawns
starts = [(sx * 400.0, sy * 400.0, 600, math.degrees(math.atan2(-sy, -sx))) for sx in (-1, 1) for sy in (-1, 1)]
starts += [(0, 2300, 450, 270), (0, -2300, 450, 90), (2500, 0, 800, 180), (-2500, 0, 300, 0)]
m.starts(starts)

# ---------------------------------------------------------------- light: low sun
m.sky(sun_pitch=-24.0, sun_yaw=250.0, sun_intensity=3.5, sun_rgb=(1.0, 0.70, 0.48), sky_intensity=2.2)
m.finish(kill_z=-800)
