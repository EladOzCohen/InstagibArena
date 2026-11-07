"""DM-Temple: a sandstone ziggurat with a colonnade, four corner pavilions and a golden altar on top.

  UnrealEditor-Cmd.exe InstagibArena.uproject -ExecutePythonScript="Tools/make_map_temple.py" -unattended -nullrhi -nosplash
"""

import math
import os
import sys

import unreal

sys.path.insert(0, os.path.join(unreal.SystemLibrary.get_project_directory(), "Tools"))
from mapkit import MapBuilder

m = MapBuilder("/Game/Maps/DM-Temple")

sand = m.material("MI_Sand", (0.62, 0.50, 0.32))
stone = m.material("MI_TempleStone", (0.55, 0.45, 0.34))
dark = m.material("MI_DarkStone", (0.30, 0.24, 0.18))
pale = m.material("MI_PaleStone", (0.80, 0.72, 0.54))
gold = m.material("MI_Gold", (0.95, 0.62, 0.08), 0.3)
jade = m.material("MI_Jade", (0.08, 0.55, 0.38), 0.4)

HALF = 2300.0

# ---------------------------------------------------------------- shell
m.box("Floor", 0, 0, -50, HALF * 2 + 200, HALF * 2 + 200, 100, mat=sand)
T, H = 100.0, 1400.0
m.box("Wall_N", 0, HALF + T / 2, H / 2 - 50, HALF * 2 + 200, T, H + 100, mat=dark)
m.box("Wall_S", 0, -HALF - T / 2, H / 2 - 50, HALF * 2 + 200, T, H + 100, mat=dark)
m.box("Wall_E", HALF + T / 2, 0, H / 2 - 50, T, HALF * 2, H + 100, mat=dark)
m.box("Wall_W", -HALF - T / 2, 0, H / 2 - 50, T, HALF * 2, H + 100, mat=dark)
# Decorative band along the top of the walls.
for i, (x, y, sx, sy) in enumerate([(0, HALF - 60, HALF * 2, 40), (0, -HALF + 60, HALF * 2, 40),
                                    (HALF - 60, 0, 40, HALF * 2), (-HALF + 60, 0, 40, HALF * 2)]):
    m.box("WallBand_%d" % i, x, y, 900, sx, sy, 80, mat=gold, solid=False)

# ---------------------------------------------------------------- ziggurat
# (size, top height, stair run). Each tier is climbed by two 100 cm steps on every side.
tiers = [(2000.0, 200.0, 200.0), (1100.0, 400.0, 200.0), (500.0, 600.0, 140.0)]
prev_top = 0.0
for i, (size, top, run) in enumerate(tiers):
    mat = (stone, pale, pale)[i]
    m.box("Tier_%d" % i, 0, 0, top / 2.0, size, size, top, mat=mat)
    half = size / 2.0
    for yaw_out in (0, 90, 180, 270):
        ox, oy = math.cos(math.radians(yaw_out)), math.sin(math.radians(yaw_out))
        dist = half + 2 * run
        m.stairs("Stairs_%d_%d" % (i, yaw_out), ox * dist, oy * dist, prev_top,
                 yaw_out + 180, 380.0, 2, 100.0, run, mat=mat)
    prev_top = top

m.box("Altar", 0, 0, 640, 200, 200, 80, mat=gold)
for sx in (-1, 1):
    m.column("AltarPost", sx * 180, 0, 600, 760, 50, mat=jade)

# ---------------------------------------------------------------- corner pavilions
for sx in (-1, 1):
    for sy in (-1, 1):
        px, py = sx * 1650.0, sy * 1650.0
        m.box("Pavilion", px, py, 100, 800, 800, 200, mat=stone)
        # Stairs from the two sides that face the middle of the map.
        m.stairs("PavStairX", px - sx * (400 + 400), py, 0, 0 if sx > 0 else 180, 380.0, 2, 100.0, 200.0, mat=stone)
        m.stairs("PavStairY", px, py - sy * (400 + 400), 0, 90 if sy > 0 else 270, 380.0, 2, 100.0, 200.0, mat=stone)
        for cx in (-1, 1):
            for cy in (-1, 1):
                m.column("PavColumn", px + cx * 350, py + cy * 350, 200, 820, 120, mat=pale)
        m.box("PavRoof", px, py, 850, 880, 880, 60, mat=dark)
        m.box("PavJade", px, py, 215, 220, 220, 30, mat=jade)

# ---------------------------------------------------------------- colonnade
for i in range(-2, 3):
    m.column("ColumnN", i * 400.0, 1250, 0, 700, 160, mat=pale)
    m.column("ColumnS", i * 400.0, -1250, 0, 700, 160, mat=pale)
    m.column("ColumnE", 1250, i * 400.0, 0, 700, 160, mat=pale)
    m.column("ColumnW", -1250, i * 400.0, 0, 700, 160, mat=pale)

# Low walls that give cover without blocking movement completely.
for label, x, y, yaw in [("CoverE", 1750, 0, 90), ("CoverW", -1750, 0, 90), ("CoverN", 0, 1750, 0), ("CoverS", 0, -1750, 0)]:
    m.box(label, x, y, 65, 500, 120, 130, yaw=yaw, mat=dark)

# ---------------------------------------------------------------- spawns
spawns = [(sx * 1900.0, sy * 600.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
spawns += [(sx * 600.0, sy * 1900.0, 0) for sx in (-1, 1) for sy in (-1, 1)]
m.face_center_starts(spawns)

# ---------------------------------------------------------------- light
m.sky(sun_pitch=-42.0, sun_yaw=210.0, sun_intensity=3.5, sun_rgb=(1.0, 0.80, 0.58), sky_intensity=2.2)
m.finish(kill_z=-2000)
